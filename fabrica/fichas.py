"""Fichas com âncora (ARQUITETURA §5.4, Anexos A e E; brief 015).

O programa faz a base da ficha (casa da matriz, combinação, datas, dados fictícios,
identificadores SINT-) e a grava em `saida/fichas/<peça>_base.json` antes do pedido
ao Haiku, que escreve só os campos de `RespostaFicha*`. A ficha final,
`saida/fichas/<peça>.json`, junta as duas partes e só é gravada quando passa em
todas as conferências.

Etapas (registro de decisão 002): `EtapaFicha` recebe a primeira resposta;
`EtapaRetorno` manda a ficha que falhou de volta ao Haiku uma vez, com o motivo.
Falhando de novo, a ficha é descartada e a mesma casa recebe uma ficha nova, até
`fichas_novas_por_casa` vezes; depois a casa fica vazia e registrada.

O texto enviado ao Haiku é lido de `instrucoes/ficha.md`; nenhum trecho dele fica aqui.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import math
import random
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, ValidationError

from fabrica import estado, estruturas, matriz
from fabrica.comum import normalizacao
from fabrica.comum.api_claude import ApiClaude
from fabrica.comum.arquivos import RODADAS, Arquivos
from fabrica.comum.config import Config
from fabrica.comum.congelamento import Congelamento, diferencas
from fabrica.comum.formatos import (
    NOME_POR_ROTULO,
    Advogado,
    BaseFicha,
    CatalogoTipos,
    Categoria,
    Configuracao,
    FeriadosNacionais,
    Ficha,
    FichaEmbargos,
    FichaInicial,
    FichaQualquer,
    ListasFicticias,
    Matriz,
    PalavrasIgnoradas,
    Parte,
    ParteDoPedido,
    Pedido,
    PrazoProcessual,
    Processo,
    Resposta,
    RespostaFichaEmbargos,
    RespostaFichaInicial,
    RespostaFichaManifestacao,
    Rodada,
    Rodadas,
    TabelaNormas,
    TipoCatalogo,
    Travas,
)
from fabrica.estado import FORA_DO_FORMATO, RefPeca, Servicos
from fabrica.ficticios import Ficticios

PASTA = "saida/fichas"
PEDIDOS = "saida/pedidos"
CONDUCAO = "saida/conducao"
INSTRUCAO = "instrucoes/ficha.md"
ETAPA_FICHA = "ficha"
ETAPA_RETORNO = "ficha_retorno"
INICIAL = "peticao_inicial_jec"
EMBARGOS = "embargos_declaracao"
MANIFESTACAO = "manifestacao_ar_negativo"
JUIZADO = "juizado_especial_civel"
DECISAO = ("contradicao", "obscuridade", "erro_material")
MODELOS: dict[str, type[BaseModel]] = {
    INICIAL: RespostaFichaInicial,
    EMBARGOS: RespostaFichaEmbargos,
    MANIFESTACAO: RespostaFichaManifestacao,
}
# Fase escrita na ficha, pelo momento fixo de cada tipo (Anexo A.6).
FASES = {
    INICIAL: "antes da citação",
    EMBARGOS: "depois da decisão embargada",
    MANIFESTACAO: "depois da juntada do aviso de recebimento",
}
# Provisórios, registrados no relatório do brief 015: prazo da determinação judicial
# (None = o juiz não fixou, 5 dias úteis) e prazo pedido na ciência e prazo.
PRAZOS_DA_DETERMINACAO: tuple[int | None, ...] = (None, 10, 15)
PRAZOS_PEDIDOS = (10, 15, 20, 30)
IDENTIFICADORES_POR_FICHA = 4
CATEGORIA_PADRAO_AUTOR: Categoria = "pessoa_fisica"
CATEGORIA_PADRAO_REU: Categoria = "pessoa_juridica_privada"

# Códigos de falha (o motivo que volta ao Haiku começa pelo código).
FORMATO = "formato"
DATAS_FORA_DE_ORDEM = "datas_fora_de_ordem"
FATO_FORA_DO_PERIODO = "fato_fora_do_periodo"
DADO_DA_BASE = "dado_da_base_mudado"
IDENTIFICADOR = "identificador_fora_da_base"
VALOR_INEXISTENTE = "valor_inexistente"
VALOR_CAUSA_DIFERENTE = "valor_causa_diferente"
ALCADA = "alcada"
VALOR_LEGAL = "valor_igual_a_referencia_legal"
FUNDAMENTO_FORA_DO_TRECHO = "fundamento_fora_do_trecho"
TRAVA = "trava"
ARGUMENTOS_INSUFICIENTES = "argumentos_insuficientes"
ORIGEM_DA_ANCORA = "origem_da_ancora"
TRECHO_FORA_DA_DECISAO = "trecho_fora_da_decisao"
TRECHO_FORA_DO_ARGUMENTO = "trecho_fora_do_argumento"
ANCORA_FRACA = "ancora_fraca"
TERMOS_NA_DECISAO = "termos_na_decisao"
MENCAO_FORA_DA_DECISAO = "mencao_fora_da_decisao"
MENCAO_LONGA = "mencao_longa"
POUCOS_TERMOS_NA_MENCAO = "poucos_termos_na_mencao"
TERMOS_FORA_DA_MENCAO = "termos_fora_da_mencao"
ARGUMENTOS_MINIMOS = 3


class ErroFichas(Exception):
    """Comando `fichas` ou `ensaio` que não pode seguir."""


@dataclass(frozen=True)
class Falha:
    codigo: str
    detalhe: str

    def texto(self) -> str:
        return f"{self.codigo}: {self.detalhe}"


@dataclass(frozen=True)
class Contexto:
    config: Configuracao
    catalogo: dict[str, TipoCatalogo]
    matrizes: dict[str, Matriz]
    travas: Travas
    tabela: TabelaNormas
    trechos: dict[str, estruturas.Trecho]
    ignoradas: PalavrasIgnoradas
    feriados: frozenset[datetime.date]
    listas: ListasFicticias
    instrucao: str


def carregar_contexto(arquivos: Arquivos, config: Config) -> Contexto:
    catalogo = arquivos.ler_json("dados/catalogo/tipos.json", CatalogoTipos)
    tabela = arquivos.ler_json("dados/normas/tabela_normas.json", TabelaNormas)
    geral = config.geral
    nomes = [t.nome_curto for t in catalogo.tipos]
    feriados = arquivos.ler_json("dados/conferencia/feriados_nacionais.json", FeriadosNacionais)
    return Contexto(
        config=geral,
        catalogo={t.nome_curto: t for t in catalogo.tipos},
        matrizes={n: arquivos.ler_json(f"dados/matrizes/{n}.json", Matriz) for n in nomes},
        travas=arquivos.ler_json("dados/travas/travas.json", Travas),
        tabela=tabela,
        trechos={
            n: estruturas.trecho_da_tabela(tabela, n, geral.trecho.teto_tokens) for n in nomes
        },
        ignoradas=arquivos.ler_json("dados/conferencia/palavras_ignoradas.json", PalavrasIgnoradas),
        feriados=frozenset(f.data for f in feriados.feriados),
        listas=arquivos.ler_json("dados/ficticios/listas_ficticias.json", ListasFicticias),
        instrucao=arquivos.ler_texto(INSTRUCAO),
    )


# ---------------------------------------------------------------------------
# Base da ficha
# ---------------------------------------------------------------------------


def _semente_da_peca(semente: int, peca: str) -> int:
    return int(hashlib.sha256(f"{semente}:{peca}".encode()).hexdigest()[:12], 16)


def _parte(
    fic: Ficticios,
    rng: random.Random,
    papel: str,
    categoria: Categoria,
    cidade: str | None,
    estados_civis: list[str],
) -> Parte:
    pf = categoria == "pessoa_fisica"
    return Parte(
        id="parte_autora" if papel == "autor" else "parte_re",
        papel=papel,  # type: ignore[arg-type]
        categoria=categoria,
        nome=fic.nome(papel, categoria),
        documento=fic.cpf() if pf else fic.cnpj(),
        estado_civil=rng.choice(estados_civis) if pf else None,
        profissao=fic.profissao() if pf else None,
        endereco=fic.endereco(cidade),
        email=fic.email(papel),
        telefone=fic.telefone(),
        capaz=True if pf else None,
        preso=False if pf else None,
    )


def gerar_base(
    ctx: Contexto,
    rodada: str,
    semente: int,
    comb: matriz.Combinacao,
    numero: int,
    casa: int,
    tentativa: int,
) -> BaseFicha:
    """A parte da ficha que o programa faz, tirada da semente e do nome da peça."""
    cfg = ctx.config
    listas = ctx.listas
    peca = f"{rodada}_{comb.tipo}_{numero:03d}"
    fic = Ficticios(
        _semente_da_peca(semente, peca),
        cfg.ddds.inexistentes,
        listas.ruas,
        listas.bairros,
        listas.cidades,
        listas.tribunais,
        listas.profissoes,
    )
    rng = matriz.gerador(semente, peca, "ficha")
    cidade = rng.choice(listas.cidades)
    prazo_fixado = rng.choice(PRAZOS_DA_DETERMINACAO) if comb.tipo == MANIFESTACAO else None
    datas = matriz.sortear_datas(rng, comb.tipo, ctx.feriados, cfg.matriz, prazo_fixado)
    juizo = cidade.juizo_jec if comb.rito == JUIZADO else rng.choice(cidade.varas_civeis)
    autor = _parte(
        fic,
        rng,
        "autor",
        comb.categoria_autor or CATEGORIA_PADRAO_AUTOR,
        cidade.nome,
        listas.estados_civis,
    )
    reu = _parte(
        fic, rng, "reu", comb.categoria_reu or CATEGORIA_PADRAO_REU, None, listas.estados_civis
    )
    ano = cfg.referencias_legais.ano_das_fichas
    processo = Processo(
        identificador_ficticio=fic.identificador(ano),
        numero_cnj=None
        if comb.tipo == INICIAL
        else fic.numero_processo(cidade.uf, datas.ajuizamento.year),
        rito=comb.rito,
        comarca=cidade.nome,
        uf=cidade.uf,
        juizo=juizo,
        data_ajuizamento=datas.ajuizamento,
    )
    advogado = Advogado(
        nome=fic.nome_advogado(),
        oab=fic.oab(),
        email=fic.email("advogado"),
        telefone=fic.telefone(),
        endereco_escritorio=fic.endereco(cidade.nome),
        representa=autor.id if comb.polo == "autor" else reu.id,
    )
    prazo = None
    if datas.termo_final is not None and datas.prazo_inicio and datas.prazo_dias:
        prazo = PrazoProcessual(
            inicio=datas.prazo_inicio, dias_uteis=datas.prazo_dias, termo_final=datas.termo_final
        )
    pedido_ar = comb.pedido_ar
    manifestacao = comb.tipo == MANIFESTACAO
    nova_diligencia = pedido_ar in ("informar_novo_endereco", "renovar_mesmo_endereco")
    return BaseFicha(
        peca=peca,
        rodada=rodada,
        tipo=comb.rotulo,
        classe_risco=ctx.catalogo[comb.tipo].classe_risco,
        semente=semente,
        casa=casa,
        tentativa=tentativa,
        casa_matriz=comb.casa(),
        rito=comb.rito,
        categoria_autor=autor.categoria,
        categoria_reu=reu.categoria,
        defeito=comb.defeito,
        tipo_decisao=comb.tipo_decisao,
        motivo_devolucao=comb.motivo_devolucao,
        pedido_ar=pedido_ar,
        processo=processo,
        partes=[autor, reu],
        advogado=advogado,
        identificadores=[fic.identificador(ano) for _ in range(IDENTIFICADORES_POR_FICHA)],
        salario_minimo_referencia=cfg.referencias_legais.salario_minimo_centavos,
        limite_fatos=datas.limite_fatos,
        data_decisao=datas.decisao,
        data_intimacao=datas.intimacao,
        data_juntada_aviso=datas.juntada_aviso,
        fase=FASES[comb.tipo],
        prazo=prazo,
        data_peca=datas.data_peca,
        local_peca=cidade.nome,
        endereco_tentado=reu.endereco if manifestacao else None,
        novo_endereco=fic.endereco() if pedido_ar == "informar_novo_endereco" else None,
        meio_nova_diligencia=rng.choice(["correio", "oficial_de_justica"])
        if nova_diligencia
        else None,
        prazo_pedido_dias=rng.choice(PRAZOS_PEDIDOS) if pedido_ar == "ciencia_e_prazo" else None,
    )


def nome_curto(base: BaseFicha) -> str:
    return NOME_POR_ROTULO[base.tipo]


def combinacao_da_base(base: BaseFicha) -> matriz.Combinacao:
    c = base.casa_matriz
    return matriz.Combinacao(
        tipo=nome_curto(base),  # type: ignore[arg-type]
        materia=c.materia,
        tese=c.tese,
        polo=c.polo,
        complexidade=c.complexidade,
        estilo=c.estilo,
        momento=c.momento,
        rito=base.rito,
        categoria_autor=base.categoria_autor,
        categoria_reu=base.categoria_reu,
        defeito=base.defeito,
        tipo_decisao=base.tipo_decisao,
        motivo_devolucao=base.motivo_devolucao,
        pedido_ar=base.pedido_ar,
    )


# ---------------------------------------------------------------------------
# Ficha final: base mais resposta
# ---------------------------------------------------------------------------


def _json(modelo: BaseModel | None) -> Any:
    return None if modelo is None else modelo.model_dump(mode="json")


def _id_do_papel(base: BaseFicha, papel: str) -> str:
    return next(p.id for p in base.partes if p.papel == papel)


def montar(base: BaseFicha, resposta: BaseModel) -> FichaQualquer:
    """Junta a base e a resposta; levanta ValidationError fora do formato da ficha."""
    r = resposta.model_dump(mode="json")
    dados: dict[str, Any] = {
        "id": base.peca,
        "tipo": base.tipo,
        "classe_risco": base.classe_risco,
        "casa_matriz": _json(base.casa_matriz),
        "semente": base.semente,
        "processo": _json(base.processo),
        "partes": [_json(p) for p in base.partes],
        "advogado": _json(base.advogado),
        "fatos": r["fatos"],
        "valores": r["valores"],
        "provas": r["provas"],
        "valor_causa": r["valor_causa"],
        "fundamentos": r["fundamentos"],
        "momento_processual": {
            "fase": base.fase,
            "ultima_decisao": r["momento_processual"]["ultima_decisao"],
            "prazo": _json(base.prazo),
        },
        "pecas_anteriores": r["pecas_anteriores"],
        "data_peca": base.data_peca.isoformat(),
        "local_peca": base.local_peca,
        "pedidos": r["pedidos"],
    }
    tipo = nome_curto(base)
    if tipo == INICIAL:
        dados |= {
            "materia": base.casa_matriz.materia,
            "relacao_consumo": r["relacao_consumo"],
            "inversao_onus_pedida": r["inversao_onus_pedida"],
            "tutela_urgencia": r["tutela_urgencia"],
            "tentativa_previa": r["tentativa_previa"],
            "salario_minimo_referencia": base.salario_minimo_referencia,
        }
    elif tipo == EMBARGOS:
        intimacao = base.data_intimacao.isoformat() if base.data_intimacao else None
        dados |= {
            "embargante": _id_do_papel(base, base.casa_matriz.polo),
            "decisao_embargada": {**r["decisao_embargada"], "data_intimacao": intimacao},
            "argumentos_das_partes": r["argumentos_das_partes"],
            "defeito": {"tipo": base.defeito, **r["defeito"]},
        }
    else:
        dados |= {
            "peticionante": _id_do_papel(base, "autor"),
            "citando": _id_do_papel(base, "reu"),
            "endereco_tentado": _json(base.endereco_tentado),
            "aviso_recebimento": {
                "data_juntada": base.data_juntada_aviso.isoformat()
                if base.data_juntada_aviso
                else None,
                "motivo_devolucao": base.motivo_devolucao,
            },
            "determinacao_judicial": {
                "data_intimacao": base.data_intimacao.isoformat() if base.data_intimacao else None,
                "prazo_dias_uteis": base.prazo.dias_uteis if base.prazo else None,
            },
            "pedido_ar": base.pedido_ar,
            "novo_endereco": _json(base.novo_endereco),
            "meio_nova_diligencia": base.meio_nova_diligencia,
            "prazo_pedido_dias": base.prazo_pedido_dias,
        }
    return Ficha.model_validate_json(json.dumps(dados)).root


def _resumo_do_erro(erro: ValidationError) -> str:
    return "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in erro.errors()[:5])


def conferir(
    base: BaseFicha, conteudo: str, ctx: Contexto
) -> tuple[FichaQualquer | None, list[Falha]]:
    """Formato, dados que vêm da base e as conferências da ficha pronta."""
    try:
        resposta = MODELOS[nome_curto(base)].model_validate_json(conteudo)
        ficha = montar(base, resposta)
    except ValidationError as erro:
        return None, [Falha(FORMATO, _resumo_do_erro(erro))]
    falhas = _conferir_com_base(base, ficha) + conferir_pronta(ficha, ctx)
    return ficha, falhas


def _conferir_com_base(base: BaseFicha, ficha: FichaQualquer) -> list[Falha]:
    falhas: list[Falha] = []
    usados = [p.identificador for p in ficha.provas]
    if isinstance(ficha, FichaInicial) and ficha.tentativa_previa is not None:
        usados.append(ficha.tentativa_previa.protocolo)
    fora = [u for u in usados if u not in base.identificadores]
    if fora:
        falhas.append(Falha(IDENTIFICADOR, f"identificadores fora da base: {', '.join(fora)}"))
    if isinstance(ficha, FichaEmbargos):
        d = ficha.decisao_embargada
        if d.tipo != base.tipo_decisao or d.data != base.data_decisao:
            falhas.append(
                Falha(
                    DADO_DA_BASE,
                    f"decisão {d.tipo} de {d.data}; a base pede "
                    f"{base.tipo_decisao} de {base.data_decisao}",
                )
            )
        if d.juizo != base.processo.juizo:
            falhas.append(
                Falha(DADO_DA_BASE, f"juízo da decisão {d.juizo!r} diferente do processo")
            )
    return falhas


def _anos_antes(data: datetime.date, anos: int) -> datetime.date:
    try:
        return data.replace(year=data.year - anos)
    except ValueError:  # 29 de fevereiro
        return data.replace(year=data.year - anos, day=28)


def _datas(ficha: FichaQualquer, ctx: Contexto) -> list[Falha]:
    falhas: list[Falha] = []
    ajuizamento = ficha.processo.data_ajuizamento
    limite = _anos_antes(ajuizamento, ctx.config.matriz.anos_maximos_dos_fatos)
    datas = [f.data for f in ficha.fatos]
    if datas != sorted(datas):
        falhas.append(Falha(DATAS_FORA_DE_ORDEM, "os fatos não estão em ordem de data"))
    periodo = list(datas)
    if isinstance(ficha, FichaInicial) and ficha.tentativa_previa is not None:
        periodo.append(ficha.tentativa_previa.data)
    fora = [d.isoformat() for d in periodo if d < limite or d > ajuizamento]
    if fora:
        falhas.append(
            Falha(
                FATO_FORA_DO_PERIODO, f"datas fora de {limite} a {ajuizamento}: {', '.join(fora)}"
            )
        )
    depois = [p.data.isoformat() for p in ficha.pecas_anteriores if p.data > ficha.data_peca]
    if isinstance(ficha, FichaEmbargos):
        d = ficha.decisao_embargada
        if not ajuizamento <= d.data <= d.data_intimacao <= ficha.data_peca:
            depois.append(f"decisão {d.data}, intimação {d.data_intimacao}")
    if depois:
        falhas.append(Falha(DATAS_FORA_DE_ORDEM, f"datas depois da peça: {', '.join(depois)}"))
    return falhas


def _valores(ficha: FichaQualquer, ctx: Contexto) -> list[Falha]:
    falhas: list[Falha] = []
    legais = ctx.config.referencias_legais
    centavos = {v.id: v.centavos for v in ficha.valores}
    usados = [i for f in ficha.fatos for i in f.valores]
    usados += [p.valor for p in ficha.pedidos if p.valor is not None]
    if ficha.valor_causa is not None:
        usados.append(ficha.valor_causa)
    faltam = sorted({i for i in usados if i not in centavos})
    if faltam:
        falhas.append(Falha(VALOR_INEXISTENTE, f"ids fora de valores[]: {', '.join(faltam)}"))
    if isinstance(ficha, FichaInicial):
        soma = sum(centavos.get(p.valor, 0) for p in ficha.pedidos if p.valor is not None)
        causa = centavos.get(ficha.valor_causa or "")
        if causa != soma:
            falhas.append(
                Falha(
                    VALOR_CAUSA_DIFERENTE,
                    f"valor da causa {causa} e soma dos pedidos {soma} (art. 292, V e VI, do CPC)",
                )
            )
    elif ficha.valor_causa is not None:
        falhas.append(Falha(VALOR_CAUSA_DIFERENTE, "valor da causa não se aplica a este tipo"))
    salario = legais.salario_minimo_centavos
    alcada = legais.alcada_em_salarios_minimos * salario
    causa_ = centavos.get(ficha.valor_causa or "")
    if ficha.processo.rito == JUIZADO and causa_ is not None and causa_ > alcada:
        falhas.append(Falha(ALCADA, f"valor da causa {causa_} acima da alçada {alcada}"))
    iguais = [v.id for v in ficha.valores if v.centavos in (salario, alcada)]
    if iguais:
        falhas.append(
            Falha(VALOR_LEGAL, f"valores iguais ao salário mínimo ou à alçada: {', '.join(iguais)}")
        )
    return falhas


def conferir_pronta(ficha: FichaQualquer, ctx: Contexto) -> list[Falha]:
    """As conferências de ARQUITETURA §5.4 sobre a ficha montada."""
    falhas = _datas(ficha, ctx) + _valores(ficha, ctx)
    trecho = {d.id for d in ctx.trechos[NOME_POR_ROTULO[ficha.tipo]].dispositivos}
    fora = [f for f in ficha.fundamentos if f not in trecho]
    if fora:
        falhas.append(
            Falha(FUNDAMENTO_FORA_DO_TRECHO, f"fora do trecho do tipo: {', '.join(fora)}")
        )
    for trava in matriz.violacoes(ctx.travas.travas, matriz.visao_da_ficha(ficha)):
        falhas.append(
            Falha(TRAVA, f"{trava.efeito} {trava.campo_exigido or ''}: {trava.base_legal}")
        )
    if isinstance(ficha, FichaEmbargos):
        if len(ficha.argumentos_das_partes) < ARGUMENTOS_MINIMOS:
            falhas.append(
                Falha(ARGUMENTOS_INSUFICIENTES, f"menos de {ARGUMENTOS_MINIMOS} argumentos")
            )
        falhas += conferir_ancora(ficha, ctx.ignoradas, ctx.config.ancora)
    return falhas


# ---------------------------------------------------------------------------
# Âncora do defeito (Anexo E.1)
# ---------------------------------------------------------------------------


def _na_decisao(ficha: FichaEmbargos, trecho: str) -> bool:
    d = ficha.decisao_embargada
    return normalizacao.contem_trecho(d.fundamentacao, trecho) or normalizacao.contem_trecho(
        d.dispositivo, trecho
    )


def conferir_ancora(ficha: FichaEmbargos, ignoradas: PalavrasIgnoradas, cfg: Any) -> list[Falha]:
    """As regras de E.1, com os termos principais de E.2 (`normalizacao.py`)."""
    defeito = ficha.defeito
    ancora = defeito.ancora
    decisao = ficha.decisao_embargada
    trecho = ancora.trecho_literal
    if defeito.tipo in DECISAO:
        if ancora.origem != "decisao":
            return [Falha(ORIGEM_DA_ANCORA, f"no defeito {defeito.tipo}, a âncora é da decisão")]
        if not _na_decisao(ficha, trecho):
            return [
                Falha(
                    TRECHO_FORA_DA_DECISAO, "o trecho não está na fundamentação nem no dispositivo"
                )
            ]
        return []
    if ancora.origem != "argumento":
        return [Falha(ORIGEM_DA_ANCORA, f"na {defeito.tipo}, a âncora é de um argumento")]
    argumento = next((a for a in ficha.argumentos_das_partes if a.id == ancora.argumento_id), None)
    if argumento is None or not normalizacao.contem_trecho(argumento.texto, trecho):
        return [
            Falha(TRECHO_FORA_DO_ARGUMENTO, f"o trecho não está no argumento {ancora.argumento_id}")
        ]
    contexto = [f.descricao for f in ficha.fatos]
    contexto += [a.texto for a in ficha.argumentos_das_partes if a.id != argumento.id]
    termos = normalizacao.termos_principais(
        trecho,
        contexto,
        [*ignoradas.comuns, *ignoradas.juridicas],
        cfg.letras_minimas,
        cfg.letras_do_radical,
    )
    if len(termos) < cfg.termos_minimos:
        return [Falha(ANCORA_FRACA, f"{len(termos)} termo(s) principal(is): {', '.join(termos)}")]
    maximo = math.floor(cfg.fracao_maxima_fora_da_mencao * len(termos) + 1e-9)
    letras = cfg.letras_do_radical
    if defeito.tipo == "omissao_total":
        texto = f"{decisao.fundamentacao}\n{decisao.dispositivo}"
        achados = normalizacao.presentes(termos, texto, letras)
        if achados > maximo:
            return [
                Falha(
                    TERMOS_NA_DECISAO,
                    f"{achados} de {len(termos)} termos na decisão (máximo {maximo})",
                )
            ]
        return []
    mencao = defeito.trecho_mencao
    if mencao is None or not _na_decisao(ficha, mencao):
        return [Falha(MENCAO_FORA_DA_DECISAO, "o trecho da menção não está na decisão")]
    falhas: list[Falha] = []
    palavras = len(mencao.split())
    if palavras > cfg.palavras_maximas_mencao:
        falhas.append(Falha(MENCAO_LONGA, f"menção com {palavras} palavras"))
    na_mencao = normalizacao.presentes(termos, mencao, letras)
    metade = math.ceil(len(termos) / 2)
    if na_mencao < metade:
        falhas.append(
            Falha(
                POUCOS_TERMOS_NA_MENCAO,
                f"{na_mencao} de {len(termos)} termos na menção (mínimo {metade})",
            )
        )
    fora = " ".join(
        normalizacao.sem_trecho(t, mencao) if normalizacao.contem_trecho(t, mencao) else t
        for t in (decisao.fundamentacao, decisao.dispositivo)
    )
    achados = normalizacao.presentes(termos, fora, letras)
    if achados > maximo:
        falhas.append(
            Falha(
                TERMOS_FORA_DA_MENCAO,
                f"{achados} de {len(termos)} termos fora da menção (máximo {maximo})",
            )
        )
    return falhas


# ---------------------------------------------------------------------------
# Pedidos e arquivos
# ---------------------------------------------------------------------------


class _SemCliente:
    """Gravar o pedido não fala com a API; só `coletar` precisa da chave."""

    @property
    def messages(self) -> Any:
        raise ErroFichas("sem a chave da API: o pedido só pode ser gravado")


def _api(servicos: Servicos) -> ApiClaude:
    if servicos.api_claude is not None:
        return servicos.api_claude
    return ApiClaude(
        _SemCliente(),
        servicos.config,
        servicos.arquivos,
        servicos.registro,
        servicos.gasto,
        relogio=servicos.relogio,
    )


def ref_da_peca(peca: str) -> RefPeca:
    rodada, _, resto = peca.partition("_")
    tipo, _, numero = resto.rpartition("_")
    return RefPeca(rodada=rodada, tipo=tipo, numero=int(numero))


def _caminho_base(peca: str) -> str:
    return f"{PASTA}/{peca}_base.json"


def _gravar_pedido(servicos: Servicos, ctx: Contexto, base: BaseFicha) -> str:
    tipo = nome_curto(base)
    return _api(servicos).gravar_pedido(
        rodada=base.rodada,
        peca=base.peca,
        versao=None,
        tarefa="ficha",
        partes={
            "instrucoes": ctx.instrucao,
            "trecho": ctx.trechos[tipo].texto,
            "ficha": base.model_dump_json(indent=2),
        },
        modelo_resposta=MODELOS[tipo],
    )


def gravar(servicos: Servicos, ctx: Contexto, base: BaseFicha) -> str:
    """Grava a base e o pedido de ficha e liga o pedido à etapa da peça."""
    servicos.arquivos.gravar_json(_caminho_base(base.peca), base)
    caminho = _gravar_pedido(servicos, ctx, base)
    estado.registrar_pedido(ref_da_peca(base.peca), ETAPA_FICHA, caminho, servicos.arquivos)
    return caminho


def _resultado(peca: RefPeca, etapa: str) -> str:
    return f"{PASTA}/{peca.id}_conferencia_{etapa}.json"


def _ler_resultado(arquivos: Arquivos, caminho: str) -> dict[str, Any] | None:
    if not arquivos.existe(caminho):
        return None
    lido: dict[str, Any] = json.loads(arquivos.ler_texto(caminho))
    return lido


def _gravar_resultado(arquivos: Arquivos, caminho: str, falhas: list[Falha]) -> None:
    conteudo = {
        "passou": not falhas,
        "falhas": [{"codigo": f.codigo, "detalhe": f.detalhe} for f in falhas],
    }
    arquivos.gravar_texto(caminho, json.dumps(conteudo, ensure_ascii=False, indent=2) + "\n")


def _proximo_numero(arquivos: Arquivos, rodada: str, tipo: str) -> int:
    numeros = [
        int(c.rsplit("/", 1)[-1][len(f"{rodada}_{tipo}_") :].split("_")[0])
        for c in arquivos.listar(PASTA, f"{rodada}_{tipo}_*_base.json")
    ]
    return max(numeros, default=0) + 1


def descartar_e_trocar(
    servicos: Servicos, ctx: Contexto, base: BaseFicha, causa: str
) -> str | None:
    """Descarta a ficha; a mesma casa recebe uma ficha nova ou fica vazia."""
    arquivos = servicos.arquivos
    registro = {"peca": base.peca, "casa": base.casa, "tentativa": base.tentativa, "causa": causa}
    arquivos.gravar_texto(
        f"{PASTA}/{base.peca}_descartada.json",
        json.dumps(registro, ensure_ascii=False, indent=2) + "\n",
    )
    tipo = nome_curto(base)
    if base.tentativa - 1 < ctx.config.fichas.fichas_novas_por_casa:
        numero = _proximo_numero(arquivos, base.rodada, tipo)
        nova = gerar_base(
            ctx,
            base.rodada,
            base.semente,
            combinacao_da_base(base),
            numero,
            base.casa,
            base.tentativa + 1,
        )
        gravar(servicos, ctx, nova)
        return nova.peca
    vazia = {"rodada": base.rodada, "tipo": tipo, "casa": base.casa, "ultima_peca": base.peca}
    arquivos.gravar_texto(
        f"{PASTA}/{base.rodada}_{tipo}_casa{base.casa:02d}_vazia.json",
        json.dumps(vazia, ensure_ascii=False, indent=2) + "\n",
    )
    return None


def repor_falhas_de_formato(servicos: Servicos) -> list[str]:
    """Fichas que o condutor encerrou por formato (ARQUITETURA §5.12.8) seguem a regra
    da ficha que falha: descarte e ficha nova na casa. Repetir não troca de novo."""
    arquivos = servicos.arquivos
    novas: list[str] = []
    ctx: Contexto | None = None
    for caminho in arquivos.listar(CONDUCAO, "*_v1_destino.txt"):
        if arquivos.ler_texto(caminho).strip() != estado.FICHA_FALHOU:
            continue
        peca = caminho.rsplit("/", 1)[-1].removesuffix("_v1_destino.txt")
        if arquivos.existe(f"{PASTA}/{peca}_descartada.json"):
            continue
        if not arquivos.existe(_caminho_base(peca)):
            continue
        ctx = ctx or carregar_contexto(arquivos, servicos.config)
        base = arquivos.ler_json(_caminho_base(peca), BaseFicha)
        nova = descartar_e_trocar(servicos, ctx, base, "resposta fora do formato duas vezes")
        if nova:
            novas.append(nova)
    return novas


# ---------------------------------------------------------------------------
# Etapas
# ---------------------------------------------------------------------------


def _receber(peca: RefPeca, resposta: Resposta, servicos: Servicos, etapa: str) -> str | None:
    arquivos = servicos.arquivos
    base = arquivos.ler_json(_caminho_base(peca.id), BaseFicha)
    try:
        MODELOS[nome_curto(base)].model_validate_json(resposta.conteudo)
    except ValidationError:
        return FORA_DO_FORMATO
    ctx = carregar_contexto(arquivos, servicos.config)
    ficha, falhas = conferir(base, resposta.conteudo, ctx)
    _gravar_resultado(arquivos, _resultado(peca, etapa), falhas)
    if not falhas and ficha is not None:
        arquivos.gravar_json(f"{PASTA}/{peca.id}.json", Ficha(ficha))
        return None
    if etapa == ETAPA_FICHA and ctx.config.fichas.retornos_ao_haiku >= 1:
        return None  # a EtapaRetorno manda de volta, com o motivo
    causa = "; ".join(f.texto() for f in falhas)
    descartar_e_trocar(servicos, ctx, base, causa)
    return None


class EtapaFicha:
    nome = ETAPA_FICHA

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        return peca.copia is None

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return _resultado(peca, self.nome)

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        """O pedido é gravado por `fichas`, `ensaio` ou pela troca da casa."""
        caminho = f"{PEDIDOS}/{peca.id}_ficha_t1.json"
        if servicos.arquivos.existe(caminho):
            return caminho
        ctx = carregar_contexto(servicos.arquivos, servicos.config)
        base = servicos.arquivos.ler_json(_caminho_base(peca.id), BaseFicha)
        return _gravar_pedido(servicos, ctx, base)

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        return _receber(peca, resposta, servicos, self.nome)


class EtapaRetorno:
    nome = ETAPA_RETORNO

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        if peca.copia is not None or servicos.config.geral.fichas.retornos_ao_haiku < 1:
            return False
        lido = _ler_resultado(servicos.arquivos, _resultado(peca, ETAPA_FICHA))
        return lido is not None and not lido["passou"]

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return _resultado(peca, self.nome)

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        arquivos = servicos.arquivos
        original = arquivos.ler_json(f"{PEDIDOS}/{peca.id}_ficha_t1.json", Pedido)
        lido = _ler_resultado(arquivos, _resultado(peca, ETAPA_FICHA)) or {"falhas": []}
        motivo = "\n".join(f"- {f['codigo']}: {f['detalhe']}" for f in lido["falhas"])
        nome = f"{peca.id}_{ETAPA_RETORNO}_t1"
        partes = [p for p in original.partes if p.nome != "motivo"]
        novo = original.model_copy(
            update={
                "nome": nome,
                "tentativa": 1,
                "partes": [*partes, ParteDoPedido(nome="motivo", texto=motivo)],
                "criado_em": servicos.relogio(),
            }
        )
        caminho = f"{PEDIDOS}/{nome}.json"
        arquivos.gravar_json(caminho, novo)
        return caminho

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        return _receber(peca, resposta, servicos, self.nome)


# ---------------------------------------------------------------------------
# Comandos `ensaio` e `fichas`
# ---------------------------------------------------------------------------


def _rodadas(arquivos: Arquivos) -> list[Rodada]:
    if not arquivos.existe(RODADAS):
        return []
    return arquivos.ler_json(RODADAS, Rodadas).rodadas


def _seguinte(rodadas: list[Rodada], letra: str) -> str:
    numeros = [int(r.id[1:]) for r in rodadas if r.id.startswith(letra)]
    return f"{letra}{max(numeros, default=0) + 1:02d}"


def _sorteada() -> int:
    return random.SystemRandom().randrange(1, 10**9)


def abrir_ensaio(servicos: Servicos, semente: int | None) -> tuple[str, list[str]]:
    """Abre a rodada eNN seguinte e grava uma base e um pedido por tipo."""
    arquivos = servicos.arquivos
    ctx = carregar_contexto(arquivos, servicos.config)
    semente = semente if semente is not None else _sorteada()
    combinacoes = []
    for tipo, m in ctx.matrizes.items():
        sorteio = matriz.combinacao_do_ensaio(m, ctx.travas, semente, ctx.config.matriz)
        if sorteio.situacao != "ok":
            raise ErroFichas(f"{tipo}: a matriz {matriz.VOLTA}")
        combinacoes.append(sorteio.combinacoes[0])
    identificador = _seguinte(_rodadas(arquivos), "e")
    Congelamento(arquivos, servicos.registro, servicos.relogio).abrir_rodada(
        identificador, semente, None
    )
    pecas = []
    for comb in combinacoes:
        base = gerar_base(ctx, identificador, semente, comb, 1, 1, 1)
        gravar(servicos, ctx, base)
        pecas.append(base.peca)
    return identificador, pecas


def abrir_fichas(servicos: Servicos, tipo: str, semente: int | None) -> tuple[str, list[str]]:
    """Sorteia as combinações do tipo e grava as bases e os pedidos de ficha."""
    arquivos = servicos.arquivos
    ctx = carregar_contexto(arquivos, servicos.config)
    if tipo not in ctx.matrizes:
        raise ErroFichas(f"tipo desconhecido: {tipo} (use {', '.join(ctx.matrizes)})")
    rodadas = _rodadas(arquivos)
    aprovados = [r for r in rodadas if r.id.startswith("e") and r.ensaio_aprovado]
    if not aprovados:
        raise ErroFichas(f"não há ensaio aprovado em {RODADAS}: a rodada do MVP não começa")
    ensaio = aprovados[-1]
    congelamento = Congelamento(arquivos, servicos.registro, servicos.relogio)
    mudaram = diferencas(ensaio.impressoes, congelamento.impressoes())
    if mudaram:
        raise ErroFichas(
            f"os arquivos congelados diferem dos do ensaio aprovado {ensaio.id}: "
            + ", ".join(mudaram)
        )
    abertas = [r for r in rodadas if r.id.startswith("r") and r.estado == "aberta"]
    if abertas:
        rodada = abertas[-1]
        mudaram = congelamento.comparar(rodada, ensaio)
        if mudaram:
            raise ErroFichas(
                f"a rodada {rodada.id} difere do ensaio {ensaio.id}: {', '.join(mudaram)}"
            )
    else:
        semente = semente if semente is not None else _sorteada()
        rodada = congelamento.abrir_rodada(_seguinte(rodadas, "r"), semente, ensaio.id)
    if arquivos.listar(PASTA, f"{rodada.id}_{tipo}_*_base.json"):
        raise ErroFichas(f"as fichas de {tipo} já foram gravadas na rodada {rodada.id}")
    sorteio = matriz.sortear(ctx.matrizes[tipo], ctx.travas, rodada.semente, ctx.config.matriz)
    if sorteio.situacao != "ok":
        raise ErroFichas(f"{tipo}: a matriz {matriz.VOLTA}")
    pecas = []
    for i, comb in enumerate(sorteio.combinacoes, start=1):
        base = gerar_base(ctx, rodada.id, rodada.semente, comb, i, i, 1)
        gravar(servicos, ctx, base)
        pecas.append(base.peca)
    return rodada.id, pecas
