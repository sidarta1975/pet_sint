"""Relatório do MVP e fechamento do ensaio (ARQUITETURA §5.11, §5.12.1 e §6; brief 023).

`gerar` lê só arquivos (`saida/registro/`, conferências, cartões e respostas, o banco
fechado e o resultado do teste) e escreve `saida/relatorios/relatorio_mvp.md` na
rodada, ou `saida/relatorios/relatorio_<rodada>.md` no ensaio, com o aviso de que o
ensaio não tem valor de medida. O relatório só descreve e marca: a decisão de escalar é
do responsável.

`fechar_ensaio` aplica a regra de 5.12.1 e, se o ensaio passar, registra o ensaio
aprovado em `saida/rodadas.json` (registro de decisão 001, itens 4 e 18). Não muda o
`config.toml`.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Literal

from fabrica import erros_plantados, estado, teste_conferentes
from fabrica.comum.congelamento import Congelamento, diferencas
from fabrica.comum.estatistica import wilson
from fabrica.comum.formatos import (
    Amostras,
    CatalogoTipos,
    Chamada,
    Conferencia,
    Descartada,
    Ficha,
    Gabarito,
    Ocorrencia,
    Pedido,
    RespostasCartao,
    ResultadoConferenteLocal,
    ResultadoTeste,
    Rodada,
    Rodadas,
)
from fabrica.estado import RefPeca, Servicos

RELATORIOS = "saida/relatorios"
CARTOES = "saida/cartoes"
CONFERENCIAS = "saida/conferencias"
FICHAS = "saida/fichas"
CATALOGO = "dados/catalogo/tipos.json"
AVISO_ENSAIO = "ensaio: sem valor de medida"
FINAL = "A decisão de escalar é do responsável: este relatório só descreve e marca."
# A estimativa de gasto do MVP é da ARQUITETURA §6; só serve para comparar.
ESTIMATIVA_GASTO_DOLARES = (19, 25)
MILIONESIMOS_POR_DOLAR = 100 * 1_000_000  # custo em milionésimos de centavo (ADR 001, item 3)
CORTE = "corte_de_gasto"
GRUPOS_DE_ERRO = {
    "cabimento": "cabimento",
    "prazo_e_momento": "prazo",
    "fora_do_prazo": "prazo",
    "valor_trocado": "valor",
    "acima_da_alcada": "valor",
    "funcao_trocada": "dispositivo com função trocada",
}
ORDEM_DOS_GRUPOS = ("cabimento", "prazo", "valor", "dispositivo com função trocada", "outros")
FORMATO = frozenset(
    {
        estado.REPROVADA_FORMATO,
        estado.VERSAO_PERDIDA,
        estado.COPIA_NAO_PEGA,
        estado.BANCO_DESCARTE,
        estado.FICHA_FALHOU,
    }
)


class ErroRelatorio(Exception):
    """Rodada que não existe."""


def caminho_relatorio(rodada: str) -> str:
    if rodada.startswith("e"):
        return f"{RELATORIOS}/relatorio_{rodada}.md"
    return f"{RELATORIOS}/relatorio_mvp.md"


def dolares(milionesimos: int) -> str:
    return f"US$ {milionesimos / MILIONESIMOS_POR_DOLAR:.4f}"


def milhar(numero: int) -> str:
    return f"{numero:,}".replace(",", ".")


def pct(valor: float | None) -> str:
    return "—" if valor is None else f"{valor * 100:.1f}%".replace(".", ",")


def margem(sucessos: int, total: int) -> str:
    if total == 0:
        return "sem casos"
    i = wilson(sucessos, total)
    return f"{pct(i.inferior)} a {pct(i.superior)} (Wilson, 95%)"


# ---------------------------------------------------------------------------
# Leitura
# ---------------------------------------------------------------------------


@dataclass
class Dados:
    rodada: str
    ensaio: bool
    pecas: list[RefPeca]
    chamadas: list[Chamada]
    ocorrencias: list[Ocorrencia]
    teste: ResultadoTeste | None
    tipos: Mapping[str, Any]
    cartoes: dict[str, RespostasCartao] = field(default_factory=dict)


def _ler_json(servicos: Servicos, caminho: str) -> Any:
    return json.loads(servicos.arquivos.ler_texto(caminho))


def ler(rodada: str, servicos: Servicos) -> Dados:
    arquivos = servicos.arquivos
    rodadas = (
        arquivos.ler_json("saida/rodadas.json", Rodadas)
        if arquivos.existe("saida/rodadas.json")
        else Rodadas(rodadas=[])
    )
    if rodada not in {r.id for r in rodadas.rodadas}:
        raise ErroRelatorio(f"rodada {rodada} não existe em saida/rodadas.json")
    pecas = [p for p in estado.descobrir_pecas(arquivos) if p.rodada == rodada]
    caminho_teste = teste_conferentes.caminho_relatorio(rodada)
    teste = (
        arquivos.ler_json(caminho_teste, ResultadoTeste) if arquivos.existe(caminho_teste) else None
    )
    tipos: dict[str, Any] = {
        t.nome_curto: t for t in arquivos.ler_json(CATALOGO, CatalogoTipos).tipos
    }
    dados = Dados(
        rodada=rodada,
        ensaio=rodada.startswith("e"),
        pecas=pecas,
        chamadas=servicos.registro.chamadas(),
        ocorrencias=servicos.registro.ocorrencias(),
        teste=teste,
        tipos=tipos,
    )
    for p in pecas:
        caminho = f"{CARTOES}/{p.id}_respostas.json"
        if arquivos.existe(caminho):
            dados.cartoes[p.id] = arquivos.ler_json(caminho, RespostasCartao)
    return dados


def versoes(ref: RefPeca, servicos: Servicos) -> list[Conferencia]:
    maxima = servicos.config.geral.volume.versoes_maximas
    lidas = []
    for k in range(1, maxima + 1):
        conferencia = estado.veredito(ref.com_versao(k), servicos.arquivos)
        if conferencia is not None:
            lidas.append(conferencia)
    return lidas


def tem_rascunho(ref: RefPeca, servicos: Servicos) -> bool:
    return servicos.arquivos.existe(f"saida/rascunhos/{ref.com_versao(1).nome_versao}.md")


def aprovada_pela_fabrica(ref: RefPeca, servicos: Servicos) -> bool:
    return any(c.veredito == "aprovada" for c in versoes(ref, servicos))


def encerrada(ref: RefPeca, servicos: Servicos) -> bool:
    """A peça fechou: aprovada, descartada ou encerrada pelo condutor."""
    maxima = servicos.config.geral.volume.versoes_maximas
    for k in range(1, maxima + 1):
        v = ref.com_versao(k)
        if estado.destino(v, servicos.arquivos) is not None:
            return True
        conferencia = estado.veredito(v, servicos.arquivos)
        if conferencia is None:
            return False
        if conferencia.veredito in ("aprovada", "descartada") or k == maxima:
            return True
    return False


def boa(dados: Dados, ref: RefPeca) -> bool:
    c = dados.cartoes.get(ref.id)
    return c is not None and c.veredito_ficha == "aprovada" and c.veredito_peca == "aprovada"


def da_rodada(dados: Dados, causa: str | None = None, tipo: str | None = None) -> list[Ocorrencia]:
    return [
        o
        for o in dados.ocorrencias
        if o.rodada == dados.rodada
        and (causa is None or o.causa == causa)
        and (tipo is None or o.tipo == tipo)
    ]


def _producao(c: Chamada) -> bool:
    return not c.peca.endswith(erros_plantados.SUFIXO_BANCO) and not c.peca.startswith(
        teste_conferentes.PREFIXO
    )


# ---------------------------------------------------------------------------
# Critérios da seção 6
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Criterio:
    nome: str
    resultado: str
    exigencia: str
    margem: str
    papel: Literal["decide", "indicador"]
    ao_lado: tuple[str, ...] = ()


def _apos_corte(dados: Dados, texto: str) -> str:
    if da_rodada(dados, CORTE):
        return f"{texto}, depois de um corte de gasto"
    return texto


def criterio_central(dados: Dados, servicos: Servicos) -> Criterio:
    criterios = servicos.config.geral.criterios
    exigencia = (
        f"só as cópias feitas por IA: taxa de pelo menos {pct(criterios.taxa_minima)}, com o "
        f"limite inferior de Wilson em pelo menos {pct(criterios.limite_inferior_minimo)}; "
        "os erros de regra por programa precisam ser 100% pegos"
    )
    nome = "Erros plantados pegos (critério central)"
    t = dados.teste
    if t is None:
        resultado = _apos_corte(dados, "inconclusivo: o teste dos conferentes não foi feito")
        return Criterio(nome, resultado, exigencia, "sem casos", "decide")
    c = t.criterio_central
    numeros = f"{c.sucessos} de {c.total} ({pct(c.taxa)})"
    plano_b = servicos.config.geral.plano_b
    boas = sum(boa(dados, p) for p in dados.pecas)
    if t.banco.nao_confiavel:
        resultado = (
            f"{numeros}; banco não confiável: o critério central é calculado, mas não decide"
        )
    elif not t.regra_sanidade_ok:
        resultado = (
            f"{numeros}; erros de regra por programa abaixo de 100%: o critério central é "
            "calculado e registrado, mas não decide; a falha vai para o programa de regra"
        )
    elif t.decisao_criterio_central == "inconclusivo" or (
        not dados.ensaio and boas < plano_b.inconclusivo_abaixo_de
    ):
        resultado = (
            f"{numeros}; inconclusivo: menos de {plano_b.inconclusivo_abaixo_de} peças boas "
            "(plano B)"
            if not dados.ensaio and boas < plano_b.inconclusivo_abaixo_de
            else f"{numeros}; inconclusivo"
        )
    else:
        resultado = (
            f"{numeros}; {'passa' if t.decisao_criterio_central == 'passa' else 'não passa'}"
        )
    s, j = t.sem_opus, t.julgamento_programa
    descartadas = len(t.banco.descartadas_com_erro)
    ao_lado = (
        f"taxa sem o Opus: {s.sucessos} de {s.total} ({pct(s.taxa)}), "
        f"{margem(s.sucessos, s.total)}",
        f"erros de julgamento feitos por programa: {j.sucessos} de {j.total} ({pct(j.taxa)}), "
        f"{j.total} cópia(s)"
        + ("; inconclusiva, menos de 5 cópias" if t.julgamento_inconclusivo else ""),
        f"amostra das descartadas: o erro pedido existe em {descartadas} delas",
    )
    return Criterio(nome, resultado, exigencia, margem(c.sucessos, c.total), "decide", ao_lado)


def fechadas_por_tipo(dados: Dados, servicos: Servicos) -> dict[str, int]:
    contagem: Counter[str] = Counter()
    for p in dados.pecas:
        if tem_rascunho(p, servicos) and encerrada(p, servicos):
            contagem[p.tipo] += 1
    return {t: contagem[t] for t in sorted({p.tipo for p in dados.pecas} | set(contagem))}


def criterio_ponta_a_ponta(dados: Dados, servicos: Servicos) -> Criterio:
    criterios = servicos.config.geral.criterios
    por_tipo = servicos.config.geral.volume.pecas_por_tipo
    fechadas = fechadas_por_tipo(dados, servicos)
    intervencoes = da_rodada(dados, tipo="intervencao")
    abaixo = [t for t, n in fechadas.items() if n < criterios.piso_pecas_por_tipo]
    partes = [f"{t}: {n} de {por_tipo}" for t, n in fechadas.items()]
    if dados.ensaio:
        passa = not intervencoes
    else:
        passa = not intervencoes and not abaixo and len(fechadas) == len(dados.tipos)
    resultado = ("passa" if passa else "não passa") + ("; " + ", ".join(partes) if partes else "")
    if intervencoes:
        resultado += f"; {len(intervencoes)} intervenção(ões) manual(is)"
    if abaixo and not dados.ensaio:
        resultado += "; abaixo do piso: " + ", ".join(
            f"{t} (a falha vai para ficha.md e fichas.py desse tipo)" for t in abaixo
        )
    exigencia = (
        f"as peças da rodada sem intervenção manual e cada tipo fechando pelo menos "
        f"{criterios.piso_pecas_por_tipo} das {por_tipo}"
    )
    return Criterio("Ponta a ponta", resultado, exigencia, "—", "decide")


@dataclass(frozen=True)
class Reprovacoes:
    boas: list[str]
    por_conteudo: list[str]
    so_semelhanca: list[str]


def reprovacoes_das_boas(dados: Dados, servicos: Servicos) -> Reprovacoes:
    boas, conteudo, semelhanca = [], [], []
    for p in dados.pecas:
        if not boa(dados, p):
            continue
        boas.append(p.id)
        v1 = estado.veredito(p.com_versao(1), servicos.arquivos)
        destino = estado.destino(p.com_versao(1), servicos.arquivos)
        if v1 is None and destino in FORMATO:
            conteudo.append(p.id)
        elif v1 is not None and v1.veredito != "aprovada":
            if v1.categoria_motivo == "semelhanca":
                semelhanca.append(p.id)
            else:
                conteudo.append(p.id)
    return Reprovacoes(boas, conteudo, semelhanca)


def limite_de_boas_reprovadas(boas: int, fracao: float) -> int:
    """A proporção arredondada para baixo: 2 com 20 a 29 peças boas, 1 com 14 a 19."""
    return math.floor(boas * fracao + 1e-9)


def criterio_boas_reprovadas(dados: Dados, servicos: Servicos) -> tuple[Criterio, Criterio]:
    fracao = servicos.config.geral.criterios.fracao_maxima_pecas_boas_reprovadas
    r = reprovacoes_das_boas(dados, servicos)
    limite = limite_de_boas_reprovadas(len(r.boas), fracao)
    n = len(r.por_conteudo)
    if not r.boas:
        resultado = _apos_corte(dados, "inconclusivo: nenhuma peça boa apurada")
    else:
        resultado = (
            f"{'passa' if n <= limite else 'não passa'}: {n} de {len(r.boas)} peças boas "
            f"reprovadas por conteúdo na primeira versão (limite: {limite})"
        )
    exigencia = (
        f"no máximo {pct(fracao)} das peças boas, arredondado para baixo (inclusive as "
        "categorias ambos e formato); reprovações só por semelhança ficam fora"
    )
    principal = Criterio(
        "Peças boas reprovadas por engano na primeira versão",
        resultado,
        exigencia,
        margem(n, len(r.boas)),
        "decide",
    )
    lista = ", ".join(r.so_semelhanca) if r.so_semelhanca else "nenhuma"
    aviso = "; o limite é revisto antes do piloto" if r.so_semelhanca else ""
    semelhanca = Criterio(
        "Reprovação só por semelhança",
        f"{len(r.so_semelhanca)}: {lista}{aviso}",
        "peças boas reprovadas na primeira versão apenas pela semelhança, listadas",
        "—",
        "indicador",
    )
    return principal, semelhanca


def achados_de_dado_real(dados: Dados, servicos: Servicos) -> list[str]:
    achados = [
        f"{peca}: o responsável apontou ({c.dado_real_trecho or 'sem trecho'})"
        for peca, c in sorted(dados.cartoes.items())
        if c.dado_real
    ]
    for p in dados.pecas:
        for conferencia in versoes(p, servicos):
            for item in conferencia.itens:
                if item.item == "dado_real" and item.resposta == "nao_passa":
                    achados.append(f"{conferencia.peca}_v{conferencia.versao}: o detector reprovou")
    return achados


def criterio_dado_real(dados: Dados, servicos: Servicos) -> Criterio:
    achados = achados_de_dado_real(dados, servicos)
    resultado = (
        "passa: nenhum" if not achados else f"não passa: {len(achados)} — " + "; ".join(achados)
    )
    return Criterio("Dado real proibido", resultado, "zero, apurado como em 5.2", "—", "decide")


@dataclass(frozen=True)
class Custos:
    producao: int
    pecas: int
    aprovadas: int
    ensaio: int
    banco: int
    teste: int
    descartadas: int
    total_mvp: int

    @property
    def marginal(self) -> float | None:
        return None if self.aprovadas == 0 else self.producao / self.aprovadas


def custos(dados: Dados, servicos: Servicos) -> Custos:
    da = [c for c in dados.chamadas if c.rodada == dados.rodada]
    descartes = 0
    for o in da_rodada(dados, erros_plantados.CUSTO_DESCARTADA):
        primeiro = o.detalhe.split(" ", 1)[0]
        descartes += int(primeiro) if primeiro.isdigit() else 0
    return Custos(
        producao=sum(c.custo_milionesimos for c in da if _producao(c)),
        pecas=sum(tem_rascunho(p, servicos) for p in dados.pecas),
        aprovadas=sum(aprovada_pela_fabrica(p, servicos) for p in dados.pecas),
        ensaio=sum(c.custo_milionesimos for c in dados.chamadas if c.rodada.startswith("e")),
        banco=sum(
            c.custo_milionesimos for c in da if c.peca.endswith(erros_plantados.SUFIXO_BANCO)
        ),
        teste=sum(c.custo_milionesimos for c in da if c.peca.startswith(teste_conferentes.PREFIXO)),
        descartadas=descartes,
        total_mvp=sum(c.custo_milionesimos for c in dados.chamadas),
    )


def criterio_custo(dados: Dados, servicos: Servicos) -> Criterio:
    maximo = servicos.config.geral.criterios.custo_marginal_maximo_centavos
    c = custos(dados, servicos)
    marginal = c.marginal
    if marginal is None:
        resultado = _apos_corte(dados, "inconclusivo: nenhuma peça aprovada pela fábrica")
    else:
        centavos = marginal / 1_000_000
        resultado = f"{dolares(round(marginal))} por peça aprovada ({c.aprovadas} aprovada(s))" + (
            "" if centavos <= maximo else "; rever antes de escalar"
        )
    exigencia = (
        f"ficha, redação, refações e conferência da rodada, divididas pelas peças aprovadas; "
        f"fora ensaio, cópias com erro e teste; acima de US$ {maximo / 100:.2f}, rever antes "
        "de escalar"
    )
    return Criterio("Custo marginal por peça aprovada", resultado, exigencia, "—", "decide")


def criterio_gasto_total(dados: Dados, servicos: Servicos) -> Criterio:
    c = custos(dados, servicos)
    baixo, alto = ESTIMATIVA_GASTO_DOLARES
    return Criterio(
        "Gasto total do MVP",
        f"{dolares(c.total_mvp)}, somando todas as rodadas, inclusive os ensaios",
        f"comparado com a estimativa (US$ {baixo} a {alto})",
        "—",
        "indicador",
    )


def criterio_concordancia(dados: Dados, servicos: Servicos) -> Criterio:
    sentidos: Counter[str] = Counter()
    disputas = []
    for p in dados.pecas:
        caminho = f"{CARTOES}/{p.id}_concordancia.json"
        if not servicos.arquivos.existe(caminho):
            continue
        lida = _ler_json(servicos, caminho)
        sentido = str(lida.get("sentido") or "ficha reprovada")
        sentidos[sentido] += 1
        if sentido not in ("concordam", "ficha reprovada"):
            v1 = estado.veredito(p.com_versao(1), servicos.arquivos)
            causa = v1.motivo if v1 is not None and v1.motivo else "sem motivo gravado"
            disputas.append(f"{p.id} ({sentido}: {causa})")
    numeros = ", ".join(f"{s}: {n}" for s, n in sorted(sentidos.items())) or "nenhum cartão"
    resultado = numeros + ("; em disputa: " + "; ".join(disputas) if disputas else "")
    return Criterio(
        "Concordância entre a fábrica e o responsável",
        resultado,
        "sobre a mesma primeira versão, só nas peças cuja ficha foi aprovada",
        "—",
        "indicador",
    )


def estilo(dados: Dados, servicos: Servicos) -> tuple[list[str], list[str]]:
    """As peças que a regra do plano (média abaixo de 3) teria reprovado, e as que o
    responsável aprovou entre elas."""
    abaixo = []
    for p in dados.pecas:
        v1 = estado.veredito(p.com_versao(1), servicos.arquivos)
        if v1 is None or v1.notas_estilo is None:
            continue
        n = v1.notas_estilo
        if (n.clareza + n.concisao + n.linguagem_tecnica) / 3 < 3:
            abaixo.append(p.id)
    aprovadas = [p for p in abaixo if (c := dados.cartoes.get(p)) and c.veredito_peca == "aprovada"]
    return abaixo, aprovadas


def criterio_estilo(dados: Dados, servicos: Servicos) -> Criterio:
    abaixo, aprovadas = estilo(dados, servicos)
    return Criterio(
        "Notas de estilo",
        f"{len(abaixo)} peça(s) teriam sido reprovadas; "
        f"o responsável aprovou {len(aprovadas)} delas",
        "quantas a regra do plano (média abaixo de 3) teria reprovado",
        "—",
        "indicador",
    )


def criterios(dados: Dados, servicos: Servicos) -> list[Criterio]:
    boas, semelhanca = criterio_boas_reprovadas(dados, servicos)
    return [
        criterio_central(dados, servicos),
        criterio_ponta_a_ponta(dados, servicos),
        boas,
        semelhanca,
        criterio_dado_real(dados, servicos),
        criterio_custo(dados, servicos),
        criterio_gasto_total(dados, servicos),
        criterio_concordancia(dados, servicos),
        criterio_estilo(dados, servicos),
    ]


# ---------------------------------------------------------------------------
# Ressalvas e demais seções de 5.11
# ---------------------------------------------------------------------------


def sem_local(dados: Dados, servicos: Servicos) -> tuple[int, int]:
    """Peças de risco médio e alto sem a resposta do modelo local, e o total delas."""
    sem, total = 0, 0
    for p in dados.pecas:
        if dados.tipos[p.tipo].classe_risco not in ("medio", "alto") or not tem_rascunho(
            p, servicos
        ):
            continue
        total += 1
        caminho = f"{CONFERENCIAS}/{p.com_versao(1).nome_versao}_local.json"
        if not servicos.arquivos.existe(caminho):
            sem += 1
            continue
        lido = servicos.arquivos.ler_json(caminho, ResultadoConferenteLocal)
        sem += lido.resultado == "indisponivel" or lido.respostas is None
    return sem, total


def ressalvas(dados: Dados, servicos: Servicos) -> list[str]:
    marcas = []
    t = dados.teste
    if t is not None and t.dependente_do_opus:
        marcas.append(
            "**dependente do Opus**: a taxa sem o Opus fica mais de "
            f"{servicos.config.geral.criterios.pontos_dependencia_opus} pontos abaixo da completa"
        )
    if t is not None and t.banco.filtrado_pelo_verificador:
        marcas.append(
            "**filtrado pelo verificador**: o erro pedido existe em "
            f"{len(t.banco.descartadas_com_erro)} das descartadas da amostra"
        )
    sem, total = sem_local(dados, servicos)
    fracao = servicos.config.geral.valvula.fracao_sem_local_para_ressalva
    if total and sem / total > fracao:
        marcas.append(
            f"**sem conferente local estável**: {sem} de {total} peças de risco médio e alto "
            f"ficaram sem a resposta do modelo local (mais de {pct(fracao)})"
        )
    if t is not None and t.banco.nao_confiavel:
        marcas.append(
            "**banco não confiável**: com ele, o critério central não decide; a verificação "
            "precisa ser corrigida antes de um novo teste"
        )
    return marcas


def _tabela(cabecalho: Sequence[str], linhas: Sequence[Sequence[str]]) -> list[str]:
    saida = ["| " + " | ".join(cabecalho) + " |", "|" + "---|" * len(cabecalho)]
    saida += ["| " + " | ".join(str(c).replace("|", "/") for c in linha) + " |" for linha in linhas]
    return saida


def secao_custos(dados: Dados, servicos: Servicos) -> list[str]:
    c = custos(dados, servicos)
    por_peca = dolares(c.producao // c.pecas) if c.pecas else "—"
    marginal = dolares(round(c.marginal)) if c.marginal is not None else "—"
    return [
        f"- Custo por peça: {por_peca} ({c.pecas} peça(s) com rascunho, {dolares(c.producao)} "
        "de ficha, redação, refações e conferência).",
        f"- Custo marginal por peça aprovada: {marginal}.",
        f"- Custos únicos, separados: ensaios {dolares(c.ensaio)}; cópias com erro "
        f"{dolares(c.banco)}, das quais as descartadas {dolares(c.descartadas)}; teste dos "
        f"conferentes {dolares(c.teste)}.",
    ]


def secao_local(dados: Dados, servicos: Servicos) -> list[str]:
    duracao = 0.0
    for caminho in servicos.arquivos.listar(CONFERENCIAS, f"{dados.rodada}_*_local.json"):
        duracao += servicos.arquivos.ler_json(caminho, ResultadoConferenteLocal).duracao_segundos
    quedas = da_rodada(dados, estado.QUEDA_LOCAL)
    substituicoes = da_rodada(dados, estado.SUBSTITUICAO_OPUS)
    pausas = da_rodada(dados, estado.PAUSA_7_DIAS)
    sem, total = sem_local(dados, servicos)
    linhas = [
        f"- Tempo do modelo local: {duracao:.0f} segundos.",
        f"- Janelas sem conferência local: {len(quedas)} registro(s) de modelo indisponível; "
        f"{len(substituicoes)} substituição(ões) pelo Opus; {len(pausas)} pausa(s) de 7 dias.",
        f"- Peças de risco médio e alto sem a resposta do modelo local: {sem} de {total}.",
    ]
    fracao = servicos.config.geral.valvula.fracao_sem_local_para_ressalva
    if total and sem / total > fracao:
        linhas.append("- Marca: **sem conferente local estável**.")
    return linhas


def secao_causas(dados: Dados, servicos: Servicos) -> list[str]:
    categorias: Counter[str] = Counter()
    motivos = []
    for p in dados.pecas:
        for c in versoes(p, servicos):
            if c.veredito != "aprovada":
                categorias[c.categoria_motivo or "sem categoria"] += 1
                motivos.append(f"  - {c.peca}_v{c.versao} ({c.categoria_motivo}): {c.motivo}")
    linhas = [
        "- Por categoria: "
        + (", ".join(f"{k}: {n}" for k, n in sorted(categorias.items())) or "nenhuma reprovação")
    ]
    linhas += motivos
    reprovadas = [p for p, c in sorted(dados.cartoes.items()) if c.veredito_ficha == "reprovada"]
    linhas.append(
        "- Fichas reprovadas pelo responsável: "
        + (", ".join(reprovadas) if reprovadas else "nenhuma")
    )
    for caminho in servicos.arquivos.listar(FICHAS, f"{dados.rodada}_*_descartada.json"):
        lida = _ler_json(servicos, caminho)
        linhas.append(f"  - ficha descartada pelo programa: {lida['peca']} ({lida['causa']})")
    fracao = servicos.config.geral.criterios.fracao_fichas_reprovadas_por_tipo
    for tipo in sorted({p.tipo for p in dados.pecas}):
        com_cartao = [p for p in dados.pecas if p.tipo == tipo and p.id in dados.cartoes]
        if not com_cartao:
            continue
        n = sum(dados.cartoes[p.id].veredito_ficha == "reprovada" for p in com_cartao)
        if n / len(com_cartao) > fracao:
            linhas.append(
                f"- {tipo}: {n} de {len(com_cartao)} fichas reprovadas, acima de {pct(fracao)}: "
                f"a falha vai para `ficha.md` e `fichas.py` do tipo {tipo}."
            )
    return linhas


def secao_ocorrencias(dados: Dados) -> list[str]:
    linhas = [
        f"- {o.tipo} · {o.causa} · {o.peca or '—'} · {o.detalhe}"
        for o in da_rodada(dados)
        if o.tipo in ("pausa", "parada", "intervencao")
    ]
    return linhas or ["- Nenhuma pausa nem intervenção."]


def secao_tipos(dados: Dados, servicos: Servicos) -> list[str]:
    por_tipo = servicos.config.geral.volume.pecas_por_tipo
    fechadas = fechadas_por_tipo(dados, servicos)
    linhas = []
    for tipo in sorted(set(dados.tipos) & ({p.tipo for p in dados.pecas} | set(fechadas))):
        alvo = 1 if dados.ensaio else por_tipo
        linhas.append(f"- {tipo}: fechou {fechadas.get(tipo, 0)} de {alvo}.")
        for caminho in servicos.arquivos.listar(FICHAS, f"{dados.rodada}_{tipo}_casa*_vazia.json"):
            vazia = _ler_json(servicos, caminho)
            causa = "sem causa gravada"
            descarte = f"{FICHAS}/{vazia['ultima_peca']}_descartada.json"
            if servicos.arquivos.existe(descarte):
                causa = _ler_json(servicos, descarte)["causa"]
            linhas.append(f"  - casa {vazia['casa']} vazia: {causa}")
    return linhas or ["- Nenhuma peça."]


def _descartadas(dados: Dados, servicos: Servicos) -> list[Descartada]:
    caminho = teste_conferentes.caminho_descartadas(dados.rodada)
    if servicos.arquivos.existe(caminho):
        return list(servicos.arquivos.ler_json(caminho, teste_conferentes.DescartadasDoBanco).root)
    return [
        servicos.arquivos.ler_json(c, Descartada)
        for c in servicos.arquivos.listar("saida/erros", f"{dados.rodada}_*_descartada.json")
    ]


def _gabaritos(dados: Dados, servicos: Servicos) -> list[Gabarito]:
    caminho = teste_conferentes.caminho_gabarito(dados.rodada)
    if servicos.arquivos.existe(caminho):
        return list(servicos.arquivos.ler_json(caminho, teste_conferentes.GabaritoDoBanco).root)
    return [
        servicos.arquivos.ler_json(c, Gabarito)
        for c in servicos.arquivos.listar("saida/erros", f"{dados.rodada}_*_gabarito.json")
    ]


def secao_descartadas(dados: Dados, servicos: Servicos) -> list[str]:
    lidas = _descartadas(dados, servicos)
    if not lidas:
        return ["- Nenhuma cópia descartada."]

    def contar(chave: str) -> str:
        valores = Counter(str(getattr(d, chave)) for d in lidas)
        return ", ".join(f"{k}: {n}" for k, n in sorted(valores.items()))

    amostradas = [d for d in lidas if d.amostra is not None]
    existem = sum(d.amostra == "erro_existe" for d in amostradas)
    linhas = [
        f"- {len(lidas)} descartada(s).",
        f"- Por conferência: {contar('conferencia_que_falhou')}.",
        f"- Por motivo: {contar('motivo')}.",
        f"- Por tipo de erro: {contar('tipo_erro')}.",
        f"- Por sutileza: {contar('sutil')}.",
        f"- Amostra das descartadas: o erro pedido existe em {existem} de {len(amostradas)}.",
    ]
    if dados.teste is not None and dados.teste.banco.filtrado_pelo_verificador:
        linhas.append("- Marca: **banco filtrado pelo verificador**.")
    outro = [d for d in lidas if d.motivo == "outro_item"]
    for d in sorted(outro, key=lambda d: (d.tipo_erro, d.copia)):
        linhas.append(
            f"  - outro item: {d.tipo_erro} ({d.copia}), o Sonnet apontou "
            f"{d.item_apontado_pelo_verificador}"
        )
    return linhas


def secao_banco(dados: Dados, servicos: Servicos) -> list[str]:
    final: Counter[str] = Counter(
        g.tipo_erro for g in _gabaritos(dados, servicos) if g.amostra != "rejeitada"
    )
    try:
        plano = erros_plantados.plano_da_rodada(dados.rodada, servicos)
        resumo = erros_plantados.resumo_do_banco(dados.rodada, servicos)
    except Exception as erro:  # noqa: BLE001 - o relatório descreve o que falta
        return [f"- Sem o plano das vagas: {erro}."]
    planejados: Counter[str] = Counter(v.tipo_erro for v in plano.vagas)
    for g in _gabaritos(dados, servicos):
        if g.criador == "programa":
            planejados[g.tipo_erro] += 1
    linhas = _tabela(
        ("Tipo de erro", "Planejado pelo sorteio", "No banco final"),
        [(t, str(planejados[t]), str(final[t])) for t in sorted(set(planejados) | set(final))],
    )
    linhas.append("")
    linhas.append(
        f"- Vagas que trocaram de tipo depois de duas falhas: {resumo.trocaram_de_tipo}; "
        f"vagas perdidas: {resumo.perdidas}."
    )
    if plano.situacao == "faixa_media":
        linhas.append(
            "- Plano B: 6 cópias do Opus por peça boa; cópias da mesma original não são "
            "independentes entre si."
        )
    return linhas


def pedidos_que_nao_couberam(dados: Dados) -> list[Ocorrencia]:
    return da_rodada(dados, estado.NAO_CABE) + da_rodada(dados, estado.ACIMA_DO_LIMITE)


def secao_local_contexto(dados: Dados) -> list[str]:
    lidas = pedidos_que_nao_couberam(dados)
    if not lidas:
        return ["- Nenhum."]
    return [f"- {o.causa}: {o.detalhe} ({o.peca})" for o in lidas]


def secao_tokens(dados: Dados) -> list[str]:
    do_ensaio = [c for c in dados.chamadas if c.rodada.startswith("e")]
    if not do_ensaio:
        return ["- Nenhuma chamada de ensaio registrada."]
    linhas = []
    for tarefa in sorted({c.tarefa for c in do_ensaio}):
        dela = [c for c in do_ensaio if c.tarefa == tarefa]
        entrada = max(c.tokens_entrada for c in dela)
        saida = max(c.tokens_saida for c in dela)
        media = sum(c.tokens_entrada + c.tokens_saida for c in dela) // len(dela)
        linhas.append((tarefa, str(len(dela)), str(entrada), str(saida), str(media)))
    return _tabela(("Tarefa", "Chamadas", "Maior entrada", "Maior saída", "Média total"), linhas)


def secao_coerencia(dados: Dados, servicos: Servicos) -> list[str]:
    linhas = []
    for p in dados.pecas:
        for c in versoes(p, servicos):
            for item in c.itens:
                if item.item != "coerencia_ficha" or item.resposta != "nao_passa":
                    continue
                for d in item.divergencias:
                    linhas.append(
                        f"- {c.peca}_v{c.versao}: {d.regra}; extraído {d.extraido!r}; "
                        f"na ficha {d.ficha!r}"
                    )
    return linhas or ["- Nenhuma."]


def secao_nao_pegos(dados: Dados) -> list[str]:
    t = dados.teste
    if t is None:
        return ["- Sem o resultado do teste dos conferentes."]
    linhas = []
    for grupo in ORDEM_DOS_GRUPOS:
        copias = [c for c in t.copias if GRUPOS_DE_ERRO.get(c.tipo_erro, "outros") == grupo]
        if not copias:
            continue
        nao = sum(not c.pego for c in copias)
        por = [
            str(sum(quem in c.conferentes for c in copias))
            for quem in teste_conferentes.CONFERENTES
        ]
        linhas.append((grupo, str(len(copias)), str(nao), *por))
    return _tabela(
        ("Tipo de erro", "Cópias", "Não pegas", "Pegas pelo programa", "Haiku", "Local", "Opus"),
        linhas,
    )


# ---------------------------------------------------------------------------
# O relatório
# ---------------------------------------------------------------------------


def montar(dados: Dados, servicos: Servicos) -> str:
    aviso = f" ({AVISO_ENSAIO})" if dados.ensaio else ""
    linhas = [f"# Relatório do MVP — {dados.rodada}", ""]
    if dados.ensaio:
        linhas += [f"**{AVISO_ENSAIO.capitalize()}.**", ""]
    linhas.append(f"Os números deste relatório são da rodada {dados.rodada}.")
    if da_rodada(dados, tipo="intervencao"):
        linhas.append("Os números vieram de uma rodada com intervenção.")
    linhas.append("")
    linhas += ["## 1. Critérios da seção 6", ""]
    for c in criterios(dados, servicos):
        linhas += [
            f"### {c.nome}{aviso}",
            "",
            f"- Resultado: {c.resultado}",
            f"- Exigência: {c.exigencia}",
            f"- Margem: {c.margem}",
            f"- Papel: {'decide' if c.papel == 'decide' else 'indicador'}",
        ]
        linhas += [f"- Ao lado: {x}" for x in c.ao_lado]
        linhas.append("")
    marcas = ressalvas(dados, servicos)
    linhas += ["## Ressalvas", ""]
    linhas += [f"- {m}" for m in marcas] or ["- Nenhuma."]
    r = reprovacoes_das_boas(dados, servicos)
    abaixo, aprovadas = estilo(dados, servicos)
    linhas += [
        "",
        "## 2. Reprovações de peças boas",
        "",
        f"- Por conteúdo: {len(r.por_conteudo)} ({', '.join(r.por_conteudo) or 'nenhuma'}).",
        f"- Por semelhança: {len(r.so_semelhanca)} ({', '.join(r.so_semelhanca) or 'nenhuma'}).",
        "",
        "## 3. O que a regra de estilo teria reprovado",
        "",
        f"- {len(abaixo)} peça(s) ({', '.join(abaixo) or 'nenhuma'}); o responsável aprovou "
        f"{len(aprovadas)} delas.",
        "",
        "## 4. Custos",
        "",
        *secao_custos(dados, servicos),
        "",
        "## 5. Modelo local",
        "",
        *secao_local(dados, servicos),
        "",
        "## 6. Causas de reprovação e fichas reprovadas",
        "",
        *secao_causas(dados, servicos),
        "",
        "## 7. Pausas e intervenções",
        "",
        *secao_ocorrencias(dados),
        "",
        "## 8. Peças por tipo e casas vazias",
        "",
        *secao_tipos(dados, servicos),
        "",
        "## 9. Cópias descartadas",
        "",
        *secao_descartadas(dados, servicos),
        "",
        "## 10. Tipos de erro do banco final",
        "",
        *secao_banco(dados, servicos),
        "",
        "## 11. Pedidos ao modelo local que não couberam no contexto",
        "",
        *secao_local_contexto(dados),
        "",
        "## 12. Tokens reais de cada tarefa, medidos no ensaio",
        "",
        *secao_tokens(dados),
        "",
        "## 13. Reprovações por coerência com a ficha",
        "",
        *secao_coerencia(dados, servicos),
        "",
        "## 14. Erros não pegos, por conferente e por tipo de erro",
        "",
        *secao_nao_pegos(dados),
        "",
        "---",
        "",
        FINAL,
    ]
    return "\n".join(linhas) + "\n"


def gerar(rodada: str, servicos: Servicos) -> tuple[str, bool]:
    """Grava o relatório da rodada; devolve o caminho e se ele foi gravado agora."""
    destino = caminho_relatorio(rodada)
    if servicos.arquivos.existe(destino):
        return destino, False
    servicos.arquivos.gravar_texto(destino, montar(ler(rodada, servicos), servicos))
    return destino, True


# ---------------------------------------------------------------------------
# Fechamento do ensaio (ARQUITETURA §5.12.1)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Fechamento:
    aprovado: bool
    motivos: list[str]
    avisos: list[str]


def _valido(servicos: Servicos, caminho: str, modelo: Any) -> bool:
    if not servicos.arquivos.existe(caminho):
        return False
    try:
        servicos.arquivos.ler_json(caminho, modelo)
    except Exception:  # noqa: BLE001 - arquivo recusado pelo formato
        return False
    return True


def conferir_ensaio(rodada: str, etapas: Sequence[Any], servicos: Servicos) -> Fechamento:
    """Só lê: as três peças de ficha a pacote, os erros em miniatura, o formato, o
    congelamento e o contexto do modelo local."""
    arquivos = servicos.arquivos
    motivos: list[str] = []
    avisos: list[str] = []
    if not rodada.startswith("e"):
        return Fechamento(False, [f"{rodada} não é rodada de ensaio"], [])
    congelamento = Congelamento(arquivos, servicos.registro, servicos.relogio)
    try:
        registro_rodada: Rodada = congelamento.rodada(rodada)
    except Exception as erro:  # noqa: BLE001
        return Fechamento(False, [str(erro)], [])
    if registro_rodada.ensaio_aprovado:
        return Fechamento(False, [f"o ensaio {rodada} já está aprovado"], [])
    pecas = [p for p in estado.descobrir_pecas(arquivos) if p.rodada == rodada]
    com_rascunho = [p for p in pecas if tem_rascunho(p, servicos)]
    tipos = sorted({p.tipo for p in com_rascunho})
    if len(com_rascunho) != 3 or len(tipos) != 3:
        motivos.append(f"o ensaio precisa de três peças, uma de cada tipo; tem {len(com_rascunho)}")
    for p in pecas:
        atual = estado.ponto(p, etapas, servicos)
        if atual.acao not in estado.FINAIS:
            motivos.append(f"{p.id}: passo que não avançou ({atual.acao} {atual.etapa})")
    for p in com_rascunho:
        if not _valido(servicos, f"{FICHAS}/{p.id}.json", Ficha):
            motivos.append(f"{p.id}: sem ficha válida")
        if not _valido(servicos, f"{CONFERENCIAS}/{p.com_versao(1).nome_versao}.json", Conferencia):
            motivos.append(f"{p.id}: sem conferência da primeira versão")
        caminho = f"{CARTOES}/{p.id}_respostas.json"
        if not _valido(servicos, caminho, RespostasCartao):
            motivos.append(f"{p.id}: cartão do ensaio sem resposta")
        else:
            cartao = arquivos.ler_json(caminho, RespostasCartao)
            if cartao.tipo_cartao != "ensaio" or cartao.formato_certo is not True:
                motivos.append(
                    f"{p.id}: o responsável não confirmou o formato certo "
                    f"({cartao.formato_errado or 'sem descrição'})"
                )
        pacote = arquivos.listar(f"saida/pacotes/ensaio_{rodada}/{p.tipo}", f"{p.id}_v*.md")
        if not pacote:
            motivos.append(f"{p.id}: sem pacote")
        if not arquivos.listar("saida/erros", f"{p.id}_erro*_*.md"):
            motivos.append(f"{p.id}: sem cópia com erro")
    amostras = erros_plantados.caminho_amostras(rodada)
    if not _valido(servicos, amostras, Amostras):
        motivos.append("erros em miniatura: sem o sorteio das amostras (vagas sem resolver)")
    else:
        faltas = teste_conferentes.faltas(rodada, servicos)
        motivos += [f"erros em miniatura: {f}" for f in faltas]
    if not _valido(servicos, teste_conferentes.caminho_relatorio(rodada), ResultadoTeste):
        motivos.append("erros em miniatura: sem o resultado do teste dos conferentes")
    if not arquivos.existe(caminho_relatorio(rodada)):
        motivos.append("sem o relatório do ensaio (rode `relatorio --rodada`)")
    # Arquivo recusado pelo formato: toda resposta fora do formato gera um pedido t2.
    for caminho in [
        *arquivos.listar("saida/pedidos", f"{rodada}_*_t2.json"),
        *arquivos.listar("saida/pedidos", f"{teste_conferentes.PREFIXO}{rodada}_*_t2.json"),
    ]:
        pedido = arquivos.ler_json(caminho, Pedido)
        motivos.append(f"resposta fora do formato no pedido {pedido.nome.removesuffix('_t2')}_t1")
    mudancas = diferencas(registro_rodada.impressoes, congelamento.impressoes())
    if arquivos.mudanca_pendente():
        mudancas.append("mudança pendente")
    paradas = [
        o
        for o in servicos.registro.ocorrencias()
        if o.rodada == rodada and o.causa == "congelamento"
    ]
    if mudancas or paradas:
        motivos.append(
            "arquivos congelados mudaram: " + ", ".join(mudancas or [o.detalhe for o in paradas])
        )
    local = servicos.config.geral.modelo_local
    contexto = [
        o
        for o in servicos.registro.ocorrencias()
        if o.rodada == rodada and o.causa in (estado.NAO_CABE, estado.ACIMA_DO_LIMITE)
    ]
    if contexto:
        lista = ", ".join(sorted({o.detalhe for o in contexto}))
        if local.num_ctx < local.num_ctx_alternativo:
            motivos.append(
                f"pedidos ao modelo local que não couberam ou passaram de "
                f"{pct(local.fracao_limite_contexto_ensaio)} do num_ctx de "
                f"{milhar(local.num_ctx)}: {lista}. Suba num_ctx para "
                f"{milhar(local.num_ctx_alternativo)} no config.toml e faça um ensaio novo"
            )
        else:
            avisos.append(
                f"pedidos acima do limite com num_ctx de {milhar(local.num_ctx)}: {lista}"
            )
    return Fechamento(not motivos, motivos, avisos)


def fechar_ensaio(rodada: str, etapas: Sequence[Any], servicos: Servicos) -> Fechamento:
    fechamento = conferir_ensaio(rodada, etapas, servicos)
    if not fechamento.aprovado:
        return fechamento
    arquivos = servicos.arquivos
    lidas = arquivos.ler_json("saida/rodadas.json", Rodadas)
    agora = servicos.relogio()
    novas = [
        r.model_copy(update={"ensaio_aprovado": True, "aprovado_em": agora})
        if r.id == rodada
        else r
        for r in lidas.rodadas
    ]
    arquivos.regravar_rodadas(Rodadas(rodadas=novas))
    return fechamento
