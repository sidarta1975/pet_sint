"""Teste de aceite do brief 016: `fabrica/redacao.py`.

Cliente da API falso, pasta temporária com repositório git próprio (o ambiente do
`test_fichas.py`), a estrutura montada gravada por `preparar` e uma ficha pronta.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import pytest

from fabrica import estado, estruturas, fichas, redacao
from fabrica.comum.formatos import Conferencia, Ficha, Pedido, Rascunho
from fabrica.estado import RefPeca, Servicos
from testes.test_fichas import RAIZ, Ambiente, preparar, resposta_inicial, texto

INICIAL = "peticao_inicial_jec"
PECA = f"e01_{INICIAL}_001"
REF = RefPeca("e01", INICIAL, 1)
RESPOSTA = "## Endereçamento\n\nTexto da peça como chegou.\n"


def conferencia(peca: RefPeca, veredito: str) -> Conferencia:
    return Conferencia.model_validate_json(
        json.dumps(
            {
                "peca": peca.id,
                "versao": peca.versao,
                "extracao": {
                    "nomes": [],
                    "documentos": [],
                    "valores": [],
                    "datas": [],
                    "comarca": None,
                    "juizo": None,
                    "pedidos": [],
                    "pecas_anteriores": [],
                    "data_peca": None,
                },
                "itens": [],
                "caminho": [],
                "notas_estilo": None,
                "alertas": [],
                "veredito": veredito,
                "categoria_motivo": None if veredito == "aprovada" else "conteudo",
                "motivo": "" if veredito == "aprovada" else f"motivo da {peca.nome_versao}",
                "semelhanca": None,
                "conferencia_local": None,
                "modo_teste": False,
            }
        )
    )


class DecisaoFalsa:
    """Grava sempre 'refazer' (a decisão de verdade é do brief 018)."""

    nome = "decisao"

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        return True

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return f"saida/conferencias/{peca.nome_versao}.json"

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        servicos.arquivos.gravar_json(self.arquivo_resultado(peca), conferencia(peca, "refazer"))
        return None

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        return None


@pytest.fixture
def amb(tmp_path: Path) -> Ambiente:
    raiz = preparar(tmp_path)
    (raiz / "testes/dados").mkdir(parents=True)
    shutil.copy(RAIZ / estruturas.RESERVADOS, raiz / estruturas.RESERVADOS)
    ambiente = Ambiente(raiz)
    assert estruturas.preparar(ambiente.arquivos, ambiente.servicos.config).passou
    assert ambiente.executar("ensaio", "--semente", "5") == 0
    for tipo in (INICIAL, "embargos_declaracao", "manifestacao_ar_negativo"):
        # Uma ficha pronta para cada peça do ensaio (o redator recebe o texto da ficha).
        base = ambiente.base(PECA)
        ficha, falhas = fichas.conferir(base, texto(resposta_inicial(base)), ambiente.ctx)
        assert ficha is not None and falhas == []
        ambiente.arquivos.gravar_json(f"saida/fichas/e01_{tipo}_001.json", Ficha(ficha))
    return ambiente


def pedido(amb: Ambiente, ref: RefPeca) -> Pedido:
    caminho = redacao.EtapaRedacao().pedir(ref, amb.servicos)
    assert caminho is not None
    return amb.arquivos.ler_json(caminho, Pedido)


def test_pedido_vai_ao_redator_da_classe_com_as_partes_na_ordem(amb: Ambiente) -> None:
    gasto = amb.servicos.gasto
    feitos: dict[str, Pedido] = {}
    for tipo, tarefa, apelido in (
        (INICIAL, "redacao_risco_medio", "sonnet"),
        ("embargos_declaracao", "redacao_risco_alto", "sonnet"),
        ("manifestacao_ar_negativo", "redacao_risco_baixo", "haiku"),
    ):
        p = feitos[tipo] = pedido(amb, RefPeca("e01", tipo, 1))
        configuracao = gasto.tarefa(tarefa)
        assert (p.tarefa, p.versao, p.tentativa) == (tarefa, 1, 1)
        assert configuracao.modelo == apelido
        assert p.modelo == gasto.modelo_da_tarefa(tarefa)
        assert (p.esforco, p.teto_saida) == (configuracao.esforco, configuracao.teto_saida_tokens)
        assert [parte.nome for parte in p.partes] == ["instrucoes", "estrutura", "trecho", "ficha"]
        # Sem formato de saída estruturada.
        assert p.formato is None and p.esquema is None
    p = feitos[INICIAL]
    instrucao = (amb.raiz / "instrucoes/redacao.md").read_text("utf-8")
    assert p.partes[0].texto == instrucao
    montada = amb.arquivos.ler_texto(f"saida/preparacao/{INICIAL}_estrutura.json")
    assert p.partes[1].texto == montada
    trecho = fichas.carregar_contexto(amb.arquivos, amb.servicos.config).trechos[INICIAL].texto
    assert p.partes[2].texto == trecho
    assert p.partes[3].texto == amb.arquivos.ler_texto(f"saida/fichas/{PECA}.json")


def test_rascunho_com_a_marca_e_os_metadados(amb: Ambiente) -> None:
    amb.cliente.fila = [RESPOSTA]
    estado.avancar([redacao.EtapaRedacao()], amb.servicos, [REF])
    md = amb.arquivos.ler_texto(f"saida/rascunhos/{PECA}_v1.md")
    assert md.splitlines()[0] == "DOCUMENTO SINTÉTICO — FICTÍCIO"
    assert md.endswith(RESPOSTA)
    meta = amb.arquivos.ler_json(f"saida/rascunhos/{PECA}_v1.json", Rascunho)
    assert (meta.peca, meta.versao, meta.tarefa) == (PECA, 1, "redacao_risco_medio")
    assert meta.ficha == f"saida/fichas/{PECA}.json"
    assert meta.estrutura == f"saida/preparacao/{INICIAL}_estrutura.json"
    assert meta.versao_instrucoes == amb.arquivos.impressao("instrucoes/redacao.md")
    assert meta.modelo == "claude-haiku-5-5"  # o modelo que respondeu
    assert meta.motivo_refacao is None
    # A resposta crua continua em saida/respostas/ como chegou.
    nome = f"{PECA}_v1_redacao_risco_medio_t1"
    crua = json.loads(amb.arquivos.ler_texto(f"saida/respostas/{nome}.json"))
    assert crua["conteudo"] == RESPOSTA and meta.resposta == f"saida/respostas/{nome}.json"


def test_refacao_gera_v2_e_v3_com_o_motivo_e_para(amb: Ambiente) -> None:
    amb.cliente.fila = ["versão 1", "versão 2", "versão 3"]
    estado.avancar([redacao.EtapaRedacao(), DecisaoFalsa()], amb.servicos, [REF])
    for k in (1, 2, 3):
        assert amb.arquivos.ler_texto(f"saida/rascunhos/{PECA}_v{k}.md").endswith(f"versão {k}")
    assert not amb.arquivos.existe(f"saida/rascunhos/{PECA}_v4.md")
    assert estado.destino(REF.com_versao(3), amb.arquivos) == estado.DESCARTADA
    v2 = amb.arquivos.ler_json(f"saida/pedidos/{PECA}_v2_redacao_risco_medio_t1.json", Pedido)
    assert [p.nome for p in v2.partes] == ["instrucoes", "estrutura", "trecho", "ficha", "motivo"]
    assert v2.partes[4].texto == f"motivo da {PECA}_v1"
    meta = amb.arquivos.ler_json(f"saida/rascunhos/{PECA}_v3.json", Rascunho)
    assert meta.motivo_refacao == f"motivo da {PECA}_v2"
    assert len(amb.cliente.enviados) == 3


def test_nunca_sobrescreve_nem_passa_da_terceira(amb: Ambiente) -> None:
    amb.cliente.fila = [RESPOSTA]
    estado.avancar([redacao.EtapaRedacao()], amb.servicos, [REF])
    resposta = amb.arquivos.ler_texto(f"saida/respostas/{PECA}_v1_redacao_risco_medio_t1.json")
    from fabrica.comum.formatos import Resposta

    lida = Resposta.model_validate_json(resposta)
    with pytest.raises(Exception, match="já existe"):
        redacao.EtapaRedacao().receber(REF, lida, amb.servicos)
    with pytest.raises(redacao.ErroRedacao):
        redacao.EtapaRedacao().receber(REF.com_versao(4), lida, amb.servicos)


def test_redacao_so_com_ficha_pronta(amb: Ambiente) -> None:
    etapa = redacao.EtapaRedacao()
    assert etapa.aplica(REF, amb.servicos)
    assert not etapa.aplica(RefPeca("e01", INICIAL, 2), amb.servicos)


def test_frase_da_instrucao_nao_esta_no_codigo() -> None:
    instrucao = (RAIZ / "instrucoes/redacao.md").read_text("utf-8")
    frases = [f.strip() for f in instrucao.replace("\n", " ").split(".") if len(f.strip()) > 40]
    assert len(frases) >= 5
    codigo = "\n".join(p.read_text("utf-8") for p in (RAIZ / "fabrica").rglob("*.py"))
    for frase in frases:
        assert frase not in codigo, frase
