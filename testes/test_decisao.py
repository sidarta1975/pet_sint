"""Teste de aceite do brief 018: `decisao.py`, `desempate.py` e `semelhanca.py`.

Resultados de conferência de exemplo escritos no teste. As etapas rodam na pasta
temporária do `test_conferencia_etapas.py`, com o cliente da API falso.
"""

from __future__ import annotations

import dataclasses
import json
from fractions import Fraction
from typing import Any

from fabrica import estado
from fabrica.comum.formatos import (
    Conferencia,
    Pedido,
    RespostaChecklist,
    RespostaDesempate,
    ResultadoConferenteLocal,
    ResultadoProgramas,
    ResultadoSemelhanca,
)
from fabrica.conferencia import decisao, desempate, semelhanca
from fabrica.conferencia.decisao import Entradas
from fabrica.conferencia.regras import MARCA
from fabrica.estado import RefPeca
from testes.test_conferencia_etapas import B2, EMB, INICIAL, MAN, amb, rascunho, resposta
from testes.test_fichas import RAIZ, Ambiente

__all__ = ["amb"]  # a fixture vem do teste do brief 017

PROGRAMA = ["estrutura", "citacao_fora_da_tabela", "termos_inequivocos", "coerencia_ficha"]
ELIMINATORIOS = frozenset(PROGRAMA + ["semelhanca", *B2[EMB]])
CLASSE = {INICIAL: "medio", EMB: "alto", MAN: "baixo"}


def programas(nao_passa: tuple[str, ...] = ()) -> ResultadoProgramas:
    return ResultadoProgramas.model_validate(
        {
            "itens": [
                {
                    "item": i,
                    "resposta": "nao_passa" if i in nao_passa else "passa",
                    "quem": "programa",
                    "trecho": f"programa {i}",
                    "divergencias": [],
                }
                for i in PROGRAMA
            ],
            "alertas": [],
            "citacoes_resolvidas": [],
            "citacoes_nao_resolvidas": [],
        }
    )


def checklist(tipo: str, nao_passa: tuple[str, ...] = (), notas: int = 4) -> RespostaChecklist:
    return RespostaChecklist.model_validate(
        {
            "itens": [
                {"item": i, "resposta": "nao_passa" if i in nao_passa else "passa", "trecho": "h"}
                for i in B2[tipo]
            ],
            "citacoes": [],
            "notas": {"clareza": notas, "concisao": notas, "linguagem_tecnica": notas},
        }
    )


def local(respostas: dict[str, str] | None) -> ResultadoConferenteLocal:
    return ResultadoConferenteLocal.model_validate(
        {
            "resultado": "rodou" if respostas is not None else "indisponivel",
            "causa": None if respostas is not None else "janela",
            "respostas": None
            if respostas is None
            else {
                "itens": [{"item": i, "resposta": r, "trecho": "l"} for i, r in respostas.items()]
            },
            "fracao_contexto": 0.3,
            "duracao_segundos": 1.0,
        }
    )


def opus(respostas: dict[str, str]) -> RespostaDesempate:
    return RespostaDesempate.model_validate(
        {"itens": [{"item": i, "resposta": r, "justificativa": "o"} for i, r in respostas.items()]}
    )


def similar(
    valor: float | None, reprova: bool = False, desligada: bool = False
) -> ResultadoSemelhanca:
    return ResultadoSemelhanca(
        valor=valor,
        comparada_com="saida/aprovadas/x_v1.md" if valor is not None else None,
        limite=0.85,
        reprova=reprova,
        desligada=desligada,
    )


def entradas(tipo: str, **troca: Any) -> Entradas:
    dados: dict[str, Any] = {
        "peca": f"e01_{tipo}_001",
        "versao": 1,
        "classe": CLASSE[tipo],
        "versoes_maximas": 3,
        "itens_conferente": B2[tipo],
        "eliminatorios": ELIMINATORIOS,
        "programas": programas(),
        "checklist": checklist(tipo),
        "local": None,
        "desempate": None,
        "semelhanca": similar(0.1),
    }
    dados.update(troca)
    return Entradas(**dados)


def caminho(conferencia: Conferencia, item: str) -> tuple[str, str, str]:
    c = next(c for c in conferencia.caminho if c.item == item)
    return c.regra, c.resposta_final, c.quem_final


# ---------------------------------------------------------------------------
# 1. Regras do Anexo B.3, item por item
# ---------------------------------------------------------------------------


def test_item_de_programa_vale_o_programa() -> None:
    c = decisao.decidir(entradas(MAN, programas=programas(("coerencia_ficha",))))
    assert caminho(c, "coerencia_ficha") == ("programa", "nao_passa", "programa")
    assert caminho(c, "estrutura") == ("programa", "passa", "programa")
    assert c.veredito == "refazer"


def test_itens_so_do_haiku_no_baixo_e_no_medio() -> None:
    for tipo in (MAN, INICIAL):
        loc = local({"coerencia": "passa", "texto_generico": "passa", "pecas_anteriores": "passa"})
        c = decisao.decidir(entradas(tipo, checklist=checklist(tipo, ("cabimento",)), local=loc))
        assert caminho(c, "cabimento") == ("só do Haiku", "nao_passa", "haiku")
        assert caminho(c, "fundamento") == ("só do Haiku", "passa", "haiku")


def test_haiku_e_local_que_concordam_e_que_discordam() -> None:
    loc = local({"coerencia": "nao_passa", "texto_generico": "passa"})
    c = decisao.decidir(
        entradas(
            INICIAL,
            checklist=checklist(INICIAL, ("coerencia", "texto_generico")),
            local=loc,
            desempate=opus({"texto_generico": "passa"}),
        )
    )
    assert caminho(c, "coerencia") == ("Haiku e local concordam", "nao_passa", "haiku")
    assert caminho(c, "texto_generico") == ("discordância: o Opus decide", "passa", "opus")
    respostas = next(x for x in c.caminho if x.item == "texto_generico").respostas
    assert [r.quem for r in respostas] == ["haiku", "local", "opus"]
    # No baixo, sem o conferente local (8 das 10), fica só o Haiku.
    c = decisao.decidir(entradas(MAN, checklist=checklist(MAN, ("coerencia",))))
    assert caminho(c, "coerencia") == ("sem conferente local: vale o Haiku", "nao_passa", "haiku")


def test_risco_alto_vale_o_opus_salvo_haiku_e_local_em_nao_passa() -> None:
    todos = {i: "passa" for i in B2[EMB]}
    loc = local(
        {"coerencia": "nao_passa", "pecas_anteriores": "nao_passa", "texto_generico": "passa"}
    )
    c = decisao.decidir(
        entradas(
            EMB,
            checklist=checklist(EMB, ("coerencia", "cabimento")),
            local=loc,
            desempate=opus({**todos, "fundamento": "nao_passa"}),
        )
    )
    # Haiku e local concordam em "não passa": reprova mesmo com o Opus dizendo "passa".
    assert caminho(c, "coerencia") == (
        "alto: Haiku e local concordam em não passa",
        "nao_passa",
        "haiku",
    )
    # Só o local reprovou: vale o Opus.
    assert caminho(c, "pecas_anteriores") == ("alto: vale o Opus", "passa", "opus")
    # Só o Haiku reprovou: vale o Opus.
    assert caminho(c, "cabimento") == ("alto: vale o Opus", "passa", "opus")
    assert caminho(c, "fundamento") == ("alto: vale o Opus", "nao_passa", "opus")


def test_medio_sem_local_por_72_horas_ou_contexto_vale_o_opus() -> None:
    c = decisao.decidir(
        entradas(
            INICIAL,
            checklist=checklist(INICIAL, ("coerencia",)),
            local=local(None),
            desempate=opus({"coerencia": "passa", "texto_generico": "nao_passa"}),
        )
    )
    assert caminho(c, "coerencia") == ("médio sem conferente local: vale o Opus", "passa", "opus")
    assert caminho(c, "texto_generico")[1:] == ("nao_passa", "opus")
    assert c.conferencia_local == "indisponivel"
    assert any(a.origem == "local" for a in c.alertas)


# ---------------------------------------------------------------------------
# 2. Regra única e as quatro categorias
# ---------------------------------------------------------------------------


def test_nao_passa_em_eliminatorio_reprova_e_as_categorias() -> None:
    assert decisao.decidir(entradas(MAN)).veredito == "aprovada"
    conteudo = decisao.decidir(entradas(MAN, checklist=checklist(MAN, ("pedidos",))))
    assert (conteudo.veredito, conteudo.categoria_motivo) == ("refazer", "conteudo")
    assert "pedidos" in conteudo.motivo
    so_sem = decisao.decidir(entradas(MAN, semelhanca=similar(0.9, reprova=True)))
    assert (so_sem.veredito, so_sem.categoria_motivo) == ("refazer", "semelhanca")
    assert so_sem.motivo.startswith("[semelhança]")  # a marca própria
    ambos = decisao.decidir(
        entradas(MAN, checklist=checklist(MAN, ("pedidos",)), semelhanca=similar(1.0, True))
    )
    assert ambos.categoria_motivo == "ambos"
    formato = decisao.decidir(entradas(MAN, formato="checklist"))
    assert (formato.veredito, formato.categoria_motivo) == ("descartada", "formato")
    # Na terceira versão reprovada, descartada.
    ultima = decisao.decidir(entradas(MAN, versao=3, checklist=checklist(MAN, ("pedidos",))))
    assert (ultima.veredito, ultima.categoria_motivo) == ("descartada", "conteudo")


def test_item_nao_eliminatorio_nao_reprova() -> None:
    c = decisao.decidir(
        entradas(MAN, checklist=checklist(MAN, ("pedidos",)), eliminatorios=frozenset(PROGRAMA))
    )
    assert c.veredito == "aprovada"


# ---------------------------------------------------------------------------
# 3 e 4. Notas de estilo e caminho gravado
# ---------------------------------------------------------------------------


def test_notas_de_estilo_gravadas_sem_mudar_o_veredito() -> None:
    c = decisao.decidir(entradas(MAN, checklist=checklist(MAN, notas=1)))
    assert c.veredito == "aprovada"
    assert c.notas_estilo is not None and c.notas_estilo.clareza == 1


def test_caminho_de_cada_item_fica_no_veredito() -> None:
    c = decisao.decidir(entradas(MAN))
    itens = [x.item for x in c.caminho]
    assert itens == [*PROGRAMA, "semelhanca", *B2[MAN]]
    assert [i.item for i in c.itens] == itens
    assert all(x.respostas for x in c.caminho)


# ---------------------------------------------------------------------------
# 5. Desempate: um pedido só e só nas três situações
# ---------------------------------------------------------------------------


def test_perguntas_ao_opus_so_nas_tres_situacoes() -> None:
    pergunta = desempate.perguntas
    # Baixo e médio sem discordância: nada ao Opus.
    concordam = local({"coerencia": "passa", "pecas_anteriores": "passa"})
    assert pergunta("baixo", B2[MAN], checklist(MAN), concordam) == []
    assert pergunta("baixo", B2[MAN], checklist(MAN), None) == []
    assert pergunta("baixo", B2[MAN], checklist(MAN), local(None)) == []  # baixo segue
    # Discordância.
    assert pergunta("baixo", B2[MAN], checklist(MAN, ("coerencia",)), concordam) == [
        desempate.Pergunta("coerencia", "discordancia")
    ]
    # Risco alto: todos os itens.
    assert [p.item for p in pergunta("alto", B2[EMB], checklist(EMB), None)] == B2[EMB]
    # Médio sem o conferente local: os itens dele.
    assert pergunta("medio", B2[INICIAL], checklist(INICIAL), local(None)) == [
        desempate.Pergunta("coerencia", "medio_sem_local"),
        desempate.Pergunta("texto_generico", "medio_sem_local"),
    ]


def test_desempate_numa_peca_vai_num_pedido_so(amb: Ambiente) -> None:
    r = RefPeca("e01", INICIAL, 1)
    arquivos = amb.arquivos
    arquivos.gravar_json(
        f"saida/conferencias/{r.nome_versao}_checklist.json",
        checklist(INICIAL, ("coerencia",)),
    )
    arquivos.gravar_json(
        f"saida/conferencias/{r.nome_versao}_local.json",
        local({"coerencia": "passa", "texto_generico": "nao_passa"}),
    )
    etapa = desempate.EtapaDesempate()
    assert etapa.aplica(r, amb.servicos)
    amb.cliente.fila = [
        json.dumps(
            {
                "itens": [
                    {"item": "coerencia", "resposta": "passa", "justificativa": "j"},
                    {"item": "texto_generico", "resposta": "passa", "justificativa": "j"},
                ]
            }
        )
    ]
    estado.avancar([etapa], amb.servicos, [r])
    pedidos = arquivos.listar("saida/pedidos", f"{r.nome_versao}_conferencia_opus_*.json")
    assert len(pedidos) == 1 and len(amb.cliente.enviados) == 1
    pedido = arquivos.ler_json(pedidos[0], Pedido)
    assert (pedido.tarefa, pedido.formato) == ("conferencia_opus", "RespostaDesempate")
    lista = json.loads(next(p.texto for p in pedido.partes if p.nome == "estrutura"))
    assert [(i["item"], i["situacao"]) for i in lista["itens"]] == [
        ("coerencia", "discordancia"),
        ("texto_generico", "discordancia"),
    ]
    assert pedido.partes[0].texto == (RAIZ / "instrucoes/opus_desempate.md").read_text("utf-8")
    assert arquivos.existe(f"saida/conferencias/{r.nome_versao}_desempate.json")
    # Resposta que não traz os itens pedidos: fora do formato.
    incompleta = resposta(json.dumps({"itens": []}))
    assert etapa.receber(r.com_versao(1), incompleta, amb.servicos) == estado.FORA_DO_FORMATO


def test_sem_situacao_nao_ha_pedido_ao_opus(amb: Ambiente) -> None:
    r = RefPeca("e01", INICIAL, 1)
    amb.arquivos.gravar_json(
        f"saida/conferencias/{r.nome_versao}_checklist.json", checklist(INICIAL)
    )
    amb.arquivos.gravar_json(
        f"saida/conferencias/{r.nome_versao}_local.json",
        local({"coerencia": "passa", "texto_generico": "passa"}),
    )
    assert not desempate.EtapaDesempate().aplica(r, amb.servicos)


# ---------------------------------------------------------------------------
# 6. Semelhança
# ---------------------------------------------------------------------------

TEXTO_A = (
    "A parte autora contratou o serviço de telefonia e recebeu cobrança indevida no mês "
    "seguinte, sem qualquer aviso prévio da operadora, o que motivou a reclamação."
)
TEXTO_B = (
    "O réu foi procurado em três endereços diferentes e nenhum deles era o atual, razão "
    "pela qual se pede a pesquisa nos sistemas conveniados do juízo."
)


def test_jaccard_exato_de_trechos_de_cinco_palavras() -> None:
    a = semelhanca.trechos("um dois tres quatro cinco seis".split(), 5)
    b = semelhanca.trechos("dois tres quatro cinco seis sete".split(), 5)
    assert a == {
        ("um", "dois", "tres", "quatro", "cinco"),
        ("dois", "tres", "quatro", "cinco", "seis"),
    }
    assert semelhanca.jaccard(a, b) == Fraction(1, 3)
    assert semelhanca.indice(TEXTO_A, TEXTO_A, 5) == 1
    assert semelhanca.indice(TEXTO_A, TEXTO_B, 5) < Fraction(85, 100)


def test_marca_titulos_e_marcadores_nao_contam() -> None:
    corpo = "Nome e Sobrenome da Parte Autora, OAB/UF nº 000.000, requer a citação do réu."
    um = f"{MARCA}\n\n## Dos Fatos\n\n{corpo}"
    outro = (
        "Dos Pedidos\n\nNome e Sobrenome da Parte Ré, OAB/UF nº 000.000, requer a citação do réu."
    )
    assert semelhanca.limpar(um) == semelhanca.limpar(outro, ["Dos Pedidos"])
    assert semelhanca.limpar(um) == ["requer", "a", "citacao", "do", "reu"]
    assert semelhanca.indice(um, outro, 5, ["Dos Pedidos"]) == 1


def test_semelhanca_reprova_a_copia_e_desliga_em_modo_de_teste(amb: Ambiente) -> None:
    arquivos = amb.arquivos
    primeira = RefPeca("e01", MAN, 1)
    segunda = RefPeca("e01", MAN, 2)
    texto = rascunho(amb, MAN, TEXTO_A)
    arquivos.gravar_texto(semelhanca.caminho_aprovada(primeira), texto)
    arquivos.gravar_texto(f"saida/rascunhos/{segunda.nome_versao}.md", texto)
    etapa = semelhanca.EtapaSemelhanca()
    etapa.pedir(segunda, amb.servicos)
    lido = arquivos.ler_json(etapa.arquivo_resultado(segunda), ResultadoSemelhanca)
    assert (lido.valor, lido.reprova, lido.comparada_com) == (
        1.0,
        True,
        semelhanca.caminho_aprovada(primeira),
    )
    # A própria peça não é comparada consigo: a primeira não acha com quem comparar.
    arquivos.gravar_texto(f"saida/rascunhos/{primeira.com_versao(2).nome_versao}.md", texto)
    etapa.pedir(primeira.com_versao(2), amb.servicos)
    propria = arquivos.ler_json(
        etapa.arquivo_resultado(primeira.com_versao(2)), ResultadoSemelhanca
    )
    assert (propria.valor, propria.reprova) == (None, False)
    # Modo de teste: desligada, sem mexer no config.toml.
    config = (amb.raiz / "config/config.toml").read_text("utf-8")
    teste = dataclasses.replace(amb.servicos, modo_teste=True)
    terceira = RefPeca("e01", MAN, 3)
    etapa.pedir(terceira, teste)
    desligada = arquivos.ler_json(etapa.arquivo_resultado(terceira), ResultadoSemelhanca)
    assert desligada.desligada and desligada.valor is None and not desligada.reprova
    assert (amb.raiz / "config/config.toml").read_text("utf-8") == config
    c = decisao.decidir(entradas(MAN, semelhanca=desligada, modo_teste=True))
    assert "semelhanca" not in [x.item for x in c.caminho]
    assert any(a.texto == semelhanca.DESLIGADA for a in c.alertas)


# ---------------------------------------------------------------------------
# 7. Aprovada vai para saida/aprovadas/
# ---------------------------------------------------------------------------


def test_aprovada_vai_para_aprovadas_e_e_base_da_semelhanca(amb: Ambiente) -> None:
    arquivos = amb.arquivos
    r = RefPeca("e01", MAN, 1)
    base = f"saida/conferencias/{r.nome_versao}"
    arquivos.gravar_json(f"{base}_programas.json", programas())
    arquivos.gravar_json(f"{base}_checklist.json", checklist(MAN))
    arquivos.gravar_json(f"{base}_semelhanca.json", similar(None))
    if decisao.EtapaLocal().se_aplica(r, amb.servicos):
        arquivos.gravar_json(
            f"{base}_local.json", local({"coerencia": "passa", "pecas_anteriores": "passa"})
        )
    etapa = decisao.EtapaDecisao()
    assert etapa.pedir(r, amb.servicos) is None
    veredito = arquivos.ler_json(etapa.arquivo_resultado(r), Conferencia)
    assert veredito.veredito == "aprovada"
    aprovada = semelhanca.caminho_aprovada(r)
    assert aprovada == f"saida/aprovadas/{r.nome_versao}.md"
    assert arquivos.ler_texto(aprovada) == arquivos.ler_texto(f"saida/rascunhos/{r.nome_versao}.md")
    assert semelhanca.aprovadas_do_tipo(RefPeca("e01", MAN, 2), amb.servicos) == [aprovada]


# ---------------------------------------------------------------------------
# 8. O código lê a instrução do arquivo
# ---------------------------------------------------------------------------


def test_frase_da_instrucao_nao_esta_no_codigo() -> None:
    instrucao = (RAIZ / "instrucoes/opus_desempate.md").read_text("utf-8")
    frases = [f.strip() for f in instrucao.replace("\n", " ").split(".") if len(f.strip()) > 30]
    assert len(frases) >= 5
    codigo = "\n".join(p.read_text("utf-8") for p in (RAIZ / "fabrica").rglob("*.py"))
    for frase in frases:
        assert frase not in codigo, frase
