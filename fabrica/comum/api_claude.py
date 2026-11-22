"""Único arquivo que fala com a API da Claude, em dois passos (ARQUITETURA §7 e §7.1).

1. `gravar_pedido` monta o `Pedido` com modelo, esforço e teto da tarefa e o grava
   em `saida/pedidos/`. Não envia nada. É o que as etapas chamam.
2. `coletar`, chamado só por `estado.py`, conta os tokens, pede autorização ao
   gasto, envia, faz as novas tentativas, grava a resposta como chegou e registra
   a chamada.

O cliente do pacote `anthropic` chega pronto, por parâmetro; este módulo não lê
a chave. Nenhuma resposta é consertada: a validação contra o esquema só lê.
"""

from __future__ import annotations

import datetime
import time
from collections.abc import Callable, Mapping
from typing import Any, Protocol

import anthropic
from pydantic import BaseModel, ValidationError

from fabrica.comum.arquivos import Arquivos
from fabrica.comum.config import Config
from fabrica.comum.formatos import (
    MODELOS_RESPOSTA,
    Chamada,
    Ocorrencia,
    ParteDoPedido,
    Pedido,
    Resposta,
    Tokens,
    esquema_resposta,
)
from fabrica.comum.gasto import ControleGasto, Previsto
from fabrica.comum.registro import Registro

PEDIDOS = "saida/pedidos"
RESPOSTAS = "saida/respostas"
ORDEM_DAS_PARTES = ("instrucoes", "estrutura", "trecho", "ficha", "motivo", "conteudo")
TAREFAS_DE_REDACAO = frozenset({"redacao_risco_baixo", "redacao_risco_medio", "redacao_risco_alto"})
TENTATIVA_MAXIMA = 2  # t1 e t2; não existe t3
ERROS_PASSAGEIROS = (
    anthropic.APIConnectionError,
    anthropic.RateLimitError,
    anthropic.OverloadedError,
)
PARADA_RECUSA = "refusal"
PARADAS_CORTADA = frozenset({"max_tokens", "model_context_window_exceeded"})
SITUACOES_FORA_DO_FORMATO = frozenset({"fora_do_formato", "recusa", "cortada"})


class ErroApi(Exception):
    """Pedido mal montado ou erro da API que não se resolve com nova tentativa."""


class _Esgotado(Exception):
    """As novas tentativas acabaram."""


class ClienteClaude(Protocol):
    @property
    def messages(self) -> Any: ...


def _agora() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


def nome_do_pedido(peca: str, versao: int | None, tarefa: str, tentativa: int) -> str:
    """ADR 001, item 9: `<peça>_v<k>_<tarefa>_t<n>`; a ficha não leva `_v<k>`."""
    meio = f"_v{versao}" if versao is not None else ""
    return f"{peca}{meio}_{tarefa}_t{tentativa}"


def _descrever(erro: Exception) -> str:
    """Descrição do erro sem o texto da API (que nunca deve levar a chave a um arquivo)."""
    status = getattr(erro, "status_code", None)
    return f"{type(erro).__name__}" + (f" (situação {status})" if status else "")


class ApiClaude:
    def __init__(
        self,
        cliente: ClienteClaude,
        config: Config,
        arquivos: Arquivos,
        registro: Registro,
        gasto: ControleGasto,
        relogio: Callable[[], datetime.datetime] = _agora,
        dormir: Callable[[float], None] = time.sleep,
    ) -> None:
        self._cliente = cliente
        self._config = config
        self._arquivos = arquivos
        self._registro = registro
        self._gasto = gasto
        self._relogio = relogio
        self._dormir = dormir

    # --- passo 1: gravar ----------------------------------------------------

    def gravar_pedido(
        self,
        rodada: str,
        peca: str,
        versao: int | None,
        tarefa: str,
        partes: Mapping[str, str],
        modelo_resposta: type[BaseModel] | None,
    ) -> str:
        desconhecidas = set(partes) - set(ORDEM_DAS_PARTES)
        if desconhecidas:
            raise ErroApi(f"parte de pedido desconhecida: {', '.join(sorted(desconhecidas))}")
        if tarefa in TAREFAS_DE_REDACAO and modelo_resposta is not None:
            raise ErroApi(f"a redação ({tarefa}) não leva formato de resposta")
        if modelo_resposta is not None and modelo_resposta.__name__ not in MODELOS_RESPOSTA:
            raise ErroApi(f"modelo de resposta sem esquema registrado: {modelo_resposta.__name__}")
        configuracao = self._gasto.tarefa(tarefa)
        nome = nome_do_pedido(peca, versao, tarefa, 1)
        pedido = Pedido(
            nome=nome,
            servico="claude",
            rodada=rodada,
            peca=peca,
            versao=versao,
            tarefa=tarefa,  # type: ignore[arg-type]
            tentativa=1,
            modelo=self._gasto.modelo_da_tarefa(tarefa),
            esforco=configuracao.esforco,
            teto_saida=configuracao.teto_saida_tokens,
            partes=[
                ParteDoPedido(nome=parte, texto=partes[parte])  # type: ignore[arg-type]
                for parte in ORDEM_DAS_PARTES
                if parte in partes
            ],
            formato=modelo_resposta.__name__ if modelo_resposta else None,
            esquema=esquema_resposta(modelo_resposta) if modelo_resposta else None,
            criado_em=self._relogio(),
        )
        caminho = f"{PEDIDOS}/{nome}.json"
        self._arquivos.gravar_json(caminho, pedido)
        return caminho

    def gravar_pedido_igual(self, caminho_do_pedido: str) -> str:
        """Grava o `t2`, idêntico ao `t1`, para a resposta fora do formato."""
        pedido = self._arquivos.ler_json(caminho_do_pedido, Pedido)
        if pedido.tentativa >= TENTATIVA_MAXIMA:
            raise ErroApi(f"{pedido.nome}: não existe t3")
        tentativa = pedido.tentativa + 1
        nome = nome_do_pedido(pedido.peca, pedido.versao, pedido.tarefa, tentativa)
        novo = pedido.model_copy(
            update={"nome": nome, "tentativa": tentativa, "criado_em": self._relogio()}
        )
        caminho = f"{PEDIDOS}/{nome}.json"
        self._arquivos.gravar_json(caminho, novo)
        return caminho

    # --- montagem do envio ----------------------------------------------------

    @staticmethod
    def _mensagens(pedido: Pedido) -> list[dict[str, Any]]:
        blocos = [{"type": "text", "text": parte.texto} for parte in pedido.partes]
        return [{"role": "user", "content": blocos}]

    @staticmethod
    def _saida(pedido: Pedido) -> dict[str, Any]:
        saida: dict[str, Any] = {"effort": pedido.esforco}
        if pedido.esquema is not None:
            saida["format"] = {"type": "json_schema", "schema": pedido.esquema}
        return saida

    def _com_novas_tentativas(self, acao: Callable[[], Any]) -> Any:
        esperas = self._config.geral.api.esperas_novas_tentativas_segundos
        for numero in range(len(esperas) + 1):
            try:
                return acao()
            except ERROS_PASSAGEIROS as erro:
                if numero == len(esperas):
                    raise _Esgotado(_descrever(erro)) from None
                self._dormir(esperas[numero])
            except anthropic.APIError as erro:
                raise ErroApi(f"a API recusou o pedido: {_descrever(erro)}") from None
        raise AssertionError("inalcançável")

    def contar_tokens(self, pedido: Pedido) -> int:
        """Contador de tokens da API, que não cobra; mesmas novas tentativas do envio."""
        contagem = self._com_novas_tentativas(
            lambda: self._cliente.messages.count_tokens(
                model=pedido.modelo,
                messages=self._mensagens(pedido),
                output_config=self._saida(pedido),
            )
        )
        return int(contagem.input_tokens)

    # --- passo 2: coletar -----------------------------------------------------

    @staticmethod
    def fora_do_formato(situacao: str) -> bool:
        return situacao in SITUACOES_FORA_DO_FORMATO

    def _pausa(self, pedido: Pedido, detalhe: str) -> str:
        self._registro.ocorrencia(
            Ocorrencia(
                tipo="pausa",
                causa="api",
                inicio=self._relogio(),
                fim=None,
                peca=pedido.peca,
                rodada=pedido.rodada,
                detalhe=f"{pedido.nome}: novas tentativas esgotadas ({detalhe})",
            )
        )
        return "pausa"

    def coletar(self, caminho_do_pedido: str) -> str:
        """Devolve ok, fora_do_formato, recusa, cortada, pausa ou corte."""
        pedido = self._arquivos.ler_json(caminho_do_pedido, Pedido)
        caminho_resposta = f"{RESPOSTAS}/{pedido.nome}.json"
        if self._arquivos.existe(caminho_resposta):
            return self._arquivos.ler_json(caminho_resposta, Resposta).situacao
        if self._config.geral.api.modo_chamada != "uma_a_uma":
            raise ErroApi(f"modo de chamada fora do MVP: {self._config.geral.api.modo_chamada}")
        try:
            tokens_contados = self.contar_tokens(pedido)
        except _Esgotado as esgotado:
            return self._pausa(pedido, str(esgotado))
        previsto = Previsto(pedido.modelo, tokens_contados, pedido.teto_saida)
        # Modo uma a uma: nenhum pedido fica enviado e não coletado.
        decisao = self._gasto.autorizar(previsto, [], rodada=pedido.rodada, peca=pedido.peca)
        if not decisao.autorizado:
            return "corte"
        inicio = self._relogio()
        try:
            mensagem = self._com_novas_tentativas(
                lambda: self._cliente.messages.create(
                    model=pedido.modelo,
                    max_tokens=pedido.teto_saida,
                    messages=self._mensagens(pedido),
                    output_config=self._saida(pedido),
                )
            )
        except _Esgotado as esgotado:
            return self._pausa(pedido, str(esgotado))
        fim = self._relogio()
        resposta = self._resposta(pedido, mensagem, fim)
        self._arquivos.gravar_json(caminho_resposta, resposta)
        self._registro.chamada(
            Chamada(
                rodada=pedido.rodada,
                peca=pedido.peca,
                pedido=pedido.nome,
                tarefa=pedido.tarefa,
                modelo=pedido.modelo,
                tokens_entrada=resposta.tokens.entrada,
                tokens_cache=resposta.tokens.cache,
                tokens_raciocinio=resposta.tokens.raciocinio,
                tokens_saida=resposta.tokens.saida,
                custo_milionesimos=self._gasto.custo_real(pedido.modelo, resposta.tokens),
                duracao_segundos=(fim - inicio).total_seconds(),
                momento=fim,
            )
        )
        return resposta.situacao

    def _resposta(self, pedido: Pedido, mensagem: Any, recebida_em: datetime.datetime) -> Resposta:
        conteudo = "".join(
            bloco.text for bloco in mensagem.content if getattr(bloco, "type", "") == "text"
        )
        uso = mensagem.usage
        detalhes = getattr(uso, "output_tokens_details", None)
        tokens = Tokens(
            entrada=int(uso.input_tokens),
            cache=int(uso.cache_read_input_tokens or 0) + int(uso.cache_creation_input_tokens or 0),
            raciocinio=int(detalhes.thinking_tokens) if detalhes is not None else 0,
            saida=int(uso.output_tokens),
        )
        parada = mensagem.stop_reason
        return Resposta(
            pedido=pedido.nome,
            modelo=str(mensagem.model),
            conteudo=conteudo,
            bruto=mensagem.model_dump(mode="json"),
            motivo_parada=parada,
            tokens=tokens,
            situacao=self._situacao(pedido, conteudo, parada),
            recebida_em=recebida_em,
        )

    @staticmethod
    def _situacao(pedido: Pedido, conteudo: str, parada: str | None) -> Any:
        if parada == PARADA_RECUSA:
            return "recusa"
        if parada in PARADAS_CORTADA:
            return "cortada"
        if pedido.formato is not None:
            try:
                MODELOS_RESPOSTA[pedido.formato].model_validate_json(conteudo)
            except ValidationError:
                return "fora_do_formato"
        return "ok"
