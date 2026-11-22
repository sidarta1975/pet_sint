"""Único arquivo que fala com o Ollama e com o `porteiro` (ARQUITETURA §7.2 e §5.12.4).

Só informa o resultado (rodou, esperou e rodou, indisponível) e nunca decide o
destino da peça: não sabe a classe de risco nem a janela. Nunca inicia, para ou
descarrega o Ollama nem um modelo. O acesso ao processo e ao HTTP chega por
parâmetro, para que os testes os troquem por falsos.
"""

from __future__ import annotations

import datetime
import json
import math
import subprocess
import time
import urllib.request
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from fabrica.comum.arquivos import Arquivos
from fabrica.comum.config import Config
from fabrica.comum.formatos import (
    MODELOS_RESPOSTA,
    CausaIndisponivel,
    Chamada,
    Pedido,
    Resposta,
    RespostaLocal,
    ResultadoLocal,
    SituacaoResposta,
    Tokens,
)
from fabrica.comum.registro import Registro

ENDERECO = "127.0.0.1"
CAMINHO_CONVERSA = "/api/chat"
RESPOSTAS = "saida/respostas"
PORTEIRO_CABE = 0
PORTEIRO_ESPERE = 1
MOTIVO_TAMANHO = "length"

Executar = Callable[[Sequence[str]], int]
Enviar = Callable[[str, dict[str, Any]], dict[str, Any]]


def _executar_processo(comando: Sequence[str]) -> int:
    """Roda o `porteiro` e devolve o código de saída."""
    return subprocess.run(list(comando), capture_output=True, check=False).returncode


def _enviar_http(url: str, corpo: dict[str, Any]) -> dict[str, Any]:
    """POST no Ollama local, sem passar por proxy nenhum."""
    abridor = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    pedido = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with abridor.open(pedido) as resposta:
        dados: dict[str, Any] = json.loads(resposta.read().decode("utf-8"))
    return dados


def _agora() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


@dataclass(frozen=True)
class ResultadoPorteiro:
    resultado: ResultadoLocal
    causa: CausaIndisponivel | None


@dataclass(frozen=True)
class Resultado:
    """O que o módulo informa a quem chama (o conferente local, brief 017)."""

    resultado: ResultadoLocal
    causa: CausaIndisponivel | None
    situacao: SituacaoResposta | None
    respostas: RespostaLocal | None
    fracao_contexto: float
    duracao_segundos: float
    resposta: str | None  # caminho da resposta gravada, quando houve envio


class ModeloLocal:
    def __init__(
        self,
        config: Config,
        arquivos: Arquivos,
        registro: Registro,
        executar: Executar = _executar_processo,
        enviar: Enviar = _enviar_http,
        relogio: Callable[[], datetime.datetime] = _agora,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self._local = config.geral.modelo_local
        self._arquivos = arquivos
        self._registro = registro
        self._executar = executar
        self._enviar = enviar
        self._relogio = relogio
        self._dormir = dormir

    @property
    def etiqueta(self) -> str | None:
        return self._local.etiqueta_completa

    def disponivel_na_configuracao(self) -> bool:
        """Etiqueta ou digest vazios: máquina sem Ollama, vale a válvula de escape."""
        return bool(self._local.etiqueta_completa) and bool(self._local.digest)

    # --- porteiro -----------------------------------------------------------

    def _comando_porteiro(self, modelo: str) -> list[str]:
        return ["porteiro", "cabe", modelo, "--porta", str(self._local.porta), "--json"]

    def consultar_porteiro(self, modelo: str) -> ResultadoPorteiro:
        intervalo = self._local.porteiro_intervalo_segundos
        novas = (self._local.porteiro_espera_maxima_minutos * 60) // intervalo
        for tentativa in range(novas + 1):
            try:
                codigo = self._executar(self._comando_porteiro(modelo))
            except Exception:  # comando ausente ou com erro
                return ResultadoPorteiro("indisponivel", "porteiro")
            if codigo == PORTEIRO_CABE:
                return ResultadoPorteiro("rodou" if tentativa == 0 else "esperou_e_rodou", None)
            if codigo != PORTEIRO_ESPERE or tentativa == novas:
                return ResultadoPorteiro("indisponivel", "porteiro")
            self._dormir(intervalo)
        raise AssertionError("inalcançável")

    # --- contexto -----------------------------------------------------------

    def estimar_tokens(self, texto: str, teto_saida: int) -> int:
        """Estimativa pessimista: caracteres divididos por 3, para cima, mais o teto."""
        return math.ceil(len(texto) / self._local.divisor_caracteres_por_token) + teto_saida

    @staticmethod
    def _texto(pedido: Pedido) -> str:
        return "\n\n".join(parte.texto for parte in pedido.partes)

    # --- conferência ----------------------------------------------------------

    def conferir(self, pedido: Pedido) -> Resultado:
        if pedido.servico != "local":
            raise ValueError(f"{pedido.nome}: pedido não é do modelo local")
        texto = self._texto(pedido)
        estimativa = self.estimar_tokens(texto, pedido.teto_saida)
        fracao = estimativa / self._local.num_ctx
        etiqueta = self._local.etiqueta_completa
        if not self.disponivel_na_configuracao() or etiqueta is None:
            return Resultado("indisponivel", "falha", None, None, fracao, 0.0, None)
        porteiro = self.consultar_porteiro(etiqueta)
        if porteiro.resultado == "indisponivel":
            return Resultado("indisponivel", porteiro.causa, None, None, fracao, 0.0, None)
        if estimativa > self._local.num_ctx:
            return Resultado("indisponivel", "contexto", None, None, fracao, 0.0, None)
        corpo: dict[str, Any] = {
            "model": etiqueta,
            "messages": [{"role": "user", "content": texto}],
            "format": pedido.esquema,
            "options": {"num_ctx": self._local.num_ctx, "num_predict": pedido.teto_saida},
            "stream": False,
        }
        url = f"http://{ENDERECO}:{self._local.porta}{CAMINHO_CONVERSA}"
        inicio = self._relogio()
        try:
            bruto = self._enviar(url, corpo)
            conteudo = str(bruto["message"]["content"])
        except Exception:
            return Resultado("indisponivel", "falha", None, None, fracao, 0.0, None)
        fim = self._relogio()
        duracao = (fim - inicio).total_seconds()
        motivo = bruto.get("done_reason")
        situacao, respostas = self._situacao(pedido, conteudo, motivo)
        tokens = Tokens(
            entrada=int(bruto.get("prompt_eval_count") or 0),
            cache=0,
            raciocinio=0,
            saida=int(bruto.get("eval_count") or 0),
        )
        caminho = f"{RESPOSTAS}/{pedido.nome}.json"
        self._arquivos.gravar_json(
            caminho,
            Resposta(
                pedido=pedido.nome,
                modelo=etiqueta,
                conteudo=conteudo,
                bruto=bruto,
                motivo_parada=str(motivo) if motivo is not None else None,
                tokens=tokens,
                situacao=situacao,
                recebida_em=fim,
            ),
        )
        self._registro.chamada(
            Chamada(
                rodada=pedido.rodada,
                peca=pedido.peca,
                pedido=pedido.nome,
                tarefa="conferente_local",
                modelo=etiqueta,
                tokens_entrada=tokens.entrada,
                tokens_cache=0,
                tokens_raciocinio=0,
                tokens_saida=tokens.saida,
                custo_milionesimos=0,
                duracao_segundos=duracao,
                momento=fim,
            )
        )
        return Resultado(porteiro.resultado, None, situacao, respostas, fracao, duracao, caminho)

    @staticmethod
    def _situacao(
        pedido: Pedido, conteudo: str, motivo: object
    ) -> tuple[SituacaoResposta, RespostaLocal | None]:
        if motivo == MOTIVO_TAMANHO:
            return "fora_do_formato", None
        modelo = MODELOS_RESPOSTA.get(pedido.formato or "", RespostaLocal)
        try:
            lida = modelo.model_validate_json(conteudo)
        except ValidationError:
            return "fora_do_formato", None
        return "ok", lida if isinstance(lida, RespostaLocal) else None
