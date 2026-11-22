"""Teste de aceite do brief 013: `fabrica/conferencia/citacoes.py`.

As 50 formas de `testes/dados/citacoes_50.json` são resolvidas em 100%, cada uma
exatamente na lista esperada, na ordem. A tabela de exemplo é escrita aqui.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from fabrica.comum.formatos import Diploma, TabelaNormas
from fabrica.conferencia import citacoes

RAIZ = Path(__file__).resolve().parent.parent
DADOS = json.loads((RAIZ / "testes/dados/citacoes_50.json").read_text("utf-8"))
DIPLOMAS = [Diploma.model_validate(d) for d in DADOS["diplomas"]]
CASOS = DADOS["casos"]


def chaves(texto: str) -> list[dict[str, Any]]:
    leitura = citacoes.ler(texto, DIPLOMAS)
    return [
        {
            "diploma": c.diploma,
            "artigo": c.artigo,
            "paragrafo": c.paragrafo,
            "inciso": c.inciso,
            "alinea": c.alinea,
        }
        for c in leitura.resolvidas
    ]


def test_cinquenta_formas_na_contagem_certa() -> None:
    assert DADOS["versao"] == "2026-11-21-v2"
    assert len(CASOS) == 50
    assert Counter(c["forma"] for c in CASOS) == {
        "simples": 14,
        "parte_do_artigo": 15,
        "multipla": 9,
        "intervalo": 5,
        "eliptica": 7,
    }


@pytest.mark.parametrize("caso", CASOS, ids=[f"{c['id']:02d}_{c['forma']}" for c in CASOS])
def test_forma_resolvida(caso: dict[str, Any]) -> None:
    leitura = citacoes.ler(caso["texto"], DIPLOMAS)
    assert chaves(caso["texto"]) == caso["esperado"]
    assert leitura.nao_resolvidas == ()
    for c in leitura.resolvidas:
        assert caso["texto"][c.posicao : c.posicao + len(c.trecho)] == c.trecho
        assert c.trecho


def test_cem_por_cento_das_cinquenta() -> None:
    certas = sum(chaves(c["texto"]) == c["esperado"] for c in CASOS)
    assert certas == 50


def test_formas_juntas_num_texto_so_mantem_a_ordem() -> None:
    texto = " ".join(c["texto"] + "." for c in CASOS[:20])
    esperado = [item for c in CASOS[:20] for item in c["esperado"]]
    assert chaves(texto) == esperado


# ---------------------------------------------------------------------------
# Conferência contra uma tabela de exemplo
# ---------------------------------------------------------------------------


def dispositivo(id_: str, diploma: str, artigo: str, paragrafo: str) -> dict[str, Any]:
    return {
        "id": id_,
        "diploma": diploma,
        "artigo": artigo,
        "paragrafo": paragrafo,
        "assunto": "a",
        "funcao": "requisito",
        "texto_vigente": "Texto.",
        "tipos": ["embargos_declaracao"],
        "fonte": "exemplo",
        "data_conferencia": "2026-11-21",
    }


TABELA = TabelaNormas.model_validate_json(
    json.dumps(
        {
            "versao": "exemplo",
            "diplomas": DADOS["diplomas"],
            "dispositivos": [
                dispositivo("cpc_319", "cpc", "319", "caput"),
                dispositivo("cpc_1022", "cpc", "1.022", "caput"),
                dispositivo("cpc_1022_pu", "cpc", "1.022", "parágrafo único"),
                dispositivo("cpc_489_p1", "cpc", "489", "§ 1º"),
                dispositivo("cdc_6", "cdc", "6º", "caput"),
            ],
        }
    )
)


def test_citacao_na_tabela_passa() -> None:
    texto = (
        "Nos termos do art. 319 do CPC e do art. 6º, VIII, do CDC; omissão do "
        "art. 1.022, parágrafo único, II, do CPC e do art. 489, § 1º, IV, do CPC."
    )
    r = citacoes.conferir(texto, TABELA)
    assert (r.item.item, r.item.resposta, r.item.quem) == (
        "citacao_fora_da_tabela",
        "passa",
        "programa",
    )
    assert len(r.resolvidas) == 4 and r.nao_resolvidas == ()
    assert r.alertas == [] and r.perguntas == []


def test_citacao_fora_da_tabela_reprova() -> None:
    r = citacoes.conferir("prazo do art. 1.023 do CPC e do art. 489, § 3º, do CPC", TABELA)
    assert r.item.resposta == "nao_passa"
    assert [d.extraido for d in r.item.divergencias] == [
        "art. 1.023 do CPC",
        "art. 489, § 3º, do CPC",
    ]
    # Inciso e alínea não mudam o resultado: a conferência é de artigo e parágrafo.
    assert citacoes.conferir("art. 319, III, do CPC", TABELA).item.resposta == "passa"


def test_artigo_sem_diploma_vira_alerta_e_pergunta() -> None:
    texto = "Conforme o art. 5º, a parte tem direito ao pedido."
    r = citacoes.conferir(texto, TABELA)
    assert r.item.resposta == "passa"  # não reprova sozinha
    assert r.resolvidas == ()
    assert [n.trecho for n in r.nao_resolvidas] == ["art. 5º"]
    assert texto[r.nao_resolvidas[0].posicao :].startswith("art. 5º")
    assert len(r.alertas) == 1 and r.alertas[0].item == "citacao_fora_da_tabela"
    assert len(r.perguntas) == 1 and "art. 5º" in r.perguntas[0]


def test_eliptica_sem_citacao_anterior_vira_nao_resolvida() -> None:
    r = citacoes.conferir("Nos termos do art. 10 do mesmo diploma, requer.", TABELA)
    assert r.resolvidas == () and len(r.nao_resolvidas) == 1
    r = citacoes.conferir("O § 2º do mesmo artigo trata do tema.", TABELA)
    assert r.resolvidas == () and len(r.nao_resolvidas) == 1
    assert r.item.resposta == "passa"


def test_outras_formas_nao_resolvidas() -> None:
    # Artigo por extenso e diploma revogado (CPC/73) não são adivinhados.
    for texto in (
        "conforme o artigo quinto do CPC",
        "art. 5º do CPC/73",
        "cf. art. 5º, conforme a doutrina",
    ):
        r = citacoes.conferir(texto, TABELA)
        assert r.resolvidas == () and len(r.nao_resolvidas) == 1, texto
    # Menção ao artigo sem número não é citação.
    assert citacoes.ler("o artigo citado acima", DIPLOMAS).nao_resolvidas == ()


def test_lista_para_o_cartao_sai_completa_e_em_ordem() -> None:
    texto = "arts. 319 a 321 do CPC; art. 6º do CDC."
    r = citacoes.conferir(texto, TABELA)
    assert [(c.diploma, c.artigo) for c in r.resolvidas] == [
        ("cpc", "319"),
        ("cpc", "320"),
        ("cpc", "321"),
        ("cdc", "6"),
    ]
    assert r.item.resposta == "nao_passa"  # 320 e 321 não estão na tabela de exemplo
    assert len(r.item.divergencias) == 2


def test_aceita_a_tabela_inteira_ou_so_os_diplomas() -> None:
    assert (
        citacoes.ler("art. 319 do CPC", TABELA).resolvidas
        == citacoes.ler("art. 319 do CPC", DIPLOMAS).resolvidas
    )
