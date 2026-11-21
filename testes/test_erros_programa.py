"""Teste de aceite do brief 019: a parte de `fabrica/erros_plantados.py` sem modelo.

Peças, extrações, fichas e a tabela de exemplo numa pasta temporária (o ambiente do
`test_conferencia_etapas.py`, com as fichas do ensaio). A extração de cada cópia é a
da original com a mesma troca aplicada, que é o que um extrator correto devolveria.
"""

from __future__ import annotations

import datetime
import itertools
import json
import random
from pathlib import Path
from typing import Any

import pytest

from fabrica import erros_plantados as ep
from fabrica.comum.formatos import (
    Extracao,
    Ficha,
    Gabarito,
    RespostasCartao,
    Rodada,
    Rodadas,
)
from fabrica.conferencia import citacoes, regras
from fabrica.conferencia.regras import MARCA
from fabrica.estado import RefPeca
from testes.test_conferencia_etapas import EMB, INICIAL, MAN, TIPOS, amb
from testes.test_fichas import Ambiente

__all__ = ["amb"]  # a fixture vem do teste do brief 017

CORPO = {
    INICIAL: {
        "enderecamento": "Excelentíssimo Senhor Doutor Juiz de Direito do {juizo}.",
        "qualificacao": "A parte autora, qualificada nos autos, vem propor a presente ação.",
        "fatos": "Em 22/02/2026, a parte autora contratou o serviço. "
        "Em 24/03/2026, a cobrança indevida foi lançada.",
        "fundamentos": "Nos termos do art. 14 do CDC, o fornecedor responde pelos danos. "
        "A competência do juizado decorre do art. 3º da Lei 9.099/1995.",
        "pedidos": "Requer a citação da parte ré. Requer a condenação ao pagamento de "
        "R$ 5.000,00 (cinco mil reais) a título de dano moral. Requer a restituição de "
        "R$ 300,00 (trezentos reais).",
        "valor_causa": "Dá-se à causa o valor de R$ 5.300,00 (cinco mil e trezentos reais).",
        "fecho": "{local}, 23 de abril de 2026.",
    },
    EMB: {
        "enderecamento": "Excelentíssimo Senhor Doutor Juiz de Direito da {juizo}.",
        "identificacao": "Processo em curso entre as partes qualificadas nos autos.",
        "tempestividade": "Os embargos são tempestivos, opostos dentro do prazo legal.",
        "vicio": "Em 28/01/2026, a autora comprou um aparelho celular que apresentou defeito.",
        "razoes": "Nos termos do art. 1.022 do CPC, cabem embargos contra a omissão.",
        "pedidos": "Requer o acolhimento dos embargos para suprir a omissão apontada.",
        "fecho": "{local}, 10 de abril de 2026.",
    },
    MAN: {
        "enderecamento": "Excelentíssimo Senhor Doutor Juiz de Direito do {juizo}.",
        "identificacao": "Processo em curso entre as partes qualificadas nos autos.",
        "exposicao": "Em 16/02/2026, ocorreu o fato do processo de origem.",
        "novo_endereco": "Indica-se o novo endereço, nos termos do art. 319 do CPC.",
        "pedidos": "Requer a nova citação da parte ré no novo endereço indicado.",
        "fecho": "{local}, 15 de maio de 2026.",
    },
}
DATAS = {
    INICIAL: [("22/02/2026", "2026-02-22"), ("24/03/2026", "2026-03-24")],
    EMB: [("28/01/2026", "2026-01-28")],
    MAN: [("16/02/2026", "2026-02-16")],
}
FECHO = {
    INICIAL: ("23 de abril de 2026", "2026-04-23"),
    EMB: ("10 de abril de 2026", "2026-04-10"),
    MAN: ("15 de maio de 2026", "2026-05-15"),
}


def ficha_de(amb: Ambiente, peca: str) -> Any:
    return amb.arquivos.ler_json(f"saida/fichas/{peca}.json", Ficha).root


def rascunho_de(amb: Ambiente, tipo: str, peca: str) -> str:
    ficha = ficha_de(amb, peca)
    montada = json.loads(amb.arquivos.ler_texto(f"saida/preparacao/{tipo}_estrutura.json"))
    blocos = []
    for bloco in montada["blocos"]:
        corpo = CORPO[tipo].get(bloco["nome"], "Conteúdo próprio deste bloco da peça.")
        texto = corpo.format(juizo=ficha.processo.juizo, local=ficha.local_peca)
        blocos.append(f"## {bloco['titulo']}\n\n{texto}")
    return f"{MARCA}\n\n" + "\n\n".join(blocos) + "\n"


def extracao_de(amb: Ambiente, tipo: str, peca: str) -> Extracao:
    ficha = ficha_de(amb, peca)
    valores = []
    if tipo == INICIAL:
        valores = [
            {"texto": "R$ 5.000,00", "centavos": 500000, "lugar": "pedido", "pedido": "dano moral"},
            {"texto": "R$ 300,00", "centavos": 30000, "lugar": "pedido", "pedido": "restituição"},
            {"texto": "R$ 5.300,00", "centavos": 530000, "lugar": "valor_causa", "pedido": None},
        ]
    texto, data = FECHO[tipo]
    datas = [{"texto": t, "data": d} for t, d in DATAS[tipo]] + [{"texto": texto, "data": data}]
    return Extracao.model_validate_json(
        json.dumps(
            {
                "nomes": [],
                "documentos": [],
                "valores": valores,
                "datas": datas,
                "comarca": ficha.processo.comarca,
                "juizo": ficha.processo.juizo,
                "pedidos": [{"natureza": p.natureza, "texto": p.descricao} for p in ficha.pedidos],
                "pecas_anteriores": [],
                "data_peca": data,
            }
        )
    )


def gravar_peca(amb: Ambiente, tipo: str, peca: str) -> None:
    caminho = amb.raiz / f"saida/rascunhos/{peca}_v1.md"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(rascunho_de(amb, tipo, peca), "utf-8")
    extracao = amb.raiz / f"saida/conferencias/{peca}_v1_extracao.json"
    extracao.parent.mkdir(parents=True, exist_ok=True)
    extracao.write_text(extracao_de(amb, tipo, peca).model_dump_json(indent=2), "utf-8")


@pytest.fixture
def pecas(amb: Ambiente) -> Ambiente:
    for tipo in TIPOS:
        gravar_peca(amb, tipo, f"e01_{tipo}_001")
    return amb


def material(amb: Ambiente, tipo: str) -> ep.Material:
    return ep.material(RefPeca("e01", tipo, 1), amb.servicos)


def itens_dos_programas(m: ep.Material, texto: str, extracao: Extracao) -> dict[str, str]:
    """Os itens de programa sobre o texto e a extração (regras e citações)."""
    perfil = ep.perfil(m)
    pedidos = [i for i in m.catalogo.itens_conferencia if i in regras.ITENS_DE_REGRAS]
    resultado = regras.conferir(
        texto,
        extracao,
        m.ficha,
        m.montada,
        perfil,
        m.termos,
        m.feriados,
        m.config,
        pedidos,
    )
    itens = {r.item: r.resposta for r in resultado}
    itens["citacao_fora_da_tabela"] = citacoes.conferir(texto, m.tabela).item.resposta
    return itens


def extracao_da_copia(m: ep.Material, copia: ep.Copia) -> Extracao:
    """A mesma troca aplicada à extração da original."""
    dados = json.loads(m.extracao.model_dump_json())
    original = copia.trecho_original
    for v in dados["valores"]:
        if v["texto"] in original and copia.valor_novo is not None:
            v["texto"], v["centavos"] = copia.trecho_novo, copia.valor_novo
    for d in dados["datas"]:
        if d["texto"] == original and copia.data_nova is not None:
            d["texto"], d["data"] = copia.trecho_novo, copia.data_nova.isoformat()
            if dados["data_peca"] and copia.tipo_erro == "fora_do_prazo":
                dados["data_peca"] = copia.data_nova.isoformat()
    if copia.tipo_erro == "juizo_trocado":
        dados["juizo"] = copia.trecho_novo
    if copia.tipo_erro == "pedido_incompativel_com_rito":
        dados["pedidos"].append({"natureza": "outro", "texto": copia.trecho_novo.strip()})
    return Extracao.model_validate_json(json.dumps(dados))


# ---------------------------------------------------------------------------
# 1. Cada erro de regra é pego no item principal
# ---------------------------------------------------------------------------

REGRAS = [
    "valor_trocado",
    "data_trocada",
    "fora_do_prazo",
    "acima_da_alcada",
    "citacao_fora_da_tabela",
    "juizo_trocado",
    "termo_inequivoco",
    "pedido_incompativel_com_rito",
]


def test_original_passa_nos_programas(pecas: Ambiente) -> None:
    for tipo in TIPOS:
        m = material(pecas, tipo)
        itens = itens_dos_programas(m, m.rascunho, m.extracao)
        assert set(itens.values()) == {"passa"}, (tipo, itens)


@pytest.mark.parametrize("tipo", TIPOS)
def test_cada_erro_de_regra_e_pego_no_item_principal(pecas: Ambiente, tipo: str) -> None:
    m = material(pecas, tipo)
    catalogo = {e.tipo_erro: e for e in m.erros.erros}
    gerados = 0
    for tipo_erro in REGRAS:
        copia = ep.gerar(tipo_erro, m, random.Random(1))
        aplica = tipo in catalogo[tipo_erro].tipos
        if not aplica or (tipo_erro == "valor_trocado" and tipo == EMB):
            # Fora dos tipos do erro, ou embargos sem valor na decisão: não há cópia.
            assert copia is None, (tipo, tipo_erro)
            continue
        assert copia is not None, (tipo, tipo_erro)
        gerados += 1
        itens = itens_dos_programas(m, copia.texto, extracao_da_copia(m, copia))
        principal = catalogo[tipo_erro].item_principal
        assert itens[principal] == "nao_passa", (tipo, tipo_erro, itens)
    assert gerados >= 6


# ---------------------------------------------------------------------------
# 2. Valor e data trocados em 1.000 sementes
# ---------------------------------------------------------------------------


def test_valor_trocado_em_mil_sementes(pecas: Ambiente) -> None:
    m = material(pecas, INICIAL)
    valores = [v.centavos for v in m.ficha.valores]
    somas = {sum(c) for n in range(1, len(valores) + 1) for c in itertools.combinations(valores, n)}
    referencias = {162100, 40 * 162100}
    proibidos = set(valores) | somas | referencias
    for semente in range(1000):
        copia = ep.gerar("valor_trocado", m, random.Random(semente))
        assert copia is not None and copia.valor_novo is not None
        novo = copia.valor_novo
        assert novo not in proibidos
        assert all(abs(novo - p) > 0.01 * p for p in proibidos), (semente, novo)
        # O extenso muda junto com os algarismos.
        assert ep.formatar_reais(novo) in copia.trecho_novo
        assert f"({ep.por_extenso(novo)})" in copia.trecho_novo
        assert "(" in copia.trecho_original


def test_data_trocada_em_mil_sementes(pecas: Ambiente) -> None:
    m = material(pecas, INICIAL)
    da_ficha = ep.datas_da_ficha(m.ficha)
    for semente in range(1000):
        copia = ep.gerar("data_trocada", m, random.Random(semente))
        assert copia is not None and copia.data_nova is not None
        assert copia.data_nova not in da_ficha
        original = datetime.date.fromisoformat(
            next(d for t, d in DATAS[INICIAL] if t == copia.trecho_original)
        )
        assert (copia.data_nova.year, copia.data_nova.month) != (original.year, original.month)


def test_por_extenso() -> None:
    assert ep.por_extenso(100) == "um real"
    assert ep.por_extenso(150000) == "mil e quinhentos reais"
    assert ep.por_extenso(530000) == "cinco mil e trezentos reais"
    assert ep.por_extenso(30050) == "trezentos reais e cinquenta centavos"
    assert ep.por_extenso(12345678) == (
        "cento e vinte e três mil, quatrocentos e cinquenta e seis reais e setenta e oito centavos"
    )
    assert ep.por_extenso(100000000) == "um milhão de reais"
    assert ep.formatar_reais(12345678) == "R$ 123.456,78"


# ---------------------------------------------------------------------------
# 3. Função trocada
# ---------------------------------------------------------------------------


def test_funcao_trocada_troca_pelo_par_e_citacoes_nao_reprova(pecas: Ambiente) -> None:
    achou = 0
    for tipo in TIPOS:
        m = material(pecas, tipo)
        copia = ep.gerar("funcao_trocada", m, random.Random(3))
        assert (copia is not None) == ep.tem_par(m), tipo
        if copia is None:
            continue
        achou += 1
        antes = {
            (c.diploma, c.artigo, c.paragrafo)
            for c in citacoes.ler(m.rascunho, m.tabela).resolvidas
        }
        depois = {
            (c.diploma, c.artigo, c.paragrafo)
            for c in citacoes.ler(copia.texto, m.tabela).resolvidas
        }
        [saiu] = antes - depois
        [entrou] = depois - antes
        trecho = {citacoes.chave(d): d for d in m.trecho.dispositivos}
        velho = trecho[(saiu[0], citacoes._artigo(saiu[1]), citacoes._paragrafo(saiu[2]))]
        novo = trecho[(entrou[0], citacoes._artigo(entrou[1]), citacoes._paragrafo(entrou[2]))]
        assert (velho.diploma, velho.assunto) == (novo.diploma, novo.assunto)
        assert velho.funcao != novo.funcao
        assert citacoes.conferir(copia.texto, m.tabela).item.resposta == "passa"
    assert achou >= 1


# ---------------------------------------------------------------------------
# 4. Sorteio
# ---------------------------------------------------------------------------


def test_sorteio_da_funcao_trocada_e_dos_erros_de_regra() -> None:
    regras_do_tipo = ["data_trocada", "juizo_trocado", "termo_inequivoco"]
    pecas = [f"r01_x_{n:03d}" for n in range(1, 11)]
    viaveis = {p: list(regras_do_tipo) for p in pecas}
    # Mais da metade com par: 5 de julgamento, todas entre as que têm par.
    com_par = set(pecas[:7])
    sorteio = ep.sortear("x", 7, pecas, com_par, viaveis, regras_do_tipo)
    julgamento = [p for p, e in sorteio.items() if e == "funcao_trocada"]
    assert len(julgamento) == 5 and set(julgamento) <= com_par
    assert all(e in regras_do_tipo for p, e in sorteio.items() if p not in julgamento)
    assert sorteio == ep.sortear("x", 7, pecas, com_par, viaveis, regras_do_tipo)
    # Equilíbrio: os erros de regra se repartem entre os tipos do tipo.
    contagem = [list(sorteio.values()).count(e) for e in regras_do_tipo]
    assert max(contagem) - min(contagem) <= 1
    # Menos da metade com par: todas as que têm recebem.
    sorteio = ep.sortear("x", 7, pecas, set(pecas[:3]), viaveis, regras_do_tipo)
    assert sorted(p for p, e in sorteio.items() if e == "funcao_trocada") == pecas[:3]
    # Nenhuma com par: zero cópias de julgamento.
    sorteio = ep.sortear("x", 7, pecas, set(), viaveis, regras_do_tipo)
    assert "funcao_trocada" not in sorteio.values() and len(sorteio) == 10
    # Metade arredondada para baixo.
    sorteio = ep.sortear("x", 7, pecas[:3], set(pecas[:3]), viaveis, regras_do_tipo)
    assert list(sorteio.values()).count("funcao_trocada") == 1
    # Só erros viáveis na peça.
    so_um = {p: ["termo_inequivoco"] for p in pecas}
    sorteio = ep.sortear("x", 7, pecas, set(), so_um, regras_do_tipo)
    assert set(sorteio.values()) == {"termo_inequivoco"}


# ---------------------------------------------------------------------------
# 5 e 6. Uma só região e o gabarito
# ---------------------------------------------------------------------------


def test_uma_so_regiao_e_a_marca_no_topo(pecas: Ambiente) -> None:
    for tipo in TIPOS:
        m = material(pecas, tipo)
        for tipo_erro in [*REGRAS, "funcao_trocada"]:
            copia = ep.gerar(tipo_erro, m, random.Random(5))
            if copia is None:
                continue
            original = m.rascunho
            assert copia.texto.splitlines()[0] == MARCA
            assert copia.texto[: copia.inicio] == original[: copia.inicio]
            fim_novo = copia.inicio + len(copia.trecho_novo)
            assert copia.texto[fim_novo:] == original[copia.fim :]
            assert original[copia.inicio : copia.fim] == copia.trecho_original
            assert copia.texto[copia.inicio : fim_novo] == copia.trecho_novo
            assert copia.inicio > len(MARCA)


def test_comando_grava_a_copia_e_o_gabarito(pecas: Ambiente) -> None:
    assert pecas.executar("erros", "--rodada", "e01") == 0
    catalogo = {e.tipo_erro: e for e in material(pecas, INICIAL).erros.erros}
    for tipo in TIPOS:
        nome = f"e01_{tipo}_001_erro1_1"
        texto = pecas.arquivos.ler_texto(f"saida/erros/{nome}.md")
        assert texto.splitlines()[0] == MARCA
        g = pecas.arquivos.ler_json(f"saida/erros/{nome}_gabarito.json", Gabarito)
        entrada = catalogo[g.tipo_erro]
        assert (g.copia, g.original) == (nome, f"e01_{tipo}_001_v1")
        assert g.origem == entrada.origem and g.origem in ("programa_regra", "programa_julgamento")
        assert (g.item_principal, g.itens_aceitos) == (
            entrada.item_principal,
            entrada.itens_aceitos,
        )
        assert (g.criador, g.amostra, g.verificador, g.sutil) == ("programa", None, None, False)
    # Retomável: não refaz o que já existe.
    antes = pecas.arquivos.ler_texto(f"saida/erros/e01_{INICIAL}_001_erro1_1.md")
    assert pecas.executar("erros", "--rodada", "e01") == 0
    assert pecas.arquivos.ler_texto(f"saida/erros/e01_{INICIAL}_001_erro1_1.md") == antes


# ---------------------------------------------------------------------------
# 7. Peças boas na rodada; as três no ensaio
# ---------------------------------------------------------------------------


def cartao(amb: Ambiente, peca: str, ficha: str, veredito: str) -> None:
    respostas = RespostasCartao.model_validate_json(
        json.dumps(
            {
                "id_cartao": peca,
                "tipo_cartao": "revisao",
                "veredito_ficha": ficha,
                "veredito_peca": veredito,
                "dado_real": False,
                "dado_real_trecho": None,
                "citacoes_nao_resolvidas": [],
                "formato_certo": None,
                "formato_errado": None,
                "amostra": [],
                "data_confirmacao": "2026-11-21T12:00:00+00:00",
            }
        )
    )
    amb.arquivos.gravar_json(f"saida/cartoes/{peca}_respostas.json", respostas)


def test_so_pecas_boas_na_rodada_e_as_tres_no_ensaio(pecas: Ambiente) -> None:
    arquivos = pecas.arquivos
    lidas = arquivos.ler_json("saida/rodadas.json", Rodadas).rodadas
    r01 = Rodada.model_validate_json(
        lidas[0].model_copy(update={"id": "r01", "ensaio_aprovado_origem": "e01"}).model_dump_json()
    )
    arquivos.regravar_rodadas(Rodadas(rodadas=[*lidas, r01]))
    for n, (ficha, peca_) in enumerate(
        [
            ("aprovada", "aprovada"),
            ("aprovada", "reprovada"),
            ("reprovada", "aprovada"),
            (None, None),
        ],
        start=1,
    ):
        nome = f"r01_{INICIAL}_{n:03d}"
        for sufixo in (".json", "_base.json"):
            origem = pecas.raiz / f"saida/fichas/e01_{INICIAL}_001{sufixo}"
            (pecas.raiz / f"saida/fichas/{nome}{sufixo}").write_text(origem.read_text("utf-8"))
        gravar_peca(pecas, INICIAL, nome)
        if ficha is not None:
            cartao(pecas, nome, ficha, peca_)
    boas = ep.pecas_base("r01", pecas.servicos)
    assert [r.id for r in boas] == [f"r01_{INICIAL}_001"]
    assert pecas.executar("erros", "--rodada", "r01") == 0
    assert arquivos.listar("saida/erros", "r01_*.md") == [
        f"saida/erros/r01_{INICIAL}_001_erro1_1.md"
    ]
    # No ensaio, as três, qualquer que seja o veredito (aqui, sem veredito nenhum).
    assert sorted(r.id for r in ep.pecas_base("e01", pecas.servicos)) == sorted(
        f"e01_{t}_001" for t in TIPOS
    )


def test_comando_erros_sem_rodada_e_recusado(pecas: Ambiente) -> None:
    assert pecas.executar("erros") == 2
    assert pecas.executar("erros", "--rodada", "r99") == 1


def test_nenhum_arquivo_fora_de_saida(pecas: Ambiente) -> None:
    pecas.executar("erros", "--rodada", "e01")
    assert not any(Path(p).parts[0] != "saida" for p in pecas.arquivos.listar("saida", "**/*"))
