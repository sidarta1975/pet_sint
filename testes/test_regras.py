"""Teste de aceite do brief 012: itens de programa de `fabrica/conferencia/regras.py`.

Peças, extrações, fichas, estrutura e termos de exemplo escritos aqui.
"""

from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any

import pytest

from fabrica.comum import config, normalizacao
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import (
    Bloco,
    Configuracao,
    EstruturaMontada,
    Extracao,
    Ficha,
    FichaInicial,
    Perfil,
    TermosInequivocos,
    ValorExtraido,
)
from fabrica.conferencia import regras

RAIZ = Path(__file__).resolve().parent.parent
D = datetime.date
MARCA = "DOCUMENTO SINTÉTICO — FICTÍCIO"
FERIADOS = [D(2026, 11, 20), D(2026, 12, 25)]


def configuracao() -> Configuracao:
    return config.carregar(Arquivos(RAIZ)).geral


# ---------------------------------------------------------------------------
# Estrutura
# ---------------------------------------------------------------------------


def estrutura() -> EstruturaMontada:
    def b(nome: str, titulo: str, ordem: int, obrigatorio: bool = True) -> Bloco:
        return Bloco(nome=nome, titulo=titulo, ordem=ordem, obrigatorio=obrigatorio, descricao="d")

    return EstruturaMontada(
        tipo="peticao_inicial_jec",
        familia="peticao_inicial",
        perfil="juizado_especial_civel",
        blocos=[
            b("enderecamento", "Endereçamento", 10),
            b("fatos", "Dos Fatos", 20),
            b("tentativa_previa", "Da Tentativa Prévia", 25, obrigatorio=False),
            b("pedidos", "Dos Pedidos", 30),
            b("valor_causa", "Do Valor da Causa", 40),
        ],
        pedidos_acessorios_padrao=[],
    )


def rascunho(*titulos: str) -> str:
    corpo = "\n\n".join(f"## {t}\n\nTexto do bloco {t}." for t in titulos)
    return f"{MARCA}\n\n{corpo}\n"


COMPLETO = ("Endereçamento", "Dos Fatos", "Da Tentativa Prévia", "Dos Pedidos", "Do Valor da Causa")


def test_estrutura_completa_passa() -> None:
    r = regras.estrutura(rascunho(*COMPLETO), estrutura())
    assert (r.item, r.resposta, r.quem) == ("estrutura", "passa", "programa")
    # O bloco opcional pode faltar; o título é comparado sem diferença de maiúsculas e acentos.
    r = regras.estrutura(
        rascunho("ENDERECAMENTO", "dos fatos", "Dos Pedidos", "Do Valor da Causa"), estrutura()
    )
    assert r.resposta == "passa"


def test_estrutura_com_bloco_obrigatorio_faltando_reprova() -> None:
    r = regras.estrutura(rascunho("Endereçamento", "Dos Fatos", "Do Valor da Causa"), estrutura())
    assert r.resposta == "nao_passa"
    assert "Dos Pedidos" in r.trecho


def test_estrutura_fora_de_ordem_reprova() -> None:
    r = regras.estrutura(
        rascunho("Endereçamento", "Dos Pedidos", "Dos Fatos", "Do Valor da Causa"), estrutura()
    )
    assert r.resposta == "nao_passa"
    assert "ordem" in r.trecho
    # O título de terceiro nível não conta como bloco.
    texto = rascunho("Endereçamento", "Dos Fatos", "Do Valor da Causa").replace(
        "## Dos Fatos", "## Dos Fatos\n\n### Dos Pedidos"
    )
    assert regras.estrutura(texto, estrutura()).resposta == "nao_passa"


# ---------------------------------------------------------------------------
# Fichas de exemplo
# ---------------------------------------------------------------------------


def endereco() -> dict[str, Any]:
    return {
        "rua": "Rua Inventada",
        "numero": "1",
        "complemento": None,
        "bairro": "Bairro",
        "cidade": "Campinas",
        "estado": "SP",
        "cep": "13010-111",
    }


def ficha(prazo: dict[str, Any] | None = None) -> FichaInicial:
    def parte(id_: str, papel: str, categoria: str) -> dict[str, Any]:
        pf = categoria == "pessoa_fisica"
        return {
            "id": id_,
            "papel": papel,
            "categoria": categoria,
            "nome": "Nome",
            "documento": "000",
            "estado_civil": None,
            "profissao": None,
            "endereco": endereco(),
            "email": "x@ficticio.example",
            "telefone": "t",
            "capaz": True if pf else None,
            "preso": False if pf else None,
        }

    dados = {
        "id": "t01_x_1",
        "tipo": "Petição Inicial em Juizado Especial Cível",
        "classe_risco": "medio",
        "casa_matriz": {
            "materia": "m",
            "tese": "t",
            "polo": "autor",
            "complexidade": "media",
            "momento": "m",
            "estilo": "detalhado",
        },
        "semente": 1,
        "processo": {
            "identificador_ficticio": "SINT-1",
            "numero_cnj": None,
            "rito": "juizado_especial_civel",
            "comarca": "Campinas",
            "uf": "SP",
            "juizo": "Juizado Especial Cível da Comarca de Campinas",
            "data_ajuizamento": "2026-11-17",
        },
        "partes": [
            parte("pa", "autor", "pessoa_fisica"),
            parte("pr", "reu", "pessoa_juridica_privada"),
        ],
        "advogado": {
            "nome": "Nome e Sobrenome do Advogado",
            "oab": "OAB/UF nº 000.000",
            "email": "a@ficticio.example",
            "telefone": "t",
            "endereco_escritorio": endereco(),
            "representa": "pa",
        },
        "fatos": [],
        "valores": [
            {"id": "v1", "descricao": "causa", "centavos": 6_484_000, "data_referencia": None}
        ],
        "provas": [],
        "valor_causa": "v1",
        "fundamentos": [],
        "momento_processual": {"fase": "f", "ultima_decisao": "d", "prazo": prazo},
        "pecas_anteriores": [],
        "data_peca": "2026-11-17",
        "local_peca": "Campinas",
        "pedidos": [],
        "materia": "m",
        "relacao_consumo": True,
        "inversao_onus_pedida": False,
        "tutela_urgencia": {"pedida": False, "fundamento": None},
        "tentativa_previa": None,
        "salario_minimo_referencia": 162_100,
    }
    lida = Ficha.model_validate_json(json.dumps(dados)).root
    assert isinstance(lida, FichaInicial)
    return lida


def extracao(**troca: Any) -> Extracao:
    campos: dict[str, Any] = {
        "nomes": [],
        "documentos": [],
        "valores": [],
        "datas": [],
        "comarca": None,
        "juizo": None,
        "pedidos": [],
        "pecas_anteriores": [],
        "data_peca": None,
    }
    campos.update(troca)
    return Extracao(**campos)


def valor_causa(texto: str, centavos: int) -> ValorExtraido:
    return ValorExtraido(texto=texto, centavos=centavos, lugar="valor_causa", pedido=None)


# ---------------------------------------------------------------------------
# Alçada
# ---------------------------------------------------------------------------


def test_alcada() -> None:
    acima = extracao(valores=[valor_causa("R$ 64.840,01", 6_484_001)])
    r = regras.alcada(acima, ficha(), configuracao())
    assert (r.item, r.resposta) == ("alcada", "nao_passa")
    assert r.divergencias[0].extraido == "6484001" and r.divergencias[0].ficha == "6484000"
    no_limite = extracao(valores=[valor_causa("R$ 64.840,00", 6_484_000)])
    assert regras.alcada(no_limite, ficha(), configuracao()).resposta == "passa"
    # Valores fora do lugar `valor_causa` não contam para a alçada.
    nos_fatos = extracao(
        valores=[
            valor_causa("R$ 64.840,00", 6_484_000),
            ValorExtraido(texto="R$ 70.000,00", centavos=7_000_000, lugar="fatos", pedido=None),
        ]
    )
    assert regras.alcada(nos_fatos, ficha(), configuracao()).resposta == "passa"
    # Sem valor da causa na peça, a alçada não é demonstrada.
    assert regras.alcada(extracao(), ficha(), configuracao()).resposta == "nao_passa"


def test_alcada_vem_do_salario_da_ficha() -> None:
    outra = ficha().model_copy(update={"salario_minimo_referencia": 100_000})
    no_limite_antigo = extracao(valores=[valor_causa("R$ 64.840,00", 6_484_000)])
    assert regras.alcada(no_limite_antigo, outra, configuracao()).resposta == "nao_passa"


# ---------------------------------------------------------------------------
# Prazo
# ---------------------------------------------------------------------------

# Intimação na quarta 18/11; 5 dias úteis com o feriado de 20/11 no meio: termo em 26/11.
PRAZO = {"inicio": "2026-11-18", "dias_uteis": 5, "termo_final": "2026-11-26"}


def test_prazo_no_termo_final_passa() -> None:
    r = regras.prazo(extracao(data_peca="2026-11-26"), ficha(PRAZO), FERIADOS)
    assert (r.item, r.resposta) == ("prazo", "passa")


def test_prazo_um_dia_util_depois_reprova() -> None:
    r = regras.prazo(extracao(data_peca="2026-11-27"), ficha(PRAZO), FERIADOS)
    assert r.resposta == "nao_passa"
    assert r.divergencias[0].extraido == "2026-11-27"
    assert r.divergencias[0].ficha == "2026-11-26"


def test_prazo_e_calculado_com_os_feriados_recebidos() -> None:
    # Sem o feriado, o termo é 25/11 e a peça de 26/11 fica fora.
    assert regras.prazo(extracao(data_peca="2026-11-26"), ficha(PRAZO), []).resposta == (
        "nao_passa"
    )
    # O termo é recalculado, não lido da ficha.
    errado = {**PRAZO, "termo_final": "2026-12-31"}
    r = regras.prazo(extracao(data_peca="2026-11-27"), ficha(errado), FERIADOS)
    assert r.resposta == "nao_passa"


def test_prazo_sem_data_completa_reprova() -> None:
    assert regras.prazo(extracao(data_peca="2026-11"), ficha(PRAZO), FERIADOS).resposta == (
        "nao_passa"
    )
    assert regras.prazo(extracao(), ficha(PRAZO), FERIADOS).resposta == "nao_passa"


def test_prazo_sem_prazo_na_ficha_e_erro() -> None:
    with pytest.raises(regras.ErroRegras):
        regras.prazo(extracao(data_peca="2026-11-26"), ficha(), FERIADOS)


# ---------------------------------------------------------------------------
# Termos inequívocos e marca
# ---------------------------------------------------------------------------

TERMOS = TermosInequivocos.model_validate_json(
    json.dumps(
        {
            "termos": [
                {
                    "termo": "citação por edital",
                    "motivo": "o juizado não admite",
                    "norma": "Lei 9.099",
                },
                {"termo": "reconvenção", "motivo": "o juizado não admite", "norma": "Lei 9.099"},
                {"termo": "réu revel", "motivo": "exemplo", "norma": "exemplo"},
            ]
        }
    )
)


@pytest.mark.parametrize(
    "forma",
    [
        "citação por edital",
        "citacao por edital",
        "CITAÇÃO POR EDITAL",
        "Citação  por\nedital",
        "reconvenção",
        "RECONVENCAO",
        "réu revel",
        "reu revel",
        "RÉU REVEL",
    ],
)
def test_termo_inequivoco_reprova(forma: str) -> None:
    texto = f"{MARCA}\n\n## Dos Pedidos\n\nRequer a {forma} da parte.\n"
    r = regras.termos_inequivocos(texto, TERMOS)
    assert (r.item, r.resposta) == ("termos_inequivocos", "nao_passa")
    assert r.divergencias


def test_peca_sem_termos_inequivocos_passa() -> None:
    texto = f"{MARCA}\n\nO réu revelou o endereço; a citação pelo correio foi pedida.\n"
    r = regras.termos_inequivocos(texto, TERMOS)
    assert r.resposta == "passa" and r.divergencias == []


def test_marca() -> None:
    assert regras.marca(rascunho(*COMPLETO)).resposta == "passa"
    sem = rascunho(*COMPLETO).replace(MARCA + "\n", "")
    r = regras.marca(sem)
    assert (r.item, r.resposta) == ("marca", "nao_passa")
    # A linha é exata: sem acento ou com hífen comum não vale.
    assert regras.marca("DOCUMENTO SINTETICO — FICTICIO\n\ntexto").resposta == "nao_passa"
    assert regras.marca("DOCUMENTO SINTÉTICO - FICTÍCIO\n\ntexto").resposta == "nao_passa"
    assert regras.marca(f"Texto com {MARCA} no meio da linha.").resposta == "nao_passa"


# ---------------------------------------------------------------------------
# Tudo junto e normalização sobre cópia
# ---------------------------------------------------------------------------


def test_conferir_devolve_os_itens_pedidos_na_ordem() -> None:
    texto = rascunho(*COMPLETO)
    perfil = Perfil(
        id="p",
        familia="peticao_inicial",
        blocos=[],
        retirar=[],
        ajustar=[],
        pedidos_acessorios_padrao=[],
    )
    e = extracao(valores=[valor_causa("R$ 64.840,00", 6_484_000)])
    itens = regras.conferir(
        texto,
        e,
        ficha(),
        estrutura(),
        perfil,
        TERMOS,
        FERIADOS,
        configuracao(),
        ["marca", "estrutura", "alcada", "termos_inequivocos", "coerencia_ficha"],
    )
    assert [i.item for i in itens] == [
        "marca",
        "estrutura",
        "alcada",
        "termos_inequivocos",
        "coerencia_ficha",
    ]
    assert all(i.resposta == "passa" for i in itens), itens
    with pytest.raises(regras.ErroRegras):
        regras.conferir(
            texto, e, ficha(), estrutura(), perfil, TERMOS, FERIADOS, configuracao(), ["cabimento"]
        )


def test_normalizacao_nao_muda_o_texto() -> None:
    original = "Citação  POR Edital, R$ 1.500,00"
    copia = str(original)
    assert normalizacao.comparavel(original) == "citacao por edital, r$ 1.500,00"
    assert original == copia
    assert normalizacao.centavos_em_algarismos("R$ 1.500,5") == 150050
    assert normalizacao.centavos_em_algarismos("sem valor") is None
    assert normalizacao.juizo("JEC de Campinas") == normalizacao.juizo(
        "Juizado Especial Cível da Comarca de Campinas"
    )
