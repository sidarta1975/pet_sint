"""Teste de aceite do brief 006: `fabrica/comum/api_claude.py`, todo com cliente falso."""

from __future__ import annotations

import datetime
import json
import shutil
import socket
from collections.abc import Callable
from pathlib import Path
from typing import Any

import anthropic
import httpx2
import pytest

from fabrica.comum import config
from fabrica.comum.api_claude import ApiClaude, ErroApi
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import Extracao, Pedido, Resposta, RespostaChecklist, esquema_resposta
from fabrica.comum.gasto import ControleGasto
from fabrica.comum.registro import Registro

RAIZ = Path(__file__).resolve().parent.parent
CHAVE_FALSA = "sk-ant-chave-falsa-do-teste-0000"
INICIO = datetime.datetime(2026, 11, 21, 10, 0, tzinfo=datetime.UTC)
PECA = "e01_peticao_inicial_jec_001"
REQUISICAO = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")

EXTRACAO_OK = {
    "nomes": [],
    "documentos": [],
    "valores": [],
    "datas": [],
    "comarca": "Campinas",
    "juizo": "Juizado Especial Cível da Comarca de Campinas",
    "pedidos": [],
    "pecas_anteriores": [],
    "data_peca": "2026-06-10",
}


def mensagem(
    texto: str,
    parada: str = "end_turn",
    entrada: int = 100,
    saida: int = 50,
    modelo: str = "claude-haiku-5-5",
) -> anthropic.types.Message:
    return anthropic.types.Message.model_validate(
        {
            "id": "msg_falsa",
            "type": "message",
            "role": "assistant",
            "model": modelo,
            "content": [{"type": "text", "text": texto}],
            "stop_reason": parada,
            "stop_sequence": None,
            "usage": {"input_tokens": entrada, "output_tokens": saida},
        }
    )


def erro_rede() -> Exception:
    return anthropic.APIConnectionError(request=REQUISICAO)


def erro_limite() -> Exception:
    return anthropic.RateLimitError(
        "limite", response=httpx2.Response(429, request=REQUISICAO), body=None
    )


def erro_sobrecarga() -> Exception:
    return anthropic.OverloadedError(
        "sobrecarga", response=httpx2.Response(529, request=REQUISICAO), body=None
    )


class Mensagens:
    def __init__(self, cliente: ClienteFalso) -> None:
        self.cliente = cliente

    def create(self, **argumentos: Any) -> anthropic.types.Message:
        self.cliente.enviados.append(argumentos)
        if self.cliente.ao_enviar:
            self.cliente.ao_enviar()
        resposta = self.cliente.respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return resposta

    def count_tokens(self, **argumentos: Any) -> anthropic.types.MessageTokensCount:
        self.cliente.contagens.append(argumentos)
        if self.cliente.erros_contagem:
            raise self.cliente.erros_contagem.pop(0)
        return anthropic.types.MessageTokensCount(input_tokens=self.cliente.tokens_contados)


class ClienteFalso:
    """No lugar do pacote anthropic: guarda cada pedido e devolve respostas preparadas."""

    def __init__(self, respostas: list[Any] | None = None) -> None:
        self.api_key = CHAVE_FALSA
        self.respostas: list[Any] = list(respostas or [])
        self.erros_contagem: list[Exception] = []
        self.tokens_contados = 1_000
        self.enviados: list[dict[str, Any]] = []
        self.contagens: list[dict[str, Any]] = []
        self.ao_enviar: Callable[[], None] | None = None
        self.messages = Mensagens(self)


class Relogio:
    def __init__(self) -> None:
        self.agora = INICIO

    def __call__(self) -> datetime.datetime:
        self.agora += datetime.timedelta(seconds=1)
        return self.agora


class Ambiente:
    def __init__(self, raiz: Path, cliente: ClienteFalso) -> None:
        self.raiz = raiz
        self.cliente = cliente
        self.esperas: list[float] = []
        relogio = Relogio()
        self.arquivos = Arquivos(raiz, relogio=relogio)
        self.config = config.carregar(self.arquivos)
        self.registro = Registro(self.arquivos)
        self.gasto = ControleGasto(self.config, self.registro, relogio=relogio)
        self.api = ApiClaude(
            cliente,
            self.config,
            self.arquivos,
            self.registro,
            self.gasto,
            relogio=relogio,
            dormir=self.esperas.append,
        )

    def pedido_extracao(self) -> str:
        return self.api.gravar_pedido(
            rodada="e01",
            peca=PECA,
            versao=1,
            tarefa="extracao",
            partes={"instrucoes": "Extraia.", "conteudo": "Texto da peça."},
            modelo_resposta=Extracao,
        )

    def textos_gravados(self) -> str:
        return "\n".join(
            caminho.read_text(encoding="utf-8")
            for caminho in sorted((self.raiz / "saida").rglob("*"))
            if caminho.is_file()
        )


@pytest.fixture
def raiz(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    for nome in ("config.toml", "gasto.toml"):
        shutil.copy(RAIZ / "config" / nome, tmp_path / "config" / nome)
    return tmp_path


def ambiente(raiz: Path, respostas: list[Any] | None = None) -> Ambiente:
    return Ambiente(raiz, ClienteFalso(respostas))


# 1 ------------------------------------------------------------------------


def test_esforco_teto_e_formato_da_tarefa(raiz: Path) -> None:
    amb = ambiente(raiz, [mensagem(json.dumps(EXTRACAO_OK))])
    caminho = amb.pedido_extracao()
    assert amb.api.coletar(caminho) == "ok"
    enviado = amb.cliente.enviados[0]
    assert enviado["model"] == "claude-haiku-5-5"
    assert enviado["max_tokens"] == 8000
    assert enviado["output_config"] == {
        "effort": "low",
        "format": {"type": "json_schema", "schema": esquema_resposta(Extracao)},
    }


def test_redacao_nao_leva_formato(raiz: Path) -> None:
    amb = ambiente(raiz, [mensagem("# Petição", modelo="claude-sonnet-5-5")])
    caminho = amb.api.gravar_pedido(
        rodada="e01",
        peca=PECA,
        versao=1,
        tarefa="redacao_risco_alto",
        partes={"instrucoes": "Redija.", "ficha": "{}"},
        modelo_resposta=None,
    )
    assert amb.api.coletar(caminho) == "ok"
    enviado = amb.cliente.enviados[0]
    assert enviado["model"] == "claude-sonnet-5-5"
    assert enviado["max_tokens"] == 16000
    assert enviado["output_config"] == {"effort": "medium"}


def test_redacao_com_formato_e_recusada(raiz: Path) -> None:
    amb = ambiente(raiz)
    with pytest.raises(ErroApi):
        amb.api.gravar_pedido(
            rodada="e01",
            peca=PECA,
            versao=1,
            tarefa="redacao_risco_baixo",
            partes={"instrucoes": "Redija."},
            modelo_resposta=Extracao,
        )


# 2 ------------------------------------------------------------------------


def test_lista_exata_de_chaves_enviadas(raiz: Path) -> None:
    amb = ambiente(raiz, [mensagem(json.dumps(EXTRACAO_OK))])
    amb.api.coletar(amb.pedido_extracao())
    enviado = amb.cliente.enviados[0]
    assert set(enviado) == {"model", "max_tokens", "messages", "output_config"}
    assert set(enviado["output_config"]) == {"effort", "format"}
    assert [m["role"] for m in enviado["messages"]] == ["user"]
    assert set(amb.cliente.contagens[0]) == {"model", "messages", "output_config"}


# 3 ------------------------------------------------------------------------


def test_pedido_gravado_antes_do_envio(raiz: Path) -> None:
    amb = ambiente(raiz, [mensagem(json.dumps(EXTRACAO_OK))])
    caminho = amb.pedido_extracao()
    assert caminho == f"saida/pedidos/{PECA}_v1_extracao_t1.json"
    vistos: list[bool] = []
    amb.cliente.ao_enviar = lambda: vistos.append((raiz / caminho).is_file())
    amb.api.coletar(caminho)
    assert vistos == [True]
    pedido = amb.arquivos.ler_json(caminho, Pedido)
    assert pedido.tentativa == 1 and pedido.formato == "Extracao"


def test_gravar_pedido_nao_envia(raiz: Path) -> None:
    amb = ambiente(raiz)
    amb.pedido_extracao()
    assert amb.cliente.enviados == [] and amb.cliente.contagens == []


def test_ficha_sem_versao_no_nome(raiz: Path) -> None:
    amb = ambiente(raiz)
    caminho = amb.api.gravar_pedido(
        rodada="e01",
        peca=PECA,
        versao=None,
        tarefa="ficha",
        partes={"instrucoes": "Monte a ficha."},
        modelo_resposta=Extracao,
    )
    assert caminho == f"saida/pedidos/{PECA}_ficha_t1.json"


# 4 ------------------------------------------------------------------------


@pytest.mark.parametrize("erro", [erro_rede, erro_limite, erro_sobrecarga])
def test_novas_tentativas_e_depois_sucesso(raiz: Path, erro: Callable[[], Exception]) -> None:
    amb = ambiente(raiz, [erro(), erro(), mensagem(json.dumps(EXTRACAO_OK))])
    assert amb.api.coletar(amb.pedido_extracao()) == "ok"
    assert amb.esperas == [30, 120]
    assert len(amb.cliente.enviados) == 3


@pytest.mark.parametrize("erro", [erro_rede, erro_limite, erro_sobrecarga])
def test_tres_novas_tentativas_e_pausa(raiz: Path, erro: Callable[[], Exception]) -> None:
    amb = ambiente(raiz, [erro(), erro(), erro(), erro()])
    caminho = amb.pedido_extracao()
    assert amb.api.coletar(caminho) == "pausa"
    assert amb.esperas == [30, 120, 480]
    assert len(amb.cliente.enviados) == 4
    ocorrencias = amb.registro.ocorrencias()
    assert [(o.tipo, o.causa, o.peca) for o in ocorrencias] == [("pausa", "api", PECA)]
    assert not list((raiz / "saida").glob("respostas/*"))
    assert amb.registro.chamadas() == []


def test_erro_que_nao_e_de_rede_nao_repete(raiz: Path) -> None:
    ruim = anthropic.BadRequestError(
        "pedido ruim", response=httpx2.Response(400, request=REQUISICAO), body=None
    )
    amb = ambiente(raiz, [ruim])
    with pytest.raises(ErroApi):
        amb.api.coletar(amb.pedido_extracao())
    assert amb.esperas == []


# 5 ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("parada", "situacao"),
    [
        ("refusal", "recusa"),
        ("max_tokens", "cortada"),
        ("model_context_window_exceeded", "cortada"),
    ],
)
def test_recusa_e_cortada_gravadas_como_chegaram(raiz: Path, parada: str, situacao: str) -> None:
    texto = '{"nomes": [], "docum'
    amb = ambiente(raiz, [mensagem(texto, parada=parada)])
    caminho = amb.pedido_extracao()
    assert amb.api.coletar(caminho) == situacao
    assert amb.api.fora_do_formato(situacao)
    resposta = amb.arquivos.ler_json(f"saida/respostas/{PECA}_v1_extracao_t1.json", Resposta)
    assert resposta.conteudo == texto
    assert resposta.situacao == situacao
    assert resposta.motivo_parada == parada


def test_json_fora_do_esquema_e_fora_do_formato(raiz: Path) -> None:
    texto = json.dumps({**EXTRACAO_OK, "campo_inventado": 1})
    amb = ambiente(raiz, [mensagem(texto)])
    assert amb.api.coletar(amb.pedido_extracao()) == "fora_do_formato"
    resposta = amb.arquivos.ler_json(f"saida/respostas/{PECA}_v1_extracao_t1.json", Resposta)
    assert resposta.conteudo == texto


def test_t2_identico_e_sem_t3(raiz: Path) -> None:
    amb = ambiente(raiz)
    primeiro = amb.pedido_extracao()
    segundo = amb.api.gravar_pedido_igual(primeiro)
    assert segundo == f"saida/pedidos/{PECA}_v1_extracao_t2.json"
    p1 = amb.arquivos.ler_json(primeiro, Pedido)
    p2 = amb.arquivos.ler_json(segundo, Pedido)
    assert p2.tentativa == 2
    assert p1.model_dump(exclude={"nome", "tentativa", "criado_em"}) == p2.model_dump(
        exclude={"nome", "tentativa", "criado_em"}
    )
    with pytest.raises(ErroApi, match="t3"):
        amb.api.gravar_pedido_igual(segundo)


# 6 ------------------------------------------------------------------------


def test_resposta_sem_mudanca_e_chamada_registrada(raiz: Path) -> None:
    texto = json.dumps(EXTRACAO_OK, ensure_ascii=False, indent=3) + "\n\n  "
    amb = ambiente(raiz, [mensagem(texto, entrada=100_001, saida=10)])
    amb.cliente.tokens_contados = 100_001
    assert amb.api.coletar(amb.pedido_extracao()) == "ok"
    resposta = amb.arquivos.ler_json(f"saida/respostas/{PECA}_v1_extracao_t1.json", Resposta)
    assert resposta.conteudo == texto
    assert resposta.bruto is not None
    assert resposta.bruto["content"][0]["text"] == texto
    chamadas = amb.registro.chamadas()
    assert len(chamadas) == 1
    chamada = chamadas[0]
    assert chamada.tokens_entrada == 100_001 and chamada.tokens_saida == 10
    assert isinstance(chamada.custo_milionesimos, int)
    assert chamada.custo_milionesimos == 100_001 * 50 + 10 * 250
    assert chamada.pedido == f"{PECA}_v1_extracao_t1"


def test_coletar_de_novo_nao_reenvia(raiz: Path) -> None:
    amb = ambiente(raiz, [mensagem(json.dumps(EXTRACAO_OK))])
    caminho = amb.pedido_extracao()
    assert amb.api.coletar(caminho) == "ok"
    assert amb.api.coletar(caminho) == "ok"
    assert len(amb.cliente.enviados) == 1


# 7 ------------------------------------------------------------------------


def test_pedido_nao_autorizado_nao_e_enviado(raiz: Path) -> None:
    amb = ambiente(raiz)
    amb.cliente.tokens_contados = 300_000_000  # passa do corte de US$ 100 sozinho
    assert amb.api.coletar(amb.pedido_extracao()) == "corte"
    assert amb.cliente.enviados == []
    assert [o.causa for o in amb.registro.ocorrencias()] == ["corte_de_gasto"]


# 8 ------------------------------------------------------------------------


def test_partes_na_ordem_fixa(raiz: Path) -> None:
    amb = ambiente(
        raiz,
        [
            mensagem(
                '{"itens": [], "citacoes": [], "notas": '
                '{"clareza": 3, "concisao": 3, "linguagem_tecnica": 3}}'
            )
        ],
    )
    caminho = amb.api.gravar_pedido(
        rodada="e01",
        peca=PECA,
        versao=1,
        tarefa="checklist",
        partes={"ficha": "F", "conteudo": "C", "instrucoes": "I", "trecho": "T"},
        modelo_resposta=RespostaChecklist,
    )
    pedido = amb.arquivos.ler_json(caminho, Pedido)
    assert [parte.nome for parte in pedido.partes] == ["instrucoes", "trecho", "ficha", "conteudo"]
    amb.api.coletar(caminho)
    blocos = amb.cliente.enviados[0]["messages"][0]["content"]
    assert [bloco["text"] for bloco in blocos] == ["I", "T", "F", "C"]


def test_parte_desconhecida_recusada(raiz: Path) -> None:
    amb = ambiente(raiz)
    with pytest.raises(ErroApi):
        amb.api.gravar_pedido(
            rodada="e01",
            peca=PECA,
            versao=1,
            tarefa="extracao",
            partes={"sistema": "x"},
            modelo_resposta=Extracao,
        )


# 9 ------------------------------------------------------------------------


def test_chave_nao_aparece_em_arquivo_nem_em_erro(raiz: Path) -> None:
    ruim = anthropic.BadRequestError(
        f"pedido ruim {CHAVE_FALSA}", response=httpx2.Response(400, request=REQUISICAO), body=None
    )
    amb = ambiente(
        raiz,
        [
            mensagem(json.dumps(EXTRACAO_OK)),
            erro_rede(),
            erro_rede(),
            erro_rede(),
            erro_rede(),
            ruim,
        ],
    )
    amb.api.coletar(amb.pedido_extracao())
    segundo = amb.api.gravar_pedido(
        rodada="e01",
        peca=PECA,
        versao=2,
        tarefa="extracao",
        partes={"instrucoes": "Extraia."},
        modelo_resposta=Extracao,
    )
    amb.api.coletar(segundo)
    terceiro = amb.api.gravar_pedido(
        rodada="e01",
        peca=PECA,
        versao=3,
        tarefa="extracao",
        partes={"instrucoes": "Extraia."},
        modelo_resposta=Extracao,
    )
    with pytest.raises(ErroApi) as erro:
        amb.api.coletar(terceiro)
    assert CHAVE_FALSA not in str(erro.value)
    assert CHAVE_FALSA not in amb.textos_gravados()


# 10 -----------------------------------------------------------------------


def test_contar_tokens_com_novas_tentativas(raiz: Path) -> None:
    amb = ambiente(raiz, [mensagem(json.dumps(EXTRACAO_OK))])
    amb.cliente.erros_contagem = [erro_rede(), erro_limite()]
    assert amb.api.coletar(amb.pedido_extracao()) == "ok"
    assert amb.esperas == [30, 120]


def test_contar_tokens_esgotado_pausa_sem_enviar(raiz: Path) -> None:
    amb = ambiente(raiz)
    amb.cliente.erros_contagem = [erro_rede(), erro_limite(), erro_rede(), erro_limite()]
    assert amb.api.coletar(amb.pedido_extracao()) == "pausa"
    assert amb.esperas == [30, 120, 480]
    assert amb.cliente.enviados == []
    assert [o.tipo for o in amb.registro.ocorrencias()] == ["pausa"]


# 11 -----------------------------------------------------------------------


@pytest.mark.parametrize("endereco", [("127.0.0.1", 11434), ("api.anthropic.com", 443)])
def test_bloqueio_de_rede(endereco: tuple[str, int]) -> None:
    with pytest.raises(RuntimeError, match="teste tentou usar a rede"):
        socket.create_connection(endereco, timeout=1)
    conexao = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(RuntimeError, match="teste tentou usar a rede"):
            conexao.connect(("127.0.0.1", 11434))
    finally:
        conexao.close()


def test_bloqueio_vale_para_ipv6() -> None:
    # A máquina pode não ter IPv6; o bloqueio olha só a família do endereço.
    class SoqueteIpv6:
        family = socket.AF_INET6

    with pytest.raises(RuntimeError, match="teste tentou usar a rede"):
        socket.socket.connect(SoqueteIpv6(), ("::1", 11434))  # type: ignore[arg-type]


def test_canais_locais_continuam_livres() -> None:
    um, outro = socket.socketpair()
    try:
        um.sendall(b"ok")
        assert outro.recv(2) == b"ok"
    finally:
        um.close()
        outro.close()
