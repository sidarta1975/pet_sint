"""Teste de aceite do brief 015: a âncora do defeito dos embargos (ARQUITETURA, Anexo E).

As fichas de embargos de exemplo são escritas aqui. As palavras ignoradas são as
de `dados/conferencia/palavras_ignoradas.json` (aprovadas no brief 014).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fabrica import fichas
from fabrica.comum import config, normalizacao
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import ConfigAncora, Ficha, FichaEmbargos, PalavrasIgnoradas

RAIZ = Path(__file__).resolve().parent.parent
IGNORADAS = PalavrasIgnoradas.model_validate_json(
    (RAIZ / "dados/conferencia/palavras_ignoradas.json").read_text("utf-8")
)
ANCORA: ConfigAncora = config.carregar(Arquivos(RAIZ)).geral.ancora
LISTA = [*IGNORADAS.comuns, *IGNORADAS.juridicas]

FUNDAMENTACAO = (
    "Trata-se de ação de indenização por vício do produto. O aparelho apresentou "
    "defeito na tela e o fornecedor reparou o equipamento dentro do prazo legal. "
    "Não houve dano moral comprovado."
)
DISPOSITIVO = "Ante o exposto, julgo improcedentes os pedidos, nos termos do art. 487, I, do CPC."
A1 = (
    "O fornecedor descumpriu o prazo de trinta dias para sanar o vício, configurando "
    "a responsabilidade solidária."
)
A2 = "A ré afirma que o reparo foi concluído e entregue ao consumidor."
A3 = (
    "A autora requer a aplicação da multa cominatória pela demora na devolução do "
    "aparelho, com juros moratórios desde a citação."
)
TRECHO_A3 = (
    "multa cominatória pela demora na devolução do aparelho, com juros moratórios desde a citação"
)
MENCAO = "A autora pede multa cominatória pela demora na devolução, o que não altera a conclusão."


def endereco() -> dict[str, Any]:
    return {
        "rua": "Rua Fictícia dos Ipês Prateados",
        "numero": "10",
        "complemento": None,
        "bairro": "Vila Inventada Aurora",
        "cidade": "Campinas",
        "estado": "SP",
        "cep": "13000-100",
    }


def parte(id_: str, papel: str) -> dict[str, Any]:
    return {
        "id": id_,
        "papel": papel,
        "categoria": "pessoa_fisica",
        "nome": "Nome e Sobrenome da Parte Autora"
        if papel == "autor"
        else "Nome e Sobrenome da Parte Ré",
        "documento": "123.456.789-00",
        "estado_civil": "solteiro",
        "profissao": "professor",
        "endereco": endereco(),
        "email": f"{id_}@ficticio.example",
        "telefone": "(20) 90000-0000",
        "capaz": True,
        "preso": False,
    }


def ficha(
    defeito: str,
    ancora: dict[str, Any],
    mencao: str | None = None,
    fundamentacao: str = FUNDAMENTACAO,
    dispositivo: str = DISPOSITIVO,
) -> FichaEmbargos:
    dados = {
        "id": "e01_embargos_declaracao_001",
        "tipo": "Embargos de Declaração",
        "classe_risco": "alto",
        "casa_matriz": {
            "materia": "vicio_produto",
            "tese": "t",
            "polo": "autor",
            "complexidade": "media",
            "momento": "depois_da_decisao_embargada",
            "estilo": "detalhado",
        },
        "semente": 1,
        "processo": {
            "identificador_ficticio": "SINT-2026-000001",
            "numero_cnj": "0000000-00.2026.8.26.0000",
            "rito": "procedimento_comum",
            "comarca": "Campinas",
            "uf": "SP",
            "juizo": "1ª Vara Cível da Comarca de Campinas",
            "data_ajuizamento": "2026-02-02",
        },
        "partes": [parte("pa", "autor"), parte("pr", "reu")],
        "advogado": {
            "nome": "Nome e Sobrenome do Advogado",
            "oab": "OAB/UF nº 000.000",
            "email": "advogado@ficticio.example",
            "telefone": "(20) 90000-0001",
            "endereco_escritorio": endereco(),
            "representa": "pa",
        },
        "fatos": [
            {
                "data": "2025-10-01",
                "descricao": "A autora comprou um aparelho celular que apresentou defeito na tela.",
                "valores": [],
            }
        ],
        "valores": [],
        "provas": [],
        "valor_causa": None,
        "fundamentos": [],
        "momento_processual": {"fase": "f", "ultima_decisao": "sentença", "prazo": None},
        "pecas_anteriores": [],
        "data_peca": "2026-05-06",
        "local_peca": "Campinas",
        "pedidos": [
            {"id": "p1", "natureza": "acolhimento_embargos", "descricao": "d", "valor": None}
        ],
        "embargante": "pa",
        "decisao_embargada": {
            "tipo": "sentenca",
            "data": "2026-04-28",
            "data_intimacao": "2026-04-29",
            "juizo": "1ª Vara Cível da Comarca de Campinas",
            "relatorio": "Relatório.",
            "fundamentacao": fundamentacao,
            "dispositivo": dispositivo,
        },
        "argumentos_das_partes": [
            {"id": "a1", "parte": "pa", "peca_de_origem": "inicial", "texto": A1},
            {"id": "a2", "parte": "pr", "peca_de_origem": "contestacao", "texto": A2},
            {"id": "a3", "parte": "pa", "peca_de_origem": "replica", "texto": A3},
        ],
        "defeito": {
            "tipo": defeito,
            "ancora": ancora,
            "trecho_mencao": mencao,
            "descricao": "d",
            "efeito_modificativo": False,
        },
    }
    lida = Ficha.model_validate_json(json.dumps(dados)).root
    assert isinstance(lida, FichaEmbargos)
    return lida


def falhas(f: FichaEmbargos) -> list[str]:
    return [falha.codigo for falha in fichas.conferir_ancora(f, IGNORADAS, ANCORA)]


def no_argumento(trecho: str = TRECHO_A3, argumento: str = "a3") -> dict[str, Any]:
    return {"origem": "argumento", "argumento_id": argumento, "trecho_literal": trecho}


def na_decisao(trecho: str) -> dict[str, Any]:
    return {"origem": "decisao", "argumento_id": None, "trecho_literal": trecho}


# ---------------------------------------------------------------------------
# Termos principais (Anexo E.2)
# ---------------------------------------------------------------------------


def test_normalizacao_tira_acento_pontuacao_e_separadores_de_numero() -> None:
    assert normalizacao.normalizar_termos("Ação, R$ 1.621,00; ÚNICO!") == "acao r 162100 unico"


def test_termos_principais_do_trecho_da_omissao() -> None:
    contexto = ["A autora comprou um aparelho.", A1, A2]
    termos = normalizacao.termos_principais(TRECHO_A3, contexto, LISTA)
    # "pela", "na", "do", "com", "desde" e "a" são ignoradas; "aparelho" está nos fatos.
    assert termos == ["multa", "comina", "demora", "devolu", "juros", "morato", "citaca"]


def test_tamanho_minimo_exceto_numeros() -> None:
    termos = normalizacao.termos_principais("art 12 do mês de rua 2025 vela", [], LISTA)
    assert termos == ["12", "2025", "vela"]


def test_radical_junta_palavras_diferentes() -> None:
    # "contrato" e "contrário" viram o mesmo termo: o termo parece presente na decisão.
    assert normalizacao.radical("contrato") == normalizacao.radical("contrario") == "contra"
    termos = normalizacao.termos_principais("contrato", [], LISTA)
    assert normalizacao.presentes(termos, "decisão contrária ao pedido") == 1


def test_radical_separa_formas_da_mesma_palavra() -> None:
    # "omissão" e "omitido", "nulidade" e "nulo": o termo parece ausente na decisão.
    assert normalizacao.radical("omissao") != normalizacao.radical("omitido")
    assert normalizacao.radical("nulidade") != normalizacao.radical("nulo")
    termos = normalizacao.termos_principais("omissão e nulidade", [], LISTA)
    assert termos == ["omissa", "nulida"]
    assert normalizacao.presentes(termos, "o ponto foi omitido e o ato é nulo") == 0


def test_contexto_comum_sai() -> None:
    termos = normalizacao.termos_principais("prazo de trinta dias", [A1], LISTA)
    assert termos == []


# ---------------------------------------------------------------------------
# Contradição, obscuridade e erro material
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("defeito", ["contradicao", "obscuridade", "erro_material"])
def test_trecho_da_decisao_certo_passa(defeito: str) -> None:
    # Espaços a mais não contam (normalização de espaços).
    trecho = "o fornecedor  reparou o equipamento\ndentro do prazo legal"
    assert falhas(ficha(defeito, na_decisao(trecho))) == []
    assert falhas(ficha(defeito, na_decisao("julgo improcedentes os pedidos"))) == []


@pytest.mark.parametrize("defeito", ["contradicao", "obscuridade", "erro_material"])
def test_trecho_fora_da_decisao_recusa(defeito: str) -> None:
    assert falhas(ficha(defeito, na_decisao("o fornecedor não reparou nada"))) == [
        fichas.TRECHO_FORA_DA_DECISAO
    ]
    # O relatório não é fundamentação nem dispositivo.
    assert falhas(ficha(defeito, na_decisao("Relatório."))) == [fichas.TRECHO_FORA_DA_DECISAO]


# ---------------------------------------------------------------------------
# Omissão total
# ---------------------------------------------------------------------------


def test_omissao_total_certa_passa() -> None:
    assert falhas(ficha("omissao_total", no_argumento())) == []


def test_omissao_total_trecho_fora_do_argumento() -> None:
    assert falhas(ficha("omissao_total", no_argumento(argumento="a1"))) == [
        fichas.TRECHO_FORA_DO_ARGUMENTO
    ]
    assert falhas(ficha("omissao_total", no_argumento(argumento="a9"))) == [
        fichas.TRECHO_FORA_DO_ARGUMENTO
    ]


def test_omissao_total_menos_de_tres_termos_e_ancora_fraca() -> None:
    assert falhas(ficha("omissao_total", no_argumento("pela demora na devolução do aparelho"))) == [
        fichas.ANCORA_FRACA
    ]


def test_omissao_total_mais_de_vinte_por_cento_na_decisao() -> None:
    fundamentacao = FUNDAMENTACAO + " A multa cominatória e os juros moratórios não são devidos."
    f = ficha("omissao_total", no_argumento(), fundamentacao=fundamentacao)
    assert falhas(f) == [fichas.TERMOS_NA_DECISAO]


def test_omissao_total_com_um_termo_na_decisao_passa() -> None:
    # 7 termos: no máximo 1 (20%, arredondado para baixo).
    f = ficha("omissao_total", no_argumento(), dispositivo=DISPOSITIVO + " Sem multa.")
    assert falhas(f) == []


def test_corte_que_junta_palavras_descarta_a_ficha() -> None:
    argumento = "contrato firmado com cláusula penal abusiva"
    f = ficha("omissao_total", no_argumento(argumento, "a3"))
    # O trecho não está no argumento a3; troca o texto do argumento pelo trecho.
    dados = f.model_dump(mode="json")
    dados["argumentos_das_partes"][2]["texto"] = argumento
    dados["decisao_embargada"]["fundamentacao"] += " Entendimento contrário, firmado e penal."
    junta = FichaEmbargos.model_validate_json(json.dumps(dados))
    assert falhas(junta) == [fichas.TERMOS_NA_DECISAO]


def test_corte_que_separa_formas_deixa_passar() -> None:
    # Limite declarado: a decisão enfrentou com "omitido" e "nulo"; o programa não vê.
    argumento = "omissão da nulidade contratual alegada tempestivamente pela consumidora"
    dados = ficha("omissao_total", no_argumento(argumento)).model_dump(mode="json")
    dados["argumentos_das_partes"][2]["texto"] = argumento
    dados["decisao_embargada"]["fundamentacao"] += " Nada foi omitido; o ato não é nulo."
    separa = FichaEmbargos.model_validate_json(json.dumps(dados))
    assert falhas(separa) == []


# ---------------------------------------------------------------------------
# Omissão parcial
# ---------------------------------------------------------------------------


def parcial(mencao: str | None = MENCAO, fundamentacao: str | None = None) -> FichaEmbargos:
    texto = fundamentacao if fundamentacao is not None else f"{FUNDAMENTACAO} {MENCAO}"
    return ficha("omissao_parcial", no_argumento(), mencao=mencao, fundamentacao=texto)


def test_omissao_parcial_certa_passa() -> None:
    assert falhas(parcial()) == []


def test_omissao_parcial_mencao_fora_da_decisao() -> None:
    assert falhas(parcial(mencao="A autora fala de multa cominatória, demora e devolução.")) == [
        fichas.MENCAO_FORA_DA_DECISAO
    ]


def test_omissao_parcial_mencao_com_mais_de_quarenta_palavras() -> None:
    longa = (
        "A autora pede multa cominatória pela demora na devolução, "
        + "e insiste " * 20
        + "no tema."
    )
    assert len(longa.split()) > 40
    f = parcial(mencao=longa, fundamentacao=f"{FUNDAMENTACAO} {longa}")
    assert falhas(f) == [fichas.MENCAO_LONGA]


def test_omissao_parcial_menos_da_metade_dos_termos_na_mencao() -> None:
    curta = "A autora pede multa pela demora, o que não altera a conclusão."
    f = parcial(mencao=curta, fundamentacao=f"{FUNDAMENTACAO} {curta}")
    assert falhas(f) == [fichas.POUCOS_TERMOS_NA_MENCAO]


def test_omissao_parcial_mais_de_vinte_por_cento_fora_da_mencao() -> None:
    texto = f"{FUNDAMENTACAO} {MENCAO} Os juros moratórios e a citação seguem a regra geral."
    assert falhas(parcial(fundamentacao=texto)) == [fichas.TERMOS_FORA_DA_MENCAO]


def test_omissao_parcial_sem_mencao_recusa() -> None:
    assert falhas(parcial(mencao=None)) == [fichas.MENCAO_FORA_DA_DECISAO]


def test_omissao_parcial_ancora_fraca() -> None:
    f = ficha(
        "omissao_parcial",
        no_argumento("pela demora na devolução do aparelho"),
        mencao=MENCAO,
        fundamentacao=f"{FUNDAMENTACAO} {MENCAO}",
    )
    assert falhas(f) == [fichas.ANCORA_FRACA]
