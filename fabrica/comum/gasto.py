"""Controle de gasto: previsão pessimista, alerta e corte (ARQUITETURA §5.12.5 e §7.4).

Custos em milionésimos de centavo de dólar, sempre inteiros: um token a um preço
de P centavos por milhão custa exatamente P milionésimos de centavo.
Não abre arquivo: recebe a configuração, o registro e os pedidos pendentes.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from fabrica.comum.config import Config
from fabrica.comum.formatos import (
    Chamada,
    ConfigTarefa,
    Ocorrencia,
    PrecoModelo,
    PrecoModeloComFaixa,
    Tokens,
)
from fabrica.comum.registro import Registro

MILIONESIMOS_POR_CENTAVO = 1_000_000

# Tarefas que entram no custo marginal por peça aprovada (ARQUITETURA §6):
# ficha, redação, refações e conferência. Fora: cópias com erro e verificação.
TAREFAS_DO_CUSTO_MARGINAL = frozenset(
    {
        "ficha",
        "redacao_risco_baixo",
        "redacao_risco_medio",
        "redacao_risco_alto",
        "extracao",
        "checklist",
        "conferencia_opus",
    }
)
MARCA_COPIA_COM_ERRO = "_erro"
PREFIXO_RODADA = "r"


class ErroGasto(Exception):
    """Modelo sem preço na configuração ou conta impossível."""


@dataclass(frozen=True)
class Previsto:
    """Pedido enviado e não coletado, ou pedido novo, para a previsão pessimista."""

    modelo: str
    tokens_entrada: int
    teto_saida: int


@dataclass(frozen=True)
class Decisao:
    autorizado: bool
    alerta: bool
    total_previsto: int


def _agora() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC)


class ControleGasto:
    def __init__(
        self,
        config: Config,
        registro: Registro,
        relogio: Callable[[], datetime.datetime] = _agora,
    ) -> None:
        self._config = config
        self._registro = registro
        self._relogio = relogio
        self._corte = config.gasto.corte_centavos * MILIONESIMOS_POR_CENTAVO
        self._alerta = config.gasto.alerta_centavos * MILIONESIMOS_POR_CENTAVO
        self._alertou = self.total_gasto() > self._alerta

    @property
    def corte_milionesimos(self) -> int:
        """O corte vem do gasto.toml e não sobe por nenhum caminho do programa."""
        return self._corte

    @property
    def alerta_milionesimos(self) -> int:
        return self._alerta

    # --- preços -------------------------------------------------------------

    def _preco(self, modelo: str) -> PrecoModelo:
        modelos = self._config.geral.modelos
        for preco in (modelos.opus, modelos.sonnet, modelos.haiku):
            if preco.id == modelo:
                return preco
        raise ErroGasto(f"modelo sem preço no config.toml: {modelo}")

    def _precos(self, modelo: str, tokens_entrada: int) -> tuple[int, int]:
        preco = self._preco(modelo)
        if (
            isinstance(preco, PrecoModeloComFaixa)
            and tokens_entrada > preco.limite_entrada_tokens_do_preco
        ):
            return (
                preco.preco_entrada_acima_do_limite_centavos_por_milhao,
                preco.preco_saida_acima_do_limite_centavos_por_milhao,
            )
        return preco.preco_entrada_centavos_por_milhao, preco.preco_saida_centavos_por_milhao

    def tarefa(self, nome: str) -> ConfigTarefa:
        tarefa: ConfigTarefa | None = getattr(self._config.geral.tarefas, nome, None)
        if tarefa is None:
            raise ErroGasto(f"tarefa sem configuração: {nome}")
        return tarefa

    def modelo_da_tarefa(self, nome: str) -> str:
        apelido = self.tarefa(nome).modelo
        preco: PrecoModelo = getattr(self._config.geral.modelos, apelido)
        return preco.id

    # --- custos -------------------------------------------------------------

    def previsto(self, tarefa: str, tokens_entrada: int) -> Previsto:
        """O pedido novo: tokens de entrada contados e o teto de saída da tarefa."""
        return Previsto(
            modelo=self.modelo_da_tarefa(tarefa),
            tokens_entrada=tokens_entrada,
            teto_saida=self.tarefa(tarefa).teto_saida_tokens,
        )

    def custo_previsto(self, previsto: Previsto) -> int:
        entrada, saida = self._precos(previsto.modelo, previsto.tokens_entrada)
        return previsto.tokens_entrada * entrada + previsto.teto_saida * saida

    def custo_real(self, modelo: str, tokens: Tokens) -> int:
        """Custo de uma resposta pelos tokens. O raciocínio já vem dentro da saída."""
        tokens_entrada = tokens.entrada + tokens.cache
        entrada, saida = self._precos(modelo, tokens_entrada)
        return tokens_entrada * entrada + tokens.saida * saida

    def total_gasto(self) -> int:
        return self._registro.custo_total_milionesimos()

    def previsao_pessimista(self, novo: Previsto, pendentes: Sequence[Previsto]) -> int:
        return (
            self.total_gasto()
            + sum(self.custo_previsto(pendente) for pendente in pendentes)
            + self.custo_previsto(novo)
        )

    # --- decisão ------------------------------------------------------------

    def autorizar(
        self,
        novo: Previsto,
        pendentes: Sequence[Previsto],
        rodada: str | None,
        peca: str | None,
    ) -> Decisao:
        total = self.previsao_pessimista(novo, pendentes)
        if total > self._corte:
            momento = self._relogio()
            self._registro.ocorrencia(
                Ocorrencia(
                    tipo="parada",
                    causa="corte_de_gasto",
                    inicio=momento,
                    fim=None,
                    peca=peca,
                    rodada=rodada,
                    detalhe=(
                        f"previsão pessimista de {total} milionésimos de centavo passaria "
                        f"do corte de {self._corte}"
                    ),
                )
            )
            return Decisao(autorizado=False, alerta=False, total_previsto=total)
        alerta = False
        if not self._alertou and total > self._alerta:
            self._alertou = True
            alerta = True
        return Decisao(autorizado=True, alerta=alerta, total_previsto=total)

    # --- relatório ----------------------------------------------------------

    def custo_marginal(self, rodada: str, pecas_aprovadas: int) -> int:
        """Custo por peça aprovada na rodada válida, sem ensaio, cópias com erro e teste."""
        if pecas_aprovadas <= 0:
            raise ErroGasto("custo marginal sem peça aprovada")
        if not rodada.startswith(PREFIXO_RODADA):
            raise ErroGasto(f"custo marginal só se calcula numa rodada, não em {rodada}")
        total = sum(
            chamada.custo_milionesimos
            for chamada in self._registro.chamadas()
            if _entra_no_marginal(chamada, rodada)
        )
        return total // pecas_aprovadas


def _entra_no_marginal(chamada: Chamada, rodada: str) -> bool:
    return (
        chamada.rodada == rodada
        and chamada.tarefa in TAREFAS_DO_CUSTO_MARGINAL
        and MARCA_COPIA_COM_ERRO not in chamada.peca
    )
