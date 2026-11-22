"""Teste de aceite do brief 011: `fabrica/matriz.py`, `fabrica/estruturas.py` e `preparar`.

Famílias, perfis, acréscimos, matrizes, travas, tabela e feriados são de exemplo,
escritos aqui, em pasta temporária. Os nomes reservados são lidos de
`testes/dados/reais_reservados.json` só durante o teste, nunca copiados para cá.
"""

from __future__ import annotations

import datetime
import json
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from fabrica import __main__ as principal
from fabrica import estruturas, matriz
from fabrica.comum.formatos import (
    Acrescimo,
    Condicao,
    ConfigMatriz,
    Familia,
    Ficha,
    Matriz,
    Perfil,
    TabelaNormas,
    Trava,
    Travas,
    VisaoTravas,
)

RAIZ = Path(__file__).resolve().parent.parent
D = datetime.date
INICIAL = "Petição Inicial em Juizado Especial Cível"
EMBARGOS = "Embargos de Declaração"
MANIFESTACAO = "Manifestação sobre Aviso de Recebimento Negativo"
JEC = "juizado_especial_civel"
COMUM = "procedimento_comum"
CONFIG = ConfigMatriz(
    tentativas_maximas=1000,
    fracao_maxima_por_materia=0.25,
    dias_uteis_de_folga=1,
    anos_maximos_dos_fatos=2,
)
FERIADOS = [
    D(2026, 1, 1),
    D(2026, 4, 21),
    D(2026, 5, 1),
    D(2026, 9, 7),
    D(2026, 10, 12),
    D(2026, 11, 2),
    D(2026, 11, 15),
    D(2026, 11, 20),
    D(2026, 12, 25),
]
ADMITIDAS_AUTOR_JEC = ["pessoa_fisica", "mei", "microempresa", "empresa_pequeno_porte"]
PROIBIDAS_PARTE_JEC = ["pessoa_juridica_direito_publico", "empresa_publica_uniao", "massa_falida"]
MOTIVOS_SEM_RENOVAR = ["mudou_se", "desconhecido", "numero_inexistente", "endereco_insuficiente"]
MATERIAS = [
    "negativacao_indevida",
    "voo_atrasado_cancelado",
    "vicio_produto",
    "cobranca_telefonia_internet",
    "falha_servico_bancario",
]


# ---------------------------------------------------------------------------
# Dados de exemplo
# ---------------------------------------------------------------------------


def cond(campo: str, op: str, valor: Any = None, outro: str | None = None) -> dict[str, Any]:
    return {"campo": campo, "op": op, "valor": valor, "outro_campo": outro}


def trava(
    condicoes: list[dict[str, Any]],
    efeito: str = "proibe",
    exigido: str | None = None,
    dispositivos: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "condicoes": condicoes,
        "efeito": efeito,
        "campo_exigido": exigido,
        "base_legal": "exemplo",
        "dispositivos": dispositivos if dispositivos is not None else ["lei9099_art8"],
    }


def travas_a5() -> dict[str, Any]:
    jec = cond("processo.rito", "igual", JEC)
    lista: list[dict[str, Any]] = [
        trava([jec, cond("autor.categoria", "fora_da_lista", ADMITIDAS_AUTOR_JEC)]),
        trava([jec, cond("materia", "na_lista", ["acidente_de_trabalho"])]),
        trava([jec, cond("valor_causa_centavos", "maior", outro="alcada_centavos")]),
        trava([cond("tipo", "igual", EMBARGOS), cond("processo.rito", "igual", JEC)]),
        trava(
            [
                cond("tipo", "igual", EMBARGOS),
                cond("defeito.tipo", "na_lista", ["omissao_total", "omissao_parcial"]),
            ],
            "exige",
            "defeito.ancora.argumento_id",
        ),
        trava(
            [cond("tipo", "igual", EMBARGOS), cond("defeito.tipo", "igual", "omissao_parcial")],
            "exige",
            "defeito.trecho_mencao",
        ),
        trava(
            [
                cond("tipo", "igual", MANIFESTACAO),
                cond("pedido_ar", "igual", "informar_novo_endereco"),
            ],
            "exige",
            "novo_endereco",
        ),
        trava(
            [
                cond("tipo", "igual", MANIFESTACAO),
                cond("aviso_recebimento.motivo_devolucao", "na_lista", MOTIVOS_SEM_RENOVAR),
                cond("pedido_ar", "igual", "renovar_mesmo_endereco"),
            ]
        ),
        trava(
            [cond("tipo", "igual", MANIFESTACAO), cond("nova_diligencia", "igual", True)],
            "exige",
            "meio_nova_diligencia",
        ),
    ]
    # As travas que falam de "parte" viram uma para o autor e outra para o réu.
    for papel in ("autor", "reu"):
        lista.append(trava([jec, cond(f"{papel}.categoria", "na_lista", PROIBIDAS_PARTE_JEC)]))
        lista.append(trava([jec, cond(f"{papel}.capaz", "igual", False)]))
        lista.append(trava([jec, cond(f"{papel}.preso", "igual", True)]))
    return {"travas": lista}


def carregar_travas(dados: dict[str, Any] | None = None) -> Travas:
    return Travas.model_validate_json(json.dumps(dados or travas_a5()))


def visao(**campos: Any) -> VisaoTravas:
    base: dict[str, Any] = {nome: None for nome in VisaoTravas.model_fields}
    base["tipo"] = INICIAL
    base.update(campos)
    return VisaoTravas(**base)


def eixo(nome: str, contagens: dict[str, int]) -> dict[str, Any]:
    return {
        "eixo": nome,
        "contagens": [{"valor": v, "quantidade": q} for v, q in contagens.items()],
    }


def matriz_dados(tipo: str) -> dict[str, Any]:
    cinco = {"complexidade": {"simples": 5, "media": 5}, "estilo": {"conciso": 5, "detalhado": 5}}
    eixos = [eixo(nome, c) for nome, c in cinco.items()]
    momento = "antes_da_citacao"
    autor = ["pessoa_fisica", "mei", "pessoa_juridica_privada"]
    reu = ["pessoa_juridica_privada", "pessoa_juridica_direito_publico", "microempresa"]
    motivos: list[str] = []
    pedidos: list[str] = []
    if tipo == "embargos_declaracao":
        momento = "depois_da_decisao_embargada"
        eixos.append(eixo("polo", {"autor": 5, "reu": 5}))
        eixos.append(
            eixo(
                "defeito",
                {
                    "omissao_total": 2,
                    "omissao_parcial": 3,
                    "contradicao": 2,
                    "obscuridade": 2,
                    "erro_material": 1,
                },
            )
        )
        eixos.append(eixo("tipo_decisao", {"sentenca": 7, "decisao_interlocutoria": 3}))
        autor = ["pessoa_fisica", "pessoa_juridica_privada", "pessoa_juridica_direito_publico"]
        reu = ["pessoa_juridica_privada", "pessoa_juridica_direito_publico"]
    if tipo == "manifestacao_ar_negativo":
        momento = "depois_da_juntada_do_aviso"
        eixos.append(eixo("rito", {JEC: 5, COMUM: 5}))
        motivos = [
            "mudou_se",
            "desconhecido",
            "endereco_insuficiente",
            "numero_inexistente",
            "ausente",
            "nao_procurado",
        ]
        pedidos = ["informar_novo_endereco", "renovar_mesmo_endereco", "ciencia_e_prazo"]
    return {
        "tipo": tipo,
        "quantidade": 10,
        "momento": momento,
        "materias": [
            {"materia": m, "teses": [f"{m}_tese_a", f"{m}_tese_b"], "quantidade": None}
            for m in MATERIAS
        ],
        "teto_por_materia": 2,
        "eixos_fixos": eixos,
        "categorias_autor": autor,
        "categorias_reu": reu,
        "motivos_devolucao": motivos,
        "pedidos_ar": pedidos,
    }


def carregar_matriz(tipo: str, **troca: Any) -> Matriz:
    dados = matriz_dados(tipo)
    dados.update(troca)
    return Matriz.model_validate_json(json.dumps(dados))


def bloco(nome: str, ordem: int, obrigatorio: bool = True) -> dict[str, Any]:
    return {
        "nome": nome,
        "titulo": nome.replace("_", " ").upper(),
        "ordem": ordem,
        "obrigatorio": obrigatorio,
        "descricao": f"Bloco {nome}.",
    }


def familia_dados(id_: str = "peticao_inicial") -> dict[str, Any]:
    return {
        "id": id_,
        "blocos": [
            bloco("enderecamento", 10),
            bloco("qualificacao", 20),
            bloco("fatos", 30),
            bloco("fundamentos", 40),
            bloco("pedidos", 50),
            bloco("valor_causa", 60),
            bloco("citacao_edital", 55, obrigatorio=False),
            bloco("fecho", 90),
        ],
    }


def perfil_dados(id_: str = "juizado_especial_civel", familia: str = "peticao_inicial") -> dict:
    return {
        "id": id_,
        "familia": familia,
        "blocos": [bloco("alcada", 65)],
        "retirar": ["citacao_edital"],
        "ajustar": [{**bloco("valor_causa", 60), "descricao": "Valor dentro da alçada."}],
        "pedidos_acessorios_padrao": ["citacao_reu", "producao_provas"],
    }


def acrescimo_dados(tipo: str = "peticao_inicial_jec") -> dict[str, Any]:
    return {
        "tipo": tipo,
        "blocos": [bloco("tentativa_previa", 35, obrigatorio=False)],
        "retirar": [],
        "ajustar": [],
    }


def dispositivo(
    id_: str,
    diploma: str,
    artigo: str,
    paragrafo: str,
    assunto: str,
    funcao: str,
    tipos: list[str],
    texto: str = "Texto vigente de exemplo.",
) -> dict[str, Any]:
    return {
        "id": id_,
        "diploma": diploma,
        "artigo": artigo,
        "paragrafo": paragrafo,
        "assunto": assunto,
        "funcao": funcao,
        "texto_vigente": texto,
        "tipos": tipos,
        "fonte": "exemplo do teste",
        "data_conferencia": "2026-11-21",
    }


TODOS = ["peticao_inicial_jec", "embargos_declaracao", "manifestacao_ar_negativo"]


def tabela_dados() -> dict[str, Any]:
    return {
        "versao": "exemplo-1",
        "diplomas": [
            {"id": "cpc", "nome": "Código de Processo Civil", "formas": ["CPC"]},
            {"id": "lei9099", "nome": "Lei 9.099/1995", "formas": ["Lei 9.099/95"]},
        ],
        "dispositivos": [
            dispositivo("lei9099_art8_p1", "lei9099", "8º", "§ 1º", "partes", "requisito", TODOS),
            dispositivo("lei9099_art8", "lei9099", "8º", "caput", "partes", "excecao", TODOS),
            dispositivo(
                "lei9099_art3",
                "lei9099",
                "3º",
                "caput",
                "competencia",
                "competencia",
                ["peticao_inicial_jec"],
            ),
            dispositivo(
                "cpc_art1023", "cpc", "1.023", "caput", "embargos", "prazo", ["embargos_declaracao"]
            ),
            dispositivo(
                "cpc_art1022_pu",
                "cpc",
                "1.022",
                "parágrafo único",
                "embargos",
                "definicao",
                ["embargos_declaracao"],
            ),
            dispositivo(
                "cpc_art1022",
                "cpc",
                "1.022",
                "caput",
                "embargos",
                "requisito",
                ["embargos_declaracao"],
            ),
            dispositivo(
                "cpc_art218_p3",
                "cpc",
                "218",
                "§ 3º",
                "prazos",
                "prazo",
                ["manifestacao_ar_negativo"],
            ),
            dispositivo(
                "cpc_art218_p2",
                "cpc",
                "218",
                "§ 2º",
                "prazos",
                "prazo",
                ["manifestacao_ar_negativo"],
            ),
            dispositivo(
                "cpc_art319", "cpc", "319", "caput", "inicial", "requisito", ["peticao_inicial_jec"]
            ),
        ],
    }


# ---------------------------------------------------------------------------
# 1 · as oito operações
# ---------------------------------------------------------------------------


def condicao(campo: str, op: str, valor: Any = None, outro: str | None = None) -> Condicao:
    return Condicao.model_validate_json(json.dumps(cond(campo, op, valor, outro)))


@pytest.mark.parametrize(
    ("op", "valor", "esperado"),
    [
        ("igual", "pessoa_fisica", True),
        ("igual", "mei", False),
        ("diferente", "mei", True),
        ("diferente", "pessoa_fisica", False),
        ("na_lista", ["mei", "pessoa_fisica"], True),
        ("na_lista", ["mei"], False),
        ("fora_da_lista", ["mei"], True),
        ("fora_da_lista", ["pessoa_fisica"], False),
        ("preenchido", None, True),
        ("vazio", None, False),
    ],
)
def test_operacoes_sobre_texto(op: str, valor: Any, esperado: bool) -> None:
    v = visao(autor_categoria="pessoa_fisica")
    assert matriz.condicao_vale(condicao("autor.categoria", op, valor), v) is esperado


def test_operacoes_sobre_numero_e_outro_campo() -> None:
    v = visao(valor_causa_centavos=7_000_000, alcada_centavos=6_484_000)
    assert matriz.condicao_vale(condicao("valor_causa_centavos", "maior", 6_484_000), v)
    assert not matriz.condicao_vale(condicao("valor_causa_centavos", "menor", 6_484_000), v)
    assert matriz.condicao_vale(condicao("alcada_centavos", "menor", 7_000_000), v)
    maior_outro = condicao("valor_causa_centavos", "maior", outro="alcada_centavos")
    menor_outro = condicao("valor_causa_centavos", "menor", outro="alcada_centavos")
    igual_outro = condicao("valor_causa_centavos", "igual", outro="alcada_centavos")
    dif_outro = condicao("valor_causa_centavos", "diferente", outro="alcada_centavos")
    assert matriz.condicao_vale(maior_outro, v)
    assert not matriz.condicao_vale(menor_outro, v)
    assert not matriz.condicao_vale(igual_outro, v)
    assert matriz.condicao_vale(dif_outro, v)
    dentro = visao(valor_causa_centavos=1_000_000, alcada_centavos=6_484_000)
    assert not matriz.condicao_vale(maior_outro, dentro)
    assert matriz.condicao_vale(menor_outro, dentro)


def test_vazio_preenchido_e_campo_vazio_nas_comparacoes() -> None:
    v = visao()
    assert matriz.condicao_vale(condicao("novo_endereco", "vazio"), v)
    assert not matriz.condicao_vale(condicao("novo_endereco", "preenchido"), v)
    # Campo vazio não compara: só `vazio` e `preenchido` valem sobre ele.
    for op, valor in (
        ("igual", "x"),
        ("diferente", "x"),
        ("na_lista", ["x"]),
        ("fora_da_lista", ["x"]),
        ("maior", 1),
        ("menor", 1),
    ):
        assert not matriz.condicao_vale(condicao("novo_endereco", op, valor), v)
    cheio = visao(novo_endereco="Rua Exemplo, 1, Cidade/SP")
    assert matriz.condicao_vale(condicao("novo_endereco", "preenchido"), cheio)
    assert matriz.condicao_vale(condicao("autor.capaz", "vazio"), cheio)


def test_booleano_nao_se_confunde_com_numero() -> None:
    v = visao(autor_capaz=True, valor_causa_centavos=1)
    assert matriz.condicao_vale(condicao("autor.capaz", "igual", True), v)
    assert not matriz.condicao_vale(condicao("valor_causa_centavos", "igual", True), v)
    assert not matriz.condicao_vale(condicao("autor.capaz", "igual", 1), v)


def test_condicao_mal_escrita_e_campo_desconhecido() -> None:
    v = visao()
    with pytest.raises(matriz.ErroMatriz, match="campo"):
        matriz.condicao_vale(condicao("parte.categoria", "vazio"), v)
    ruins = [
        trava([cond("tipo", "na_lista", "texto")]),
        trava([cond("tipo", "maior", "texto")]),
        trava([cond("tipo", "vazio", "x")]),
        trava([cond("tipo", "igual")]),
        trava([cond("tipo", "igual", "x", "materia")]),
        trava([cond("tipo", "preenchido")], "exige", None),
        trava([cond("inventado", "vazio")]),
        trava([]),
    ]
    for dados in ruins:
        problemas = matriz.conferir_trava(Trava.model_validate_json(json.dumps(dados)))
        assert problemas, dados
    for boa in carregar_travas().travas:
        assert matriz.conferir_trava(boa) == []


# ---------------------------------------------------------------------------
# 2 · travas do Anexo A.5
# ---------------------------------------------------------------------------


def violadas(v: VisaoTravas) -> int:
    return len(matriz.violacoes(carregar_travas().travas, v))


def test_juizado_com_autor_fora_das_categorias_proibe() -> None:
    for categoria in ("pessoa_juridica_privada", "massa_falida"):
        assert violadas(visao(processo_rito=JEC, autor_categoria=categoria)) >= 1
    for categoria in ADMITIDAS_AUTOR_JEC:
        capaz = True if categoria == "pessoa_fisica" else None
        preso = False if categoria == "pessoa_fisica" else None
        v = visao(
            processo_rito=JEC,
            autor_categoria=categoria,
            autor_capaz=capaz,
            autor_preso=preso,
            reu_categoria="pessoa_juridica_privada",
        )
        assert violadas(v) == 0
    # Fora do juizado, a mesma categoria passa.
    assert (
        violadas(
            visao(tipo=MANIFESTACAO, processo_rito=COMUM, autor_categoria="pessoa_juridica_privada")
        )
        == 0
    )


def test_juizado_com_pessoa_de_direito_publico_como_parte_proibe() -> None:
    pjdp = "pessoa_juridica_direito_publico"
    assert violadas(visao(processo_rito=JEC, autor_categoria="mei", reu_categoria=pjdp)) == 1
    assert (
        violadas(
            visao(processo_rito=JEC, autor_categoria=pjdp, reu_categoria="pessoa_juridica_privada")
        )
        == 2
    )
    assert violadas(visao(processo_rito=COMUM, tipo=MANIFESTACAO, reu_categoria=pjdp)) == 0
    assert (
        violadas(visao(processo_rito=JEC, autor_categoria="pessoa_fisica", autor_capaz=False)) == 1
    )
    assert (
        violadas(
            visao(
                processo_rito=JEC,
                autor_categoria="mei",
                reu_categoria="pessoa_fisica",
                reu_preso=True,
            )
        )
        == 1
    )


def test_embargos_com_rito_de_juizado_proibe() -> None:
    base = {"tipo": EMBARGOS, "defeito_tipo": "contradicao"}
    assert violadas(visao(processo_rito=JEC, **base)) >= 1
    assert violadas(visao(processo_rito=COMUM, **base)) == 0


def test_manifestacao_com_novo_endereco_exige_o_endereco() -> None:
    base = {
        "tipo": MANIFESTACAO,
        "processo_rito": COMUM,
        "pedido_ar": "informar_novo_endereco",
        "nova_diligencia": True,
        "meio_nova_diligencia": "correio",
        "aviso_recebimento_motivo_devolucao": "mudou_se",
    }
    sem = matriz.violacoes(carregar_travas().travas, visao(**base))
    assert [t.campo_exigido for t in sem] == ["novo_endereco"]
    assert violadas(visao(novo_endereco="Rua Exemplo, 1, Cidade/SP", **base)) == 0


def test_demais_travas_do_anexo() -> None:
    omissao = {"tipo": EMBARGOS, "processo_rito": COMUM, "defeito_tipo": "omissao_parcial"}
    exigidos = {
        t.campo_exigido for t in matriz.violacoes(carregar_travas().travas, visao(**omissao))
    }
    assert exigidos == {"defeito.ancora.argumento_id", "defeito.trecho_mencao"}
    assert (
        violadas(
            visao(defeito_ancora_argumento_id="arg_1", defeito_trecho_mencao="trecho", **omissao)
        )
        == 0
    )
    renovar = {
        "tipo": MANIFESTACAO,
        "processo_rito": COMUM,
        "pedido_ar": "renovar_mesmo_endereco",
        "nova_diligencia": True,
        "meio_nova_diligencia": "oficial_de_justica",
    }
    assert violadas(visao(aviso_recebimento_motivo_devolucao="mudou_se", **renovar)) == 1
    assert violadas(visao(aviso_recebimento_motivo_devolucao="ausente", **renovar)) == 0
    sem_meio = {**renovar, "meio_nova_diligencia": None}
    assert violadas(visao(aviso_recebimento_motivo_devolucao="ausente", **sem_meio)) == 1
    acima = visao(
        processo_rito=JEC,
        autor_categoria="mei",
        valor_causa_centavos=6_484_001,
        alcada_centavos=6_484_000,
    )
    assert violadas(acima) == 1
    assert (
        violadas(visao(processo_rito=JEC, autor_categoria="mei", materia="acidente_de_trabalho"))
        == 1
    )
    # Campo que a ficha preenche fica pendente na combinação e não é exigido ainda.
    pendente = matriz.violacoes(
        carregar_travas().travas, visao(**omissao), pendentes=matriz.CAMPOS_DA_FICHA
    )
    assert pendente == []


# ---------------------------------------------------------------------------
# 3 · visão das travas a partir de fichas de exemplo
# ---------------------------------------------------------------------------


def endereco(rua: str = "Rua Inventada do Exemplo") -> dict[str, Any]:
    return {
        "rua": rua,
        "numero": "10",
        "complemento": None,
        "bairro": "Bairro do Exemplo",
        "cidade": "Campinas",
        "estado": "SP",
        "cep": "13000-000",
    }


def parte(id_: str, papel: str, categoria: str) -> dict[str, Any]:
    pf = categoria == "pessoa_fisica"
    return {
        "id": id_,
        "papel": papel,
        "categoria": categoria,
        "nome": "Nome e Sobrenome da Parte Autora"
        if papel == "autor"
        else "Razão Social da Parte Ré",
        "documento": "000.000.000-00",
        "estado_civil": "solteiro" if pf else None,
        "profissao": "professor" if pf else None,
        "endereco": endereco(),
        "email": f"{papel}@ficticio.example",
        "telefone": "(20) 90000-0000",
        "capaz": True if pf else None,
        "preso": False if pf else None,
    }


def ficha_comum(tipo: str, rito: str, valor_causa: str | None) -> dict[str, Any]:
    return {
        "id": "t01_x_1",
        "tipo": tipo,
        "classe_risco": "medio",
        "casa_matriz": {
            "materia": "negativacao_indevida",
            "tese": "tese_a",
            "polo": "autor",
            "complexidade": "media",
            "momento": "m",
            "estilo": "detalhado",
        },
        "semente": 7,
        "processo": {
            "identificador_ficticio": "SINT-2026-000001",
            "numero_cnj": None,
            "rito": rito,
            "comarca": "Campinas",
            "uf": "SP",
            "juizo": "Juízo",
            "data_ajuizamento": "2026-03-02",
        },
        "partes": [
            parte("p1", "autor", "pessoa_fisica"),
            parte("p2", "reu", "pessoa_juridica_privada"),
        ],
        "advogado": {
            "nome": "Nome e Sobrenome do Advogado",
            "oab": "OAB/SP nº 000.000",
            "email": "adv@ficticio.example",
            "telefone": "(20) 90000-0001",
            "endereco_escritorio": endereco("Rua do Escritório"),
            "representa": "p1",
        },
        "fatos": [{"data": "2025-10-01", "descricao": "Fato.", "valores": ["v1"]}],
        "valores": [
            {"id": "v1", "descricao": "Dano", "centavos": 1_000_000, "data_referencia": None}
        ],
        "provas": [],
        "valor_causa": valor_causa,
        "fundamentos": ["lei9099_art3"],
        "momento_processual": {"fase": "f", "ultima_decisao": "d", "prazo": None},
        "pecas_anteriores": [],
        "data_peca": "2026-03-02",
        "local_peca": "Campinas",
    }


def ficha_inicial() -> Any:
    dados = ficha_comum(INICIAL, JEC, "v1")
    dados.update(
        {
            "pedidos": [{"id": "pd1", "natureza": "danos_morais", "descricao": "d", "valor": "v1"}],
            "materia": "negativacao_indevida",
            "relacao_consumo": True,
            "inversao_onus_pedida": True,
            "tutela_urgencia": {"pedida": False, "fundamento": None},
            "tentativa_previa": None,
            "salario_minimo_referencia": 162_100,
        }
    )
    return Ficha.model_validate_json(json.dumps(dados)).root


def ficha_embargos() -> Any:
    dados = ficha_comum(EMBARGOS, COMUM, None)
    dados.update(
        {
            "pedidos": [
                {"id": "pd1", "natureza": "suprir_omissao", "descricao": "d", "valor": None}
            ],
            "embargante": "p1",
            "decisao_embargada": {
                "tipo": "sentenca",
                "data": "2026-05-04",
                "data_intimacao": "2026-05-06",
                "juizo": "Juízo",
                "relatorio": "Relatório.",
                "fundamentacao": "Fund.",
                "dispositivo": "Disp.",
            },
            "argumentos_das_partes": [
                {"id": "arg_1", "parte": "p1", "peca_de_origem": "inicial", "texto": "Argumento."}
            ],
            "defeito": {
                "tipo": "omissao_parcial",
                "ancora": {
                    "origem": "argumento",
                    "argumento_id": "arg_1",
                    "trecho_literal": "Argumento.",
                },
                "trecho_mencao": "Menciona sem enfrentar.",
                "descricao": "Omissão.",
                "efeito_modificativo": False,
            },
        }
    )
    return Ficha.model_validate_json(json.dumps(dados)).root


def ficha_manifestacao(pedido: str = "informar_novo_endereco") -> Any:
    dados = ficha_comum(MANIFESTACAO, JEC, None)
    dados.update(
        {
            "pedidos": [
                {
                    "id": "pd1",
                    "natureza": "nova_citacao_novo_endereco",
                    "descricao": "d",
                    "valor": None,
                }
            ],
            "peticionante": "p1",
            "citando": "p2",
            "endereco_tentado": endereco(),
            "aviso_recebimento": {"data_juntada": "2026-04-01", "motivo_devolucao": "mudou_se"},
            "determinacao_judicial": {"data_intimacao": "2026-04-06", "prazo_dias_uteis": 5},
            "pedido_ar": pedido,
            "novo_endereco": endereco("Rua Nova do Exemplo")
            if pedido != "ciencia_e_prazo"
            else None,
            "meio_nova_diligencia": "correio" if pedido != "ciencia_e_prazo" else None,
            "prazo_pedido_dias": 15 if pedido == "ciencia_e_prazo" else None,
        }
    )
    return Ficha.model_validate_json(json.dumps(dados)).root


def test_visao_da_ficha_inicial() -> None:
    v = matriz.visao_da_ficha(ficha_inicial())
    assert v.tipo == INICIAL and v.processo_rito == JEC
    assert v.materia == "negativacao_indevida"
    assert (v.autor_categoria, v.autor_capaz, v.autor_preso) == ("pessoa_fisica", True, False)
    assert (v.reu_categoria, v.reu_capaz, v.reu_preso) == ("pessoa_juridica_privada", None, None)
    assert v.valor_causa_centavos == 1_000_000
    assert v.alcada_centavos == 40 * 162_100
    assert v.defeito_tipo is None and v.pedido_ar is None and v.nova_diligencia is None
    assert matriz.violacoes(carregar_travas().travas, v) == []


def test_visao_da_ficha_embargos() -> None:
    v = matriz.visao_da_ficha(ficha_embargos())
    assert v.tipo == EMBARGOS and v.processo_rito == COMUM
    assert v.materia == "negativacao_indevida"
    assert v.defeito_tipo == "omissao_parcial"
    assert v.defeito_ancora_argumento_id == "arg_1"
    assert v.defeito_trecho_mencao == "Menciona sem enfrentar."
    assert v.valor_causa_centavos is None and v.alcada_centavos is None
    assert v.pedido_ar is None and v.novo_endereco is None and v.nova_diligencia is None
    assert matriz.violacoes(carregar_travas().travas, v) == []


def test_visao_da_ficha_manifestacao_calcula_nova_diligencia() -> None:
    v = matriz.visao_da_ficha(ficha_manifestacao())
    assert v.pedido_ar == "informar_novo_endereco"
    assert v.aviso_recebimento_motivo_devolucao == "mudou_se"
    assert v.novo_endereco is not None and "Rua Nova do Exemplo" in v.novo_endereco
    assert v.meio_nova_diligencia == "correio"
    assert v.nova_diligencia is True
    assert v.defeito_tipo is None and v.valor_causa_centavos is None
    assert matriz.violacoes(carregar_travas().travas, v) == []
    ciencia = matriz.visao_da_ficha(ficha_manifestacao("ciencia_e_prazo"))
    assert ciencia.nova_diligencia is False
    assert ciencia.novo_endereco is None and ciencia.meio_nova_diligencia is None


# ---------------------------------------------------------------------------
# 4 · sorteio das combinações
# ---------------------------------------------------------------------------


def sortear(tipo: str, semente: int = 11, travas: Travas | None = None, **troca: Any) -> Any:
    return matriz.sortear(
        carregar_matriz(tipo, **troca), travas or carregar_travas(), semente, CONFIG
    )


@pytest.mark.parametrize("tipo", TODOS)
def test_sorteio_respeita_travas_teto_e_contagens(tipo: str) -> None:
    resultado = sortear(tipo)
    assert resultado.situacao == "ok"
    assert 1 <= resultado.tentativas <= 1000
    combinacoes = resultado.combinacoes
    assert len(combinacoes) == 10
    travas = carregar_travas().travas
    for c in combinacoes:
        assert c.tipo == tipo
        assert (
            matriz.violacoes(
                travas, matriz.visao_da_combinacao(c), pendentes=matriz.CAMPOS_DA_FICHA
            )
            == []
        )
        assert c.categoria_autor != "pessoa_juridica_direito_publico"  # prazo em dobro
        assert c.categoria_reu != "pessoa_juridica_direito_publico"
        assert c.tese in (f"{c.materia}_tese_a", f"{c.materia}_tese_b")
    materias = Counter(c.materia for c in combinacoes)
    assert max(materias.values()) <= 2
    assert Counter(c.complexidade for c in combinacoes) == {"simples": 5, "media": 5}
    assert Counter(c.estilo for c in combinacoes) == {"conciso": 5, "detalhado": 5}
    if tipo == "peticao_inicial_jec":
        assert materias == dict.fromkeys(MATERIAS, 2)
        assert {c.rito for c in combinacoes} == {JEC}
        assert {c.polo for c in combinacoes} == {"autor"}
        assert {c.categoria_autor for c in combinacoes} <= {"pessoa_fisica", "mei"}
    if tipo == "embargos_declaracao":
        assert Counter(c.polo for c in combinacoes) == {"autor": 5, "reu": 5}
        assert Counter(c.defeito for c in combinacoes) == {
            "omissao_total": 2,
            "omissao_parcial": 3,
            "contradicao": 2,
            "obscuridade": 2,
            "erro_material": 1,
        }
        assert Counter(c.tipo_decisao for c in combinacoes) == {
            "sentenca": 7,
            "decisao_interlocutoria": 3,
        }
        assert {c.rito for c in combinacoes} == {COMUM}
    if tipo == "manifestacao_ar_negativo":
        assert Counter(c.rito for c in combinacoes) == {JEC: 5, COMUM: 5}
        assert {c.polo for c in combinacoes} == {"autor"}
        for c in combinacoes:
            assert c.motivo_devolucao is not None and c.pedido_ar is not None
            if c.pedido_ar == "renovar_mesmo_endereco":
                assert c.motivo_devolucao not in MOTIVOS_SEM_RENOVAR
            if c.rito == JEC:
                assert c.categoria_reu != "pessoa_juridica_direito_publico"


@pytest.mark.parametrize("tipo", TODOS)
def test_sorteio_repete_com_a_mesma_semente(tipo: str) -> None:
    assert sortear(tipo, 11).combinacoes == sortear(tipo, 11).combinacoes
    assert sortear(tipo, 11).combinacoes != sortear(tipo, 12).combinacoes


def test_cada_tipo_tem_sorteio_proprio() -> None:
    a = [c.materia for c in sortear("embargos_declaracao", 11).combinacoes]
    b = [c.materia for c in sortear("manifestacao_ar_negativo", 11).combinacoes]
    assert a != b


def test_sem_combinacao_possivel_volta_para_a_preparacao() -> None:
    dados = travas_a5()
    dados["travas"].append(trava([cond("tipo", "igual", INICIAL)]))
    resultado = sortear("peticao_inicial_jec", travas=carregar_travas(dados))
    assert resultado.situacao == matriz.VOLTA == "volta para a preparação"
    assert resultado.tentativas == 1000
    assert resultado.combinacoes == ()
    # Teto impossível: 4 matérias de no máximo 2 não fazem 10 peças.
    pouco = sortear(
        "embargos_declaracao", materias=matriz_dados("embargos_declaracao")["materias"][:4]
    )
    assert pouco.situacao == matriz.VOLTA


def test_matriz_com_contagem_errada_e_recusada() -> None:
    eixos = matriz_dados("peticao_inicial_jec")["eixos_fixos"]
    eixos[0] = eixo("complexidade", {"simples": 5, "media": 4})
    with pytest.raises(matriz.ErroMatriz, match="complexidade"):
        sortear("peticao_inicial_jec", eixos_fixos=eixos)


# ---------------------------------------------------------------------------
# 5 · datas e dias úteis
# ---------------------------------------------------------------------------


def test_termo_final_em_dias_uteis() -> None:
    # Sexta 17/04: segunda 20 (1), Tiradentes 21 fica fora, quarta 22 (2), quinta 23 (3).
    assert matriz.termo_final(D(2026, 4, 17), 3, FERIADOS) == D(2026, 4, 23)
    # Quarta 18/11: 19 (1), 20 feriado, fim de semana, 23 (2), 24, 25, 26 (5).
    assert matriz.termo_final(D(2026, 11, 18), 5, FERIADOS) == D(2026, 11, 26)
    # O dia do início fica fora mesmo quando é útil; começar no sábado conta da segunda.
    assert matriz.termo_final(D(2026, 11, 23), 1, FERIADOS) == D(2026, 11, 24)
    assert matriz.termo_final(D(2026, 11, 21), 1, FERIADOS) == D(2026, 11, 23)
    # Sem o feriado de exemplo, o dia 20 conta.
    assert matriz.termo_final(D(2026, 11, 18), 5, []) == D(2026, 11, 25)
    assert matriz.eh_dia_util(D(2026, 11, 23), FERIADOS)
    assert not matriz.eh_dia_util(D(2026, 11, 20), FERIADOS)
    assert not matriz.eh_dia_util(D(2026, 11, 22), FERIADOS)
    assert matriz.prazo_da_manifestacao(None) == 5
    assert matriz.prazo_da_manifestacao(10) == 10


@pytest.mark.parametrize("tipo", TODOS)
def test_datas_sorteadas_em_2026_dentro_do_prazo(tipo: str) -> None:
    for semente in range(300):
        rng = matriz.gerador(semente, tipo, "datas")
        d = matriz.sortear_datas(rng, tipo, FERIADOS, CONFIG)
        datas = [
            x
            for x in (
                d.ajuizamento,
                d.decisao,
                d.intimacao,
                d.juntada_aviso,
                d.termo_final,
                d.data_peca,
            )
            if x is not None
        ]
        assert all(x.year == 2026 for x in datas), d
        assert d.limite_fatos == d.ajuizamento.replace(year=d.ajuizamento.year - 2)
        assert d.limite_fatos <= d.fato_inicial < d.ajuizamento
        assert matriz.eh_dia_util(d.data_peca, FERIADOS)
        if tipo == "peticao_inicial_jec":
            assert d.termo_final is None and d.data_peca == d.ajuizamento
            continue
        assert d.prazo_inicio is not None and d.prazo_dias is not None
        assert d.termo_final is not None
        assert d.prazo_dias == 5
        assert d.termo_final == matriz.termo_final(d.prazo_inicio, d.prazo_dias, FERIADOS)
        assert d.prazo_inicio < d.data_peca
        # Pelo menos um dia útil de folga antes do termo final.
        assert matriz.termo_final(d.data_peca, 1, FERIADOS) <= d.termo_final
        if tipo == "embargos_declaracao":
            assert d.decisao is not None and d.intimacao is not None
            assert d.ajuizamento < d.decisao <= d.intimacao == d.prazo_inicio
        else:
            assert d.juntada_aviso is not None and d.intimacao is not None
            assert d.ajuizamento < d.juntada_aviso <= d.intimacao == d.prazo_inicio


def test_prazo_fixado_pelo_juiz_na_manifestacao() -> None:
    rng = matriz.gerador(3, "manifestacao_ar_negativo", "datas")
    d = matriz.sortear_datas(rng, "manifestacao_ar_negativo", FERIADOS, CONFIG, prazo_fixado=15)
    assert d.prazo_dias == 15
    assert d.termo_final is not None and d.termo_final.year == 2026


# ---------------------------------------------------------------------------
# 6 · combinação do ensaio
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tipo", TODOS)
def test_combinacao_do_ensaio(tipo: str) -> None:
    resultado = matriz.combinacao_do_ensaio(carregar_matriz(tipo), carregar_travas(), 5, CONFIG)
    assert resultado.situacao == "ok"
    (c,) = resultado.combinacoes
    assert (c.complexidade, c.estilo) == ("media", "detalhado")
    if tipo == "embargos_declaracao":
        assert (c.tipo_decisao, c.defeito) == ("sentenca", "omissao_parcial")
    travas = carregar_travas().travas
    assert (
        matriz.violacoes(travas, matriz.visao_da_combinacao(c), pendentes=matriz.CAMPOS_DA_FICHA)
        == []
    )
    repetida = matriz.combinacao_do_ensaio(carregar_matriz(tipo), carregar_travas(), 5, CONFIG)
    assert repetida.combinacoes == resultado.combinacoes


# ---------------------------------------------------------------------------
# 7 · estrutura montada
# ---------------------------------------------------------------------------


def montar(
    familia: dict[str, Any] | None = None,
    perfil: dict[str, Any] | None = None,
    acrescimo: dict[str, Any] | None = None,
) -> Any:
    return estruturas.montar(
        "peticao_inicial_jec",
        Familia.model_validate_json(json.dumps(familia or familia_dados())),
        Perfil.model_validate_json(json.dumps(perfil or perfil_dados())),
        Acrescimo.model_validate_json(json.dumps(acrescimo or acrescimo_dados())),
    )


def test_estrutura_montada_na_ordem() -> None:
    e = montar()
    assert [b.nome for b in e.blocos] == [
        "enderecamento",
        "qualificacao",
        "fatos",
        "tentativa_previa",
        "fundamentos",
        "pedidos",
        "valor_causa",
        "alcada",
        "fecho",
    ]
    assert e.tipo == "peticao_inicial_jec"
    assert (e.familia, e.perfil) == ("peticao_inicial", "juizado_especial_civel")
    assert e.pedidos_acessorios_padrao == ["citacao_reu", "producao_provas"]
    assert next(b for b in e.blocos if b.nome == "valor_causa").descricao == (
        "Valor dentro da alçada."
    )
    texto = estruturas.em_markdown(e)
    assert texto.index("ENDERECAMENTO") < texto.index("FECHO")
    assert "obrigatório" in texto


def test_sem_acrescimo_tambem_monta() -> None:
    e = estruturas.montar(
        "peticao_inicial_jec",
        Familia.model_validate_json(json.dumps(familia_dados())),
        Perfil.model_validate_json(json.dumps(perfil_dados())),
        None,
    )
    assert "tentativa_previa" not in [b.nome for b in e.blocos]


def test_perfil_que_retira_bloco_obrigatorio_e_recusado() -> None:
    perfil = perfil_dados()
    perfil["retirar"] = ["citacao_edital", "fatos", "pedidos"]
    with pytest.raises(estruturas.ErroEstrutura) as erro:
        montar(perfil=perfil)
    assert erro.value.faltando == ["fatos", "pedidos"]
    acrescimo = acrescimo_dados()
    acrescimo["retirar"] = ["fecho"]
    with pytest.raises(estruturas.ErroEstrutura) as erro:
        montar(acrescimo=acrescimo)
    assert erro.value.faltando == ["fecho"]
    # Ajustar para "não obrigatório" é retirar por outro caminho.
    perfil = perfil_dados()
    perfil["ajustar"] = [bloco("fatos", 30, obrigatorio=False)]
    with pytest.raises(estruturas.ErroEstrutura) as erro:
        montar(perfil=perfil)
    assert erro.value.faltando == ["fatos"]


def test_montagem_em_que_um_bloco_obrigatorio_some_e_recusada() -> None:
    e = montar()
    sem_fatos = e.model_copy(update={"blocos": [b for b in e.blocos if b.nome != "fatos"]})
    faltou = estruturas.faltando(
        sem_fatos,
        Familia.model_validate_json(json.dumps(familia_dados())),
        Perfil.model_validate_json(json.dumps(perfil_dados())),
        Acrescimo.model_validate_json(json.dumps(acrescimo_dados())),
    )
    assert faltou == ["fatos"]


def test_estrutura_incoerente_e_recusada() -> None:
    with pytest.raises(estruturas.ErroEstrutura, match="família"):
        montar(perfil=perfil_dados(familia="outra_familia"))
    perfil = perfil_dados()
    perfil["ajustar"] = [bloco("inexistente", 70)]
    with pytest.raises(estruturas.ErroEstrutura, match="inexistente"):
        montar(perfil=perfil)
    perfil = perfil_dados()
    perfil["blocos"] = [bloco("fatos", 31)]
    with pytest.raises(estruturas.ErroEstrutura, match="fatos"):
        montar(perfil=perfil)
    acrescimo = acrescimo_dados("embargos_declaracao")
    with pytest.raises(estruturas.ErroEstrutura, match="tipo"):
        montar(acrescimo=acrescimo)


# ---------------------------------------------------------------------------
# 8 · trecho da tabela
# ---------------------------------------------------------------------------


def tabela() -> TabelaNormas:
    return TabelaNormas.model_validate_json(json.dumps(tabela_dados()))


def test_trecho_filtrado_e_ordenado() -> None:
    t = estruturas.trecho_da_tabela(tabela(), "embargos_declaracao")
    assert [d.id for d in t.dispositivos] == [
        "cpc_art1022",
        "cpc_art1022_pu",
        "cpc_art1023",
        "lei9099_art8",
        "lei9099_art8_p1",
    ]
    assert t.situacao == "ok"
    i = estruturas.trecho_da_tabela(tabela(), "peticao_inicial_jec")
    assert [d.id for d in i.dispositivos] == [
        "cpc_art319",
        "lei9099_art3",
        "lei9099_art8",
        "lei9099_art8_p1",
    ]
    m = estruturas.trecho_da_tabela(tabela(), "manifestacao_ar_negativo")
    assert [d.id for d in m.dispositivos] == [
        "cpc_art218_p2",
        "cpc_art218_p3",
        "lei9099_art8",
        "lei9099_art8_p1",
    ]
    # Mesmo trecho para todas as peças do tipo.
    assert estruturas.trecho_da_tabela(tabela(), "embargos_declaracao") == t
    assert "cpc_art1022_pu" in t.texto and "Texto vigente de exemplo." in t.texto


def test_ordem_dos_paragrafos() -> None:
    dados = tabela_dados()
    dados["dispositivos"] = [
        dispositivo("p10", "cpc", "5", "§ 10", "a", "prazo", TODOS),
        dispositivo("p2", "cpc", "5", "§ 2º", "a", "prazo", TODOS),
        dispositivo("pu", "cpc", "5", "parágrafo único", "a", "prazo", TODOS),
        dispositivo("caput", "cpc", "5", "caput", "a", "prazo", TODOS),
        dispositivo("a40", "cpc", "40", "caput", "a", "prazo", TODOS),
        dispositivo("a4", "cpc", "4º", "caput", "a", "prazo", TODOS),
    ]
    t = estruturas.trecho_da_tabela(
        TabelaNormas.model_validate_json(json.dumps(dados)), "embargos_declaracao"
    )
    assert [d.id for d in t.dispositivos] == ["a4", "caput", "pu", "p2", "p10", "a40"]


def test_pares_contados() -> None:
    # Embargos: cpc/embargos tem requisito, definição e prazo (3 com par);
    # lei9099/partes tem requisito e exceção (2 com par).
    assert estruturas.trecho_da_tabela(tabela(), "embargos_declaracao").pares == 5
    # Manifestação: cpc/prazos são os dois "prazo" (sem par); lei9099/partes, 2.
    assert estruturas.trecho_da_tabela(tabela(), "manifestacao_ar_negativo").pares == 2


def test_trecho_grande_demais_volta_para_a_preparacao() -> None:
    dados = tabela_dados()
    dados["dispositivos"].append(
        dispositivo(
            "longo",
            "cpc",
            "999",
            "caput",
            "x",
            "prazo",
            ["embargos_declaracao"],
            texto="a" * 24_001,
        )
    )
    t = estruturas.trecho_da_tabela(
        TabelaNormas.model_validate_json(json.dumps(dados)), "embargos_declaracao"
    )
    assert t.tokens_estimados > 8000
    assert t.situacao == matriz.VOLTA
    assert estruturas.trecho_da_tabela(tabela(), "embargos_declaracao").tokens_estimados < 8000


# ---------------------------------------------------------------------------
# 9 · comando preparar
# ---------------------------------------------------------------------------


def catalogo_dados() -> dict[str, Any]:
    def tipo(rotulo: str, nome: str, familia: str, perfil: str, risco: str) -> dict[str, Any]:
        return {
            "rotulo": rotulo,
            "nome_curto": nome,
            "familia": familia,
            "perfil": perfil,
            "classe_risco": risco,
            "tarefa_redacao": f"redacao_risco_{risco}",
            "quantidade": 10,
            "depende_peca_anterior": nome != "peticao_inicial_jec",
            "itens_conferencia": ["estrutura"],
        }

    return {
        "tipos": [
            tipo(
                INICIAL, "peticao_inicial_jec", "peticao_inicial", "juizado_especial_civel", "medio"
            ),
            tipo(EMBARGOS, "embargos_declaracao", "recurso", "recurso_comum", "alto"),
            tipo(
                MANIFESTACAO,
                "manifestacao_ar_negativo",
                "peticao_intermediaria",
                "intermediaria_geral",
                "baixo",
            ),
        ]
    }


def escrever(raiz: Path, relativo: str, dados: Any) -> None:
    caminho = raiz / relativo
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


def dados_de_exemplo(raiz: Path) -> None:
    (raiz / "config").mkdir(parents=True)
    shutil.copy(RAIZ / "config/config.toml", raiz / "config/config.toml")
    shutil.copy(RAIZ / "config/gasto.toml", raiz / "config/gasto.toml")
    (raiz / "testes/dados").mkdir(parents=True)
    shutil.copy(
        RAIZ / "testes/dados/reais_reservados.json", raiz / "testes/dados/reais_reservados.json"
    )
    escrever(raiz, "dados/catalogo/tipos.json", catalogo_dados())
    escrever(raiz, "dados/estruturas/familias/peticao_inicial.json", familia_dados())
    escrever(
        raiz,
        "dados/estruturas/familias/recurso.json",
        {
            "id": "recurso",
            "blocos": [
                bloco("enderecamento", 10),
                bloco("razoes", 20),
                bloco("pedidos", 30),
                bloco("fecho", 90),
            ],
        },
    )
    escrever(
        raiz,
        "dados/estruturas/familias/peticao_intermediaria.json",
        {
            "id": "peticao_intermediaria",
            "blocos": [bloco("enderecamento", 10), bloco("pedidos", 30), bloco("fecho", 90)],
        },
    )
    escrever(raiz, "dados/estruturas/perfis/juizado_especial_civel.json", perfil_dados())
    escrever(
        raiz,
        "dados/estruturas/perfis/recurso_comum.json",
        {
            "id": "recurso_comum",
            "familia": "recurso",
            "blocos": [],
            "retirar": [],
            "ajustar": [],
            "pedidos_acessorios_padrao": ["intimacao_parte_contraria"],
        },
    )
    escrever(
        raiz,
        "dados/estruturas/perfis/intermediaria_geral.json",
        {
            "id": "intermediaria_geral",
            "familia": "peticao_intermediaria",
            "blocos": [],
            "retirar": [],
            "ajustar": [],
            "pedidos_acessorios_padrao": [],
        },
    )
    escrever(raiz, "dados/estruturas/acrescimos/peticao_inicial_jec.json", acrescimo_dados())
    escrever(
        raiz,
        "dados/estruturas/acrescimos/embargos_declaracao.json",
        {
            "tipo": "embargos_declaracao",
            "blocos": [bloco("defeito_apontado", 15)],
            "retirar": [],
            "ajustar": [],
        },
    )
    for tipo in TODOS:
        escrever(raiz, f"dados/matrizes/{tipo}.json", matriz_dados(tipo))
    escrever(raiz, "dados/normas/tabela_normas.json", tabela_dados())
    escrever(raiz, "dados/travas/travas.json", travas_a5())
    escrever(
        raiz,
        "dados/conferencia/feriados_nacionais.json",
        {
            "feriados": [
                {"data": f.isoformat(), "nome": "Feriado de exemplo", "lei": "Lei de exemplo"}
                for f in FERIADOS
            ]
        },
    )
    escrever(
        raiz,
        "dados/conferencia/lista_conferencia.json",
        {
            "itens": [
                {
                    "item": "estrutura",
                    "pergunta": "Blocos?",
                    "quem": ["programa"],
                    "eliminatorio": True,
                    "tipos": TODOS,
                }
            ]
        },
    )
    escrever(
        raiz,
        "dados/conferencia/termos_inequivocos.json",
        {"termos": [{"termo": "termo de exemplo", "motivo": "m", "norma": "n"}]},
    )
    escrever(
        raiz,
        "dados/conferencia/palavras_ignoradas.json",
        {"comuns": ["de"], "juridicas": ["autos"]},
    )
    escrever(raiz, "dados/erros/catalogo_erros.json", {"erros": []})
    escrever(
        raiz,
        "dados/ficticios/listas_ficticias.json",
        {
            "ruas": ["Rua Inventada"],
            "bairros": ["Bairro Inventado"],
            "cidades": [
                {
                    "nome": "Campinas",
                    "uf": "SP",
                    "cep_inicio": "13000-000",
                    "cep_fim": "13139-999",
                    "juizo_jec": "Juizado",
                    "varas_civeis": ["1ª"],
                }
            ],
            "profissoes": ["professor"],
            "estados_civis": ["solteiro"],
            "tribunais": [{"uf": "SP", "codigo": "26"}],
            "pedidos_incompativeis": [],
        },
    )
    escrever(
        raiz,
        "dados/ficticios/reais_permitidos.json",
        {"nomes": [{"nome": "SISBAJUD", "categoria": "sistema"}]},
    )
    escrever(
        raiz,
        "dados/ficticios/reais_proibidos.json",
        {"nomes": [{"nome": "Itaú", "categoria": "banco"}]},
    )


def rodar_preparar(
    raiz: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> tuple[int, str]:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    servicos = principal.montar_servicos(raiz)
    codigo = principal.executar(["preparar"], servicos)
    saida = capsys.readouterr()
    return codigo, saida.out + saida.err


def test_preparar_grava_estruturas_e_resumo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dados_de_exemplo(tmp_path)
    codigo, saida = rodar_preparar(tmp_path, monkeypatch, capsys)
    assert codigo == 0, saida
    for tipo in TODOS:
        json_ = tmp_path / f"saida/preparacao/{tipo}_estrutura.json"
        md = tmp_path / f"saida/preparacao/{tipo}_estrutura.md"
        assert json_.is_file() and md.is_file()
        lida = estruturas.EstruturaMontada.model_validate_json(json_.read_text("utf-8"))
        assert lida.tipo == tipo
    resumo = (tmp_path / "saida/preparacao/resumo.md").read_text("utf-8")
    assert "tentativa" in resumo
    assert "par" in resumo
    assert "nomes reservados em reais_proibidos.json: 0" in resumo
    assert "falhou" not in resumo


def test_preparar_recusa_dado_fora_do_formato(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dados_de_exemplo(tmp_path)
    tabela_ruim = tabela_dados()
    tabela_ruim["dispositivos"][0]["funcao"] = "inventada"
    escrever(tmp_path, "dados/normas/tabela_normas.json", tabela_ruim)
    codigo, saida = rodar_preparar(tmp_path, monkeypatch, capsys)
    assert codigo != 0
    assert "tabela_normas.json" in saida
    resumo = (tmp_path / "saida/preparacao/resumo.md").read_text("utf-8")
    assert "falhou" in resumo


def test_preparar_recusa_arquivo_que_falta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dados_de_exemplo(tmp_path)
    (tmp_path / "dados/travas/travas.json").unlink()
    codigo, saida = rodar_preparar(tmp_path, monkeypatch, capsys)
    assert codigo != 0 and "travas.json" in saida


def test_preparar_confere_dispositivos_das_travas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dados_de_exemplo(tmp_path)
    dados = travas_a5()
    dados["travas"][0]["dispositivos"] = ["dispositivo_que_nao_existe"]
    escrever(tmp_path, "dados/travas/travas.json", dados)
    codigo, saida = rodar_preparar(tmp_path, monkeypatch, capsys)
    assert codigo != 0 and "dispositivo_que_nao_existe" in saida


def test_preparar_avisa_matriz_que_nao_cabe(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dados_de_exemplo(tmp_path)
    dados = travas_a5()
    dados["travas"].append(trava([cond("tipo", "igual", MANIFESTACAO)]))
    escrever(tmp_path, "dados/travas/travas.json", dados)
    codigo, saida = rodar_preparar(tmp_path, monkeypatch, capsys)
    assert codigo != 0 and "volta para a preparação" in saida


def test_preparar_conta_reservado_sem_mostrar_o_nome(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dados_de_exemplo(tmp_path)
    reservados = json.loads((RAIZ / "testes/dados/reais_reservados.json").read_text("utf-8"))
    nome = reservados["nomes"][0]["nome"]
    escrever(
        tmp_path,
        "dados/ficticios/reais_proibidos.json",
        {"nomes": [{"nome": "Itaú", "categoria": "banco"}, {"nome": nome, "categoria": "x"}]},
    )
    codigo, saida = rodar_preparar(tmp_path, monkeypatch, capsys)
    assert codigo != 0
    resumo = (tmp_path / "saida/preparacao/resumo.md").read_text("utf-8")
    assert "nomes reservados em reais_proibidos.json: 1" in resumo
    assert nome not in resumo and nome not in saida
