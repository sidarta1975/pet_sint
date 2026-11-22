"""Teste dos conferentes (ARQUITETURA §5.1, §5.8 e Anexo C.4; brief 022).

`testar` é retomável:
1. recusa começar sem o sorteio das amostras (021) e sem as respostas confirmadas
   das duas amostras (020);
2. fecha o banco uma vez: `saida/erros/<rodada>_gabarito.json` e
   `<rodada>_descartadas.json`, com o campo `amostra` preenchido; a cópia rejeitada sai
   do banco e as descartadas não voltam; na rodada, as marcas de banco não confiável e
   filtrado pelo verificador;
3. registra as peças do teste para o `avancar`: cada cópia do banco e cada original,
   conferida de novo, viram `saida/rascunhos/teste_<cópia ou peça>_v1.md`. O condutor
   leva cada uma pela mesma lista de etapas da conferência (018), em modo de teste
   (semelhança desligada, sem refação), e os arquivos levam o prefixo `teste_`;
4. com todas as conferências do teste terminadas, grava o resultado com as cinco
   taxas, cada uma com a margem de Wilson de `estatistica.py`.

O teste é às cegas: o pedido de cada etapa leva o texto e a ficha da original, e não o
nome da cópia.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Any

from pydantic import RootModel

from fabrica import erros_plantados, estado
from fabrica.comum.estatistica import criterio_central_passa, wilson
from fabrica.comum.formatos import (
    Amostras,
    BancoTeste,
    Conferencia,
    CopiaTeste,
    Descartada,
    Gabarito,
    RespostasCartao,
    ResultadoTeste,
    TaxaTeste,
)
from fabrica.estado import RefPeca, Servicos

PREFIXO = "teste_"
ERROS = "saida/erros"
RASCUNHOS = "saida/rascunhos"
CARTOES = "saida/cartoes"
RELATORIO = "saida/relatorios/teste_conferentes.json"
SEM_OPUS = ("programa", "haiku", "local")
CONFERENTES = ("programa", "haiku", "local", "opus")


class ErroTeste(Exception):
    """Banco ou peça do teste que falta."""


class GabaritoDoBanco(RootModel[list[Gabarito]]):
    """`saida/erros/<rodada>_gabarito.json`, gravado uma vez no fechamento do banco."""


class DescartadasDoBanco(RootModel[list[Descartada]]):
    """`saida/erros/<rodada>_descartadas.json`, gravado uma vez no fechamento do banco."""


def caminho_relatorio(rodada: str) -> str:
    if rodada.startswith("e"):
        return f"saida/relatorios/teste_conferentes_ensaio_{rodada}.json"
    return RELATORIO


def caminho_gabarito(rodada: str) -> str:
    return f"{ERROS}/{rodada}_gabarito.json"


def caminho_descartadas(rodada: str) -> str:
    return f"{ERROS}/{rodada}_descartadas.json"


def servicos_do_teste(servicos: Servicos) -> Servicos:
    """Os mesmos serviços em modo de teste; o `config.toml` não muda."""
    return replace(servicos, modo_teste=True)


# ---------------------------------------------------------------------------
# 1. As amostras respondidas
# ---------------------------------------------------------------------------


def _respostas(identificador: str, servicos: Servicos) -> RespostasCartao | None:
    caminho = f"{CARTOES}/{identificador}_respostas.json"
    if not servicos.arquivos.existe(caminho):
        return None
    return servicos.arquivos.ler_json(caminho, RespostasCartao)


def faltas(rodada: str, servicos: Servicos) -> list[str]:
    """O que falta para o teste começar; lista vazia quando nada falta."""
    caminho = erros_plantados.caminho_amostras(rodada)
    if not servicos.arquivos.existe(caminho):
        return [
            f"falta o sorteio das amostras ({caminho}): rode `erros --rodada {rodada}` e "
            "`avancar` até todas as vagas do Opus se resolverem"
        ]
    amostras = servicos.arquivos.ler_json(caminho, Amostras)
    faltando = []
    if amostras.copias and _respostas(f"{rodada}_amostra_copias", servicos) is None:
        faltando.append("faltam as respostas confirmadas da amostra de 10 cópias (rode `revisar`)")
    if amostras.descartadas and _respostas(f"{rodada}_amostra_descartadas", servicos) is None:
        faltando.append(
            "faltam as respostas confirmadas da amostra das descartadas (rode `revisar`)"
        )
    return faltando


# ---------------------------------------------------------------------------
# 2. Fechamento do banco
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Banco:
    gabaritos: tuple[Gabarito, ...]
    descartadas: tuple[Descartada, ...]
    nao_confiavel: bool
    filtrado_pelo_verificador: bool

    @property
    def rejeitadas(self) -> list[str]:
        return [g.copia for g in self.gabaritos if g.amostra == "rejeitada"]

    @property
    def no_banco(self) -> list[Gabarito]:
        return [g for g in self.gabaritos if g.amostra != "rejeitada"]

    @property
    def descartadas_com_erro(self) -> list[str]:
        return [d.copia for d in self.descartadas if d.amostra == "erro_existe"]


def _marcas(rodada: str, banco: Banco, servicos: Servicos) -> Banco:
    if rodada.startswith("e"):
        return replace(banco, nao_confiavel=False, filtrado_pelo_verificador=False)
    criterios = servicos.config.geral.criterios
    return replace(
        banco,
        nao_confiavel=len(banco.rejeitadas) >= criterios.rejeitadas_para_banco_nao_confiavel,
        filtrado_pelo_verificador=len(banco.descartadas_com_erro)
        >= criterios.existentes_para_banco_filtrado,
    )


def fechar_banco(rodada: str, servicos: Servicos) -> Banco:
    """Grava o gabarito e as descartadas do banco uma vez; depois, só lê."""
    arquivos = servicos.arquivos
    if arquivos.existe(caminho_gabarito(rodada)):
        gabaritos = arquivos.ler_json(caminho_gabarito(rodada), GabaritoDoBanco).root
        descartadas = arquivos.ler_json(caminho_descartadas(rodada), DescartadasDoBanco).root
        return _marcas(rodada, Banco(tuple(gabaritos), tuple(descartadas), False, False), servicos)
    faltando = faltas(rodada, servicos)
    if faltando:
        raise ErroTeste("; ".join(faltando))
    copias = _respostas(f"{rodada}_amostra_copias", servicos)
    descartes = _respostas(f"{rodada}_amostra_descartadas", servicos)
    por_copia = {r.copia: r for r in (copias.amostra if copias else [])}
    por_descarte = {r.copia: r for r in (descartes.amostra if descartes else [])}
    gabaritos = []
    for caminho in arquivos.listar(ERROS, f"{rodada}_*_gabarito.json"):
        g = arquivos.ler_json(caminho, Gabarito)
        resposta = por_copia.get(g.copia)
        if resposta is not None:
            aceita = resposta.erro_existe and resposta.erro_do_gabarito is True
            g = g.model_copy(update={"amostra": "aceita" if aceita else "rejeitada"})
        gabaritos.append(g)
    descartadas = []
    for caminho in arquivos.listar(ERROS, f"{rodada}_*_descartada.json"):
        d = arquivos.ler_json(caminho, Descartada)
        resposta = por_descarte.get(d.copia)
        if resposta is not None:
            amostra = "erro_existe" if resposta.erro_existe else "erro_nao_existe"
            d = d.model_copy(update={"amostra": amostra})
        descartadas.append(d)
    arquivos.gravar_json(caminho_gabarito(rodada), GabaritoDoBanco(gabaritos))
    arquivos.gravar_json(caminho_descartadas(rodada), DescartadasDoBanco(descartadas))
    return _marcas(rodada, Banco(tuple(gabaritos), tuple(descartadas), False, False), servicos)


# ---------------------------------------------------------------------------
# 3. As peças do teste
# ---------------------------------------------------------------------------


def _peca(nome: str) -> str:
    return nome.split("_erro")[0]


def ref_do_teste(rodada: str, nome: str) -> RefPeca:
    """A cópia ou a original no teste: rodada, tipo e número da original (a ficha e o
    sorteio do conferente local são os dela) e o id `teste_<nome>`."""
    original = erros_plantados.ref_da_peca(rodada, _peca(nome))
    return replace(original, copia=f"{PREFIXO}{nome}")


def _nome(ref: RefPeca) -> str:
    assert ref.copia is not None
    return ref.copia.removeprefix(PREFIXO)


def _originais(banco: Banco) -> list[str]:
    return sorted({g.original.removesuffix("_v1") for g in banco.no_banco})


def registrar(rodada: str, servicos: Servicos) -> list[RefPeca]:
    """Grava o texto de cada peça do teste (as cópias do banco e as originais)."""
    banco = fechar_banco(rodada, servicos)
    arquivos = servicos.arquivos
    refs = []
    for nome in [*_originais(banco), *(g.copia for g in banco.no_banco)]:
        ref = ref_do_teste(rodada, nome)
        destino = f"{RASCUNHOS}/{ref.nome_versao}.md"
        if not arquivos.existe(destino):
            origem = f"{RASCUNHOS}/{nome}_v1.md" if "_erro" not in nome else f"{ERROS}/{nome}.md"
            arquivos.gravar_texto(destino, arquivos.ler_texto(origem))
        refs.append(ref)
    return sorted(refs)


def refs_do_teste(rodada: str | None, servicos: Servicos) -> list[RefPeca]:
    padrao = f"{PREFIXO}{rodada}_*_v1.md" if rodada else f"{PREFIXO}*_v1.md"
    refs = []
    for caminho in servicos.arquivos.listar(RASCUNHOS, padrao):
        nome = caminho.removeprefix(f"{RASCUNHOS}/{PREFIXO}").removesuffix("_v1.md")
        refs.append(ref_do_teste(nome[:3], nome))
    return sorted(refs)


def terminada(ref: RefPeca, servicos: Servicos) -> bool:
    arquivos = servicos.arquivos
    return estado.veredito(ref, arquivos) is not None or estado.destino(ref, arquivos) is not None


def coletar(etapas: Sequence[Any], servicos: Servicos) -> estado.ResumoAvanco:
    """A parte do `avancar` que leva as peças do teste, em modo de teste."""
    teste = servicos_do_teste(servicos)
    refs = [r for r in refs_do_teste(None, servicos) if not terminada(r, teste)]
    if not refs:
        return estado.ResumoAvanco()
    return estado.avancar(etapas, teste, refs)


# ---------------------------------------------------------------------------
# 4. A regra do pego e as taxas
# ---------------------------------------------------------------------------


def _finais(conferencia: Conferencia | None) -> dict[str, str]:
    if conferencia is None:
        return {}
    return {c.item: c.resposta_final for c in conferencia.caminho}


def avaliar(g: Gabarito, copia: Conferencia | None, original: Conferencia | None) -> CopiaTeste:
    """ARQUITETURA §5.1: pego só se a cópia reprova, um item aceito reprova nela e o
    mesmo item passou na original, conferida de novo no teste."""
    formato = copia is None
    pegos: list[str] = []
    conferentes: set[str] = set()
    sem_opus = False
    if copia is not None and copia.veredito != "aprovada":
        na_original = _finais(original)
        for caminho in copia.caminho:
            if caminho.item not in g.itens_aceitos or caminho.resposta_final != "nao_passa":
                continue
            if na_original.get(caminho.item) != "passa":
                continue
            pegos.append(caminho.item)
            quem = {r.quem for r in caminho.respostas if r.resposta == "nao_passa"}
            conferentes |= quem
            sem_opus = sem_opus or bool(quem & set(SEM_OPUS))
    return CopiaTeste(
        copia=g.copia,
        original=g.original,
        origem=g.origem,
        tipo_erro=g.tipo_erro,
        sutil=g.sutil,
        pego=bool(pegos),
        pego_sem_opus=sem_opus,
        itens_pegos=pegos,  # type: ignore[arg-type]
        conferentes=[c for c in CONFERENTES if c in conferentes],  # type: ignore[misc]
        formato=formato,
    )


def taxa(sucessos: int, total: int) -> TaxaTeste:
    if total == 0:
        return TaxaTeste(sucessos=0, total=0, taxa=None, inferior=None, superior=None)
    intervalo = wilson(sucessos, total)
    return TaxaTeste(
        sucessos=sucessos,
        total=total,
        taxa=intervalo.taxa,
        inferior=intervalo.inferior,
        superior=intervalo.superior,
    )


def _contar(copias: Sequence[CopiaTeste], sem_opus: bool = False) -> TaxaTeste:
    campo = "pego_sem_opus" if sem_opus else "pego"
    return taxa(sum(getattr(c, campo) for c in copias), len(copias))


def _inconclusivo_no_plano_b(rodada: str, servicos: Servicos) -> bool:
    return any(
        o.causa == erros_plantados.INCONCLUSIVO and o.rodada == rodada
        for o in servicos.registro.ocorrencias()
    )


def calcular(rodada: str, banco: Banco, servicos: Servicos) -> ResultadoTeste:
    arquivos = servicos.arquivos
    criterios = servicos.config.geral.criterios
    copias = []
    for g in banco.no_banco:
        da_copia = estado.veredito(ref_do_teste(rodada, g.copia), arquivos)
        da_original = estado.veredito(ref_do_teste(rodada, _peca(g.copia)), arquivos)
        copias.append(avaliar(g, da_copia, da_original))
    ia = [c for c in copias if c.origem == "opus"]
    julgamento = [c for c in copias if c.origem == "programa_julgamento"]
    regra = [c for c in copias if c.origem == "programa_regra"]
    completa, sem = _contar(ia), _contar(ia, sem_opus=True)
    originais = _originais(banco)
    reprovadas = 0
    for nome in originais:
        conferencia = estado.veredito(ref_do_teste(rodada, nome), arquivos)
        reprovadas += conferencia is None or conferencia.veredito != "aprovada"
    if banco.nao_confiavel:
        decisao = "nao_decide"
    elif not ia or _inconclusivo_no_plano_b(rodada, servicos):
        decisao = "inconclusivo"
    else:
        intervalo = wilson(completa.sucessos, completa.total)
        passa = criterio_central_passa(
            intervalo, criterios.taxa_minima, criterios.limite_inferior_minimo
        )
        decisao = "passa" if passa else "nao_passa"
    dependente = (
        completa.taxa is not None
        and sem.taxa is not None
        and (completa.taxa - sem.taxa) * 100 > criterios.pontos_dependencia_opus
    )
    por_conferente = {
        quem: taxa(sum(quem in c.conferentes for c in copias), len(copias)) for quem in CONFERENTES
    }
    por_tipo: dict[str, TaxaTeste] = {
        t: _contar([c for c in copias if c.tipo_erro == t])
        for t in sorted({c.tipo_erro for c in copias})
    }
    por_origem: dict[str, TaxaTeste] = {
        o: _contar([c for c in copias if c.origem == o]) for o in sorted({c.origem for c in copias})
    }
    return ResultadoTeste(
        rodada=rodada,
        gravado_em=servicos.relogio(),
        banco=BancoTeste(
            copias=len(banco.no_banco),
            copias_ia=len(ia),
            rejeitadas=banco.rejeitadas,
            descartadas=len(banco.descartadas),
            descartadas_com_erro=banco.descartadas_com_erro,
            nao_confiavel=banco.nao_confiavel,
            filtrado_pelo_verificador=banco.filtrado_pelo_verificador,
        ),
        criterio_central=completa,
        sem_opus=sem,
        julgamento_programa=_contar(julgamento),
        julgamento_inconclusivo=len(julgamento) < criterios.minimo_copias_julgamento,
        regra_programa=_contar(regra),
        regra_sanidade_ok=all(c.pego for c in regra),
        reprovacao_pecas_boas=taxa(reprovadas, len(originais)),
        decisao_criterio_central=decisao,  # type: ignore[arg-type]
        dependente_do_opus=dependente,
        nao_pegas_formato=[c.copia for c in copias if c.formato],
        copias=copias,
        por_conferente=por_conferente,
        por_tipo_erro=por_tipo,
        por_origem=por_origem,
    )


# ---------------------------------------------------------------------------
# O comando
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Situacao:
    recusa: list[str]
    faltam: int
    relatorio: str | None
    resultado: ResultadoTeste | None = None


def testar(rodada: str, etapas: Sequence[Any], servicos: Servicos) -> Situacao:
    """Uma chamada do comando `testar`; `etapas` é a lista da conferência (018)."""
    arquivos = servicos.arquivos
    destino = caminho_relatorio(rodada)
    if arquivos.existe(destino):
        return Situacao([], 0, destino, arquivos.ler_json(destino, ResultadoTeste))
    if not arquivos.existe(caminho_gabarito(rodada)):
        faltando = faltas(rodada, servicos)
        if faltando:
            return Situacao(faltando, 0, None)
    refs = registrar(rodada, servicos)
    faltam = sum(not terminada(r, servicos) for r in refs)
    if faltam:
        return Situacao([], faltam, None)
    banco = fechar_banco(rodada, servicos)
    resultado = calcular(rodada, banco, servicos)
    arquivos.gravar_json(destino, resultado)
    return Situacao([], 0, destino, resultado)
