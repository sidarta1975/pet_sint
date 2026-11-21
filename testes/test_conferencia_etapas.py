"""Teste de aceite do brief 017: etapas de extração, programas, checklist e conferente local.

Clientes falsos (API e modelo local), pasta temporária com repositório git próprio (o
ambiente de `test_fichas.py`), a estrutura gravada por `preparar`, as fichas prontas
das três peças do ensaio e rascunhos de exemplo.
"""

from __future__ import annotations

import dataclasses
import datetime
import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from fabrica import estado, estruturas, fichas
from fabrica.comum.formatos import (
    BaseFicha,
    EstruturaMontada,
    Extracao,
    Ficha,
    Pedido,
    Resposta,
    RespostaChecklist,
    ResultadoConferenteLocal,
    ResultadoProgramas,
    Rodadas,
    Tokens,
)
from fabrica.comum.modelo_local import ModeloLocal, Resultado
from fabrica.conferencia import checklist, extracao, local, regras
from fabrica.conferencia.regras import MARCA
from fabrica.estado import FORA_DO_FORMATO, RefPeca
from testes.test_fichas import (
    RAIZ,
    Ambiente,
    git,
    preparar,
    resposta_inicial,
    resposta_manifestacao,
    texto,
)

INICIAL = "peticao_inicial_jec"
EMB = "embargos_declaracao"
MAN = "manifestacao_ar_negativo"
TIPOS = (INICIAL, EMB, MAN)
LOCAL_OK = json.dumps(
    {
        "itens": [
            {"item": "coerencia", "resposta": "passa", "trecho": "t"},
            {"item": "texto_generico", "resposta": "passa", "trecho": "t"},
        ]
    }
)

FUNDAMENTACAO = (
    "Trata-se de ação de indenização por vício do produto. O aparelho apresentou "
    "defeito na tela e o fornecedor reparou o equipamento dentro do prazo legal. "
    "Não houve dano moral comprovado."
)
MENCAO = "A autora pede multa cominatória pela demora na devolução, o que não altera a conclusão."
A3 = (
    "A autora requer a aplicação da multa cominatória pela demora na devolução do "
    "aparelho, com juros moratórios desde a citação."
)


def ref(tipo: str, numero: int = 1, versao: int = 1) -> RefPeca:
    return RefPeca("e01", tipo, numero, versao)


def resposta_embargos(base: BaseFicha) -> dict[str, Any]:
    assert base.data_decisao is not None
    return {
        "fatos": [
            {
                "data": str(base.processo.data_ajuizamento - datetime.timedelta(days=30)),
                "descricao": "A autora comprou um aparelho celular que apresentou defeito na tela.",
                "valores": [],
            }
        ],
        "valores": [],
        "provas": [],
        "valor_causa": None,
        "fundamentos": ["cpc_art1022"],
        "momento_processual": {"ultima_decisao": "Sentença de improcedência."},
        "pecas_anteriores": [],
        "pedidos": [
            {"id": "p1", "natureza": "acolhimento_embargos", "descricao": "d", "valor": None},
            {"id": "p2", "natureza": "suprir_omissao", "descricao": "d", "valor": None},
        ],
        "decisao_embargada": {
            "tipo": base.tipo_decisao,
            "data": str(base.data_decisao),
            "juizo": base.processo.juizo,
            "relatorio": "Relatório.",
            "fundamentacao": f"{FUNDAMENTACAO} {MENCAO}",
            "dispositivo": "Ante o exposto, julgo improcedentes os pedidos.",
        },
        "argumentos_das_partes": [
            {
                "id": "a1",
                "parte": "parte_autora",
                "peca_de_origem": "inicial",
                "texto": "O fornecedor descumpriu o prazo de trinta dias para sanar o vício, "
                "configurando a responsabilidade solidária.",
            },
            {
                "id": "a2",
                "parte": "parte_re",
                "peca_de_origem": "contestacao",
                "texto": "A ré afirma que o reparo foi concluído e entregue ao consumidor.",
            },
            {"id": "a3", "parte": "parte_autora", "peca_de_origem": "replica", "texto": A3},
        ],
        "defeito": {
            "ancora": {
                "origem": "argumento",
                "argumento_id": "a3",
                "trecho_literal": "multa cominatória pela demora na devolução do aparelho, "
                "com juros moratórios desde a citação",
            },
            "trecho_mencao": MENCAO,
            "descricao": "A sentença menciona a multa e não a enfrenta.",
            "efeito_modificativo": False,
        },
    }


RESPOSTAS = {
    INICIAL: resposta_inicial,
    EMB: resposta_embargos,
    MAN: resposta_manifestacao,
}


def rascunho(ambiente: Ambiente, tipo: str, extra: str = "") -> str:
    montada = ambiente.arquivos.ler_json(
        f"saida/preparacao/{tipo}_estrutura.json", EstruturaMontada
    )
    blocos = "\n\n".join(f"## {b.titulo}\n\nTexto do bloco." for b in montada.blocos)
    return f"{MARCA}\n\n{blocos}\n\n{extra}\n"


@pytest.fixture
def amb(tmp_path: Path) -> Ambiente:
    raiz = preparar(tmp_path)
    (raiz / "testes/dados").mkdir(parents=True)
    shutil.copy(RAIZ / estruturas.RESERVADOS, raiz / estruturas.RESERVADOS)
    config = raiz / "config/config.toml"
    texto_config = config.read_text("utf-8")
    texto_config = texto_config.replace(
        'etiqueta_completa = ""', 'etiqueta_completa = "gemma3:27b"'
    )
    config.write_text(texto_config.replace('digest = ""', 'digest = "sha256:abc"'), "utf-8")
    git(raiz, "commit", "-q", "-am", "modelo local")
    ambiente = Ambiente(raiz)
    assert estruturas.preparar(ambiente.arquivos, ambiente.servicos.config).passou
    assert ambiente.executar("ensaio", "--semente", "5") == 0
    for tipo in TIPOS:
        peca = f"e01_{tipo}_001"
        base = ambiente.base(peca)
        ficha, falhas = fichas.conferir(base, texto(RESPOSTAS[tipo](base)), ambiente.ctx)
        assert ficha is not None and falhas == [], (tipo, falhas)
        ambiente.arquivos.gravar_json(f"saida/fichas/{peca}.json", Ficha(ficha))
        ambiente.arquivos.gravar_texto(f"saida/rascunhos/{peca}_v1.md", rascunho(ambiente, tipo))
    return ambiente


def resposta(conteudo: str) -> Resposta:
    return Resposta(
        pedido="x",
        modelo="m",
        conteudo=conteudo,
        bruto=None,
        motivo_parada="end_turn",
        tokens=Tokens(entrada=1, cache=0, raciocinio=0, saida=1),
        situacao="ok",
        recebida_em=datetime.datetime(2026, 11, 21, tzinfo=datetime.UTC),
    )


def extracao_vazia(**troca: Any) -> dict[str, Any]:
    dados: dict[str, Any] = {
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
    dados.update(troca)
    return dados


def gravar_extracao(amb: Ambiente, r: RefPeca, dados: dict[str, Any]) -> None:
    amb.arquivos.gravar_json(
        f"saida/conferencias/{r.nome_versao}_extracao.json",
        Extracao.model_validate_json(json.dumps(dados)),
    )


# ---------------------------------------------------------------------------
# 1. Extração
# ---------------------------------------------------------------------------


def test_extracao_pede_o_esquema_e_grava_a_resposta(amb: Ambiente) -> None:
    r = ref(INICIAL)
    amb.cliente.fila = [json.dumps(extracao_vazia(comarca="Campinas"))]
    estado.avancar([extracao.EtapaExtracao()], amb.servicos, [r])
    pedido = amb.arquivos.ler_json(f"saida/pedidos/{r.nome_versao}_extracao_t1.json", Pedido)
    assert (pedido.tarefa, pedido.formato) == ("extracao", "Extracao")
    assert pedido.esquema is not None
    conteudo = next(p.texto for p in pedido.partes if p.nome == "conteudo")
    assert conteudo == amb.arquivos.ler_texto(f"saida/rascunhos/{r.nome_versao}.md")
    assert not any(p.nome == "ficha" for p in pedido.partes)  # a extração não vê a ficha
    gravada = amb.arquivos.ler_json(f"saida/conferencias/{r.nome_versao}_extracao.json", Extracao)
    assert gravada.comarca == "Campinas"


def test_extracao_fora_do_esquema_volta_fora_do_formato(amb: Ambiente) -> None:
    r = ref(INICIAL)
    resposta = Resposta(
        pedido="x",
        modelo="m",
        conteudo='{"nomes": "não é lista"}',
        bruto=None,
        motivo_parada="end_turn",
        tokens=Tokens(entrada=1, cache=0, raciocinio=0, saida=1),
        situacao="ok",
        recebida_em=datetime.datetime(2026, 11, 21, tzinfo=datetime.UTC),
    )
    assert extracao.EtapaExtracao().receber(r, resposta, amb.servicos) == FORA_DO_FORMATO
    assert not amb.arquivos.existe(f"saida/conferencias/{r.nome_versao}_extracao.json")
    # Pelo condutor: t1 e t2 fora do esquema, a peça é reprovada por formato.
    amb.cliente.fila = ["{}", "{}"]
    estado.avancar([extracao.EtapaExtracao()], amb.servicos, [r])
    assert estado.destino(r, amb.arquivos) == estado.REPROVADA_FORMATO


# ---------------------------------------------------------------------------
# 2. Programas
# ---------------------------------------------------------------------------


def programas(amb: Ambiente, r: RefPeca) -> ResultadoProgramas:
    etapa = regras.EtapaProgramas()
    assert etapa.aplica(r, amb.servicos)
    assert etapa.pedir(r, amb.servicos) is None
    return amb.arquivos.ler_json(etapa.arquivo_resultado(r), ResultadoProgramas)


def test_programas_grava_os_itens_de_cada_tipo(amb: Ambiente) -> None:
    comuns = {
        "estrutura",
        "citacao_fora_da_tabela",
        "termos_inequivocos",
        "coerencia_ficha",
        "dado_real",
        "marca",
    }
    for tipo, proprio in ((INICIAL, "alcada"), (EMB, "prazo"), (MAN, "prazo")):
        r = ref(tipo)
        gravar_extracao(amb, r, extracao_vazia())
        resultado = programas(amb, r)
        assert {i.item for i in resultado.itens} == comuns | {proprio}, tipo
        assert all(i.quem == "programa" for i in resultado.itens)
        respostas = {i.item: i.resposta for i in resultado.itens}
        assert respostas["estrutura"] == "passa" and respostas["marca"] == "passa"


def test_programas_pega_o_que_falha_e_a_citacao_nao_resolvida_vira_alerta(amb: Ambiente) -> None:
    r = ref(INICIAL, versao=2)
    extra = (
        "Conforme o art. 5º, cabe a indenização. Nos termos do art. 14 do CDC. "
        "Requer prazo em quádruplo. Telefone (11) 98888-7777."
    )
    amb.arquivos.gravar_texto(f"saida/rascunhos/{r.nome_versao}.md", rascunho(amb, INICIAL, extra))
    gravar_extracao(amb, r, extracao_vazia())
    resultado = programas(amb, r)
    respostas = {i.item: i.resposta for i in resultado.itens}
    assert respostas["termos_inequivocos"] == "nao_passa"
    assert respostas["dado_real"] == "nao_passa"
    assert respostas["citacao_fora_da_tabela"] == "passa"
    assert [n.trecho for n in resultado.citacoes_nao_resolvidas] == ["art. 5º"]
    assert any(a.item == "citacao_fora_da_tabela" for a in resultado.alertas)
    assert [(c.diploma, c.artigo) for c in resultado.citacoes_resolvidas] == [("cdc", "14")]


# ---------------------------------------------------------------------------
# 3. Checklist
# ---------------------------------------------------------------------------

B2 = {
    INICIAL: [
        "cabimento",
        "competencia_enderecamento",
        "prazo_e_momento",
        "legitimidade",
        "pedidos",
        "fundamento",
        "coerencia",
        "argumentacao_suficiente",
        "texto_generico",
    ],
    EMB: [
        "cabimento",
        "competencia_enderecamento",
        "prazo_e_momento",
        "legitimidade",
        "pedidos",
        "fundamento",
        "coerencia",
        "pecas_anteriores",
        "argumentacao_suficiente",
        "texto_generico",
    ],
    MAN: [
        "cabimento",
        "competencia_enderecamento",
        "prazo_e_momento",
        "legitimidade",
        "pedidos",
        "fundamento",
        "coerencia",
        "pecas_anteriores",
    ],
}


def resposta_checklist(itens: list[str]) -> str:
    return json.dumps(
        {
            "itens": [{"item": i, "resposta": "passa", "trecho": "t"} for i in itens],
            "citacoes": [],
            "notas": {"clareza": 4, "concisao": 3, "linguagem_tecnica": 5},
        }
    )


def test_checklist_leva_so_os_itens_do_tipo_e_as_perguntas(amb: Ambiente) -> None:
    for tipo in TIPOS:
        r = ref(tipo)
        gravar_extracao(amb, r, extracao_vazia())
        programas(amb, r)
        caminho = checklist.EtapaChecklist().pedir(r, amb.servicos)
        assert caminho is not None
        pedido = amb.arquivos.ler_json(caminho, Pedido)
        assert (pedido.tarefa, pedido.formato) == ("checklist", "RespostaChecklist")
        lista = json.loads(next(p.texto for p in pedido.partes if p.nome == "estrutura"))
        assert [i["item"] for i in lista["itens"]] == B2[tipo], tipo
        assert all(i["eliminatorio"] is True for i in lista["itens"])
        assert lista["citacoes_nao_resolvidas"] == []


def test_checklist_com_citacao_nao_resolvida_e_resposta_gravada(amb: Ambiente) -> None:
    r = ref(MAN, versao=2)
    extra = "Conforme o art. 5º, requer a nova citação."
    amb.arquivos.gravar_texto(f"saida/rascunhos/{r.nome_versao}.md", rascunho(amb, MAN, extra))
    gravar_extracao(amb, r, extracao_vazia())
    programas(amb, r)
    etapa = checklist.EtapaChecklist()
    caminho = etapa.pedir(r, amb.servicos)
    assert caminho is not None
    pedido = amb.arquivos.ler_json(caminho, Pedido)
    assert etapa.receber(r, resposta(resposta_checklist(B2[MAN])), amb.servicos) is None
    lista = json.loads(next(p.texto for p in pedido.partes if p.nome == "estrutura"))
    assert (
        len(lista["citacoes_nao_resolvidas"]) == 1
        and "art. 5º" in lista["citacoes_nao_resolvidas"][0]
    )
    gravada = amb.arquivos.ler_json(
        f"saida/conferencias/{r.nome_versao}_checklist.json", RespostaChecklist
    )
    assert [i.item for i in gravada.itens] == B2[MAN]
    assert (gravada.notas.clareza, gravada.notas.concisao, gravada.notas.linguagem_tecnica) == (
        4,
        3,
        5,
    )


def test_checklist_sem_todos_os_itens_e_fora_do_formato(amb: Ambiente) -> None:
    r = ref(MAN)
    gravar_extracao(amb, r, extracao_vazia())
    programas(amb, r)
    resposta = Resposta(
        pedido="x",
        modelo="m",
        conteudo=resposta_checklist(B2[MAN][:-1]),
        bruto=None,
        motivo_parada="end_turn",
        tokens=Tokens(entrada=1, cache=0, raciocinio=0, saida=1),
        situacao="ok",
        recebida_em=datetime.datetime(2026, 11, 21, tzinfo=datetime.UTC),
    )
    assert checklist.EtapaChecklist().receber(r, resposta, amb.servicos) == FORA_DO_FORMATO


# ---------------------------------------------------------------------------
# 4. Conferente local
# ---------------------------------------------------------------------------


def semente(amb: Ambiente) -> int:
    rodadas = amb.arquivos.ler_json("saida/rodadas.json", Rodadas)
    return next(r.semente for r in rodadas.rodadas if r.id == "e01")


def test_local_aplica_em_medio_alto_e_em_duas_de_dez_do_baixo(amb: Ambiente) -> None:
    etapa = local.EtapaLocal()
    assert etapa.se_aplica(ref(INICIAL), amb.servicos) and etapa.se_aplica(ref(EMB), amb.servicos)
    escolhidas = local.sorteadas(MAN, semente(amb), 10, 0.2)
    assert len(escolhidas) == 2 and escolhidas == local.sorteadas(MAN, semente(amb), 10, 0.2)
    for n in range(1, 11):
        assert etapa.se_aplica(ref(MAN, n), amb.servicos) == (n in escolhidas)
    # No teste dos conferentes, a cópia segue a sua original.
    for n in range(1, 11):
        copia = dataclasses.replace(ref(MAN, n), copia=f"e01_{MAN}_{n:03d}_erro1")
        assert etapa.se_aplica(copia, amb.servicos) == (n in escolhidas)


def test_local_pede_so_os_itens_do_tipo(amb: Ambiente) -> None:
    for tipo, itens in (
        (INICIAL, ["coerencia", "texto_generico"]),
        (EMB, ["coerencia", "pecas_anteriores", "texto_generico"]),
        (MAN, ["coerencia", "pecas_anteriores"]),
    ):
        caminho = local.EtapaLocal().pedir(ref(tipo), amb.servicos)
        assert caminho is not None
        pedido = amb.arquivos.ler_json(caminho, Pedido)
        assert (pedido.servico, pedido.tarefa, pedido.formato) == (
            "local",
            "conferente_local",
            "RespostaLocal",
        )
        lista = json.loads(next(p.texto for p in pedido.partes if p.nome == "estrutura"))
        assert [i["item"] for i in lista["itens"]] == itens, tipo


def test_local_envia_com_o_num_ctx_e_grava_o_resultado(amb: Ambiente) -> None:
    enviados: list[dict[str, Any]] = []

    def enviar(url: str, corpo: dict[str, Any]) -> dict[str, Any]:
        enviados.append(corpo)
        return {"message": {"content": LOCAL_OK}, "done_reason": "stop"}

    s = amb.servicos
    modelo = ModeloLocal(
        s.config, s.arquivos, s.registro, executar=lambda c: 0, enviar=enviar, relogio=s.relogio
    )
    servicos = dataclasses.replace(s, modelo_local=modelo)
    r = ref(INICIAL)
    assert not local.EtapaLocal().aplica(r, servicos)  # o local vem depois do checklist
    amb.arquivos.gravar_json(
        f"saida/conferencias/{r.nome_versao}_checklist.json",
        RespostaChecklist.model_validate_json(resposta_checklist(B2[INICIAL])),
    )
    estado.avancar([local.EtapaLocal()], servicos, [r])
    assert enviados[0]["options"]["num_ctx"] == s.config.geral.modelo_local.num_ctx
    gravado = amb.arquivos.ler_json(
        f"saida/conferencias/{r.nome_versao}_local.json", ResultadoConferenteLocal
    )
    assert gravado.resultado == "rodou" and gravado.respostas is not None


def test_local_indisponivel_e_gravado_com_a_causa(amb: Ambiente) -> None:
    r = ref(INICIAL)
    indisponivel = Resultado("indisponivel", "porteiro", None, None, 0.4, 0.0, None)
    assert local.EtapaLocal().receber(r, indisponivel, amb.servicos) is None
    gravado = amb.arquivos.ler_json(
        f"saida/conferencias/{r.nome_versao}_local.json", ResultadoConferenteLocal
    )
    assert (gravado.resultado, gravado.causa, gravado.respostas) == (
        "indisponivel",
        "porteiro",
        None,
    )


# ---------------------------------------------------------------------------
# 5. Instruções lidas do arquivo
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("arquivo", ["extracao.md", "checklist.md", "conferente_local.md"])
def test_frase_da_instrucao_nao_esta_no_codigo(arquivo: str) -> None:
    instrucao = (RAIZ / "instrucoes" / arquivo).read_text("utf-8")
    frases = [f.strip() for f in instrucao.replace("\n", " ").split(".") if len(f.strip()) > 30]
    assert len(frases) >= 2
    codigo = "\n".join(p.read_text("utf-8") for p in (RAIZ / "fabrica").rglob("*.py"))
    for frase in frases:
        assert frase not in codigo, frase
