"""Teste de aceite do brief 020: `fabrica/revisao.py` e o comando `revisar`.

As fichas, os rascunhos, as extrações e as conferências de exemplo saem do fluxo de
verdade com os clientes falsos do teste de integração (ensaio `e01` e a rodada `r01`
de manifestações); as respostas digitadas são trocadas por uma função falsa.
"""

from __future__ import annotations

import datetime
import json
import shutil
from collections.abc import Iterator
from pathlib import Path

import pytest

from fabrica import revisao
from fabrica.comum.formatos import Amostras, Descartada, Gabarito, RespostasCartao, Rodadas
from fabrica.estado import RefPeca
from testes import test_integracao
from testes.test_integracao import (
    EMB,
    MAN,
    Integracao,
    checklist_que_reprova,
    preparar_e_abrir_ensaio,
)

PERGUNTA_PECA = "a peça pode virar modelo como está, na forma e no conteúdo"
PERGUNTA_DADO = "há algum nome, número ou dado que pareça real?"


def aprovar_ensaio(integ: Integracao) -> None:
    lidas = integ.arquivos.ler_json("saida/rodadas.json", Rodadas)
    agora = integ.relogio()
    novas = [
        r.model_copy(update={"ensaio_aprovado": True, "aprovado_em": agora}) for r in lidas.rodadas
    ]
    integ.arquivos.regravar_rodadas(Rodadas(rodadas=novas))


@pytest.fixture(scope="module")
def base_da_rodada(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """O fluxo roda uma vez por módulo; cada teste recebe uma cópia da pasta."""
    integ = Integracao(tmp_path_factory.mktemp("base"))
    preparar_e_abrir_ensaio(integ)
    integ.avancar_ate_parar()
    aprovar_ensaio(integ)
    # A primeira manifestação da r01 é reprovada na v1 e aprovada na v2.
    integ.api.especiais[("checklist", MAN)] = [checklist_que_reprova("pedidos")]
    assert integ.executar("fichas", "--tipo", MAN, "--semente", "3") == 0
    integ.avancar_ate_parar()
    return integ.raiz


@pytest.fixture
def rodada(base_da_rodada: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Integracao:
    copia = tmp_path / "repo"
    shutil.copytree(base_da_rodada, copia)
    monkeypatch.setattr(test_integracao, "montar_pasta", lambda _: copia)
    return Integracao(tmp_path)


class Teclado:
    """A função falsa de leitura: devolve as respostas na ordem e guarda as perguntas."""

    def __init__(self, respostas: list[str]) -> None:
        self.respostas: Iterator[str] = iter(respostas)
        self.perguntas: list[str] = []

    def __call__(self, pergunta: str) -> str:
        self.perguntas.append(pergunta)
        return next(self.respostas)


def revisar(integ: Integracao, *respostas: str) -> Teclado:
    teclado = Teclado(list(respostas))
    assert principal_revisar(integ, teclado) == 0
    return teclado


def principal_revisar(integ: Integracao, teclado: Teclado, *argumentos: str) -> int:
    from fabrica import __main__ as principal

    return principal.executar(["revisar", *argumentos], integ.servicos, teclado)


def peca(n: int, rodada: str = "r01", tipo: str = MAN) -> str:
    return f"{rodada}_{tipo}_{n:03d}"


def respostas(integ: Integracao, identificador: str) -> RespostasCartao:
    return integ.arquivos.ler_json(f"saida/cartoes/{identificador}_respostas.json", RespostasCartao)


def responder_ensaio(integ: Integracao) -> None:
    for _ in range(3):
        revisar(integ, "s", "n", "s")


# ---------------------------------------------------------------------------
# 1. Primeira etapa do cartão de revisão
# ---------------------------------------------------------------------------


def test_primeira_etapa_mostra_o_caso_e_esconde_o_veredito(rodada: Integracao) -> None:
    texto = revisao.cartao_revisao(RefPeca("r01", MAN, 2), rodada.servicos)
    rascunho = rodada.arquivos.ler_texto(f"saida/rascunhos/{peca(2)}_v1.md")
    assert rascunho in texto
    ficha = json.loads(rodada.arquivos.ler_texto(f"saida/fichas/{peca(2)}.json"))
    assert ficha["processo"]["identificador_ficticio"] in texto
    assert "Fatos e valores da extração" in texto and "Dispositivos citados" in texto
    assert "Citações resolvidas pelo programa" in texto
    assert PERGUNTA_PECA in texto and PERGUNTA_DADO in texto
    assert "veredito da fábrica" not in texto.lower()
    conferencia = json.loads(rodada.arquivos.ler_texto(f"saida/conferencias/{peca(2)}_v1.json"))
    assert conferencia["veredito"] not in texto.split("## Perguntas")[0].lower().split()
    # Nos embargos, a decisão fictícia com o trecho da âncora destacado.
    embargos = revisao.cartao_revisao(RefPeca("e01", EMB, 1), rodada.servicos)
    ficha_emb = json.loads(rodada.arquivos.ler_texto(f"saida/fichas/e01_{EMB}_001.json"))
    ancora = ficha_emb["defeito"]["ancora"]["trecho_literal"]
    assert f"**[[{ancora}]]**" in embargos
    assert ficha_emb["decisao_embargada"]["dispositivo"] in embargos


# ---------------------------------------------------------------------------
# 2 e 3. Correção antes de confirmar; respostas imutáveis; segunda etapa depois
# ---------------------------------------------------------------------------


def test_corrigir_antes_de_confirmar_e_nunca_depois(rodada: Integracao) -> None:
    responder_ensaio(rodada)
    alvo = peca(1)
    assert not rodada.existe(f"saida/cartoes/{alvo}_etapa2.md")
    # Responde, corrige a pergunta 2 (a peça) e confirma.
    teclado = revisar(rodada, "aprovada", "reprovada", "n", "", "2", "aprovada", "s")
    assert any("Confirmar" in p for p in teclado.perguntas)
    lidas = respostas(rodada, alvo)
    assert (lidas.veredito_ficha, lidas.veredito_peca, lidas.dado_real) == (
        "aprovada",
        "aprovada",
        False,
    )
    assert lidas.tipo_cartao == "revisao" and lidas.id_cartao == alvo
    assert rodada.existe(f"saida/cartoes/{alvo}_etapa1.md")
    # A segunda etapa só existe depois da confirmação.
    segunda = rodada.arquivos.ler_texto(f"saida/cartoes/{alvo}_etapa2.md")
    conferencia = json.loads(rodada.arquivos.ler_texto(f"saida/conferencias/{alvo}_v1.json"))
    assert "Veredito da fábrica" in segunda and conferencia["veredito"] in segunda
    assert "Categoria do motivo: conteudo" in segunda and "Alertas" in segunda
    assert "origem: haiku" in segunda  # o item que o checklist reprovou
    # Uma segunda gravação é recusada.
    with pytest.raises(Exception, match="já existe"):
        revisao.gravar_respostas(lidas, rodada.servicos)
    antes = rodada.arquivos.ler_texto(f"saida/cartoes/{alvo}_respostas.json")
    revisar(rodada, "aprovada", "aprovada", "n", "", "s")  # vai para a peça seguinte
    assert rodada.arquivos.ler_texto(f"saida/cartoes/{alvo}_respostas.json") == antes
    assert respostas(rodada, peca(2)).veredito_peca == "aprovada"


def test_resposta_invalida_e_perguntada_de_novo(rodada: Integracao) -> None:
    responder_ensaio(rodada)
    teclado = revisar(rodada, "talvez", "aprovada", "aprovada", "x", "s", "CPF 123", "", "s")
    lidas = respostas(rodada, peca(1))
    assert lidas.dado_real and lidas.dado_real_trecho == "CPF 123"
    assert sum("ficha" in p.lower() for p in teclado.perguntas) >= 2


# ---------------------------------------------------------------------------
# 4. Concordância e destino
# ---------------------------------------------------------------------------


def test_concordancia_nos_dois_sentidos_so_com_ficha_aprovada(rodada: Integracao) -> None:
    responder_ensaio(rodada)
    revisar(rodada, "aprovada", "aprovada", "n", "", "s")  # 001: fábrica reprovou a v1
    revisar(rodada, "aprovada", "reprovada", "n", "", "s")  # 002: fábrica aprovou
    revisar(rodada, "reprovada", "aprovada", "n", "", "s")  # 003: ficha reprovada
    revisar(rodada, "aprovada", "aprovada", "n", "", "s")  # 004: os dois aprovaram
    lidas = {n: revisao.concordancia(peca(n), rodada.servicos) for n in (1, 2, 3, 4)}
    assert lidas[1]["sentido"] == "so_o_responsavel_aprovou"
    assert lidas[2]["sentido"] == "so_a_fabrica_aprovou"
    assert lidas[3]["sentido"] is None  # fora das medidas
    assert lidas[4]["sentido"] == "concordam"
    assert [lidas[n]["destino"] for n in (1, 2, 3, 4)] == [
        "peca_boa",
        "peca_ruim",
        "fora_das_medidas",
        "peca_boa",
    ]
    assert lidas[1]["versao_final_da_fabrica"] == 2  # o destino final, à parte
    gravada = json.loads(rodada.arquivos.ler_texto(f"saida/cartoes/{peca(2)}_concordancia.json"))
    assert gravada == lidas[2]
    assert revisao.destino_das_respostas("reprovada", "reprovada") == "fora_das_medidas"


# ---------------------------------------------------------------------------
# 5. Cartão do ensaio
# ---------------------------------------------------------------------------


def test_cartao_do_ensaio_mostra_as_duas_etapas_e_pergunta_o_formato(rodada: Integracao) -> None:
    teclado = revisar(rodada, "n", "faltou o bloco de provas", "n", "s")
    primeiro = sorted(rodada.arquivos.listar("saida/cartoes", "e01_*_ensaio.md"))[0]
    texto = rodada.arquivos.ler_texto(primeiro)
    assert "Veredito da fábrica" in texto and PERGUNTA_DADO in texto
    assert "formato certo" in texto
    identificador = primeiro.removeprefix("saida/cartoes/").removesuffix("_ensaio.md")
    lidas = respostas(rodada, identificador)
    assert (lidas.tipo_cartao, lidas.formato_certo, lidas.formato_errado) == (
        "ensaio",
        False,
        "faltou o bloco de provas",
    )
    assert lidas.veredito_ficha is None and not lidas.dado_real
    assert any("formato certo" in p for p in teclado.perguntas)


# ---------------------------------------------------------------------------
# 6. Cartões das amostras
# ---------------------------------------------------------------------------


def gravar_amostras(integ: Integracao) -> tuple[str, str]:
    arquivos = integ.arquivos
    original = arquivos.ler_texto(f"saida/rascunhos/{peca(2)}_v1.md")
    aceita, descartada = f"{peca(2)}_erro2_1", f"{peca(2)}_erro3_1"
    arquivos.gravar_texto(f"saida/erros/{aceita}.md", original + "\nTrecho com o erro.\n")
    arquivos.gravar_texto(f"saida/erros/{descartada}.md", original + "\nOutro trecho.\n")
    arquivos.gravar_json(
        f"saida/erros/{aceita}_gabarito.json",
        Gabarito(
            copia=aceita,
            original=f"{peca(2)}_v1",
            origem="opus",
            tipo_erro="legitimidade",
            sutil=True,
            item_principal="legitimidade",
            itens_aceitos=["legitimidade"],
            criador="opus",
            verificador="sonnet",
            item_apontado_pelo_verificador="legitimidade",
            amostra=None,
        ),
    )
    arquivos.gravar_json(
        f"saida/erros/{descartada}_descartada.json",
        Descartada(
            copia=descartada,
            original=f"{peca(2)}_v1",
            tipo_erro="cabimento",
            sutil=False,
            criador="opus",
            conferencia_que_falhou="verificador",
            item_apontado_pelo_verificador=None,
            outro_problema=False,
            motivo="nao_viu_erro",
            amostra=None,
        ),
    )
    arquivos.gravar_json(
        revisao.caminho_amostras("r01"),
        Amostras(
            rodada="r01",
            copias=[aceita],
            descartadas=[descartada],
            sorteado_em=datetime.datetime(2026, 11, 21, tzinfo=datetime.UTC),
        ),
    )
    return aceita, descartada


def responder_revisoes(integ: Integracao) -> None:
    responder_ensaio(integ)
    for _ in range(10):
        revisar(integ, "aprovada", "aprovada", "n", "", "s")


def test_cartoes_das_amostras(rodada: Integracao) -> None:
    aceita, descartada = gravar_amostras(rodada)
    responder_revisoes(rodada)
    revisar(rodada, "s", "n", "s")  # amostra de 10 cópias: existe, não é o do gabarito
    copias = respostas(rodada, "r01_amostra_copias")
    assert copias.tipo_cartao == "amostra_copias"
    assert [(a.copia, a.erro_existe, a.erro_do_gabarito) for a in copias.amostra] == [
        (aceita, True, False)
    ]
    texto = rodada.arquivos.ler_texto("saida/cartoes/r01_amostra_copias.md")
    assert "Trecho com o erro." in texto and "legitimidade" in texto
    teclado = revisar(rodada, "n", "s")
    lidas = respostas(rodada, "r01_amostra_descartadas")
    assert [(a.copia, a.erro_existe, a.erro_do_gabarito) for a in lidas.amostra] == [
        (descartada, False, None)
    ]
    texto = rodada.arquivos.ler_texto("saida/cartoes/r01_amostra_descartadas.md")
    assert "Outro trecho." in texto and "cabimento" in texto
    # Sem mostrar o que o Sonnet respondeu.
    assert "nao_viu_erro" not in texto and "verificador" not in texto.lower()
    assert all("sonnet" not in p.lower() for p in teclado.perguntas)


# ---------------------------------------------------------------------------
# 7. Leitura de publicação
# ---------------------------------------------------------------------------


def test_leitura_de_publicacao_da_versao_refeita(rodada: Integracao) -> None:
    responder_revisoes(rodada)
    identificador = f"{peca(1)}_v2_leitura_publicacao"
    assert revisao.pendente(rodada.servicos) == ("leitura_publicacao", identificador)
    revisar(rodada, "aprovada", "n", "s")
    texto = rodada.arquivos.ler_texto(f"saida/cartoes/{identificador}.md")
    assert rodada.arquivos.ler_texto(f"saida/rascunhos/{peca(1)}_v2.md") in texto
    assert "Veredito da fábrica" in texto and PERGUNTA_DADO in texto  # não é às cegas
    lidas = respostas(rodada, identificador)
    assert (lidas.tipo_cartao, lidas.veredito_peca, lidas.dado_real) == (
        "leitura_publicacao",
        "aprovada",
        False,
    )
    assert revisao.pendente(rodada.servicos) is None


# ---------------------------------------------------------------------------
# 8. revisar --resumo
# ---------------------------------------------------------------------------


def test_resumo_lista_sem_mudar_nada(
    rodada: Integracao, capsys: pytest.CaptureFixture[str]
) -> None:
    responder_ensaio(rodada)
    revisar(rodada, "aprovada", "reprovada", "s", "um CPF", "", "s")
    capsys.readouterr()
    antes = sorted(rodada.arquivos.listar("saida", "**/*"))
    teclado = Teclado([])
    assert principal_revisar(rodada, teclado, "--resumo") == 0
    saida = capsys.readouterr().out
    assert peca(1) in saida and "reprovada" in saida and "um CPF" in saida
    assert "2026" in saida  # a data da confirmação
    assert sorted(rodada.arquivos.listar("saida", "**/*")) == antes
    assert teclado.perguntas == []


def test_ordem_dos_pendentes_e_sem_pendente(
    rodada: Integracao, capsys: pytest.CaptureFixture[str]
) -> None:
    assert revisao.pendente(rodada.servicos)[0] == "ensaio"  # type: ignore[index]
    responder_ensaio(rodada)
    assert revisao.pendente(rodada.servicos) == ("revisao", peca(1))
    # A revisão só aparece depois que a conferência da primeira versão terminou.
    assert all(rodada.existe(f"saida/conferencias/{peca(n)}_v1.json") for n in range(1, 11))
