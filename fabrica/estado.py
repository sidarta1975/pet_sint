"""Condutor das peças (ARQUITETURA §5.3; registro de decisão 002).

Descobre pelos arquivos de `saida/` o ponto de cada peça, a cada `avancar`, e a
leva ao próximo passo pela interface fixa das etapas. Não importa nenhum módulo
de etapa: recebe a lista de etapas e os serviços por parâmetro. Não guarda
estado próprio fora dos arquivos.

Só aqui ficam a regra do modelo local indisponível (§5.12.4) e o destino das
respostas fora do formato (§5.12.8).

Arquivos do próprio condutor, em `saida/conducao/`:
- `<peça>_v<k>_<etapa>_t<n>.txt`: o caminho do pedido que a etapa gravou;
- `<peça>_v<k>_destino.txt`: o destino da versão quando ela sai do caminho normal.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Literal, Protocol

from fabrica.comum.api_claude import ApiClaude
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.config import Config
from fabrica.comum.congelamento import Congelamento
from fabrica.comum.formatos import (
    CatalogoTipos,
    Conferencia,
    Ocorrencia,
    Pedido,
    Resposta,
    RespostaLocal,
)
from fabrica.comum.gasto import ControleGasto
from fabrica.comum.modelo_local import ModeloLocal, Resultado
from fabrica.comum.registro import Registro

FORA_DO_FORMATO = "fora do formato"
CONDUCAO = "saida/conducao"
CONFERENCIAS = "saida/conferencias"
PEDIDOS = "saida/pedidos"
RESPOSTAS = "saida/respostas"
CATALOGO = "dados/catalogo/tipos.json"
TENTATIVA_MAXIMA = 2
TAREFAS_DE_REDACAO = frozenset({"redacao_risco_baixo", "redacao_risco_medio", "redacao_risco_alto"})
TAREFAS_DE_CONFERENCIA = frozenset({"extracao", "checklist", "conferencia_opus"})
TAREFAS_DO_BANCO = frozenset({"copia_com_erro", "verificacao_copia"})

# Destinos gravados em <peça>_v<k>_destino.txt
DESCARTADA = "descartada"
FICHA_FALHOU = "ficha_falhou"
FICHA_NOVA_NA_CASA = "ficha_nova_na_casa"
VERSAO_PERDIDA = "versao_perdida_formato"
REPROVADA_FORMATO = "reprovada_formato"
COPIA_NAO_PEGA = "copia_nao_pega"
BANCO_DESCARTE = "banco_descarte"

# Causas das ocorrências gravadas pelo condutor
QUEDA_LOCAL = "modelo_local"
SUBSTITUICAO_OPUS = "substituicao_opus"
PAUSA_7_DIAS = "modelo_local_7_dias"
NAO_CABE = "nao_cabe"
ACIMA_DO_LIMITE = "acima_do_limite_do_ensaio"

Acao = Literal[
    "pedir",
    "coletar",
    "esperar_local",
    "descartar",
    "aprovada",
    "descartada",
    "encerrada",
    "concluida",
    "refazer_em_teste",
]
FINAIS = frozenset({"aprovada", "descartada", "encerrada", "concluida", "refazer_em_teste"})
Passo = Literal["seguir", "esperar", "pausa", "corte"]


class ErroEstado(Exception):
    """Etapa que não cumpre a interface ou peça impossível de conduzir."""


class ErroServicos(Exception):
    """Serviço que falta para o passo (por exemplo, a chave da API)."""


@dataclass(frozen=True, order=True)
class RefPeca:
    """Referência de uma peça (registro de decisão 002, item 1)."""

    rodada: str
    tipo: str
    numero: int
    versao: int = 1
    copia: str | None = None

    @property
    def id(self) -> str:
        return self.copia or f"{self.rodada}_{self.tipo}_{self.numero:03d}"

    @property
    def nome_versao(self) -> str:
        return f"{self.id}_v{self.versao}"

    def com_versao(self, versao: int) -> RefPeca:
        return replace(self, versao=versao)


@dataclass(frozen=True)
class Servicos:
    """Os serviços entregues a toda etapa (registro de decisão 002, item 2)."""

    api_claude: ApiClaude | None
    modelo_local: ModeloLocal
    arquivos: Arquivos
    config: Config
    registro: Registro
    gasto: ControleGasto
    relogio: Callable[[], datetime.datetime]
    modo_teste: bool


class Etapa(Protocol):
    """Interface fixa das etapas (registro de decisão 002, item 3)."""

    nome: str

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool: ...

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None: ...

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None: ...

    def arquivo_resultado(self, peca: RefPeca) -> str: ...


@dataclass(frozen=True)
class Ponto:
    peca: RefPeca
    etapa: str | None
    acao: Acao
    pedido: str | None = None
    destino: str | None = None


@dataclass
class ResumoAvanco:
    passos: int = 0
    parada: str | None = None
    alerta_de_gasto: bool = False
    esperando: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Arquivos do condutor
# ---------------------------------------------------------------------------


def _marcador(ref: RefPeca, etapa: str, tentativa: int) -> str:
    return f"{CONDUCAO}/{ref.nome_versao}_{etapa}_t{tentativa}.txt"


def registrar_pedido(ref: RefPeca, etapa: str, caminho: str, arquivos: Arquivos) -> None:
    """Liga o pedido gravado à etapa da peça. Também para quem grava o pedido fora do
    condutor (o comando `fichas`, brief 015)."""
    pedido = arquivos.ler_json(caminho, Pedido)
    arquivos.gravar_texto(_marcador(ref, etapa, pedido.tentativa), caminho)


def _pedido_da_etapa(ref: RefPeca, etapa: str, arquivos: Arquivos) -> str | None:
    for tentativa in range(TENTATIVA_MAXIMA, 0, -1):
        marcador = _marcador(ref, etapa, tentativa)
        if arquivos.existe(marcador):
            return arquivos.ler_texto(marcador).strip()
    return None


def destino(ref: RefPeca, arquivos: Arquivos) -> str | None:
    caminho = f"{CONDUCAO}/{ref.nome_versao}_destino.txt"
    return arquivos.ler_texto(caminho).strip() if arquivos.existe(caminho) else None


def _gravar_destino(ref: RefPeca, valor: str, arquivos: Arquivos) -> None:
    arquivos.gravar_texto(f"{CONDUCAO}/{ref.nome_versao}_destino.txt", valor + "\n")


def veredito(ref: RefPeca, arquivos: Arquivos) -> Conferencia | None:
    caminho = f"{CONFERENCIAS}/{ref.nome_versao}.json"
    return arquivos.ler_json(caminho, Conferencia) if arquivos.existe(caminho) else None


def motivo_da_refacao(ref: RefPeca, arquivos: Arquivos) -> str | None:
    """O motivo da última versão reprovada antes desta (para a redação da refação)."""
    for anterior in range(ref.versao - 1, 0, -1):
        conferencia = veredito(ref.com_versao(anterior), arquivos)
        if conferencia is not None:
            return conferencia.motivo
    return None


def descobrir_pecas(arquivos: Arquivos) -> list[RefPeca]:
    """As peças são as que têm pedido de ficha (gravado pelo comando `fichas`)."""
    pecas = set()
    for caminho in arquivos.listar(PEDIDOS, "*_ficha_t1.json"):
        pedido = arquivos.ler_json(caminho, Pedido)
        prefixo = f"{pedido.rodada}_"
        if not pedido.peca.startswith(prefixo):
            raise ErroEstado(f"{caminho}: peça {pedido.peca} fora da rodada {pedido.rodada}")
        tipo, _, numero = pedido.peca[len(prefixo) :].rpartition("_")
        pecas.add(RefPeca(rodada=pedido.rodada, tipo=tipo, numero=int(numero)))
    return sorted(pecas)


def classe_risco(tipo: str, arquivos: Arquivos) -> str:
    catalogo = arquivos.ler_json(CATALOGO, CatalogoTipos)
    for item in catalogo.tipos:
        if item.nome_curto == tipo:
            return item.classe_risco
    raise ErroEstado(f"tipo {tipo} fora do catálogo {CATALOGO}")


# ---------------------------------------------------------------------------
# Ponto de cada peça
# ---------------------------------------------------------------------------


def _quedas(
    ref: RefPeca, etapa: str, servicos: Servicos, causa: str = QUEDA_LOCAL
) -> list[Ocorrencia]:
    return [
        ocorrencia
        for ocorrencia in servicos.registro.ocorrencias()
        if ocorrencia.causa == causa
        and ocorrencia.peca == ref.nome_versao
        and ocorrencia.detalhe.startswith(f"{etapa}:")
    ]


def ponto(peca: RefPeca, etapas: Sequence[Etapa], servicos: Servicos) -> Ponto:
    arquivos = servicos.arquivos
    maxima = servicos.config.geral.volume.versoes_maximas
    versao = 1
    while True:
        ref = peca.com_versao(versao)
        marcado = destino(ref, arquivos)
        if marcado == VERSAO_PERDIDA and versao < maxima:
            versao += 1
            continue
        if marcado is not None:
            return Ponto(ref, None, "encerrada", destino=marcado)
        for etapa in etapas:
            if not etapa.aplica(ref, servicos):
                continue
            if arquivos.existe(etapa.arquivo_resultado(ref)):
                continue
            caminho = _pedido_da_etapa(ref, etapa.nome, arquivos)
            if caminho is None:
                return Ponto(ref, etapa.nome, "pedir")
            pedido = arquivos.ler_json(caminho, Pedido)
            if pedido.servico == "local" and _quedas(ref, etapa.nome, servicos):
                return Ponto(ref, etapa.nome, "esperar_local", pedido=caminho)
            return Ponto(ref, etapa.nome, "coletar", pedido=caminho)
        conferencia = veredito(ref, arquivos)
        if conferencia is None:
            return Ponto(ref, None, "concluida")
        if conferencia.veredito == "aprovada":
            return Ponto(ref, None, "aprovada")
        if conferencia.veredito == "descartada":
            return Ponto(ref, None, "descartada")
        if servicos.modo_teste:
            return Ponto(ref, None, "refazer_em_teste")
        if versao >= maxima:
            return Ponto(ref, None, "descartar")
        versao += 1


# ---------------------------------------------------------------------------
# Passos
# ---------------------------------------------------------------------------


def _ocorrencia(
    servicos: Servicos,
    ref: RefPeca,
    tipo: Literal["pausa", "parada", "intervencao", "contexto"],
    causa: str,
    detalhe: str,
    inicio: datetime.datetime | None = None,
    fim: datetime.datetime | None = None,
) -> None:
    servicos.registro.ocorrencia(
        Ocorrencia(
            tipo=tipo,
            causa=causa,
            inicio=inicio or servicos.relogio(),
            fim=fim,
            peca=ref.nome_versao,
            rodada=ref.rodada,
            detalhe=detalhe,
        )
    )


def _gravar_t2(caminho: str, servicos: Servicos) -> str:
    """O pedido `t2`, idêntico ao `t1`. Não existe `t3`."""
    pedido = servicos.arquivos.ler_json(caminho, Pedido)
    # O nome do t2 sai do nome do t1 (brief 015: `<peça>_ficha_retorno_t1` vira `_t2`).
    if not pedido.nome.endswith("_t1"):
        raise ErroEstado(f"{pedido.nome}: o t2 sai só de um pedido t1")
    nome = f"{pedido.nome.removesuffix('_t1')}_t{TENTATIVA_MAXIMA}"
    novo = pedido.model_copy(
        update={"nome": nome, "tentativa": TENTATIVA_MAXIMA, "criado_em": servicos.relogio()}
    )
    destino_t2 = f"{PEDIDOS}/{nome}.json"
    servicos.arquivos.gravar_json(destino_t2, novo)
    return destino_t2


def _receber(etapa: Etapa, ref: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
    devolvido = etapa.receber(ref, resposta, servicos)
    if devolvido not in (None, FORA_DO_FORMATO):
        raise ErroEstado(f"etapa {etapa.nome} devolveu {devolvido!r}")
    return devolvido


def _destino_do_formato(ref: RefPeca, pedido: Pedido, servicos: Servicos) -> str:
    """ARQUITETURA §5.12.8: a segunda resposta também saiu fora do formato."""
    maxima = servicos.config.geral.volume.versoes_maximas
    if pedido.tarefa in TAREFAS_DO_BANCO:
        return BANCO_DESCARTE
    if ref.copia is not None:
        return COPIA_NAO_PEGA
    if pedido.tarefa == "ficha":
        return FICHA_FALHOU
    if pedido.tarefa in TAREFAS_DE_REDACAO:
        if ref.versao == 1:
            return FICHA_NOVA_NA_CASA
        return VERSAO_PERDIDA if ref.versao < maxima else DESCARTADA
    if pedido.tarefa in TAREFAS_DE_CONFERENCIA:
        return REPROVADA_FORMATO
    raise ErroEstado(f"{pedido.nome}: tarefa sem destino de formato ({pedido.tarefa})")


def _fora_do_formato(
    ref: RefPeca, etapa: Etapa, pedido: Pedido, caminho: str, servicos: Servicos
) -> Passo:
    if pedido.tentativa < TENTATIVA_MAXIMA:
        registrar_pedido(ref, etapa.nome, _gravar_t2(caminho, servicos), servicos.arquivos)
        return "seguir"
    _gravar_destino(ref, _destino_do_formato(ref, pedido, servicos), servicos.arquivos)
    return "seguir"


def _coletar(ref: RefPeca, etapa: Etapa, caminho: str, servicos: Servicos) -> Passo:
    pedido = servicos.arquivos.ler_json(caminho, Pedido)
    if pedido.servico == "local":
        return _coletar_local(ref, etapa, pedido, caminho, servicos)
    api = servicos.api_claude
    if api is None:
        raise ErroServicos(
            "a variável de ambiente ANTHROPIC_API_KEY não está definida: "
            "o passo precisa da API da Claude. Defina a variável e rode de novo."
        )
    situacao = api.coletar(caminho)
    if situacao in ("pausa", "corte"):
        return situacao  # type: ignore[return-value]
    if situacao == "ok":
        resposta = servicos.arquivos.ler_json(f"{RESPOSTAS}/{pedido.nome}.json", Resposta)
        if _receber(etapa, ref, resposta, servicos) is None:
            return "seguir"
    return _fora_do_formato(ref, etapa, pedido, caminho, servicos)


def dentro_da_janela(agora: datetime.datetime, servicos: Servicos) -> bool:
    """A janela é lida do config.toml a cada avancar, no horário local da máquina."""
    janela = servicos.config.geral.janela_local
    hora = agora.astimezone().time().replace(tzinfo=None)
    if janela.inicio <= janela.fim:
        return janela.inicio <= hora < janela.fim
    return hora >= janela.inicio or hora < janela.fim


def _uma_vez(servicos: Servicos, ref: RefPeca, causa: str, pedido: Pedido) -> None:
    ja = any(
        o.tipo == "contexto" and o.causa == causa and pedido.nome in o.detalhe
        for o in servicos.registro.ocorrencias()
    )
    if not ja:
        _ocorrencia(servicos, ref, "contexto", causa, f"{pedido.nome}")


def _coletar_local(
    ref: RefPeca, etapa: Etapa, pedido: Pedido, caminho: str, servicos: Servicos
) -> Passo:
    local = servicos.config.geral.modelo_local
    texto = "\n\n".join(parte.texto for parte in pedido.partes)
    estimativa = servicos.modelo_local.estimar_tokens(texto, pedido.teto_saida)
    fracao = estimativa / local.num_ctx
    nao_cabe = Resultado("indisponivel", "contexto", None, None, fracao, 0.0, None)
    if estimativa > local.num_ctx:
        # Esperar não resolve: não espera a janela, em nenhuma classe.
        _uma_vez(servicos, ref, NAO_CABE, pedido)
        _receber(etapa, ref, nao_cabe, servicos)
        return "seguir"
    if ref.rodada.startswith("e") and fracao > local.fracao_limite_contexto_ensaio:
        _uma_vez(servicos, ref, ACIMA_DO_LIMITE, pedido)
    agora = servicos.relogio()
    gravada = f"{RESPOSTAS}/{pedido.nome}.json"
    if servicos.arquivos.existe(gravada):
        resposta = servicos.arquivos.ler_json(gravada, Resposta)
        resultado = Resultado("rodou", None, resposta.situacao, None, fracao, 0.0, gravada)
        if resposta.situacao == "ok":
            resultado = replace(resultado, respostas=_ler_respostas_locais(resposta))
    elif not dentro_da_janela(agora, servicos):
        resultado = Resultado("indisponivel", "janela", None, None, fracao, 0.0, None)
    else:
        resultado = servicos.modelo_local.conferir(pedido)
    if resultado.resultado != "indisponivel":
        if resultado.situacao == "ok" and _receber(etapa, ref, resultado, servicos) is None:
            return "seguir"
        if pedido.tentativa < TENTATIVA_MAXIMA:
            registrar_pedido(ref, etapa.nome, _gravar_t2(caminho, servicos), servicos.arquivos)
            return "seguir"
        # Segunda falha do conferente local: não é formato, é modelo local indisponível.
        resultado = replace(resultado, resultado="indisponivel", causa="falha", respostas=None)
    if resultado.causa == "contexto":
        _uma_vez(servicos, ref, NAO_CABE, pedido)
        _receber(etapa, ref, resultado, servicos)
        return "seguir"
    return _valvula(ref, etapa, resultado, servicos)


def _ler_respostas_locais(resposta: Resposta) -> RespostaLocal:
    return RespostaLocal.model_validate_json(resposta.conteudo)


def _valvula(ref: RefPeca, etapa: Etapa, resultado: Resultado, servicos: Servicos) -> Passo:
    """ARQUITETURA §5.12.4: o destino da peça quando o modelo local está indisponível."""
    valvula = servicos.config.geral.valvula
    agora = servicos.relogio()
    _ocorrencia(servicos, ref, "pausa", QUEDA_LOCAL, f"{etapa.nome}: {resultado.causa}", agora)
    primeira = min(o.inicio for o in _quedas(ref, etapa.nome, servicos))
    esperou = agora - primeira
    classe = classe_risco(ref.tipo, servicos.arquivos)
    if classe == "baixo":
        _receber(etapa, ref, resultado, servicos)
        return "seguir"
    if classe == "medio":
        if esperou > datetime.timedelta(hours=valvula.espera_risco_medio_horas):
            _ocorrencia(
                servicos,
                ref,
                "pausa",
                SUBSTITUICAO_OPUS,
                f"{etapa.nome}: o Opus responde os itens do conferente local",
                inicio=primeira,
                fim=agora,
            )
            _receber(etapa, ref, resultado, servicos)
            return "seguir"
        return "esperar"
    if esperou > datetime.timedelta(days=valvula.espera_risco_alto_dias) and not _quedas(
        ref, etapa.nome, servicos, PAUSA_7_DIAS
    ):
        _ocorrencia(
            servicos,
            ref,
            "pausa",
            PAUSA_7_DIAS,
            f"{etapa.nome}: mais de {valvula.espera_risco_alto_dias} dias sem o modelo local",
            inicio=primeira,
        )
    return "esperar"


def _executar(passo: Ponto, etapas: Sequence[Etapa], servicos: Servicos) -> Passo:
    ref = passo.peca
    if passo.acao == "descartar":
        _gravar_destino(ref, DESCARTADA, servicos.arquivos)
        return "seguir"
    etapa = next(e for e in etapas if e.nome == passo.etapa)
    caminho = passo.pedido
    if passo.acao == "pedir":
        caminho = etapa.pedir(ref, servicos)
        if caminho is None:
            if not servicos.arquivos.existe(etapa.arquivo_resultado(ref)):
                raise ErroEstado(f"etapa {etapa.nome} não gravou pedido nem resultado")
            return "seguir"
        registrar_pedido(ref, etapa.nome, caminho, servicos.arquivos)
    assert caminho is not None
    return _coletar(ref, etapa, caminho, servicos)


def avancar(
    etapas: Sequence[Etapa], servicos: Servicos, pecas: Sequence[RefPeca] | None = None
) -> ResumoAvanco:
    """Leva cada peça ao próximo passo possível. Pode ser repetido a qualquer momento."""
    resumo = ResumoAvanco()
    congelamento = Congelamento(servicos.arquivos, servicos.registro, servicos.relogio)
    lista = list(pecas) if pecas is not None else descobrir_pecas(servicos.arquivos)
    for peca in lista:
        while True:
            atual = ponto(peca, etapas, servicos)
            if atual.acao in FINAIS:
                break
            conferido = congelamento.conferir(peca.rodada, peca=atual.peca.nome_versao)
            if conferido.parar:
                resumo.parada = "congelamento"
                return resumo
            resultado = _executar(atual, etapas, servicos)
            resumo.passos += 1
            if resultado == "corte":
                resumo.parada = "corte"
                return resumo
            if resultado in ("esperar", "pausa"):
                resumo.esperando.append(atual.peca.nome_versao)
                break
    resumo.alerta_de_gasto = servicos.gasto.total_gasto() > servicos.gasto.alerta_milionesimos
    return resumo
