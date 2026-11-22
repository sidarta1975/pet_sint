"""Teste de aceite do brief 023: `fabrica/relatorios.py`, `relatorio` e `ensaio --fechar`.

Registro, ocorrências, conferências, cartões e resultado do teste falsos, escritos aqui
numa pasta temporária nos formatos de `formatos.py`. Nenhum modelo é chamado.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
from pathlib import Path
from typing import Any

import pytest

from fabrica import relatorios as rel
from fabrica import teste_conferentes as tc
from fabrica.comum.formatos import (
    Chamada,
    Ocorrencia,
    ResultadoTeste,
    Rodada,
    Rodadas,
)
from fabrica.conferencia.regras import MARCA
from testes.test_conferencia_etapas import TIPOS, amb
from testes.test_fichas import Ambiente, git, preparar

__all__ = ["amb"]  # a fixture vem do teste do brief 017

INICIAL, EMB, MAN = "peticao_inicial_jec", "embargos_declaracao", "manifestacao_ar_negativo"
R = "r01"
MOMENTO = "2026-11-21T12:00:00+00:00"
ITENS_DA_SECAO = [
    "## 1. Critérios da seção 6",
    "## Ressalvas",
    "## 2. Reprovações de peças boas",
    "## 3. O que a regra de estilo teria reprovado",
    "## 4. Custos",
    "## 5. Modelo local",
    "## 6. Causas de reprovação e fichas reprovadas",
    "## 7. Pausas e intervenções",
    "## 8. Peças por tipo e casas vazias",
    "## 9. Cópias descartadas",
    "## 10. Tipos de erro do banco final",
    "## 11. Pedidos ao modelo local que não couberam no contexto",
    "## 12. Tokens reais de cada tarefa, medidos no ensaio",
    "## 13. Reprovações por coerência com a ficha",
    "## 14. Erros não pegos, por conferente e por tipo de erro",
]
CRITERIOS = [
    "Erros plantados pegos (critério central)",
    "Ponta a ponta",
    "Peças boas reprovadas por engano na primeira versão",
    "Reprovação só por semelhança",
    "Dado real proibido",
    "Custo marginal por peça aprovada",
    "Gasto total do MVP",
    "Concordância entre a fábrica e o responsável",
    "Notas de estilo",
]


# ---------------------------------------------------------------------------
# A rodada falsa
# ---------------------------------------------------------------------------


def gravar(amb_: Ambiente, caminho: str, texto: str) -> None:
    destino = amb_.raiz / caminho
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, "utf-8")


def rodadas(amb_: Ambiente, *ids: str) -> None:
    lidas = []
    for i in ids:
        lidas.append(
            Rodada.model_validate_json(
                json.dumps(
                    {
                        "id": i,
                        "semente": 7,
                        "impressoes": {},
                        "ensaio_aprovado_origem": None if i.startswith("e") else "e01",
                        "estado": "aberta",
                        "aberta_em": MOMENTO,
                        "ensaio_aprovado": not i.startswith("r"),
                        "aprovado_em": MOMENTO if i.startswith("e") else None,
                    }
                )
            )
        )
    amb_.arquivos.regravar_rodadas(Rodadas(rodadas=lidas))


def pedido_de_ficha(amb_: Ambiente, peca: str) -> None:
    dados: dict[str, Any] = {
        "nome": f"{peca}_ficha_t1",
        "servico": "claude",
        "rodada": peca[:3],
        "peca": peca,
        "versao": None,
        "tarefa": "ficha",
        "tentativa": 1,
        "modelo": "claude-haiku-5-5",
        "esforco": None,
        "teto_saida": 100,
        "partes": [],
        "formato": None,
        "esquema": None,
        "criado_em": MOMENTO,
    }
    gravar(amb_, f"saida/pedidos/{peca}_ficha_t1.json", json.dumps(dados))


def conferencia(
    amb_: Ambiente,
    peca: str,
    versao: int,
    veredito: str,
    categoria: str | None = None,
    notas: tuple[int, int, int] = (4, 4, 4),
    itens: list[dict[str, Any]] | None = None,
) -> None:
    dados: dict[str, Any] = {
        "peca": peca,
        "versao": versao,
        "extracao": None,
        "itens": itens or [],
        "caminho": [],
        "notas_estilo": dict(zip(("clareza", "concisao", "linguagem_tecnica"), notas, strict=True)),
        "alertas": [],
        "veredito": veredito,
        "categoria_motivo": categoria if veredito != "aprovada" else None,
        "motivo": "" if veredito == "aprovada" else f"motivo de {peca}",
        "semelhanca": None,
        "conferencia_local": None,
        "modo_teste": False,
    }
    gravar(amb_, f"saida/conferencias/{peca}_v{versao}.json", json.dumps(dados))


def cartao(
    amb_: Ambiente,
    peca: str,
    ficha: str = "aprovada",
    veredito: str = "aprovada",
    dado_real: bool = False,
) -> None:
    dados: dict[str, Any] = {
        "id_cartao": peca,
        "tipo_cartao": "revisao",
        "veredito_ficha": ficha,
        "veredito_peca": veredito,
        "dado_real": dado_real,
        "dado_real_trecho": "CPF 123" if dado_real else None,
        "citacoes_nao_resolvidas": [],
        "formato_certo": None,
        "formato_errado": None,
        "amostra": [],
        "data_confirmacao": MOMENTO,
    }
    gravar(amb_, f"saida/cartoes/{peca}_respostas.json", json.dumps(dados))


def local(amb_: Ambiente, peca: str, rodou: bool = True) -> None:
    dados: dict[str, Any] = {
        "resultado": "rodou" if rodou else "indisponivel",
        "causa": None if rodou else "janela",
        "respostas": {"itens": []} if rodou else None,
        "fracao_contexto": 0.3,
        "duracao_segundos": 12.0,
    }
    gravar(amb_, f"saida/conferencias/{peca}_v1_local.json", json.dumps(dados))


def chamada(
    amb_: Ambiente, rodada: str, peca: str, centavos: float, tarefa: str = "redacao_risco_medio"
) -> None:
    amb_.servicos.registro.chamada(
        Chamada(
            rodada=rodada,
            peca=peca,
            pedido=f"{peca}_{tarefa}_t1",
            tarefa=tarefa,  # type: ignore[arg-type]
            modelo="claude-sonnet-5-5",
            tokens_entrada=1000,
            tokens_cache=0,
            tokens_raciocinio=0,
            tokens_saida=200,
            custo_milionesimos=round(centavos * 1_000_000),
            duracao_segundos=1.0,
            momento=datetime.datetime(2026, 11, 21, tzinfo=datetime.UTC),
        )
    )


def ocorrencia(
    amb_: Ambiente,
    tipo: str,
    causa: str,
    rodada: str = R,
    peca: str | None = None,
    detalhe: str = "x",
) -> None:
    amb_.servicos.registro.ocorrencia(
        Ocorrencia(
            tipo=tipo,  # type: ignore[arg-type]
            causa=causa,
            inicio=datetime.datetime(2026, 11, 21, tzinfo=datetime.UTC),
            fim=None,
            peca=peca,
            rodada=rodada,
            detalhe=detalhe,
        )
    )


def taxa(s: int, t: int) -> dict[str, Any]:
    return {
        "sucessos": s,
        "total": t,
        "taxa": s / t if t else None,
        "inferior": None,
        "superior": None,
    }


def resultado_do_teste(amb_: Ambiente, rodada: str = R, **troca: Any) -> None:
    banco = {
        "copias": 50,
        "copias_ia": 40,
        "rejeitadas": [],
        "descartadas": 3,
        "descartadas_com_erro": [],
        "nao_confiavel": False,
        "filtrado_pelo_verificador": False,
        **troca.pop("banco", {}),
    }
    dados: dict[str, Any] = {
        "rodada": rodada,
        "gravado_em": MOMENTO,
        "banco": banco,
        "criterio_central": taxa(34, 40),
        "sem_opus": taxa(30, 40),
        "julgamento_programa": taxa(6, 8),
        "julgamento_inconclusivo": False,
        "regra_programa": taxa(2, 2),
        "regra_sanidade_ok": True,
        "reprovacao_pecas_boas": taxa(1, 25),
        "decisao_criterio_central": "passa",
        "dependente_do_opus": False,
        "nao_pegas_formato": [],
        "copias": [
            {
                "copia": f"{R}_{INICIAL}_001_erro2_1",
                "original": f"{R}_{INICIAL}_001_v1",
                "origem": "opus",
                "tipo_erro": "cabimento",
                "sutil": True,
                "pego": False,
                "pego_sem_opus": False,
                "itens_pegos": [],
                "conferentes": [],
                "formato": False,
            }
        ],
        "por_conferente": {},
        "por_tipo_erro": {},
        "por_origem": {},
        **troca,
    }
    gravar(
        amb_,
        tc.caminho_relatorio(rodada),
        json.dumps(ResultadoTeste.model_validate_json(json.dumps(dados)).model_dump(mode="json")),
    )


def montar_rodada(amb_: Ambiente, boas: int = 25, por_tipo: int = 10) -> list[str]:
    """30 peças (10 por tipo); as `boas` primeiras com os dois vereditos aprovados."""
    rodadas(amb_, "e01", R)
    nomes = []
    for tipo in TIPOS:
        for n in range(1, por_tipo + 1):
            nomes.append(f"{R}_{tipo}_{n:03d}")
    for i, peca in enumerate(nomes):
        pedido_de_ficha(amb_, peca)
        gravar(amb_, f"saida/rascunhos/{peca}_v1.md", f"{MARCA}\n\nTexto.\n")
        conferencia(amb_, peca, 1, "aprovada")
        cartao(amb_, peca, "aprovada", "aprovada" if i < boas else "reprovada")
        if not peca.split("_")[1].startswith("manifestacao"):
            local(amb_, peca)
        chamada(amb_, R, peca, 5)
    return nomes


@pytest.fixture
def sint(tmp_path: Path) -> Ambiente:
    return Ambiente(preparar(tmp_path))


def relatorio(amb_: Ambiente, rodada: str = R) -> str:
    assert amb_.executar("relatorio", "--rodada", rodada) == 0
    return amb_.arquivos.ler_texto(rel.caminho_relatorio(rodada))


def bloco(texto: str, titulo: str) -> str:
    inicio = texto.index(f"### {titulo}")
    fim = texto.find("\n### ", inicio + 1)
    return texto[inicio : fim if fim != -1 else texto.index("## Ressalvas")]


# ---------------------------------------------------------------------------
# 1 e 6. Cada item de 5.11, na ordem, e a última linha
# ---------------------------------------------------------------------------


def test_relatorio_traz_cada_item_na_ordem(sint: Ambiente) -> None:
    montar_rodada(sint)
    resultado_do_teste(sint)
    texto = relatorio(sint)
    assert sint.arquivos.existe("saida/relatorios/relatorio_mvp.md")
    posicoes = [texto.index(t) for t in ITENS_DA_SECAO]
    assert posicoes == sorted(posicoes)
    criterios = [texto.index(f"### {c}") for c in CRITERIOS]
    assert criterios == sorted(criterios) and criterios[0] < texto.index("### Ponta a ponta")
    central = bloco(texto, CRITERIOS[0])
    assert "34 de 40" in central and "passa" in central
    assert "Ao lado: taxa sem o Opus: 30 de 40" in central
    assert "Ao lado: erros de julgamento feitos por programa: 6 de 8" in central
    assert "Wilson" in central
    for nome in CRITERIOS:
        b = bloco(texto, nome)
        assert "- Resultado:" in b and "- Exigência:" in b and "- Margem:" in b
        papel = "indicador" if nome in CRITERIOS[3:4] + CRITERIOS[6:] else "decide"
        assert f"- Papel: {papel}" in b, nome
    assert "Os números deste relatório são da rodada r01." in texto
    assert texto.rstrip().splitlines()[-1] == rel.FINAL
    assert "## Ressalvas\n\n- Nenhuma." in texto
    assert "intervenção" not in texto.split("## 1.")[0]
    # O relatório não decide: nenhuma frase de decisão de escalar.
    assert "escalar: sim" not in texto.lower() and "pode escalar" not in texto.lower()
    # Não regrava.
    assert sint.executar("relatorio", "--rodada", R) == 0


# ---------------------------------------------------------------------------
# 2. As ressalvas, cada uma sozinha, com o seu gatilho
# ---------------------------------------------------------------------------


def test_ressalva_dependente_do_opus(sint: Ambiente) -> None:
    montar_rodada(sint)
    resultado_do_teste(sint, dependente_do_opus=True)
    ressalvas = relatorio(sint).split("## Ressalvas")[1].split("## 2.")[0]
    assert "dependente do Opus" in ressalvas
    assert (
        "filtrado" not in ressalvas
        and "estável" not in ressalvas
        and "não confiável" not in ressalvas
    )


def test_ressalva_filtrado_pelo_verificador(sint: Ambiente) -> None:
    montar_rodada(sint)
    resultado_do_teste(
        sint, banco={"filtrado_pelo_verificador": True, "descartadas_com_erro": ["a", "b"]}
    )
    texto = relatorio(sint)
    ressalvas = texto.split("## Ressalvas")[1].split("## 2.")[0]
    assert "filtrado pelo verificador" in ressalvas and "dependente" not in ressalvas
    assert "Passa" not in ressalvas and "não decide" not in bloco(texto, CRITERIOS[0])


def test_ressalva_sem_conferente_local_estavel(sint: Ambiente) -> None:
    montar_rodada(sint)
    resultado_do_teste(sint)
    # 5 de 20 peças de risco médio e alto (25%) sem a resposta do modelo local.
    for n in range(1, 6):
        (sint.raiz / f"saida/conferencias/{R}_{INICIAL}_{n:03d}_v1_local.json").unlink()
        local(sint, f"{R}_{INICIAL}_{n:03d}", rodou=False)
    ressalvas = relatorio(sint).split("## Ressalvas")[1].split("## 2.")[0]
    assert "sem conferente local estável" in ressalvas and "5 de 20" in ressalvas
    assert "dependente" not in ressalvas


def test_sem_ressalva_local_com_20_por_cento(sint: Ambiente) -> None:
    montar_rodada(sint)
    resultado_do_teste(sint)
    for n in range(1, 5):  # 4 de 20: não passa de 20%
        (sint.raiz / f"saida/conferencias/{R}_{INICIAL}_{n:03d}_v1_local.json").unlink()
    assert "sem conferente local estável" not in relatorio(sint)


def test_banco_nao_confiavel_o_criterio_central_nao_decide(sint: Ambiente) -> None:
    montar_rodada(sint)
    resultado_do_teste(sint, banco={"nao_confiavel": True, "rejeitadas": ["x", "y"]})
    texto = relatorio(sint)
    assert "banco não confiável" in texto.split("## Ressalvas")[1]
    assert "o critério central é calculado, mas não decide" in bloco(texto, CRITERIOS[0])


def test_central_inconclusivo_com_menos_de_14_boas(sint: Ambiente) -> None:
    montar_rodada(sint, boas=13)
    resultado_do_teste(sint)
    central = bloco(relatorio(sint), CRITERIOS[0])
    assert "inconclusivo: menos de 14 peças boas" in central


def test_inconclusivo_depois_de_um_corte_de_gasto(sint: Ambiente) -> None:
    montar_rodada(sint)
    ocorrencia(sint, "parada", rel.CORTE)
    texto = relatorio(sint)  # sem o resultado do teste: ele não foi feito
    assert "inconclusivo: o teste dos conferentes não foi feito, depois de um corte de gasto" in (
        bloco(texto, CRITERIOS[0])
    )


# ---------------------------------------------------------------------------
# 3. O limite de peças boas reprovadas e a semelhança à parte
# ---------------------------------------------------------------------------


def test_limite_de_pecas_boas_reprovadas_pela_proporcao() -> None:
    for boas in range(20, 30):
        assert rel.limite_de_boas_reprovadas(boas, 0.10) == 2
    for boas in range(14, 20):
        assert rel.limite_de_boas_reprovadas(boas, 0.10) == 1


@pytest.mark.parametrize(
    ("conteudo", "esperado"), [(2, "passa: 2 de 25"), (3, "não passa: 3 de 25")]
)
def test_reprovadas_por_conteudo_e_por_semelhanca(
    sint: Ambiente, conteudo: int, esperado: str
) -> None:
    nomes = montar_rodada(sint)
    resultado_do_teste(sint)
    categorias = ["conteudo", "ambos", "formato"]
    for i in range(conteudo):
        (sint.raiz / f"saida/conferencias/{nomes[i]}_v1.json").unlink()
        conferencia(sint, nomes[i], 1, "refazer", categorias[i % 3])
    (sint.raiz / f"saida/conferencias/{nomes[10]}_v1.json").unlink()
    conferencia(sint, nomes[10], 1, "refazer", "semelhanca")
    texto = relatorio(sint)
    boas = bloco(texto, CRITERIOS[2])
    assert esperado in boas and "(limite: 2)" in boas
    so = bloco(texto, CRITERIOS[3])
    assert f"1: {nomes[10]}" in so and "revisto antes do piloto" in so
    assert f"- Por semelhança: 1 ({nomes[10]})" in texto


# ---------------------------------------------------------------------------
# 4. Custos
# ---------------------------------------------------------------------------


def test_custo_marginal_exclui_ensaio_copias_e_teste(sint: Ambiente) -> None:
    montar_rodada(sint)  # 30 peças a 5 centavos: 150 centavos para 30 aprovadas
    resultado_do_teste(sint)
    chamada(sint, R, f"{R}_{INICIAL}_001_erro2_1_banco", 900, "copia_com_erro")
    chamada(sint, R, f"teste_{R}_{INICIAL}_001", 900, "extracao")
    chamada(sint, "e01", f"e01_{INICIAL}_001", 300)
    texto = relatorio(sint)
    custo = bloco(texto, CRITERIOS[5])
    assert "US$ 0.0500 por peça aprovada (30 aprovada(s))" in custo
    assert "rever antes de escalar" not in custo.split("- Exigência")[0]
    gasto = bloco(texto, CRITERIOS[6])
    assert "US$ 22.5000" in gasto  # 150 + 900 + 900 + 300 centavos


def test_custo_marginal_acima_de_15_centavos(sint: Ambiente) -> None:
    montar_rodada(sint)
    resultado_do_teste(sint)
    chamada(sint, R, f"{R}_{INICIAL}_001", 400)  # 550 centavos para 30: 18 centavos
    custo = bloco(relatorio(sint), CRITERIOS[5])
    assert "rever antes de escalar" in custo.split("- Exigência")[0]


# ---------------------------------------------------------------------------
# 5. Intervenção, rodada dos números, peças por tipo e fichas reprovadas
# ---------------------------------------------------------------------------


def test_intervencao_tipos_e_fichas_reprovadas(sint: Ambiente) -> None:
    montar_rodada(sint)
    resultado_do_teste(sint)
    ocorrencia(sint, "intervencao", "manual", detalhe="o responsável mexeu num arquivo")
    # Manifestação: a casa 10 ficou vazia; a peça 010 não fechou.
    (sint.raiz / f"saida/rascunhos/{R}_{MAN}_010_v1.md").unlink()
    gravar(
        sint,
        f"saida/fichas/{R}_{MAN}_casa10_vazia.json",
        json.dumps({"rodada": R, "tipo": MAN, "casa": 10, "ultima_peca": f"{R}_{MAN}_012"}),
    )
    gravar(
        sint,
        f"saida/fichas/{R}_{MAN}_012_descartada.json",
        json.dumps(
            {"peca": f"{R}_{MAN}_012", "casa": 10, "tentativa": 3, "causa": "fato fora do período"}
        ),
    )
    # Embargos: 3 de 10 fichas reprovadas pelo responsável (30%, acima de 20%).
    for n in range(1, 4):
        cartao(sint, f"{R}_{EMB}_{n:03d}", ficha="reprovada", veredito="reprovada")
    texto = relatorio(sint)
    assert "Os números vieram de uma rodada com intervenção." in texto
    assert f"- {MAN}: fechou 9 de 10." in texto and f"- {INICIAL}: fechou 10 de 10." in texto
    assert "casa 10 vazia: fato fora do período" in texto
    assert f"`ficha.md` e `fichas.py` do tipo {EMB}" in texto
    assert f"`ficha.md` e `fichas.py` do tipo {INICIAL}" not in texto
    assert "intervencao · manual" in texto
    assert "1 intervenção(ões) manual(is)" in bloco(texto, CRITERIOS[1])


def test_relatorio_do_ensaio_com_o_aviso(sint: Ambiente) -> None:
    rodadas(sint, "e01")
    for tipo in TIPOS:
        peca = f"e01_{tipo}_001"
        pedido_de_ficha(sint, peca)
        gravar(sint, f"saida/rascunhos/{peca}_v1.md", f"{MARCA}\n\nTexto.\n")
        conferencia(sint, peca, 1, "aprovada")
    chamada(sint, "e01", f"e01_{INICIAL}_001", 3, "extracao")
    ocorrencia(
        sint,
        "contexto",
        "acima_do_limite_do_ensaio",
        "e01",
        f"e01_{EMB}_001_v1",
        "pedido local grande",
    )
    texto = relatorio(sint, "e01")
    assert sint.arquivos.existe("saida/relatorios/relatorio_e01.md")
    assert texto.splitlines()[2] == f"**{rel.AVISO_ENSAIO.capitalize()}.**"
    for nome in CRITERIOS:
        assert f"### {nome} ({rel.AVISO_ENSAIO})" in texto
    assert "| extracao | 1 |" in texto  # tokens reais do ensaio
    assert "pedido local grande" in texto.split("## 11.")[1].split("## 12.")[0]


# ---------------------------------------------------------------------------
# 7. Fechamento do ensaio
# ---------------------------------------------------------------------------


def ensaio_completo(amb_: Ambiente) -> None:
    """O ensaio do teste do 017 levado, com arquivos falsos, até o relatório."""
    for tipo in TIPOS:
        peca = f"e01_{tipo}_001"
        conferencia(amb_, peca, 1, "aprovada")
        dados: dict[str, Any] = {
            "id_cartao": peca,
            "tipo_cartao": "ensaio",
            "veredito_ficha": None,
            "veredito_peca": None,
            "dado_real": False,
            "dado_real_trecho": None,
            "citacoes_nao_resolvidas": [],
            "formato_certo": True,
            "formato_errado": None,
            "amostra": [],
            "data_confirmacao": MOMENTO,
        }
        gravar(amb_, f"saida/cartoes/{peca}_respostas.json", json.dumps(dados))
        gravar(amb_, f"saida/pacotes/ensaio_e01/{tipo}/{peca}_v1.md", f"{MARCA}\n")
        gravar(amb_, f"saida/erros/{peca}_erro2_1.md", f"{MARCA}\n")
    gravar(
        amb_,
        "saida/erros/e01_amostras.json",
        json.dumps({"rodada": "e01", "copias": [], "descartadas": [], "sorteado_em": MOMENTO}),
    )
    resultado_do_teste(amb_, "e01")
    gravar(amb_, rel.caminho_relatorio("e01"), "relatório\n")


def aprovado(amb_: Ambiente) -> bool:
    lidas = amb_.arquivos.ler_json("saida/rodadas.json", Rodadas)
    return next(r for r in lidas.rodadas if r.id == "e01").ensaio_aprovado


def test_ensaio_completo_e_aprovado(amb: Ambiente) -> None:
    ensaio_completo(amb)
    antes = amb.arquivos.ler_json("saida/rodadas.json", Rodadas).rodadas[0]
    fechamento = rel.fechar_ensaio("e01", [], amb.servicos)
    assert fechamento.aprovado, fechamento.motivos
    depois = amb.arquivos.ler_json("saida/rodadas.json", Rodadas).rodadas[0]
    assert depois.ensaio_aprovado and depois.aprovado_em is not None
    assert depois.impressoes == antes.impressoes and depois.impressoes
    assert amb.arquivos.listar("saida/registro/rodadas_anteriores", "*.json")
    # Já aprovado: fechar de novo não regrava.
    assert not rel.fechar_ensaio("e01", [], amb.servicos).aprovado


@pytest.mark.parametrize(
    ("estrago", "motivo"),
    [
        ("cartao", "não confirmou o formato certo"),
        ("pacote", "sem pacote"),
        ("copias", "sem cópia com erro"),
        ("amostras", "sem o sorteio das amostras"),
        ("teste", "sem o resultado do teste dos conferentes"),
        ("relatorio", "sem o relatório do ensaio"),
        ("conferencia", "sem conferência da primeira versão"),
        ("formato", "resposta fora do formato"),
        ("congelado", "arquivos congelados mudaram"),
    ],
)
def test_ensaio_reprovado_mostra_o_motivo_e_nao_grava(
    amb: Ambiente, estrago: str, motivo: str, capsys: pytest.CaptureFixture[str]
) -> None:
    ensaio_completo(amb)
    peca = f"e01_{INICIAL}_001"
    raiz = amb.raiz
    if estrago == "cartao":
        dados = json.loads((raiz / f"saida/cartoes/{peca}_respostas.json").read_text("utf-8"))
        dados.update(formato_certo=False, formato_errado="faltou o fecho")
        (raiz / f"saida/cartoes/{peca}_respostas.json").write_text(json.dumps(dados), "utf-8")
    elif estrago == "pacote":
        (raiz / f"saida/pacotes/ensaio_e01/{INICIAL}/{peca}_v1.md").unlink()
    elif estrago == "copias":
        (raiz / f"saida/erros/{peca}_erro2_1.md").unlink()
    elif estrago == "amostras":
        (raiz / "saida/erros/e01_amostras.json").unlink()
    elif estrago == "teste":
        (raiz / tc.caminho_relatorio("e01")).unlink()
    elif estrago == "relatorio":
        (raiz / rel.caminho_relatorio("e01")).unlink()
    elif estrago == "conferencia":
        (raiz / f"saida/conferencias/{peca}_v1.json").unlink()
    elif estrago == "formato":
        primeiro = next((raiz / "saida/pedidos").glob("e01_*_ficha_t1.json"))
        dados = json.loads(primeiro.read_text("utf-8"))
        dados.update(nome=dados["nome"].replace("_t1", "_t2"), tentativa=2)
        (raiz / "saida/pedidos" / f"{dados['nome']}.json").write_text(json.dumps(dados), "utf-8")
    else:
        alvo = raiz / "dados/catalogo/tipos.json"
        alvo.write_text(alvo.read_text("utf-8") + "\n", "utf-8")
    fechamento = rel.fechar_ensaio("e01", [], amb.servicos)
    assert not fechamento.aprovado
    assert any(motivo in m for m in fechamento.motivos), fechamento.motivos
    assert not aprovado(amb)


def test_contexto_do_modelo_local_no_ensaio(amb: Ambiente) -> None:
    ensaio_completo(amb)
    ocorrencia(
        amb, "contexto", "acima_do_limite_do_ensaio", "e01", f"e01_{EMB}_001_v1", "e01_x_local_t1"
    )
    fechamento = rel.fechar_ensaio("e01", [], amb.servicos)
    assert not fechamento.aprovado and not aprovado(amb)
    texto = " ".join(fechamento.motivos)
    assert "16.384" in texto and "32.768" in texto and "ensaio novo" in texto
    # Com 32.768, o ensaio passa nesse ponto e o pedido fica listado.
    geral = amb.servicos.config.geral
    maior = geral.model_copy(
        update={"modelo_local": geral.modelo_local.model_copy(update={"num_ctx": 32768})}
    )
    servicos = dataclasses.replace(
        amb.servicos, config=dataclasses.replace(amb.servicos.config, geral=maior)
    )
    fechamento = rel.fechar_ensaio("e01", [], servicos)
    assert fechamento.aprovado, fechamento.motivos
    assert any("e01_x_local_t1" in a for a in fechamento.avisos)


def test_comandos_relatorio_e_ensaio_fechar(
    amb: Ambiente, capsys: pytest.CaptureFixture[str]
) -> None:
    assert amb.executar("relatorio") == 2
    assert amb.executar("relatorio", "--rodada", "r09") == 1
    assert amb.executar("ensaio", "--fechar") == 2
    assert amb.executar("ensaio", "--fechar", "e01") == 1
    assert "ensaio reprovado" in capsys.readouterr().err
    assert not aprovado(amb)
    git(amb.raiz, "status")  # o repositório da pasta temporária continua íntegro
