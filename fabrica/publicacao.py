"""Publicação (ARQUITETURA §5.10 e §4; registro de decisão 001, item 17; brief 020).

Monta o pacote das peças publicáveis: `.md`, `.json` com os `Metadados` (§3), `.docx`
com a marca no rodapé de todas as páginas e nas propriedades do arquivo, e o índice em
Markdown, com a marca no topo. É publicável a peça cuja ficha o responsável aprovou e
cuja versão aprovada pela fábrica ele leu e aprovou: a primeira versão pelo cartão de
revisão; a v2 ou a v3 só pela leitura de publicação. Nenhum arquivo sai sem a marca: a
peça sem a marca no rascunho faz o pacote recusar, em vez de acrescentá-la escondido.
No ensaio, o pacote das três peças, qualquer que seja o veredito, vai para
`saida/pacotes/ensaio_<rodada>/<tipo>/`.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import docx

from fabrica import revisao
from fabrica.comum.congelamento import Congelamento
from fabrica.comum.formatos import (
    CatalogoTipos,
    Conferencia,
    Ficha,
    ItemMetadados,
    Metadados,
    Rascunho,
    TabelaNormas,
)
from fabrica.conferencia.regras import MARCA
from fabrica.estado import RefPeca, Servicos

PACOTES = "saida/pacotes"


class ErroPublicacao(Exception):
    """Pacote recusado (peça sem a marca, ou rodada sem peça)."""


@dataclass(frozen=True)
class Publicavel:
    ref: RefPeca  # com a versão publicada
    pasta: str


def publicaveis(rodada: str, servicos: Servicos) -> list[Publicavel]:
    Congelamento(servicos.arquivos, servicos.registro, servicos.relogio).rodada(rodada)
    escolhidas: list[Publicavel] = []
    if rodada.startswith("e"):
        for ref in revisao.pecas_conferidas(servicos, rodada):
            do_ensaio = revisao.versao_aprovada(ref, servicos) or 1
            pasta = f"{PACOTES}/ensaio_{rodada}/{ref.tipo}"
            escolhidas.append(Publicavel(ref.com_versao(do_ensaio), pasta))
        return escolhidas
    for ref in revisao.pecas_conferidas(servicos, rodada):
        lidas = revisao._respostas(ref.id, servicos)
        versao = revisao.versao_aprovada(ref, servicos)
        if lidas is None or lidas.veredito_ficha != "aprovada" or lidas.dado_real or not versao:
            continue
        if versao == 1:
            leitura = lidas
        else:
            identificador = f"{ref.com_versao(versao).nome_versao}_leitura_publicacao"
            leitura = revisao._respostas(identificador, servicos)  # type: ignore[assignment]
        if leitura is None or leitura.veredito_peca != "aprovada" or leitura.dado_real:
            continue
        escolhidas.append(Publicavel(ref.com_versao(versao), f"{PACOTES}/{ref.tipo}"))
    return escolhidas


def _texto(p: Publicavel, servicos: Servicos) -> str:
    texto = servicos.arquivos.ler_texto(f"saida/rascunhos/{p.ref.nome_versao}.md")
    if not texto.splitlines() or texto.splitlines()[0].strip() != MARCA:
        raise ErroPublicacao(
            f"{p.ref.nome_versao}: o rascunho não traz a marca {MARCA!r} no topo; "
            "o pacote recusa em vez de acrescentá-la"
        )
    return texto


def metadados(p: Publicavel, servicos: Servicos) -> Metadados:
    arquivos = servicos.arquivos
    ref = p.ref
    ficha = arquivos.ler_json(f"saida/fichas/{ref.id}.json", Ficha)
    rascunho = arquivos.ler_json(f"saida/rascunhos/{ref.nome_versao}.json", Rascunho)
    conferencia = arquivos.ler_json(f"saida/conferencias/{ref.nome_versao}.json", Conferencia)
    tabela = arquivos.ler_json("dados/normas/tabela_normas.json", TabelaNormas)
    catalogo = next(
        t
        for t in arquivos.ler_json("dados/catalogo/tipos.json", CatalogoTipos).tipos
        if t.nome_curto == ref.tipo
    )
    casa = ficha.root.casa_matriz
    custo = sum(c.custo_milionesimos for c in servicos.registro.chamadas() if c.peca == ref.id)
    return Metadados(
        tipo=catalogo.rotulo,
        classe_risco=catalogo.classe_risco,
        familia=catalogo.familia,
        perfil=catalogo.perfil,
        materia=casa.materia,
        tese=casa.tese,
        polo=casa.polo,
        complexidade=casa.complexidade,
        estilo=casa.estilo,
        ficha=ficha,
        identificador_processo=ficha.root.processo.identificador_ficticio,
        semente=ficha.root.semente,
        modelo_redator=rascunho.modelo,
        esforco=servicos.gasto.tarefa(rascunho.tarefa).esforco,
        versao_instrucoes=rascunho.versao_instrucoes,
        custo_milionesimos=custo,
        versao_tabela_normas=tabela.versao,
        conferencia=[
            ItemMetadados(item=i.item, resposta_final=i.resposta, quem_final=i.quem)
            for i in conferencia.itens
        ],
        conferencia_local_rodou=conferencia.conferencia_local in ("rodou", "esperou_e_rodou"),
        marca_sintetico="DOCUMENTO SINTÉTICO — FICTÍCIO",
    )


def documento(texto: str, nome: str) -> bytes:
    """O `.docx`, com a marca no rodapé de todas as páginas e nas propriedades."""
    saida = docx.Document()
    propriedades = saida.core_properties
    propriedades.title = f"{MARCA} — {nome}"
    propriedades.subject = MARCA
    propriedades.comments = MARCA
    for secao in saida.sections:
        secao.footer.paragraphs[0].text = MARCA
    for linha in texto.splitlines():
        if not linha.strip():
            continue
        if linha.startswith("## "):
            saida.add_heading(linha[3:].strip(), level=2)
        elif linha.startswith("# "):
            saida.add_heading(linha[2:].strip(), level=1)
        else:
            saida.add_paragraph(linha)
    memoria = io.BytesIO()
    saida.save(memoria)
    return memoria.getvalue()


def publicar(rodada: str, servicos: Servicos) -> list[str]:
    """Grava o pacote da rodada; confere a marca de todas as peças antes de gravar."""
    arquivos = servicos.arquivos
    escolhidas = publicaveis(rodada, servicos)
    textos = {p.ref.nome_versao: _texto(p, servicos) for p in escolhidas}
    gravadas: list[str] = []
    for p in escolhidas:
        nome = p.ref.nome_versao
        base = f"{p.pasta}/{nome}"
        if not arquivos.existe(f"{base}.md"):
            arquivos.gravar_texto(f"{base}.md", textos[nome])
        if not arquivos.existe(f"{base}.json"):
            arquivos.gravar_json(f"{base}.json", metadados(p, servicos))
        if not arquivos.existe(f"{base}.docx"):
            arquivos.gravar_bytes(f"{base}.docx", documento(textos[nome], nome))
        gravadas.append(nome)
    for pasta in sorted({p.pasta for p in escolhidas}):
        nome_indice = "indice.md" if rodada.startswith("e") else f"indice_{rodada}.md"
        if arquivos.existe(f"{pasta}/{nome_indice}"):
            continue
        linhas = [
            MARCA,
            "",
            f"# Pacote da rodada {rodada}",
            "",
            "| Peça | Versão | Tipo |",
            "|---|---|---|",
        ]
        for p in escolhidas:
            if p.pasta == pasta:
                tipo = revisao.rotulo(p.ref.tipo, servicos)
                linhas.append(f"| {p.ref.id} | v{p.ref.versao} | {tipo} |")
        arquivos.gravar_texto(f"{pasta}/{nome_indice}", "\n".join(linhas) + "\n")
    return gravadas
