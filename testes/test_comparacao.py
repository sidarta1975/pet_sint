"""Teste de aceite do brief 012: os exemplos do Anexo D em `comparacao_exemplos.json`.

Cada caso com `"verificado_por": "regras"` vira uma extração completa e certa,
mais o elemento do caso, e passa por `regras.coerencia_ficha` contra a ficha de
base do arquivo. Os casos de `"fichas"` ficam para o brief 015.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fabrica.comum import config
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import (
    Configuracao,
    DataExtraida,
    DocumentoExtraido,
    Extracao,
    Ficha,
    FichaInicial,
    NomeExtraido,
    PedidoExtraido,
    Perfil,
    ValorExtraido,
)
from fabrica.conferencia import regras

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLOS = json.loads((RAIZ / "testes/dados/comparacao_exemplos.json").read_text("utf-8"))
BASE = EXEMPLOS["ficha_base"]
CASOS = [c for c in EXEMPLOS["casos"] if c["verificado_por"] == "regras"]
CAMPO_DOCUMENTO = {
    "documento_autor": "cpf",
    "documento_reu": "cnpj",
    "numero_processo": "numero_processo",
    "protocolo": "protocolo",
}


def endereco(cep: str) -> dict[str, Any]:
    return {
        "rua": "Rua Inventada do Exemplo",
        "numero": "1",
        "complemento": None,
        "bairro": "Bairro do Exemplo",
        "cidade": BASE["comarca"],
        "estado": "SP",
        "cep": cep,
    }


def parte(dados: dict[str, Any], id_: str) -> dict[str, Any]:
    pf = dados["categoria"] == "pessoa_fisica"
    return {
        "id": id_,
        "papel": dados["papel"],
        "categoria": dados["categoria"],
        "nome": dados["nome"],
        "documento": dados["documento"],
        "estado_civil": "solteiro" if pf else None,
        "profissao": "professor" if pf else None,
        "endereco": endereco(dados["cep"]),
        "email": f"{id_}@ficticio.example",
        "telefone": "(20) 90000-0000",
        "capaz": True if pf else None,
        "preso": False if pf else None,
    }


def ficha_base() -> FichaInicial:
    d1, d2, d3 = BASE["datas"]
    autor, reu = BASE["partes"]
    dados = {
        "id": "t01_peticao_inicial_jec_1",
        "tipo": "Petição Inicial em Juizado Especial Cível",
        "classe_risco": "medio",
        "casa_matriz": {
            "materia": "negativacao_indevida",
            "tese": "t",
            "polo": "autor",
            "complexidade": "media",
            "momento": "antes_da_citacao",
            "estilo": "detalhado",
        },
        "semente": 1,
        "processo": {
            "identificador_ficticio": BASE["protocolo"],
            "numero_cnj": BASE["numero_processo"],
            "rito": "juizado_especial_civel",
            "comarca": BASE["comarca"],
            "uf": "SP",
            "juizo": BASE["juizo"],
            "data_ajuizamento": d3,
        },
        "partes": [parte(autor, "pa"), parte(reu, "pr")],
        "advogado": {
            "nome": BASE["advogado"]["nome"],
            "oab": BASE["advogado"]["oab"],
            "email": "adv@ficticio.example",
            "telefone": "(20) 90000-0001",
            "endereco_escritorio": endereco(autor["cep"]),
            "representa": "pa",
        },
        "fatos": [
            {"data": d1, "descricao": "Fato.", "valores": ["v5"]},
            {"data": d2, "descricao": "Fato.", "valores": ["v1"]},
        ],
        "valores": [{**v, "data_referencia": None} for v in BASE["valores"]],
        "provas": [],
        "valor_causa": BASE["valor_causa"],
        "fundamentos": [],
        "momento_processual": {
            "fase": "antes da citação",
            "ultima_decisao": "nenhuma",
            "prazo": None,
        },
        "pecas_anteriores": [],
        "data_peca": d3,
        "local_peca": BASE["comarca"],
        "pedidos": [{**p, "descricao": p["natureza"]} for p in BASE["pedidos"]],
        "materia": "negativacao_indevida",
        "relacao_consumo": True,
        "inversao_onus_pedida": False,
        "tutela_urgencia": {"pedida": False, "fundamento": None},
        "tentativa_previa": {"data": d2, "protocolo": BASE["protocolo"]},
        "salario_minimo_referencia": BASE["salario_minimo_referencia_centavos"],
    }
    ficha = Ficha.model_validate_json(json.dumps(dados)).root
    assert isinstance(ficha, FichaInicial)
    return ficha


def perfil() -> Perfil:
    return Perfil(
        id="juizado_especial_civel",
        familia="peticao_inicial",
        blocos=[],
        retirar=[],
        ajustar=[],
        pedidos_acessorios_padrao=BASE["pedidos_acessorios_padrao"],
    )


def configuracao() -> Configuracao:
    return config.carregar(Arquivos(RAIZ)).geral


def extracao_certa(**troca: Any) -> Extracao:
    campos: dict[str, Any] = {
        "nomes": [],
        "documentos": [],
        "valores": [],
        "datas": [],
        "comarca": None,
        "juizo": None,
        "pedidos": [
            PedidoExtraido(natureza=p["natureza"], texto=p["natureza"]) for p in BASE["pedidos"]
        ],
        "pecas_anteriores": [],
        "data_peca": None,
    }
    campos.update(troca)
    return Extracao(**campos)


def extracao_do_caso(caso: dict[str, Any]) -> Extracao:
    e = caso["entrada"]
    regra = caso["regra"]
    if regra == "valor":
        return extracao_certa(valores=[ValorExtraido(**e)])
    if regra == "data":
        return extracao_certa(datas=[DataExtraida(**e)])
    if regra == "cep":
        return extracao_certa(documentos=[DocumentoExtraido(tipo="cep", texto=e["texto"])])
    if regra == "documento":
        tipo = CAMPO_DOCUMENTO[e["campo"]]
        return extracao_certa(documentos=[DocumentoExtraido(tipo=tipo, texto=e["texto"])])
    if regra == "nome":
        return extracao_certa(nomes=[NomeExtraido(texto=e["texto"], papel=e["papel"])])
    if regra == "oab":
        return extracao_certa(documentos=[DocumentoExtraido(tipo="oab", texto=e["texto"])])
    if regra == "designacao":
        return extracao_certa(nomes=[NomeExtraido(texto=e["texto"], papel="autor")])
    if regra == "juizo":
        return extracao_certa(comarca=e["comarca"], juizo=e["juizo"])
    if regra == "pedidos":
        pedidos = [PedidoExtraido(natureza=n, texto=n) for n in e["naturezas"]]
        pedidos += [PedidoExtraido(natureza="outro", texto=t) for t in e["outros"]]
        return extracao_certa(pedidos=pedidos)
    raise AssertionError(f"regra sem conversão: {regra}")


def test_arquivo_tem_os_88_casos() -> None:
    assert EXEMPLOS["versao"] == "2026-11-21-v2"
    assert len(EXEMPLOS["casos"]) == 88
    assert len(CASOS) == 86
    assert len({c["id"] for c in EXEMPLOS["casos"]}) == 88


def test_extracao_certa_passa() -> None:
    resultado = regras.coerencia_ficha(extracao_certa(), ficha_base(), perfil(), configuracao())
    assert resultado.resposta == "passa", resultado
    assert resultado.item == "coerencia_ficha" and resultado.quem == "programa"


@pytest.mark.parametrize("caso", CASOS, ids=[c["id"] for c in CASOS])
def test_caso_do_anexo_d(caso: dict[str, Any]) -> None:
    resultado = regras.coerencia_ficha(
        extracao_do_caso(caso), ficha_base(), perfil(), configuracao()
    )
    esperado = "passa" if caso["esperado"] == "passa" else "nao_passa"
    assert resultado.resposta == esperado, (caso, resultado)
    if esperado == "nao_passa":
        # Cada reprovação guarda o valor extraído e o da ficha.
        assert resultado.divergencias
        assert all(d.extraido and d.ficha for d in resultado.divergencias)
    else:
        assert resultado.divergencias == []


def test_varios_erros_juntos_viram_varias_divergencias() -> None:
    extracao = extracao_certa(
        valores=[ValorExtraido(texto="R$ 3.000,00", centavos=300000, lugar="pedido", pedido="p1")],
        datas=[DataExtraida(texto="16 de março de 2026", data="2026-03-16")],
        comarca="Jundiaí",
        juizo="Juizado Especial Cível da Comarca de Jundiaí",
    )
    resultado = regras.coerencia_ficha(extracao, ficha_base(), perfil(), configuracao())
    assert resultado.resposta == "nao_passa"
    assert [d.regra for d in resultado.divergencias] == ["valor", "data", "comarca", "juizo"]
