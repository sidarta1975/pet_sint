"""Teste de aceite do brief 007: `fabrica/comum/modelo_local.py`, com falsos."""

from __future__ import annotations

import datetime
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from fabrica.comum import config
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import ParteDoPedido, Pedido, Resposta, RespostaLocal, esquema_resposta
from fabrica.comum.modelo_local import ModeloLocal
from fabrica.comum.registro import Registro

RAIZ = Path(__file__).resolve().parent.parent
INICIO = datetime.datetime(2026, 11, 21, 23, 0, tzinfo=datetime.UTC)
PECA = "e01_embargos_declaracao_001"
ETIQUETA = "gemma3:27b"
URL = "http://127.0.0.1:11434/api/chat"
COMANDO_PORTEIRO = ["porteiro", "cabe", ETIQUETA, "--porta", "11434", "--json"]
RESPOSTA_OK = {"itens": [{"item": "coerencia", "resposta": "passa", "trecho": "t"}]}


class Porteiro:
    """Falso do processo `porteiro`: devolve as saídas preparadas, em ordem."""

    def __init__(self, saidas: list[int | Exception]) -> None:
        self.saidas = list(saidas)
        self.comandos: list[list[str]] = []

    def __call__(self, comando: list[str]) -> int:
        self.comandos.append(list(comando))
        saida = self.saidas.pop(0)
        if isinstance(saida, Exception):
            raise saida
        return saida


class Ollama:
    """Falso do HTTP do Ollama."""

    def __init__(self, respostas: list[dict[str, Any] | Exception] | None = None) -> None:
        self.respostas = list(respostas or [])
        self.pedidos: list[tuple[str, dict[str, Any]]] = []

    def __call__(self, url: str, corpo: dict[str, Any]) -> dict[str, Any]:
        self.pedidos.append((url, corpo))
        resposta = self.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def resposta_ollama(conteudo: str, motivo: str = "stop") -> dict[str, Any]:
    return {
        "model": ETIQUETA,
        "message": {"role": "assistant", "content": conteudo},
        "done": True,
        "done_reason": motivo,
        "prompt_eval_count": 1200,
        "eval_count": 300,
    }


class Relogio:
    def __init__(self) -> None:
        self.agora = INICIO

    def __call__(self) -> datetime.datetime:
        self.agora += datetime.timedelta(seconds=2)
        return self.agora


def preparar(tmp_path: Path, etiqueta: str = ETIQUETA, digest: str = "sha256:abc") -> Path:
    (tmp_path / "config").mkdir()
    shutil.copy(RAIZ / "config/gasto.toml", tmp_path / "config/gasto.toml")
    texto = (RAIZ / "config/config.toml").read_text(encoding="utf-8")
    texto = texto.replace('etiqueta_completa = ""', f'etiqueta_completa = "{etiqueta}"', 1)
    texto = texto.replace('digest = ""', f'digest = "{digest}"', 1)
    (tmp_path / "config/config.toml").write_text(texto, encoding="utf-8")
    return tmp_path


class Ambiente:
    def __init__(self, raiz: Path, porteiro: Porteiro, ollama: Ollama) -> None:
        self.esperas: list[float] = []
        self.porteiro = porteiro
        self.ollama = ollama
        relogio = Relogio()
        self.arquivos = Arquivos(raiz, relogio=relogio)
        self.config = config.carregar(self.arquivos)
        self.registro = Registro(self.arquivos)
        self.local = ModeloLocal(
            self.config,
            self.arquivos,
            self.registro,
            executar=porteiro,
            enviar=ollama,
            relogio=relogio,
            dormir=self.esperas.append,
        )


def pedido(texto: str = "Confira a peça.", teto: int = 2000) -> Pedido:
    return Pedido(
        nome=f"{PECA}_v1_conferente_local_t1",
        servico="local",
        rodada="e01",
        peca=PECA,
        versao=1,
        tarefa="conferente_local",
        tentativa=1,
        modelo=ETIQUETA,
        esforco=None,
        teto_saida=teto,
        partes=[ParteDoPedido(nome="instrucoes", texto=texto)],
        formato="RespostaLocal",
        esquema=esquema_resposta(RespostaLocal),
        criado_em=INICIO,
    )


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    return preparar(tmp_path)


# 1 ------------------------------------------------------------------------


def test_porteiro_zero_rodou(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([0]), Ollama())
    resultado = amb.local.consultar_porteiro(ETIQUETA)
    assert (resultado.resultado, resultado.causa) == ("rodou", None)
    assert amb.esperas == []


def test_porteiro_um_espera_e_roda(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([1, 1, 1, 0]), Ollama())
    resultado = amb.local.consultar_porteiro(ETIQUETA)
    assert (resultado.resultado, resultado.causa) == ("esperou_e_rodou", None)
    assert amb.esperas == [60, 60, 60]


def test_porteiro_um_por_15_minutos_indisponivel(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([1] * 16), Ollama())
    resultado = amb.local.consultar_porteiro(ETIQUETA)
    assert (resultado.resultado, resultado.causa) == ("indisponivel", "porteiro")
    assert amb.esperas == [60] * 15
    assert sum(amb.esperas) == 15 * 60
    assert len(amb.porteiro.comandos) == 16


@pytest.mark.parametrize(
    "saida", [2, 3, 7, -9, FileNotFoundError("porteiro"), OSError("falhou"), RuntimeError("x")]
)
def test_porteiro_outras_saidas_indisponivel(raiz: Path, saida: int | Exception) -> None:
    amb = Ambiente(raiz, Porteiro([saida]), Ollama())
    resultado = amb.local.consultar_porteiro(ETIQUETA)
    assert (resultado.resultado, resultado.causa) == ("indisponivel", "porteiro")
    assert amb.esperas == []


def test_conferir_com_porteiro_indisponivel_nao_envia(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([2]), Ollama())
    resultado = amb.local.conferir(pedido())
    assert (resultado.resultado, resultado.causa) == ("indisponivel", "porteiro")
    assert amb.ollama.pedidos == []


# 2 ------------------------------------------------------------------------


def test_estimativa_pessimista(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([]), Ollama())
    assert amb.local.estimar_tokens("a" * 300, 100) == 200
    assert amb.local.estimar_tokens("a" * 301, 100) == 201  # arredonda para cima


def test_pedido_maior_que_o_contexto_nao_e_enviado(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([0]), Ollama())
    # 16384 de contexto: 3 * (16384 - 2000) + 3 caracteres dá 14385 + 2000 = 16385 tokens.
    texto = "a" * (3 * (16_384 - 2_000) + 3)
    resultado = amb.local.conferir(pedido(texto, teto=2_000))
    assert (resultado.resultado, resultado.causa) == ("indisponivel", "contexto")
    assert resultado.fracao_contexto == pytest.approx(16_385 / 16_384)
    assert amb.ollama.pedidos == []


def test_pedido_que_cabe_exatamente_e_enviado(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([0]), Ollama([resposta_ollama(json.dumps(RESPOSTA_OK))]))
    texto = "a" * (3 * (16_384 - 2_000))
    resultado = amb.local.conferir(pedido(texto, teto=2_000))
    assert resultado.resultado == "rodou"
    assert resultado.fracao_contexto == pytest.approx(1.0)


def test_fracao_do_contexto_informada(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([0]), Ollama([resposta_ollama(json.dumps(RESPOSTA_OK))]))
    texto = "a" * (3 * 10_288)  # 10288 + 2000 = 12288 = 75% de 16384
    resultado = amb.local.conferir(pedido(texto, teto=2_000))
    assert resultado.fracao_contexto == pytest.approx(0.75)


# 3 ------------------------------------------------------------------------


def test_num_ctx_explicito_e_esquema_no_formato(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([0]), Ollama([resposta_ollama(json.dumps(RESPOSTA_OK))]))
    resultado = amb.local.conferir(pedido())
    assert resultado.resultado == "rodou" and resultado.situacao == "ok"
    url, corpo = amb.ollama.pedidos[0]
    assert url == URL
    assert corpo["model"] == ETIQUETA
    assert corpo["options"]["num_ctx"] == 16_384
    assert corpo["options"]["num_predict"] == 2_000
    assert corpo["format"] == esquema_resposta(RespostaLocal)
    assert corpo["stream"] is False
    assert set(corpo) == {"model", "messages", "format", "options", "stream"}


def test_resposta_gravada_como_chegou(raiz: Path) -> None:
    conteudo = json.dumps(RESPOSTA_OK, indent=4) + "\n "
    amb = Ambiente(raiz, Porteiro([1, 0]), Ollama([resposta_ollama(conteudo)]))
    resultado = amb.local.conferir(pedido())
    assert resultado.resultado == "esperou_e_rodou"
    assert resultado.respostas == RespostaLocal.model_validate_json(conteudo)
    assert resultado.duracao_segundos > 0
    gravada = amb.arquivos.ler_json(f"saida/respostas/{PECA}_v1_conferente_local_t1.json", Resposta)
    assert gravada.conteudo == conteudo
    assert gravada.situacao == "ok"
    chamadas = amb.registro.chamadas()
    assert [(c.tarefa, c.custo_milionesimos) for c in chamadas] == [("conferente_local", 0)]


# 4 ------------------------------------------------------------------------


def test_encerrada_por_tamanho_e_fora_do_formato(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([0]), Ollama([resposta_ollama('{"itens": [', "length")]))
    resultado = amb.local.conferir(pedido())
    assert resultado.resultado == "rodou"
    assert resultado.situacao == "fora_do_formato"
    assert resultado.respostas is None


def test_fora_do_esquema_e_fora_do_formato(raiz: Path) -> None:
    ruim = json.dumps({"itens": [{"item": "estilo", "resposta": "passa", "trecho": "t"}]})
    amb = Ambiente(raiz, Porteiro([0]), Ollama([resposta_ollama(ruim)]))
    resultado = amb.local.conferir(pedido())
    assert resultado.situacao == "fora_do_formato"
    gravada = amb.arquivos.ler_json(f"saida/respostas/{PECA}_v1_conferente_local_t1.json", Resposta)
    assert gravada.conteudo == ruim


def test_falha_do_ollama_indisponivel(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([0]), Ollama([OSError("conexão recusada")]))
    resultado = amb.local.conferir(pedido())
    assert (resultado.resultado, resultado.causa) == ("indisponivel", "falha")


# 5 ------------------------------------------------------------------------


@pytest.mark.parametrize(("etiqueta", "digest"), [("", "sha256:abc"), (ETIQUETA, ""), ("", "")])
def test_sem_etiqueta_ou_digest_indisponivel_sem_chamar(
    tmp_path: Path, etiqueta: str, digest: str
) -> None:
    amb = Ambiente(preparar(tmp_path, etiqueta, digest), Porteiro([]), Ollama())
    resultado = amb.local.conferir(pedido())
    assert resultado.resultado == "indisponivel"
    assert amb.porteiro.comandos == [] and amb.ollama.pedidos == []


def test_configuracao_do_repositorio_esta_sem_etiqueta(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    for nome in ("config.toml", "gasto.toml"):
        shutil.copy(RAIZ / "config" / nome, tmp_path / "config" / nome)
    amb = Ambiente(tmp_path, Porteiro([]), Ollama())
    assert not amb.local.disponivel_na_configuracao()


# 6 ------------------------------------------------------------------------


def test_so_porteiro_cabe_e_conversa_no_127(raiz: Path) -> None:
    amb = Ambiente(
        raiz,
        Porteiro([1, 0, 0, 2]),
        Ollama([resposta_ollama(json.dumps(RESPOSTA_OK)), resposta_ollama("{", "length")]),
    )
    amb.local.conferir(pedido())
    amb.local.conferir(pedido().model_copy(update={"nome": f"{PECA}_v2_conferente_local_t1"}))
    amb.local.conferir(pedido().model_copy(update={"nome": f"{PECA}_v3_conferente_local_t1"}))
    assert amb.porteiro.comandos == [COMANDO_PORTEIRO] * 4
    assert {url for url, _ in amb.ollama.pedidos} == {URL}
    proibidas = {"serve", "run", "stop", "pull", "rm", "unload", "kill", "keep_alive"}
    for comando in amb.porteiro.comandos:
        assert not proibidas & set(comando)
    for _, corpo in amb.ollama.pedidos:
        assert "keep_alive" not in corpo


def test_pedido_que_nao_e_local_recusado(raiz: Path) -> None:
    amb = Ambiente(raiz, Porteiro([]), Ollama())
    with pytest.raises(ValueError):
        amb.local.conferir(pedido().model_copy(update={"servico": "claude"}))
