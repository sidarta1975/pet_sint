"""Teste de aceite do brief 020: `fabrica/publicacao.py` e o comando `publicar`.

Peças saídas do fluxo com os clientes falsos (ensaio `e01` e a rodada `r01` de
manifestações) e respostas do responsável gravadas pelo comando `revisar`.
"""

from __future__ import annotations

import json
from pathlib import Path

import docx
import pytest

from fabrica import __main__ as principal
from fabrica import publicacao
from fabrica.comum.formatos import Metadados
from fabrica.conferencia.regras import MARCA
from testes.test_integracao import EMB, INICIAL, MAN, Integracao
from testes.test_revisao import Teclado, base_da_rodada, peca, revisar, rodada

__all__ = ["base_da_rodada", "rodada"]  # as fixtures vêm do teste de revisão
TIPOS = (INICIAL, EMB, MAN)


def responder(rodada: Integracao) -> None:
    for _ in range(3):
        revisar(rodada, "s", "n", "s")  # ensaio
    revisar(rodada, "aprovada", "aprovada", "n", "", "s")  # 001: a fábrica aprovou a v2
    revisar(rodada, "aprovada", "reprovada", "n", "", "s")  # 002: o responsável reprovou
    revisar(rodada, "reprovada", "aprovada", "n", "", "s")  # 003: ficha reprovada
    revisar(rodada, "aprovada", "aprovada", "s", "um nome", "", "s")  # 004: dado real
    for _ in range(6):
        revisar(rodada, "aprovada", "aprovada", "n", "", "s")  # 005 a 010
    revisar(rodada, "aprovada", "n", "s")  # leitura de publicação da v2 da 001


def publicar(rodada: Integracao, nome: str = "r01") -> int:
    return principal.executar(["publicar", "--rodada", nome], rodada.servicos, Teclado([]))


def test_so_a_peca_publicavel_entra_no_pacote(rodada: Integracao) -> None:
    responder(rodada)
    assert publicar(rodada) == 0
    pasta = f"saida/pacotes/{MAN}"
    publicadas = sorted(
        c.removeprefix(f"{pasta}/").removesuffix(".md")
        for c in rodada.arquivos.listar(pasta, "*_v*.md")
    )
    esperadas = [f"{peca(1)}_v2"] + [f"{peca(n)}_v1" for n in range(5, 11)]
    assert publicadas == esperadas
    for nome in esperadas:
        for extensao in (".md", ".json", ".docx"):
            assert rodada.existe(f"{pasta}/{nome}{extensao}"), (nome, extensao)
    indice = rodada.arquivos.ler_texto(f"{pasta}/indice_r01.md")
    assert indice.splitlines()[0] == MARCA
    assert sum(1 for linha in indice.splitlines() if linha.startswith("| r01_")) == len(esperadas)


def test_nenhum_arquivo_sai_sem_a_marca(rodada: Integracao) -> None:
    responder(rodada)
    assert publicar(rodada) == 0
    pasta = rodada.raiz / f"saida/pacotes/{MAN}"
    nome = f"{peca(5)}_v1"
    texto = (pasta / f"{nome}.md").read_text("utf-8")
    assert texto.splitlines()[0] == MARCA
    metadados = Metadados.model_validate_json((pasta / f"{nome}.json").read_text("utf-8"))
    assert metadados.marca_sintetico == MARCA
    assert metadados.tipo == "Manifestação sobre Aviso de Recebimento Negativo"
    assert metadados.ficha.root.id == peca(5)
    assert metadados.conferencia and metadados.modelo_redator
    documento = docx.Document(str(pasta / f"{nome}.docx"))
    propriedades = documento.core_properties
    for campo in (propriedades.title, propriedades.subject, propriedades.comments):
        assert MARCA in campo
    for secao in documento.sections:
        assert any(MARCA in p.text for p in secao.footer.paragraphs)
    corpo = "\n".join(p.text for p in documento.paragraphs)
    assert MARCA in corpo
    for arquivo in pasta.iterdir():
        if arquivo.suffix in (".md", ".json"):
            assert MARCA in arquivo.read_text("utf-8"), arquivo.name


def test_peca_sem_a_marca_faz_o_pacote_recusar(rodada: Integracao) -> None:
    responder(rodada)
    rascunho = rodada.raiz / f"saida/rascunhos/{peca(6)}_v1.md"
    rascunho.write_text(rascunho.read_text("utf-8").replace(MARCA, "").lstrip(), "utf-8")
    assert publicar(rodada) == 1
    assert not (rodada.raiz / "saida/pacotes").exists()


def test_ensaio_publica_as_tres_pecas_em_pasta_propria(rodada: Integracao) -> None:
    assert publicar(rodada, "e01") == 0
    for tipo in TIPOS:
        pasta = f"saida/pacotes/ensaio_e01/{tipo}"
        assert len(rodada.arquivos.listar(pasta, "e01_*.docx")) == 1, tipo
        assert rodada.existe(f"{pasta}/indice.md")


def test_comando_publicar_sem_rodada(rodada: Integracao) -> None:
    assert principal.executar(["publicar"], rodada.servicos, Teclado([])) == 2
    assert publicar(rodada, "r09") == 1


def test_metadados_tem_a_origem(rodada: Integracao) -> None:
    responder(rodada)
    publicar(rodada)
    lido = json.loads((rodada.raiz / f"saida/pacotes/{MAN}/{peca(1)}_v2.json").read_text("utf-8"))
    assert lido["versao_instrucoes"] and lido["versao_tabela_normas"]
    assert lido["custo_milionesimos"] > 0
    assert lido["identificador_processo"].startswith("SINT-")
    assert isinstance(lido["conferencia_local_rodou"], bool)
    assert Path(lido["ficha"]["id"]).name == peca(1)


@pytest.mark.parametrize("arquivo", ["revisao.py", "publicacao.py"])
def test_modulos_existem(arquivo: str) -> None:
    assert (Path(publicacao.__file__).parent / arquivo).exists()
