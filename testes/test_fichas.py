"""Teste de aceite do brief 015: `fabrica/fichas.py` e os comandos `fichas` e `ensaio`.

Cliente da API falso (nenhuma chamada de verdade), relógio falso e pasta temporária
com repositório git próprio, com cópias de `dados/`, `config/` e `instrucoes/`.
"""

from __future__ import annotations

import datetime
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import anthropic
import pytest

from fabrica import __main__ as principal
from fabrica import estado, fichas, matriz
from fabrica.comum import config
from fabrica.comum.api_claude import ApiClaude
from fabrica.comum.arquivos import RODADAS, Arquivos
from fabrica.comum.formatos import BaseFicha, Ficha, Pedido, Rodadas
from fabrica.comum.gasto import ControleGasto
from fabrica.comum.modelo_local import ModeloLocal
from fabrica.comum.registro import Registro
from fabrica.estado import RefPeca, Servicos

RAIZ = Path(__file__).resolve().parent.parent
INICIO = datetime.datetime(2026, 11, 21, 23, 0).astimezone()
INICIAL = "peticao_inicial_jec"
EMB = "embargos_declaracao"
MAN = "manifestacao_ar_negativo"


# ---------------------------------------------------------------------------
# Falsos e ambiente
# ---------------------------------------------------------------------------


def mensagem(texto: str) -> anthropic.types.Message:
    return anthropic.types.Message.model_validate(
        {
            "id": "msg_falsa",
            "type": "message",
            "role": "assistant",
            "model": "claude-haiku-5-5",
            "content": [{"type": "text", "text": texto}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )


class Mensagens:
    def __init__(self, cliente: ClienteFalso) -> None:
        self.cliente = cliente

    def create(self, **argumentos: Any) -> anthropic.types.Message:
        blocos = argumentos["messages"][0]["content"]
        self.cliente.enviados.append([b["text"] for b in blocos])
        if not self.cliente.fila:
            raise AssertionError("o teste não previu esta chamada")
        return mensagem(self.cliente.fila.pop(0))

    def count_tokens(self, **argumentos: Any) -> anthropic.types.MessageTokensCount:
        return anthropic.types.MessageTokensCount(input_tokens=10)


class ClienteFalso:
    def __init__(self) -> None:
        self.fila: list[str] = []
        self.enviados: list[list[str]] = []
        self.messages = Mensagens(self)


class Relogio:
    def __init__(self) -> None:
        self.agora = INICIO

    def __call__(self) -> datetime.datetime:
        self.agora += datetime.timedelta(seconds=1)
        return self.agora


def git(raiz: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=raiz, check=True, capture_output=True)


def preparar(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "teste@ficticio.example")
    git(tmp_path, "config", "user.name", "Teste")
    shutil.copytree(RAIZ / "dados", tmp_path / "dados")
    shutil.copytree(RAIZ / "instrucoes", tmp_path / "instrucoes")
    (tmp_path / "config").mkdir()
    shutil.copy(RAIZ / "config/gasto.toml", tmp_path / "config/gasto.toml")
    shutil.copy(RAIZ / "config/config.toml", tmp_path / "config/config.toml")
    (tmp_path / "fabrica").mkdir()
    (tmp_path / "fabrica/__init__.py").write_text("")
    (tmp_path / "pyproject.toml").write_text("[project]\n")
    (tmp_path / ".gitignore").write_text("saida/\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "x")
    return tmp_path


class Ambiente:
    def __init__(self, raiz: Path) -> None:
        self.raiz = raiz
        self.relogio = Relogio()
        self.cliente = ClienteFalso()
        arquivos = Arquivos(raiz, relogio=self.relogio)
        lida = config.carregar(arquivos)
        registro = Registro(arquivos)
        gasto = ControleGasto(lida, registro, relogio=self.relogio)
        self.servicos = Servicos(
            api_claude=ApiClaude(
                self.cliente, lida, arquivos, registro, gasto, relogio=self.relogio
            ),
            modelo_local=ModeloLocal(lida, arquivos, registro, relogio=self.relogio),
            arquivos=arquivos,
            config=lida,
            registro=registro,
            gasto=gasto,
            relogio=self.relogio,
            modo_teste=False,
        )
        self.ctx = fichas.carregar_contexto(arquivos, lida)

    @property
    def arquivos(self) -> Arquivos:
        return self.servicos.arquivos

    def executar(self, *argumentos: str) -> int:
        return principal.executar(list(argumentos), self.servicos)

    def base(self, peca: str) -> BaseFicha:
        return self.arquivos.ler_json(f"saida/fichas/{peca}_base.json", BaseFicha)

    def rodadas(self) -> Rodadas:
        return self.arquivos.ler_json(RODADAS, Rodadas)

    def aprovar(self, rodada: str) -> None:
        lidas = self.rodadas()
        novas = [
            r.model_copy(update={"ensaio_aprovado": True, "aprovado_em": self.relogio()})
            if r.id == rodada
            else r
            for r in lidas.rodadas
        ]
        self.arquivos.regravar_rodadas(Rodadas(rodadas=novas))

    def avancar(self, peca: str) -> estado.ResumoAvanco:
        rodada, _, resto = peca.partition("_")
        tipo, _, numero = resto.rpartition("_")
        fichas.repor_falhas_de_formato(self.servicos)
        ref = RefPeca(rodada=rodada, tipo=tipo, numero=int(numero))
        # Só as etapas da ficha: as seguintes (redação, 016) pedem a estrutura preparada.
        etapas = [fichas.EtapaFicha(), fichas.EtapaRetorno()]
        return estado.avancar(etapas, self.servicos, [ref])


@pytest.fixture
def amb(tmp_path: Path) -> Ambiente:
    return Ambiente(preparar(tmp_path))


# ---------------------------------------------------------------------------
# Respostas do Haiku escritas no teste
# ---------------------------------------------------------------------------


def resposta_inicial(base: BaseFicha, **troca: Any) -> dict[str, Any]:
    ajuizamento = base.processo.data_ajuizamento
    dados: dict[str, Any] = {
        "fatos": [
            {
                "data": str(ajuizamento - datetime.timedelta(days=60)),
                "descricao": "A parte autora contratou o serviço.",
                "valores": ["v2"],
            },
            {
                "data": str(ajuizamento - datetime.timedelta(days=30)),
                "descricao": "A cobrança indevida foi lançada.",
                "valores": ["v2"],
            },
        ],
        "valores": [
            {"id": "v1", "descricao": "dano moral", "centavos": 500000, "data_referencia": None},
            {"id": "v2", "descricao": "cobrança", "centavos": 30000, "data_referencia": None},
            {
                "id": "v3",
                "descricao": "valor da causa",
                "centavos": 530000,
                "data_referencia": None,
            },
        ],
        "provas": [{"id": "d1", "descricao": "fatura", "identificador": base.identificadores[0]}],
        "valor_causa": "v3",
        "fundamentos": ["cdc_art14", "lei_9099_1995_art3"],
        "momento_processual": {"ultima_decisao": "nenhuma"},
        "pecas_anteriores": [],
        "pedidos": [
            {"id": "p1", "natureza": "citacao_reu", "descricao": "citação", "valor": None},
            {"id": "p2", "natureza": "danos_morais", "descricao": "dano moral", "valor": "v1"},
            {"id": "p3", "natureza": "danos_materiais", "descricao": "material", "valor": "v2"},
        ],
        "relacao_consumo": True,
        "inversao_onus_pedida": False,
        "tutela_urgencia": {"pedida": False, "fundamento": None},
        "tentativa_previa": None,
    }
    dados.update(troca)
    return dados


def resposta_manifestacao(base: BaseFicha) -> dict[str, Any]:
    return {
        "fatos": [
            {
                "data": str(base.processo.data_ajuizamento - datetime.timedelta(days=10)),
                "descricao": "Fato do processo de origem.",
                "valores": [],
            }
        ],
        "valores": [],
        "provas": [],
        "valor_causa": None,
        "fundamentos": ["cpc_art319"],
        "momento_processual": {"ultima_decisao": "Intimação para manifestação."},
        "pecas_anteriores": [],
        "pedidos": [
            {"id": "p1", "natureza": "nova_citacao_novo_endereco", "descricao": "d", "valor": None}
        ],
    }


def texto(dados: dict[str, Any]) -> str:
    return json.dumps(dados, ensure_ascii=False)


def codigos(base: BaseFicha, dados: dict[str, Any], ctx: fichas.Contexto) -> list[str]:
    _, falhas = fichas.conferir(base, texto(dados), ctx)
    return [f.codigo for f in falhas]


# ---------------------------------------------------------------------------
# Comando ensaio
# ---------------------------------------------------------------------------


def test_ensaio_abre_a_rodada_e_grava_uma_base_por_tipo(amb: Ambiente) -> None:
    assert amb.executar("ensaio", "--semente", "5") == 0
    [rodada] = amb.rodadas().rodadas
    assert (rodada.id, rodada.semente, rodada.ensaio_aprovado) == ("e01", 5, False)
    assert rodada.impressoes  # impressões digitais gravadas
    for tipo in (INICIAL, EMB, MAN):
        peca = f"e01_{tipo}_001"
        base = amb.base(peca)
        esperada = matriz.combinacao_do_ensaio(
            amb.ctx.matrizes[tipo], amb.ctx.travas, 5, amb.servicos.config.geral.matriz
        ).combinacoes[0]
        assert base.casa_matriz == esperada.casa()
        assert (base.casa, base.tentativa, base.peca) == (1, 1, peca)
        pedido = amb.arquivos.ler_json(f"saida/pedidos/{peca}_ficha_t1.json", Pedido)
        assert pedido.tarefa == "ficha" and pedido.formato is not None
        # O código lê a instrução do arquivo.
        instrucao = (amb.raiz / "instrucoes/ficha.md").read_text("utf-8")
        assert pedido.partes[0].nome == "instrucoes" and pedido.partes[0].texto == instrucao
    assert amb.executar("ensaio") == 0
    assert [r.id for r in amb.rodadas().rodadas] == ["e01", "e02"]


def test_base_tem_os_dados_do_programa(amb: Ambiente) -> None:
    amb.executar("ensaio", "--semente", "5")
    inicial = amb.base(f"e01_{INICIAL}_001")
    assert inicial.processo.numero_cnj is None and inicial.processo.rito == "juizado_especial_civel"
    assert (
        inicial.salario_minimo_referencia
        == amb.servicos.config.geral.referencias_legais.salario_minimo_centavos
    )
    assert all(i.startswith("SINT-") for i in inicial.identificadores)
    assert {p.papel for p in inicial.partes} == {"autor", "reu"}
    embargos = amb.base(f"e01_{EMB}_001")
    assert embargos.processo.rito == "procedimento_comum"
    assert embargos.defeito == "omissao_parcial" and embargos.tipo_decisao == "sentenca"
    assert embargos.prazo is not None and embargos.prazo.dias_uteis == 5
    assert embargos.data_peca <= embargos.prazo.termo_final


# ---------------------------------------------------------------------------
# Comando fichas
# ---------------------------------------------------------------------------


def test_fichas_recusa_sem_ensaio_aprovado(
    amb: Ambiente, capsys: pytest.CaptureFixture[str]
) -> None:
    assert amb.executar("fichas", "--tipo", INICIAL) == 1
    assert "ensaio aprovado" in capsys.readouterr().err
    amb.executar("ensaio")
    assert amb.executar("fichas", "--tipo", INICIAL) == 1
    assert not amb.arquivos.listar("saida/fichas", "r01_*")


def test_fichas_recusa_arquivos_diferentes_do_ensaio(
    amb: Ambiente, capsys: pytest.CaptureFixture[str]
) -> None:
    amb.executar("ensaio")
    amb.aprovar("e01")
    alterado = amb.raiz / "dados/conferencia/termos_inequivocos.json"
    alterado.write_text(alterado.read_text("utf-8").replace("quádruplo", "quadruplo", 1))
    git(amb.raiz, "commit", "-q", "-am", "muda")
    capsys.readouterr()
    assert amb.executar("fichas", "--tipo", INICIAL) == 1
    erro = capsys.readouterr().err
    assert "dados/conferencia/termos_inequivocos.json" in erro
    assert [r.id for r in amb.rodadas().rodadas] == ["e01"]


def test_fichas_abre_a_rodada_e_grava_as_dez_bases(amb: Ambiente) -> None:
    amb.executar("ensaio")
    amb.aprovar("e01")
    assert amb.executar("fichas", "--tipo", INICIAL, "--semente", "3") == 0
    rodada = amb.rodadas().rodadas[-1]
    assert (rodada.id, rodada.semente, rodada.ensaio_aprovado_origem) == ("r01", 3, "e01")
    bases = [amb.base(f"r01_{INICIAL}_{n:03d}") for n in range(1, 11)]
    assert [b.casa for b in bases] == list(range(1, 11))
    sorteio = matriz.sortear(
        amb.ctx.matrizes[INICIAL], amb.ctx.travas, 3, amb.servicos.config.geral.matriz
    )
    assert [b.casa_matriz for b in bases] == [c.casa() for c in sorteio.combinacoes]
    assert len(amb.arquivos.listar("saida/pedidos", f"r01_{INICIAL}_*_ficha_t1.json")) == 10
    # O tipo seguinte usa a rodada aberta e a semente dela.
    assert amb.executar("fichas", "--tipo", MAN) == 0
    assert amb.base(f"r01_{MAN}_001").semente == 3
    # O mesmo tipo não é gravado duas vezes.
    assert amb.executar("fichas", "--tipo", INICIAL) == 1


# ---------------------------------------------------------------------------
# Ficha que falha: retorno, ficha nova na casa e casa vazia
# ---------------------------------------------------------------------------

PECA = f"e01_{INICIAL}_001"


def test_ficha_certa_e_gravada(amb: Ambiente) -> None:
    amb.executar("ensaio", "--semente", "5")
    amb.cliente.fila = [texto(resposta_inicial(amb.base(PECA)))]
    amb.avancar(PECA)
    ficha = amb.arquivos.ler_json(f"saida/fichas/{PECA}.json", Ficha).root
    assert ficha.id == PECA and ficha.valor_causa == "v3"
    assert len(amb.cliente.enviados) == 1


def test_ficha_que_falha_volta_uma_vez_com_o_motivo(amb: Ambiente) -> None:
    amb.executar("ensaio", "--semente", "5")
    base = amb.base(PECA)
    errada = resposta_inicial(base, valor_causa="v1")
    amb.cliente.fila = [texto(errada), texto(resposta_inicial(base))]
    amb.avancar(PECA)
    assert len(amb.cliente.enviados) == 2
    retorno = amb.arquivos.ler_json(f"saida/pedidos/{PECA}_ficha_retorno_t1.json", Pedido)
    motivo = next(p.texto for p in retorno.partes if p.nome == "motivo")
    assert fichas.VALOR_CAUSA_DIFERENTE in motivo
    assert amb.arquivos.existe(f"saida/fichas/{PECA}.json")


def test_ficha_que_falha_duas_vezes_e_trocada_ate_duas_vezes(amb: Ambiente) -> None:
    amb.executar("ensaio", "--semente", "5")
    errada = texto(resposta_inicial(amb.base(PECA), valor_causa="v1"))
    amb.cliente.fila = [errada] * 6
    amb.avancar(PECA)
    assert amb.arquivos.existe(f"saida/fichas/{PECA}_descartada.json")
    nova = amb.base(f"e01_{INICIAL}_002")
    assert (nova.casa, nova.tentativa, nova.casa_matriz) == (1, 2, amb.base(PECA).casa_matriz)
    assert nova.partes != amb.base(PECA).partes  # dados fictícios novos
    amb.avancar(f"e01_{INICIAL}_002")
    assert amb.base(f"e01_{INICIAL}_003").tentativa == 3
    amb.avancar(f"e01_{INICIAL}_003")
    assert not amb.arquivos.existe(f"saida/fichas/e01_{INICIAL}_004_base.json")
    assert amb.arquivos.existe(f"saida/fichas/e01_{INICIAL}_casa01_vazia.json")
    assert len(amb.cliente.enviados) == 6


def test_resposta_fora_do_formato_t2_e_depois_ficha_nova(amb: Ambiente) -> None:
    amb.executar("ensaio", "--semente", "5")
    amb.cliente.fila = ["isto não é JSON", "nem isto"]
    amb.avancar(PECA)
    assert amb.arquivos.existe(f"saida/pedidos/{PECA}_ficha_t2.json")
    assert estado.destino(RefPeca("e01", INICIAL, 1), amb.arquivos) == estado.FICHA_FALHOU
    fichas.repor_falhas_de_formato(amb.servicos)
    assert amb.arquivos.existe(f"saida/fichas/{PECA}_descartada.json")
    assert amb.base(f"e01_{INICIAL}_002").tentativa == 2
    # Repetir não troca de novo.
    fichas.repor_falhas_de_formato(amb.servicos)
    assert not amb.arquivos.existe(f"saida/fichas/e01_{INICIAL}_003_base.json")


# ---------------------------------------------------------------------------
# Conferências da ficha
# ---------------------------------------------------------------------------


def test_conferencia_pega_cada_problema(amb: Ambiente) -> None:
    amb.executar("ensaio", "--semente", "5")
    base, ctx = amb.base(PECA), amb.ctx
    certa = resposta_inicial(base)
    assert codigos(base, certa, ctx) == []
    fatos = list(reversed(certa["fatos"]))
    assert fichas.DATAS_FORA_DE_ORDEM in codigos(base, resposta_inicial(base, fatos=fatos), ctx)
    antigo = [{**certa["fatos"][0], "data": "2020-01-01"}]
    assert fichas.FATO_FORA_DO_PERIODO in codigos(base, resposta_inicial(base, fatos=antigo), ctx)
    assert fichas.VALOR_CAUSA_DIFERENTE in codigos(
        base, resposta_inicial(base, valor_causa="v2"), ctx
    )
    alto = [
        {"id": "v1", "descricao": "dano moral", "centavos": 7000000, "data_referencia": None},
        {"id": "v2", "descricao": "cobrança", "centavos": 30000, "data_referencia": None},
        {"id": "v3", "descricao": "valor da causa", "centavos": 7030000, "data_referencia": None},
    ]
    falhas = codigos(base, resposta_inicial(base, valores=alto), ctx)
    assert fichas.ALCADA in falhas and fichas.TRAVA in falhas
    fora = resposta_inicial(base, fundamentos=["cdc_art14", "cpc_art1022"])
    assert codigos(base, fora, ctx) == [fichas.FUNDAMENTO_FORA_DO_TRECHO]
    assert codigos(base, {"fatos": "não"}, ctx) == [fichas.FORMATO]


def test_trava_violada_na_ficha_pronta(amb: Ambiente) -> None:
    amb.executar("ensaio", "--semente", "5")
    base = amb.base(f"e01_{MAN}_001").model_copy(
        update={"pedido_ar": "informar_novo_endereco", "novo_endereco": None}
    )
    assert fichas.TRAVA in codigos(base, resposta_manifestacao(base), amb.ctx)
    certa = base.model_copy(update={"novo_endereco": base.endereco_tentado})
    certa = certa.model_copy(update={"meio_nova_diligencia": "correio"})
    assert fichas.TRAVA not in codigos(certa, resposta_manifestacao(certa), amb.ctx)


def test_valor_legal_na_ficha_recusa(amb: Ambiente) -> None:
    amb.executar("ensaio", "--semente", "5")
    base = amb.base(PECA)
    for centavos in (162100, 6484000):
        valores = [
            {"id": "v1", "descricao": "dano moral", "centavos": 500000, "data_referencia": None},
            {"id": "v2", "descricao": "cobrança", "centavos": 30000, "data_referencia": None},
            {
                "id": "v3",
                "descricao": "valor da causa",
                "centavos": 530000,
                "data_referencia": None,
            },
            {"id": "v4", "descricao": "outro", "centavos": centavos, "data_referencia": None},
        ]
        falhas = codigos(base, resposta_inicial(base, valores=valores), amb.ctx)
        assert falhas == [fichas.VALOR_LEGAL]


# ---------------------------------------------------------------------------
# Instrução lida do arquivo
# ---------------------------------------------------------------------------


def test_frase_da_instrucao_nao_esta_no_codigo() -> None:
    instrucao = (RAIZ / "instrucoes/ficha.md").read_text("utf-8")
    frases = [f.strip() for f in instrucao.replace("\n", " ").split(".") if len(f.strip()) > 40]
    assert len(frases) >= 5
    codigo = "\n".join(p.read_text("utf-8") for p in (RAIZ / "fabrica").rglob("*.py"))
    for frase in frases:
        assert frase not in codigo, frase
