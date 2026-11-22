"""Teste de aceite do brief 008: `fabrica/estado.py` e a montagem em `__main__.py`.

Clientes falsos (API e modelo local), etapas falsas (nenhum módulo de etapa existe
ainda), relógio falso e pasta temporária com repositório git próprio.
"""

from __future__ import annotations

import datetime
import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import anthropic
import httpx2
import pytest

from fabrica import __main__ as principal
from fabrica import estado
from fabrica.comum import config
from fabrica.comum.api_claude import ApiClaude
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.congelamento import Congelamento
from fabrica.comum.formatos import (
    CatalogoTipos,
    Conferencia,
    ParteDoPedido,
    Pedido,
    RespostaLocal,
    esquema_resposta,
)
from fabrica.comum.gasto import ControleGasto
from fabrica.comum.modelo_local import ModeloLocal
from fabrica.comum.registro import Registro
from fabrica.estado import FORA_DO_FORMATO, RefPeca, Servicos

RAIZ = Path(__file__).resolve().parent.parent
# Horário local da máquina: 23h, dentro da janela provisória (22h às 6h).
INICIO = datetime.datetime(2026, 11, 21, 23, 0).astimezone()
HORA = datetime.timedelta(hours=1)
REQUISICAO = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")
RESPOSTA_LOCAL = json.dumps({"itens": [{"item": "coerencia", "resposta": "passa", "trecho": "t"}]})

TIPOS = {
    "tipos": [
        {
            "rotulo": "Petição Inicial em Juizado Especial Cível",
            "nome_curto": "peticao_inicial_jec",
            "familia": "peticao_inicial",
            "perfil": "juizado_especial_civel",
            "classe_risco": "medio",
            "tarefa_redacao": "redacao_risco_medio",
            "quantidade": 10,
            "depende_peca_anterior": False,
            "itens_conferencia": ["cabimento"],
        },
        {
            "rotulo": "Embargos de Declaração",
            "nome_curto": "embargos_declaracao",
            "familia": "embargos",
            "perfil": "procedimento_comum",
            "classe_risco": "alto",
            "tarefa_redacao": "redacao_risco_alto",
            "quantidade": 10,
            "depende_peca_anterior": True,
            "itens_conferencia": ["cabimento"],
        },
        {
            "rotulo": "Manifestação sobre Aviso de Recebimento Negativo",
            "nome_curto": "manifestacao_ar_negativo",
            "familia": "manifestacao",
            "perfil": "procedimento_comum",
            "classe_risco": "baixo",
            "tarefa_redacao": "redacao_risco_baixo",
            "quantidade": 10,
            "depende_peca_anterior": True,
            "itens_conferencia": ["cabimento"],
        },
    ]
}


# ---------------------------------------------------------------------------
# Falsos
# ---------------------------------------------------------------------------


def mensagem(texto: str = "ok", parada: str = "end_turn") -> anthropic.types.Message:
    return anthropic.types.Message.model_validate(
        {
            "id": "msg_falsa",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-5-5",
            "content": [{"type": "text", "text": texto}],
            "stop_reason": parada,
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )


def erro_rede() -> Exception:
    return anthropic.APIConnectionError(request=REQUISICAO)


class Mensagens:
    def __init__(self, cliente: ClienteFalso) -> None:
        self.cliente = cliente

    def create(self, **argumentos: Any) -> anthropic.types.Message:
        texto = argumentos["messages"][0]["content"][0]["text"]
        self.cliente.enviados.append(texto)
        for chave, fila in self.cliente.roteiro.items():
            if chave in texto and fila:
                resposta = fila.pop(0)
                if isinstance(resposta, Exception):
                    raise resposta
                return resposta
        return mensagem()

    def count_tokens(self, **argumentos: Any) -> anthropic.types.MessageTokensCount:
        return anthropic.types.MessageTokensCount(input_tokens=10)


class ClienteFalso:
    def __init__(self) -> None:
        self.roteiro: dict[str, list[Any]] = {}
        self.enviados: list[str] = []
        self.messages = Mensagens(self)


class Porteiro:
    def __init__(self) -> None:
        self.codigo = 0
        self.comandos: list[list[str]] = []

    def __call__(self, comando: Any) -> int:
        self.comandos.append(list(comando))
        return self.codigo


class Ollama:
    def __init__(self) -> None:
        self.pedidos: list[dict[str, Any]] = []
        self.respostas: list[dict[str, Any]] = []

    def __call__(self, url: str, corpo: dict[str, Any]) -> dict[str, Any]:
        self.pedidos.append(corpo)
        if self.respostas:
            return self.respostas.pop(0)
        return {"message": {"content": RESPOSTA_LOCAL}, "done_reason": "stop"}


class Relogio:
    def __init__(self) -> None:
        self.agora = INICIO

    def __call__(self) -> datetime.datetime:
        self.agora += datetime.timedelta(seconds=1)
        return self.agora

    def andar(self, delta: datetime.timedelta) -> None:
        self.agora += delta


# ---------------------------------------------------------------------------
# Etapas falsas, pela interface do registro de decisão 002
# ---------------------------------------------------------------------------


class EtapaFalsa:
    def __init__(
        self,
        nome: str,
        servico: str,
        tarefa: str = "",
        aplica: Callable[[RefPeca], bool] = lambda ref: True,
        texto: Callable[[RefPeca], str] | None = None,
    ) -> None:
        self.nome = nome
        self.servico = servico
        self.tarefa = tarefa
        self._aplica = aplica
        self._texto = texto
        self.recebidas: list[tuple[RefPeca, Any]] = []
        self.modos: list[bool] = []
        self.fora: set[str] = set()  # nome_versao que devolve fora do formato

    def aplica(self, peca: RefPeca, servicos: Servicos) -> bool:
        return self._aplica(peca)

    def arquivo_resultado(self, peca: RefPeca) -> str:
        if self.nome == "ficha":
            return f"saida/fichas/{peca.id}.txt"
        return f"saida/etapas/{peca.nome_versao}_{self.nome}.txt"

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        self.modos.append(servicos.modo_teste)
        texto = f"{self.nome} {peca.nome_versao}"
        if self._texto is not None:
            texto += self._texto(peca)
        if self.servico == "programa":
            servicos.arquivos.gravar_texto(self.arquivo_resultado(peca), "feito")
            return None
        if self.servico == "local":
            caminho = f"saida/pedidos/{peca.nome_versao}_conferente_local_t1.json"
            servicos.arquivos.gravar_json(
                caminho,
                Pedido(
                    nome=f"{peca.nome_versao}_conferente_local_t1",
                    servico="local",
                    rodada=peca.rodada,
                    peca=peca.id,
                    versao=peca.versao,
                    tarefa="conferente_local",
                    tentativa=1,
                    modelo="gemma3:27b",
                    esforco=None,
                    teto_saida=2000,
                    partes=[ParteDoPedido(nome="instrucoes", texto=texto)],
                    formato="RespostaLocal",
                    esquema=esquema_resposta(RespostaLocal),
                    criado_em=servicos.relogio(),
                ),
            )
            return caminho
        partes = {"instrucoes": texto}
        motivo = estado.motivo_da_refacao(peca, servicos.arquivos)
        if motivo is not None:
            partes["motivo"] = motivo
        assert servicos.api_claude is not None
        return servicos.api_claude.gravar_pedido(
            rodada=peca.rodada,
            peca=peca.id,
            versao=None if self.nome == "ficha" else peca.versao,
            tarefa=self.tarefa,
            partes=partes,
            modelo_resposta=None,
        )

    def receber(self, peca: RefPeca, resposta: Any, servicos: Servicos) -> str | None:
        self.recebidas.append((peca, resposta))
        if peca.nome_versao in self.fora:
            return FORA_DO_FORMATO
        servicos.arquivos.gravar_texto(self.arquivo_resultado(peca), "recebido")
        return None


class DecisaoFalsa(EtapaFalsa):
    """Grava o veredito final pelo plano: {nome_versao: veredito}."""

    def __init__(self) -> None:
        super().__init__("decisao", "programa")
        self.plano: dict[str, str] = {}

    def arquivo_resultado(self, peca: RefPeca) -> str:
        return f"saida/conferencias/{peca.nome_versao}.json"

    def pedir(self, peca: RefPeca, servicos: Servicos) -> str | None:
        self.modos.append(servicos.modo_teste)
        veredito = self.plano.get(peca.nome_versao, "aprovada")
        servicos.arquivos.gravar_json(self.arquivo_resultado(peca), conferencia(peca, veredito))
        return None


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
                    "comarca": "Campinas",
                    "juizo": "Juizado",
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


# ---------------------------------------------------------------------------
# Ambiente
# ---------------------------------------------------------------------------


def git(raiz: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=raiz, check=True, capture_output=True)


class Ambiente:
    def __init__(self, raiz: Path, rodada: str = "e01", modo_teste: bool = False) -> None:
        self.raiz = raiz
        self.rodada = rodada
        self.relogio = Relogio()
        self.cliente = ClienteFalso()
        self.porteiro = Porteiro()
        self.ollama = Ollama()
        arquivos = Arquivos(raiz, relogio=self.relogio)
        lida = config.carregar(arquivos)
        registro = Registro(arquivos)
        gasto = ControleGasto(lida, registro, relogio=self.relogio)
        self.servicos = Servicos(
            api_claude=ApiClaude(
                self.cliente,
                lida,
                arquivos,
                registro,
                gasto,
                relogio=self.relogio,
                dormir=lambda segundos: None,
            ),
            modelo_local=ModeloLocal(
                lida,
                arquivos,
                registro,
                executar=self.porteiro,
                enviar=self.ollama,
                relogio=self.relogio,
                dormir=lambda segundos: None,
            ),
            arquivos=arquivos,
            config=lida,
            registro=registro,
            gasto=gasto,
            relogio=self.relogio,
            modo_teste=modo_teste,
        )
        Congelamento(arquivos, registro, self.relogio).abrir_rodada(
            rodada, semente=7, ensaio_aprovado_origem=None
        )
        self.ficha = EtapaFalsa("ficha", "claude", "ficha")
        self.redacao = EtapaFalsa("redacao", "claude", "redacao_risco_medio")
        self.extracao = EtapaFalsa("extracao", "claude", "extracao")
        self.regras = EtapaFalsa("regras", "programa")
        self.local = EtapaFalsa("local", "local")
        self.checklist = EtapaFalsa("checklist", "claude", "checklist")
        self.desempate = EtapaFalsa("desempate", "claude", "conferencia_opus")
        self.decisao = DecisaoFalsa()
        self.etapas: list[Any] = [
            self.ficha,
            self.redacao,
            self.extracao,
            self.regras,
            self.local,
            self.checklist,
            self.desempate,
            self.decisao,
        ]

    @property
    def arquivos(self) -> Arquivos:
        return self.servicos.arquivos

    def peca(self, tipo: str = "peticao_inicial_jec", numero: int = 1) -> RefPeca:
        return RefPeca(rodada=self.rodada, tipo=tipo, numero=numero)

    def avancar(self, *pecas: RefPeca) -> estado.ResumoAvanco:
        return estado.avancar(self.etapas, self.servicos, list(pecas) or None)

    def ponto(self, peca: RefPeca) -> estado.Ponto:
        return estado.ponto(peca, self.etapas, self.servicos)

    def ocorrencias(self) -> list[tuple[str, str]]:
        return [(o.tipo, o.causa) for o in self.servicos.registro.ocorrencias()]

    def destino(self, ref: RefPeca) -> str | None:
        return estado.destino(ref, self.arquivos)


def preparar(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "teste@ficticio.example")
    git(tmp_path, "config", "user.name", "Teste")
    for pasta in ("config", "dados/catalogo", "instrucoes", "fabrica"):
        (tmp_path / pasta).mkdir(parents=True)
    shutil.copy(RAIZ / "config/gasto.toml", tmp_path / "config/gasto.toml")
    texto = (RAIZ / "config/config.toml").read_text(encoding="utf-8")
    texto = texto.replace('etiqueta_completa = ""', 'etiqueta_completa = "gemma3:27b"', 1)
    texto = texto.replace('digest = ""', 'digest = "sha256:abc"', 1)
    (tmp_path / "config/config.toml").write_text(texto, encoding="utf-8")
    (tmp_path / "dados/catalogo/tipos.json").write_text(json.dumps(TIPOS), encoding="utf-8")
    CatalogoTipos.model_validate_json(json.dumps(TIPOS))
    (tmp_path / "instrucoes/ficha.md").write_text("Instrução.\n")
    (tmp_path / "fabrica/__init__.py").write_text("")
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    (tmp_path / ".gitignore").write_text("saida/\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "x")
    return tmp_path


@pytest.fixture
def amb(tmp_path: Path) -> Ambiente:
    return Ambiente(preparar(tmp_path))


# 1 · ponto de cada peça ------------------------------------------------------


def test_peca_nova_pede_a_ficha(amb: Ambiente) -> None:
    ponto = amb.ponto(amb.peca())
    assert (ponto.acao, ponto.etapa) == ("pedir", "ficha")
    assert ponto.peca.versao == 1


def test_percorre_todas_as_etapas_ate_aprovada(amb: Ambiente) -> None:
    peca = amb.peca()
    resumo = amb.avancar(peca)
    assert resumo.parada is None
    assert amb.ponto(peca).acao == "aprovada"
    nomes = [texto.split()[0] for texto in amb.cliente.enviados]
    assert nomes == ["ficha", "redacao", "extracao", "checklist", "desempate"]
    assert len(amb.ollama.pedidos) == 1


def test_ponto_depois_da_ficha_e_de_cada_conferencia(amb: Ambiente) -> None:
    peca = amb.peca()
    v1 = peca.com_versao(1)
    amb.arquivos.gravar_texto(amb.ficha.arquivo_resultado(v1), "ficha pronta")
    assert (amb.ponto(peca).acao, amb.ponto(peca).etapa) == ("pedir", "redacao")
    amb.arquivos.gravar_texto(amb.redacao.arquivo_resultado(v1), "rascunho pronto")
    assert (amb.ponto(peca).acao, amb.ponto(peca).etapa) == ("pedir", "extracao")
    for etapa, seguinte in (
        (amb.extracao, "regras"),
        (amb.regras, "local"),
        (amb.local, "checklist"),
        (amb.checklist, "desempate"),
        (amb.desempate, "decisao"),
    ):
        amb.arquivos.gravar_texto(etapa.arquivo_resultado(v1), "feito")
        assert (amb.ponto(peca).acao, amb.ponto(peca).etapa) == ("pedir", seguinte)


def test_etapa_que_nao_se_aplica_e_pulada(amb: Ambiente) -> None:
    amb.local._aplica = lambda ref: ref.tipo != "manifestacao_ar_negativo"
    peca = amb.peca("manifestacao_ar_negativo")
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "aprovada"
    assert amb.ollama.pedidos == [] and amb.porteiro.comandos == []


def test_pedido_de_redacao_sem_resposta_e_coleta(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.cliente.roteiro["redacao"] = [erro_rede()] * 4
    amb.avancar(peca)
    ponto = amb.ponto(peca)
    assert (ponto.acao, ponto.etapa) == ("coletar", "redacao")
    assert ("pausa", "api") in amb.ocorrencias()


def test_esperando_modelo_local(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.porteiro.codigo = 2
    amb.avancar(peca)
    ponto = amb.ponto(peca)
    assert (ponto.acao, ponto.etapa) == ("esperar_local", "local")


def test_reprovada_com_refacao_pendente_e_descartada(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.decisao.plano = {"e01_peticao_inicial_jec_001_v1": "refazer"}
    amb.cliente.roteiro["redacao e01_peticao_inicial_jec_001_v2"] = [erro_rede()] * 4
    amb.avancar(peca)
    ponto = amb.ponto(peca)
    assert (ponto.acao, ponto.etapa, ponto.peca.versao) == ("coletar", "redacao", 2)
    amb.decisao.plano["e01_peticao_inicial_jec_001_v2"] = "descartada"
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "descartada"


# 2 · retomada -------------------------------------------------------------------


def test_peca_interrompida_e_retomada_sem_pedido_novo(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.cliente.roteiro["redacao"] = [erro_rede()] * 4
    amb.avancar(peca)
    pedidos = amb.arquivos.listar("saida/pedidos", "*redacao*")
    assert pedidos == ["saida/pedidos/e01_peticao_inicial_jec_001_v1_redacao_risco_medio_t1.json"]
    (amb.raiz / "saida/pedidos/e01_peticao_inicial_jec_001_v1_redacao_x.json.tmp-abc").write_text(
        "pela metade"
    )
    amb.avancar(peca)
    assert amb.arquivos.listar("saida/pedidos", "*redacao*") == pedidos
    assert amb.ponto(peca).acao == "aprovada"
    assert len(amb.redacao.modos) == 1  # o pedido não foi gravado de novo


# 3 · refação ----------------------------------------------------------------------


def test_refacao_gera_versao_seguinte_com_motivo(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.decisao.plano = {"e01_peticao_inicial_jec_001_v1": "refazer"}
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "aprovada"
    assert amb.ponto(peca).peca.versao == 2
    pedido = amb.arquivos.ler_json(
        "saida/pedidos/e01_peticao_inicial_jec_001_v2_redacao_risco_medio_t1.json", Pedido
    )
    motivos = [parte.texto for parte in pedido.partes if parte.nome == "motivo"]
    assert motivos == ["motivo da e01_peticao_inicial_jec_001_v1"]
    fichas = [texto for texto in amb.cliente.enviados if texto.startswith("ficha")]
    assert len(fichas) == 1  # a ficha não se refaz


def test_reprovada_na_terceira_versao_e_descartada_sem_quarta(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.decisao.plano = {f"e01_peticao_inicial_jec_001_v{k}": "refazer" for k in (1, 2, 3)}
    amb.avancar(peca)
    ponto = amb.ponto(peca)
    assert ponto.acao == "encerrada"
    assert ponto.peca.versao == 3
    assert amb.destino(peca.com_versao(3)) == "descartada"
    assert not amb.arquivos.listar("saida/pedidos", "*_v4_*")


# 4 · fora do formato -----------------------------------------------------------------


def cortada() -> anthropic.types.Message:
    return mensagem("{", parada="max_tokens")


def test_fora_do_formato_gera_t2(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.cliente.roteiro["extracao"] = [cortada()]
    amb.avancar(peca)
    assert amb.arquivos.existe("saida/pedidos/e01_peticao_inicial_jec_001_v1_extracao_t2.json")
    assert amb.ponto(peca).acao == "aprovada"


def test_receber_fora_do_formato_tambem_gera_t2(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.checklist.fora = {"e01_peticao_inicial_jec_001_v1"}
    amb.avancar(peca)
    assert amb.arquivos.existe("saida/pedidos/e01_peticao_inicial_jec_001_v1_checklist_t2.json")
    assert amb.destino(peca.com_versao(1)) == "reprovada_formato"


@pytest.mark.parametrize(
    ("etapa", "versao", "esperado"),
    [
        ("ficha", 1, "ficha_falhou"),
        ("redacao", 1, "ficha_nova_na_casa"),
        ("extracao", 1, "reprovada_formato"),
        ("checklist", 1, "reprovada_formato"),
        ("desempate", 1, "reprovada_formato"),
    ],
)
def test_segunda_falha_segue_o_destino(
    amb: Ambiente, etapa: str, versao: int, esperado: str
) -> None:
    peca = amb.peca()
    amb.cliente.roteiro[etapa] = [cortada(), cortada()]
    amb.avancar(peca)
    ponto = amb.ponto(peca)
    assert ponto.acao == "encerrada"
    assert amb.destino(peca.com_versao(versao)) == esperado
    assert not amb.arquivos.listar("saida/pedidos", f"*{etapa}*_t3.json")
    assert not amb.arquivos.listar("saida/pedidos", "*_v2_*")


def test_segunda_falha_da_redacao_de_refacao_conta_como_versao(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.decisao.plano = {"e01_peticao_inicial_jec_001_v1": "refazer"}
    amb.cliente.roteiro["redacao e01_peticao_inicial_jec_001_v2"] = [cortada(), cortada()]
    amb.avancar(peca)
    assert amb.destino(peca.com_versao(2)) == "versao_perdida_formato"
    ponto = amb.ponto(peca)
    assert (ponto.acao, ponto.peca.versao) == ("aprovada", 3)


def test_segunda_falha_na_redacao_da_terceira_versao_descarta(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.decisao.plano = {f"e01_peticao_inicial_jec_001_v{k}": "refazer" for k in (1, 2)}
    amb.cliente.roteiro["redacao e01_peticao_inicial_jec_001_v3"] = [cortada(), cortada()]
    amb.avancar(peca)
    assert amb.destino(peca.com_versao(3)) == "descartada"
    assert amb.ponto(peca).acao == "encerrada"


def test_segunda_falha_numa_copia_conta_como_nao_pega(amb: Ambiente) -> None:
    copia = RefPeca(
        rodada="e01",
        tipo="peticao_inicial_jec",
        numero=1,
        copia="e01_peticao_inicial_jec_001_erro1_1",
    )
    for etapa in (amb.ficha, amb.redacao):
        amb.arquivos.gravar_texto(etapa.arquivo_resultado(copia), "da original")
    amb.cliente.roteiro["checklist"] = [cortada(), cortada()]
    amb.avancar(copia)
    assert amb.destino(copia) == "copia_nao_pega"


def test_segunda_falha_do_conferente_local_e_valvula(amb: Ambiente) -> None:
    peca = amb.peca("manifestacao_ar_negativo")
    amb.ollama.respostas = [
        {"message": {"content": "{"}, "done_reason": "length"},
        {"message": {"content": "{"}, "done_reason": "length"},
    ]
    amb.avancar(peca)
    assert amb.arquivos.existe(
        "saida/pedidos/e01_manifestacao_ar_negativo_001_v1_conferente_local_t2.json"
    )
    assert amb.destino(peca.com_versao(1)) is None
    assert amb.ponto(peca).acao == "aprovada"  # risco baixo segue sem ele
    recebida = amb.local.recebidas[-1][1]
    assert recebida.resultado == "indisponivel"


# 5 · válvula do modelo local ------------------------------------------------------------


def test_risco_baixo_segue_sem_o_local_e_registra(amb: Ambiente) -> None:
    peca = amb.peca("manifestacao_ar_negativo")
    amb.porteiro.codigo = 3
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "aprovada"
    assert amb.local.recebidas[-1][1].resultado == "indisponivel"
    assert ("pausa", "modelo_local") in amb.ocorrencias()


def test_risco_medio_espera_72_horas_e_chama_o_opus(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.porteiro.codigo = 2
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "esperar_local"
    amb.relogio.andar(71 * HORA)
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "esperar_local"
    assert "desempate" not in " ".join(amb.cliente.enviados)
    amb.relogio.andar(2 * HORA)
    amb.avancar(peca)
    assert ("pausa", "substituicao_opus") in amb.ocorrencias()
    assert amb.local.recebidas[-1][1].resultado == "indisponivel"
    assert amb.ponto(peca).acao == "aprovada"
    quedas = [o for o in amb.ocorrencias() if o == ("pausa", "modelo_local")]
    assert len(quedas) == 3  # cada queda registrada


def test_contagem_nunca_zera_com_volta_e_nova_queda(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.porteiro.codigo = 2
    amb.avancar(peca)
    amb.relogio.andar(40 * HORA)
    amb.ollama.respostas = [
        {"message": {"content": "{"}, "done_reason": "length"},
        {"message": {"content": "{"}, "done_reason": "length"},
    ]
    amb.porteiro.codigo = 0  # volta, responde duas vezes fora do formato e cai de novo
    amb.avancar(peca)
    amb.porteiro.codigo = 2
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "esperar_local"
    amb.relogio.andar(33 * HORA)  # 73 horas desde a primeira queda
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "aprovada"


def test_risco_alto_espera_e_pausa_aos_7_dias(amb: Ambiente) -> None:
    peca = amb.peca("embargos_declaracao")
    amb.porteiro.codigo = 2
    amb.avancar(peca)
    amb.relogio.andar(6 * 24 * HORA)
    amb.avancar(peca)
    assert ("pausa", "modelo_local_7_dias") not in amb.ocorrencias()
    amb.relogio.andar(2 * 24 * HORA)
    amb.avancar(peca)
    amb.avancar(peca)
    assert amb.ocorrencias().count(("pausa", "modelo_local_7_dias")) == 1
    assert amb.ponto(peca).acao == "esperar_local"
    amb.porteiro.codigo = 0
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "aprovada"
    assert amb.local.recebidas[-1][1].resultado == "rodou"


def test_fora_da_janela_espera_sem_chamar_o_porteiro(amb: Ambiente) -> None:
    peca = amb.peca()
    amb.relogio.andar(13 * HORA)  # meio-dia
    amb.avancar(peca)
    assert amb.porteiro.comandos == []
    assert amb.ponto(peca).acao == "esperar_local"
    amb.relogio.andar(11 * HORA)  # 23h do dia seguinte
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "aprovada"


@pytest.mark.parametrize(
    "tipo", ["manifestacao_ar_negativo", "peticao_inicial_jec", "embargos_declaracao"]
)
def test_pedido_que_nao_cabe_nao_espera(amb: Ambiente, tipo: str) -> None:
    amb.local._texto = lambda ref: "a" * 60_000
    peca = amb.peca(tipo)
    amb.relogio.andar(13 * HORA)  # fora da janela: mesmo assim não espera
    amb.avancar(peca)
    assert amb.ponto(peca).acao == "aprovada"
    assert amb.local.recebidas[-1][1].causa == "contexto"
    assert ("contexto", "nao_cabe") in amb.ocorrencias()
    assert amb.ollama.pedidos == []


# 6 · contexto no ensaio e na rodada ---------------------------------------------------


def test_ensaio_registra_pedido_acima_de_75_por_cento(amb: Ambiente) -> None:
    amb.local._texto = lambda ref: "a" * (3 * 11_000)  # 13 mil de 16.384: 79%
    peca = amb.peca()
    amb.avancar(peca)
    assert ("contexto", "acima_do_limite_do_ensaio") in amb.ocorrencias()
    assert amb.ponto(peca).acao == "aprovada"
    assert len(amb.ollama.pedidos) == 1


def test_rodada_so_bloqueia_o_que_nao_cabe(tmp_path: Path) -> None:
    amb = Ambiente(preparar(tmp_path), rodada="r01")
    amb.local._texto = lambda ref: "a" * (3 * 11_000)
    peca = amb.peca()
    amb.avancar(peca)
    assert not [o for o in amb.ocorrencias() if o[0] == "contexto"]
    assert len(amb.ollama.pedidos) == 1


# 7 · congelamento ------------------------------------------------------------------------


def test_arquivo_congelado_mudado_para_antes_do_passo(amb: Ambiente) -> None:
    peca = amb.peca()
    (amb.raiz / "dados/catalogo/tipos.json").write_text(json.dumps(TIPOS, indent=1))
    resumo = amb.avancar(peca)
    assert resumo.parada == "congelamento"
    assert amb.cliente.enviados == []
    assert ("parada", "congelamento") in amb.ocorrencias()


# 8 · corte de gasto -----------------------------------------------------------------------


def test_corte_para_a_peca_sem_perder_nada(amb: Ambiente) -> None:
    from fabrica.comum.formatos import Chamada

    amb.servicos.registro.chamada(
        Chamada(
            rodada="e01",
            peca="outra",
            pedido="outra",
            tarefa="ficha",
            modelo="claude-haiku-5-5",
            tokens_entrada=0,
            tokens_cache=0,
            tokens_raciocinio=0,
            tokens_saida=0,
            custo_milionesimos=10_000 * 1_000_000,
            duracao_segundos=0.0,
            momento=INICIO,
        )
    )
    peca = amb.peca()
    resumo = amb.avancar(peca)
    assert resumo.parada == "corte"
    assert amb.cliente.enviados == []
    assert amb.arquivos.existe("saida/pedidos/e01_peticao_inicial_jec_001_ficha_t1.json")
    assert ("parada", "corte_de_gasto") in amb.ocorrencias()
    assert amb.avancar(peca).parada == "corte"
    assert amb.cliente.enviados == []
    assert amb.ponto(peca).acao == "coletar"


def test_alerta_de_gasto_avisado(amb: Ambiente) -> None:
    from fabrica.comum.formatos import Chamada

    amb.servicos.registro.chamada(
        Chamada(
            rodada="e01",
            peca="outra",
            pedido="outra",
            tarefa="ficha",
            modelo="claude-haiku-5-5",
            tokens_entrada=0,
            tokens_cache=0,
            tokens_raciocinio=0,
            tokens_saida=0,
            custo_milionesimos=3_001 * 1_000_000,
            duracao_segundos=0.0,
            momento=INICIO,
        )
    )
    resumo = amb.avancar(amb.peca())
    assert resumo.alerta_de_gasto
    assert resumo.parada is None


# 9 · modo de teste -------------------------------------------------------------------------


def test_modo_de_teste_uma_passagem_e_passa_o_modo(tmp_path: Path) -> None:
    amb = Ambiente(preparar(tmp_path), modo_teste=True)
    peca = amb.peca()
    amb.decisao.plano = {"e01_peticao_inicial_jec_001_v1": "refazer"}
    amb.avancar(peca)
    ponto = amb.ponto(peca)
    assert ponto.acao == "refazer_em_teste"
    assert ponto.peca.versao == 1
    assert not amb.arquivos.listar("saida/pedidos", "*_v2_*")
    assert all(amb.redacao.modos) and all(amb.decisao.modos)


# descoberta das peças ------------------------------------------------------------------


def test_descobre_as_pecas_pelos_pedidos_de_ficha(amb: Ambiente) -> None:
    assert estado.descobrir_pecas(amb.arquivos) == []
    for numero in (2, 1):
        ref = amb.peca(numero=numero)
        amb.ficha.pedir(ref, amb.servicos)
    amb.ficha.pedir(amb.peca("embargos_declaracao", 1), amb.servicos)
    assert estado.descobrir_pecas(amb.arquivos) == [
        RefPeca("e01", "embargos_declaracao", 1),
        RefPeca("e01", "peticao_inicial_jec", 1),
        RefPeca("e01", "peticao_inicial_jec", 2),
    ]


# 10 · comando avancar ----------------------------------------------------------------------


def test_executar_avancar_com_servicos_falsos(
    amb: Ambiente, monkeypatch: pytest.MonkeyPatch
) -> None:
    chamados: list[Any] = []

    def falso(etapas: Any, servicos: Servicos, pecas: Any = None) -> estado.ResumoAvanco:
        chamados.append(servicos)
        return estado.ResumoAvanco()

    monkeypatch.setattr(estado, "avancar", falso)
    assert principal.executar(["avancar"], amb.servicos) == 0
    assert chamados == [amb.servicos]


def test_comando_desconhecido_recusado(amb: Ambiente) -> None:
    assert principal.executar(["inventado"], amb.servicos) == 2
    assert principal.executar([], amb.servicos) == 2


def test_montar_servicos_com_chave(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    raiz = preparar(tmp_path)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-chave-falsa-do-teste")
    servicos = principal.montar_servicos(raiz)
    assert isinstance(servicos.api_claude, ApiClaude)
    assert isinstance(servicos.modelo_local, ModeloLocal)
    assert servicos.modo_teste is False
    assert principal.executar(["avancar"], servicos) == 0  # sem peças, nada a fazer
    gravados = [p for p in raiz.rglob("*") if p.is_file() and ".git" not in p.parts]
    assert all("sk-ant-chave-falsa" not in p.read_text(errors="ignore") for p in gravados)


def test_montar_servicos_sem_chave_para_com_mensagem_clara(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    raiz = preparar(tmp_path)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    servicos = principal.montar_servicos(raiz)
    assert servicos.api_claude is None
    Congelamento(servicos.arquivos, servicos.registro).abrir_rodada(
        "e01", semente=1, ensaio_aprovado_origem=None
    )
    etapa = EtapaFalsa("ficha", "claude", "ficha")
    monkeypatch.setattr(principal, "ETAPAS", [etapa])
    caminho = raiz / "saida/pedidos/e01_peticao_inicial_jec_001_ficha_t1.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(
        Pedido(
            nome="e01_peticao_inicial_jec_001_ficha_t1",
            servico="claude",
            rodada="e01",
            peca="e01_peticao_inicial_jec_001",
            versao=None,
            tarefa="ficha",
            tentativa=1,
            modelo="claude-haiku-5-5",
            esforco="low",
            teto_saida=8000,
            partes=[ParteDoPedido(nome="instrucoes", texto="x")],
            formato=None,
            esquema=None,
            criado_em=INICIO,
        ).model_dump_json()
    )
    estado.registrar_pedido(
        RefPeca("e01", "peticao_inicial_jec", 1),
        "ficha",
        "saida/pedidos/e01_peticao_inicial_jec_001_ficha_t1.json",
        servicos.arquivos,
    )
    assert principal.executar(["avancar"], servicos) != 0
    erro = capsys.readouterr().err
    assert "ANTHROPIC_API_KEY" in erro
