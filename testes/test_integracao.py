"""Primeiro teste de integração (brief 018).

Os módulos de verdade, ligados pela lista de etapas de `fabrica/__main__.py`, com o
cliente falso da API e o modelo local falso, numa pasta temporária com cópias de
`fabrica/`, `pyproject.toml`, `dados/`, `instrucoes/` e `config/`, transformada num
repositório git local com um commit (sem remoto e sem rede). As respostas falsas são
escritas aqui, uma por tarefa, válidas pelos modelos de `formatos.py`: imitam só o
formato, não a qualidade. Cada cenário tem a sua pasta e não depende de outro.
"""

from __future__ import annotations

import datetime
import json
import random
import shutil
import socket
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any

import anthropic
import pytest

from fabrica import __main__ as principal
from fabrica import erros_plantados, estado
from fabrica.comum import config
from fabrica.comum.api_claude import ApiClaude
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.congelamento import Congelamento
from fabrica.comum.formatos import (
    BaseFicha,
    CatalogoErros,
    Conferencia,
    Ficha,
    Pedido,
    Rodada,
    Rodadas,
    Tokens,
)
from fabrica.comum.gasto import ControleGasto
from fabrica.comum.modelo_local import PORTEIRO_CABE, ModeloLocal
from fabrica.comum.registro import Registro
from fabrica.conferencia.local import EtapaLocal
from fabrica.estado import RefPeca, Servicos
from testes import apoio_config
from testes.test_conferencia_etapas import resposta_embargos
from testes.test_fichas import INICIO, RAIZ, resposta_inicial, resposta_manifestacao

INICIAL = "peticao_inicial_jec"
EMB = "embargos_declaracao"
MAN = "manifestacao_ar_negativo"
TIPOS = (INICIAL, EMB, MAN)
FICHA = {INICIAL: resposta_inicial, EMB: resposta_embargos, MAN: resposta_manifestacao}
ITENS_LOCAIS = ("coerencia", "pecas_anteriores", "texto_generico")
PALAVRAS = (
    "contrato serviço cobrança prazo documento parte pedido valor fato processo prova "
    "decisão relação consumo fornecedor consumidor obrigação pagamento entrega produto "
    "reparo garantia dano boleto fatura conta mensalidade contratação cancelamento "
    "atendimento protocolo reclamação resposta aviso endereço tentativa diligência "
    "intimação citação certidão juntada oficial carta correspondência devolução retorno"
).split()


# ---------------------------------------------------------------------------
# Pasta temporária com repositório git próprio
# ---------------------------------------------------------------------------


def git(raiz: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=raiz, check=True, capture_output=True)


def montar_pasta(tmp_path: Path) -> Path:
    raiz = tmp_path / "repo"
    sem_cache = shutil.ignore_patterns("__pycache__", "*.pyc")
    shutil.copytree(RAIZ / "fabrica", raiz / "fabrica", ignore=sem_cache)
    for pasta in ("dados", "instrucoes", "config"):
        shutil.copytree(RAIZ / pasta, raiz / pasta)
    shutil.copy(RAIZ / "pyproject.toml", raiz / "pyproject.toml")
    (raiz / "testes/dados").mkdir(parents=True)
    shutil.copy(
        RAIZ / "testes/dados/reais_reservados.json", raiz / "testes/dados/reais_reservados.json"
    )
    caminho = raiz / "config/config.toml"
    texto = caminho.read_text("utf-8")
    texto = apoio_config.provisorio(texto, etiqueta_completa="gemma3:27b", digest="sha256:falso")
    caminho.write_text(texto, "utf-8")
    (raiz / ".gitignore").write_text("saida/\n")
    git(raiz, "init", "-q")
    git(raiz, "config", "user.email", "teste@ficticio.example")
    git(raiz, "config", "user.name", "Teste")
    git(raiz, "add", ".")
    git(raiz, "commit", "-q", "-m", "pasta do teste de integração")
    return raiz


# ---------------------------------------------------------------------------
# Falsos
# ---------------------------------------------------------------------------


class Relogio:
    def __init__(self) -> None:
        self.agora = INICIO

    def __call__(self) -> datetime.datetime:
        self.agora += datetime.timedelta(seconds=1)
        return self.agora

    def pular(self, **duracao: float) -> None:
        self.agora += datetime.timedelta(**duracao)


def mensagem(texto: str, modelo: str) -> anthropic.types.Message:
    return anthropic.types.Message.model_validate(
        {
            "id": "msg_falsa",
            "type": "message",
            "role": "assistant",
            "model": modelo,
            "content": [{"type": "text", "text": texto}],
            "stop_reason": "end_turn",
            "stop_sequence": None,
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }
    )


def tipo_no_texto(textos: list[str]) -> str | None:
    for texto in textos:
        for tipo in TIPOS:
            if f"_{tipo}_" in texto:
                return tipo
    return None


class ApiFalsa:
    """Responde pela instrução que abre o pedido (o código lê cada uma do arquivo) e
    pelo tipo da peça. `especiais[(instrução, tipo)]` é uma fila de respostas que passa
    na frente da resposta padrão."""

    def __init__(self, raiz: Path, arquivos: Arquivos) -> None:
        self.instrucoes = {p.read_text("utf-8"): p.stem for p in (raiz / "instrucoes").glob("*.md")}
        # A instrução das cópias do brief 021 vai em duas seções, uma por modelo.
        plantar = (raiz / "instrucoes/plantar_erro.md").read_text("utf-8")
        self.instrucoes[erros_plantados.secao(plantar, erros_plantados.TITULO_OPUS)] = (
            "plantar_erro_opus"
        )
        self.instrucoes[erros_plantados.secao(plantar, erros_plantados.TITULO_SONNET)] = (
            "plantar_erro_sonnet"
        )
        catalogo = CatalogoErros.model_validate_json(
            (raiz / erros_plantados.ERROS).read_text("utf-8")
        )
        self.item_principal = {e.tipo_erro: e.item_principal for e in catalogo.erros}
        self.tipo_da_copia: dict[str, str] = {}  # texto da cópia do Opus -> tipo de erro
        self.arquivos = arquivos
        self.chamadas: list[tuple[str, str, str]] = []
        self.especiais: dict[tuple[str, str], list[Callable[[list[str]], str]]] = {}
        self.rascunhos: dict[str, str] = {}  # texto devolvido pela redação -> peça
        self.texto_fixo: dict[str, str] = {}  # tipo -> texto igual para todas as peças
        self.messages = self

    def create(self, **argumentos: Any) -> anthropic.types.Message:
        textos = [b["text"] for b in argumentos["messages"][0]["content"]]
        instrucao = self.instrucoes[textos[0]]
        if instrucao == "plantar_erro_sonnet":
            tipo = self._tipo_do_rascunho([json.loads(textos[-1])["copia"]])
        else:
            tipo = tipo_no_texto(textos[1:]) or self._tipo_do_rascunho(textos)
        self.chamadas.append((instrucao, tipo, argumentos["model"]))
        fila = self.especiais.get((instrucao, tipo))
        responder = fila.pop(0) if fila else getattr(self, f"_{instrucao}")
        return mensagem(responder(textos), argumentos["model"])

    def count_tokens(self, **argumentos: Any) -> anthropic.types.MessageTokensCount:
        return anthropic.types.MessageTokensCount(input_tokens=10)

    # --- leitura do pedido ----------------------------------------------------

    def _tipo_do_rascunho(self, textos: list[str]) -> str:
        peca = self._peca_do_rascunho(textos)
        return next(t for t in TIPOS if f"_{t}_" in peca)

    def _peca_do_rascunho(self, textos: list[str]) -> str:
        for texto in textos:
            for devolvido, peca in self.rascunhos.items():
                if texto.endswith(devolvido):
                    return peca
        # As cópias com erro gravadas pelo programa (brief 019): a peça vem do nome.
        for caminho in self.arquivos.listar("saida/erros", "*_erro*_*.md"):
            copia = self.arquivos.ler_texto(caminho)
            if any(
                len(texto) > 100 and (texto.endswith(copia.strip()) or copia.endswith(texto))
                for texto in textos
            ):
                return caminho.removeprefix("saida/erros/").partition("_erro")[0]
        raise AssertionError("rascunho que a redação falsa não escreveu")

    @staticmethod
    def _json(textos: list[str], chave: str) -> dict[str, Any]:
        for texto in textos:
            try:
                dados = json.loads(texto)
            except ValueError:
                continue
            if isinstance(dados, dict) and chave in dados:
                return dados
        raise AssertionError(f"pedido sem parte com {chave}")

    def ficha_da_peca(self, textos: list[str]) -> Ficha:
        dados = self._json(textos, "momento_processual")
        return self.arquivos.ler_json(f"saida/fichas/{dados['id']}.json", Ficha)

    # --- respostas padrão -------------------------------------------------------

    def _ficha(self, textos: list[str]) -> str:
        base = BaseFicha.model_validate_json(json.dumps(self._json(textos, "casa_matriz")))
        tipo = tipo_no_texto([base.peca]) or ""
        return json.dumps(FICHA[tipo](base), ensure_ascii=False)

    def _redacao(self, textos: list[str]) -> str:
        ficha = self.ficha_da_peca(textos).root
        tipo = tipo_no_texto([ficha.id]) or ""
        estrutura = self._json(textos, "blocos")
        if tipo in self.texto_fixo:
            texto = self.texto_fixo[tipo]
        else:
            sorteio = random.Random(f"{ficha.id}:{len(textos)}:{len(self.rascunhos)}")
            texto = "\n\n".join(
                f"## {b['titulo']}\n\n" + " ".join(sorteio.choices(PALAVRAS, k=30)) + "."
                for b in estrutura["blocos"]
            )
        self.rascunhos[texto] = ficha.id
        return texto

    def _extracao(self, textos: list[str]) -> str:
        peca = self._peca_do_rascunho(textos)
        ficha = self.arquivos.ler_json(f"saida/fichas/{peca}.json", Ficha).root
        valores = []
        if ficha.valor_causa is not None:
            causa = next(v for v in ficha.valores if v.id == ficha.valor_causa)
            valores.append(
                {
                    "texto": "R$ 1,00",
                    "centavos": causa.centavos,
                    "lugar": "valor_causa",
                    "pedido": None,
                }
            )
        return json.dumps(
            {
                "nomes": [],
                "documentos": [],
                "valores": valores,
                "datas": [],
                "comarca": None,
                "juizo": None,
                "pedidos": [{"natureza": p.natureza, "texto": p.descricao} for p in ficha.pedidos],
                "pecas_anteriores": [],
                "data_peca": str(ficha.data_peca),
            }
        )

    @staticmethod
    def _checklist(textos: list[str], nao_passa: tuple[str, ...] = ()) -> str:
        lista = ApiFalsa._json(textos, "citacoes_nao_resolvidas")
        return json.dumps(
            {
                "itens": [
                    {
                        "item": i["item"],
                        "resposta": "nao_passa" if i["item"] in nao_passa else "passa",
                        "trecho": f"trecho do {i['item']}",
                    }
                    for i in lista["itens"]
                ],
                "citacoes": [],
                "notas": {"clareza": 4, "concisao": 4, "linguagem_tecnica": 4},
            }
        )

    def _opus_desempate(self, textos: list[str]) -> str:
        lista = self._json(textos, "itens")
        return json.dumps(
            {
                "itens": [
                    {"item": i["item"], "resposta": "passa", "justificativa": "o Opus decidiu"}
                    for i in lista["itens"]
                ]
            }
        )

    def _plantar_erro_opus(self, textos: list[str]) -> str:
        """Acrescenta uma frase ao texto do primeiro bloco (uma linha que aparece uma vez)."""
        pedido, original = json.loads(textos[1]), textos[-1]
        peca = self._peca_do_rascunho([original])
        velho = next(
            linha for linha in original.splitlines()[2:] if linha and not linha.startswith("#")
        )
        novo = f"{velho} A parte já foi citada no mesmo endereço."
        copia = original.replace(velho, novo)
        self.rascunhos[copia] = peca
        self.tipo_da_copia[copia] = pedido["tipo_erro"]
        return json.dumps({"trecho_original": velho, "trecho_novo": novo}, ensure_ascii=False)

    def _plantar_erro_sonnet(self, textos: list[str]) -> str:
        copia = json.loads(textos[-1])["copia"]
        item = self.item_principal[self.tipo_da_copia[copia]]
        return json.dumps(
            {
                "item_apontado": item,
                "descricao_erro": "a frase acrescentada traz o erro",
                "outro_problema": False,
                "descricao_outro_problema": None,
            }
        )


def checklist_que_reprova(*itens: str) -> Callable[[list[str]], str]:
    return lambda textos: ApiFalsa._checklist(textos, itens)


class LocalFalso:
    """O porteiro e o Ollama falsos. `disponivel` liga e desliga o porteiro; `falha`
    faz o envio cair; `respostas[tipo]` troca a resposta de um item."""

    def __init__(self) -> None:
        self.disponivel = True
        self.falha = False
        self.respostas: dict[str, dict[str, str]] = {}
        self.envios = 0

    def executar(self, comando: Any) -> int:
        return PORTEIRO_CABE if self.disponivel else 2

    def enviar(self, url: str, corpo: dict[str, Any]) -> dict[str, Any]:
        self.envios += 1
        if self.falha:
            raise ConnectionError("o modelo caiu antes de responder")
        texto = corpo["messages"][0]["content"]
        tipo = tipo_no_texto([texto]) or ""
        trocas = self.respostas.get(tipo, {})
        itens = [
            {"item": i, "resposta": trocas.get(i, "passa"), "trecho": f"local {i}"}
            for i in ITENS_LOCAIS
            if f'"item": "{i}"' in texto
        ]
        return {"message": {"content": json.dumps({"itens": itens})}, "done_reason": "stop"}


class Integracao:
    def __init__(self, tmp_path: Path) -> None:
        self.raiz = montar_pasta(tmp_path)
        self.relogio = Relogio()
        arquivos = Arquivos(self.raiz, relogio=self.relogio)
        lida = config.carregar(arquivos)
        registro = Registro(arquivos)
        gasto = ControleGasto(lida, registro, relogio=self.relogio)
        self.api = ApiFalsa(self.raiz, arquivos)
        self.local = LocalFalso()
        self.servicos = Servicos(
            api_claude=ApiClaude(self.api, lida, arquivos, registro, gasto, relogio=self.relogio),
            modelo_local=ModeloLocal(
                lida,
                arquivos,
                registro,
                executar=self.local.executar,
                enviar=self.local.enviar,
                relogio=self.relogio,
                dormir=lambda segundos: None,
            ),
            arquivos=arquivos,
            config=lida,
            registro=registro,
            gasto=gasto,
            relogio=self.relogio,
            modo_teste=False,
        )

    @property
    def arquivos(self) -> Arquivos:
        return self.servicos.arquivos

    def executar(self, *argumentos: str) -> int:
        return principal.executar(list(argumentos), self.servicos)

    def avancar_ate_parar(self, limite: int = 20) -> int:
        """`avancar` até não haver mais o que fazer; devolve quantas vezes rodou."""
        for vez in range(1, limite + 1):
            antes = len(self.arquivos.listar("saida", "**/*"))
            assert self.executar("avancar") == 0
            if len(self.arquivos.listar("saida", "**/*")) == antes:
                return vez
        raise AssertionError("o avancar não parou")

    def veredito(self, peca: str, versao: int) -> Conferencia:
        return self.arquivos.ler_json(f"saida/conferencias/{peca}_v{versao}.json", Conferencia)

    def existe(self, caminho: str) -> bool:
        return self.arquivos.existe(caminho)

    def ocorrencias(self, causa: str) -> list[Any]:
        return [o for o in self.servicos.registro.ocorrencias() if o.causa == causa]


@pytest.fixture
def integ(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Integracao:
    tentativas: list[Any] = []
    original = socket.socket.connect

    def conectar(self: socket.socket, endereco: Any) -> None:
        tentativas.append(endereco)
        original(self, endereco)

    monkeypatch.setattr(socket.socket, "connect", conectar)
    ambiente = Integracao(tmp_path)
    ambiente.tentativas_de_rede = tentativas  # type: ignore[attr-defined]
    return ambiente


def peca(tipo: str, numero: int = 1, rodada: str = "e01") -> str:
    return f"{rodada}_{tipo}_{numero:03d}"


def arquivos_das_etapas(integ: Integracao, tipo: str, versao: int, numero: int = 1) -> list[str]:
    nome = f"{peca(tipo, numero)}_v{versao}"
    etapas = ["extracao", "programas", "checklist", "semelhanca"]
    ref = RefPeca("e01", tipo, numero, versao)
    if EtapaLocal().se_aplica(ref, integ.servicos):
        etapas.append("local")
    faltam = [e for e in etapas if not integ.existe(f"saida/conferencias/{nome}_{e}.json")]
    if not integ.existe(f"saida/rascunhos/{nome}.md"):
        faltam.append("redacao")
    if not integ.existe(f"saida/conferencias/{nome}.json"):
        faltam.append("decisao")
    return faltam


def preparar_e_abrir_ensaio(integ: Integracao) -> None:
    assert integ.executar("preparar") == 0
    assert integ.executar("ensaio", "--semente", "5") == 0


# ---------------------------------------------------------------------------
# 9 a 12. As três peças do ensaio, de ficha até veredito
# ---------------------------------------------------------------------------


def test_ensaio_leva_as_tres_pecas_de_ficha_a_veredito(integ: Integracao) -> None:
    preparar_e_abrir_ensaio(integ)
    integ.api.especiais[("checklist", INICIAL)] = [checklist_que_reprova("cabimento")]
    integ.local.respostas[EMB] = {"coerencia": "nao_passa"}
    integ.avancar_ate_parar()

    # Uma aprovada de primeira, uma depois de uma refação, a de risco alto com o Opus.
    assert integ.veredito(peca(MAN), 1).veredito == "aprovada"
    assert integ.veredito(peca(INICIAL), 1).veredito == "refazer"
    assert integ.veredito(peca(INICIAL), 1).categoria_motivo == "conteudo"
    assert integ.veredito(peca(INICIAL), 2).veredito == "aprovada"
    alto = integ.veredito(peca(EMB), 1)
    assert alto.veredito == "aprovada"
    coerencia = next(c for c in alto.caminho if c.item == "coerencia")
    assert [r.quem for r in coerencia.respostas] == ["haiku", "local", "opus"]
    assert [r.resposta for r in coerencia.respostas] == ["passa", "nao_passa", "passa"]
    assert (coerencia.regra, coerencia.quem_final) == ("alto: vale o Opus", "opus")
    aprovadas = sorted(integ.arquivos.listar("saida/aprovadas", "*.md"))
    assert aprovadas == sorted(
        f"saida/aprovadas/{p}.md"
        for p in (f"{peca(INICIAL)}_v2", f"{peca(EMB)}_v1", f"{peca(MAN)}_v1")
    )
    assert integ.arquivos.ler_texto(f"saida/aprovadas/{peca(INICIAL)}_v2.md") == (
        integ.arquivos.ler_texto(f"saida/rascunhos/{peca(INICIAL)}_v2.md")
    )
    # Nenhuma etapa pulada.
    for tipo, versao in ((MAN, 1), (INICIAL, 1), (INICIAL, 2), (EMB, 1)):
        assert arquivos_das_etapas(integ, tipo, versao) == [], (tipo, versao)
    assert integ.existe(f"saida/conferencias/{peca(EMB)}_v1_desempate.json")
    # Semelhança em todas as peças, com o valor no veredito (nenhuma aprovada antes no tipo).
    for tipo, versao in ((MAN, 1), (INICIAL, 2), (EMB, 1)):
        assert any(c.item == "semelhanca" for c in integ.veredito(peca(tipo), versao).caminho)

    # 11. Todo pedido no formato do registro de decisão 002 e com o gasto controlado.
    pedidos = integ.arquivos.listar("saida/pedidos", "*.json")
    for caminho in pedidos:
        lido = integ.arquivos.ler_json(caminho, Pedido)
        assert caminho == f"saida/pedidos/{lido.nome}.json"
        assert integ.existe(f"saida/respostas/{lido.nome}.json")
        assert lido.nome.endswith(f"_{lido.tarefa}_t{lido.tentativa}")
    gasto = integ.servicos.gasto
    esperado = sum(
        gasto.custo_real(modelo, Tokens(entrada=10, cache=0, raciocinio=0, saida=5))
        for _, _, modelo in integ.api.chamadas
    )
    assert esperado > 0 and gasto.total_gasto() == esperado
    nuvem = [p for p in pedidos if integ.arquivos.ler_json(p, Pedido).servico == "claude"]
    assert len(nuvem) == len(integ.api.chamadas)

    # 12. Nada gravado fora de saida/ e nenhuma tentativa de rede.
    saida = subprocess.run(
        ["git", "status", "--porcelain", "--ignored", "--untracked-files=all"],
        cwd=integ.raiz,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    fora = [linha for linha in saida.splitlines() if not linha[3:].startswith("saida/")]
    assert fora == []
    assert integ.tentativas_de_rede == []  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# 13. Ficha que falha, casa vazia e peça descartada nas três versões
# ---------------------------------------------------------------------------


def ficha_com_fato_fora_do_periodo(textos: list[str]) -> str:
    base = BaseFicha.model_validate_json(json.dumps(ApiFalsa._json(textos, "casa_matriz")))
    depois = str(base.processo.data_ajuizamento + datetime.timedelta(days=10))
    fatos = [{"data": depois, "descricao": "Fato depois do ajuizamento.", "valores": []}]
    return json.dumps(resposta_inicial(base, fatos=fatos), ensure_ascii=False)


def test_ficha_que_falha_casa_vazia_e_peca_descartada(integ: Integracao) -> None:
    preparar_e_abrir_ensaio(integ)
    # A inicial falha sempre: 001 (com o retorno), 002 e 003; depois, casa vazia.
    integ.api.especiais[("ficha", INICIAL)] = [ficha_com_fato_fora_do_periodo] * 6
    # Os embargos são reprovados nas três versões.
    integ.api.especiais[("checklist", EMB)] = [checklist_que_reprova("fundamento")] * 3
    integ.api.especiais[("opus_desempate", EMB)] = [
        lambda textos: json.dumps(
            {
                "itens": [
                    {
                        "item": i["item"],
                        "resposta": "nao_passa" if i["item"] == "fundamento" else "passa",
                        "justificativa": "o dispositivo não sustenta",
                    }
                    for i in ApiFalsa._json(textos, "itens")["itens"]
                ]
            }
        )
    ] * 3
    integ.avancar_ate_parar()

    chamadas_ficha = [c for c in integ.api.chamadas if c[:2] == ("ficha", INICIAL)]
    assert len(chamadas_ficha) == 6  # cada ficha volta ao Haiku uma vez
    for numero in (1, 2):
        assert integ.existe(f"saida/pedidos/{peca(INICIAL, numero)}_ficha_retorno_t1.json")
        assert integ.existe(f"saida/fichas/{peca(INICIAL, numero)}_descartada.json")
    terceira = BaseFicha.model_validate_json(
        integ.arquivos.ler_texto(f"saida/fichas/{peca(INICIAL, 3)}_base.json")
    )
    assert (terceira.casa, terceira.tentativa) == (1, 3)
    vazia = json.loads(integ.arquivos.ler_texto(f"saida/fichas/e01_{INICIAL}_casa01_vazia.json"))
    assert vazia["ultima_peca"] == peca(INICIAL, 3)
    causa = json.loads(integ.arquivos.ler_texto(f"saida/fichas/{peca(INICIAL, 3)}_descartada.json"))
    assert "fato_fora_do_periodo" in causa["causa"]
    assert not integ.arquivos.listar("saida/rascunhos", f"e01_{INICIAL}_*")

    for versao in (1, 2):
        assert integ.veredito(peca(EMB), versao).veredito == "refazer"
    ultima = integ.veredito(peca(EMB), 3)
    assert (ultima.veredito, ultima.categoria_motivo) == ("descartada", "conteudo")
    assert "fundamento" in ultima.motivo
    assert not integ.arquivos.listar("saida/aprovadas", f"e01_{EMB}_*")
    assert not integ.existe(f"saida/rascunhos/{peca(EMB)}_v4.md")
    assert integ.veredito(peca(MAN), 1).veredito == "aprovada"


# ---------------------------------------------------------------------------
# 14. Modelo local indisponível: 72 horas no médio e 7 dias no alto
# ---------------------------------------------------------------------------


def test_modelo_local_indisponivel_72_horas_e_7_dias(integ: Integracao) -> None:
    preparar_e_abrir_ensaio(integ)
    integ.local.disponivel = False
    integ.avancar_ate_parar()
    medio, alto = f"{peca(INICIAL)}_v1", f"{peca(EMB)}_v1"

    def paradas() -> bool:
        return not integ.existe(f"saida/conferencias/{medio}_local.json") and not integ.existe(
            f"saida/conferencias/{alto}_local.json"
        )

    assert paradas()
    integ.relogio.pular(hours=70)  # antes das 72 horas
    integ.avancar_ate_parar()
    assert paradas() and not integ.ocorrencias(estado.SUBSTITUICAO_OPUS)

    integ.relogio.pular(hours=3)  # passadas as 72 horas
    integ.avancar_ate_parar()
    assert integ.veredito(peca(INICIAL), 1).veredito == "aprovada"
    assert [o.peca for o in integ.ocorrencias(estado.SUBSTITUICAO_OPUS)] == [medio]
    caminho = next(c for c in integ.veredito(peca(INICIAL), 1).caminho if c.item == "coerencia")
    assert (caminho.regra, caminho.quem_final) == (
        "médio sem conferente local: vale o Opus",
        "opus",
    )
    assert not integ.existe(f"saida/conferencias/{alto}_local.json")

    # O modelo volta e cai de novo antes de responder: a contagem não zera.
    integ.relogio.pular(days=3)  # 6 dias desde a primeira queda
    integ.local.disponivel, integ.local.falha = True, True
    integ.avancar_ate_parar()
    assert integ.local.envios > 0
    assert not integ.ocorrencias(estado.PAUSA_7_DIAS)
    assert not integ.existe(f"saida/conferencias/{alto}_local.json")
    integ.relogio.pular(days=1, hours=1)  # passados os 7 dias
    integ.avancar_ate_parar()
    assert [o.peca for o in integ.ocorrencias(estado.PAUSA_7_DIAS)] == [alto]
    assert not integ.existe(f"saida/conferencias/{alto}.json")

    # Com o modelo de volta, o avancar seguinte leva a de risco alto ao veredito.
    integ.local.falha = False
    assert integ.executar("avancar") == 0
    assert integ.veredito(peca(EMB), 1).veredito == "aprovada"
    assert integ.veredito(peca(EMB), 1).conferencia_local == "rodou"


# ---------------------------------------------------------------------------
# 15. Semelhança pelo comando fichas
# ---------------------------------------------------------------------------


def test_semelhanca_reprova_a_segunda_peca_igual(integ: Integracao) -> None:
    assert integ.executar("preparar") == 0
    congelamento = Congelamento(integ.arquivos, integ.servicos.registro, integ.relogio)
    agora = integ.relogio()
    integ.arquivos.regravar_rodadas(
        Rodadas(
            rodadas=[
                Rodada(
                    id="e01",
                    semente=5,
                    impressoes=congelamento.impressoes(),
                    ensaio_aprovado_origem=None,
                    estado="encerrada",
                    aberta_em=agora,
                    ensaio_aprovado=True,
                    aprovado_em=agora,
                )
            ]
        )
    )
    assert integ.executar("fichas", "--tipo", MAN, "--semente", "3") == 0
    # A redação devolve o mesmo texto para as duas primeiras peças.
    montada = json.loads(integ.arquivos.ler_texto(f"saida/preparacao/{MAN}_estrutura.json"))
    igual = "\n\n".join(
        f"## {b['titulo']}\n\n" + " ".join(random.Random(n).choices(PALAVRAS, k=30)) + "."
        for n, b in enumerate(montada["blocos"])
    )

    def redacao_registrada(textos: list[str]) -> str:
        integ.api.rascunhos[igual] = integ.api.ficha_da_peca(textos).root.id
        return igual

    integ.api.especiais[("redacao", MAN)] = [redacao_registrada, redacao_registrada]
    integ.avancar_ate_parar()

    primeira, segunda = peca(MAN, 1, "r01"), peca(MAN, 2, "r01")
    assert (
        integ.arquivos.ler_json(f"saida/conferencias/{primeira}_v1.json", Conferencia).veredito
        == "aprovada"
    )
    reprovada = integ.arquivos.ler_json(f"saida/conferencias/{segunda}_v1.json", Conferencia)
    assert (reprovada.veredito, reprovada.categoria_motivo) == ("refazer", "semelhanca")
    assert reprovada.semelhanca == 1.0
    assert not integ.existe(f"saida/aprovadas/{segunda}_v1.md")
    # A semelhança rodou em todas as peças e gravou o valor no veredito.
    for n in range(1, 11):
        nome = peca(MAN, n, "r01")
        assert integ.existe(f"saida/conferencias/{nome}_v1_semelhanca.json"), nome


# ---------------------------------------------------------------------------
# Brief 023. O ensaio inteiro pelos comandos, até `ensaio --fechar`
# ---------------------------------------------------------------------------

CHAVE_FALSA = "sk-ant-chave-falsa-do-teste"


def responder_cartao(pergunta: str) -> str:
    """O responsável falso: formato certo, sem dado real, erro existe e é o do gabarito."""
    if pergunta.startswith("Confirmar"):
        return "s"
    if pergunta.startswith("Dado real"):
        return "n"
    if "citação" in pergunta or "citações" in pergunta:
        return ""
    if "(aprovada ou reprovada)" in pergunta:
        return "a"
    return "s"


def revisar_tudo(integ: Integracao) -> None:
    for _ in range(20):
        if revisao_pendente(integ) is None:
            return
        assert principal.executar(["revisar"], integ.servicos, responder_cartao) == 0
    raise AssertionError("o revisar não terminou os cartões")


def revisao_pendente(integ: Integracao) -> Any:
    from fabrica import revisao

    return revisao.pendente(integ.servicos)


def ensaio_pelos_comandos(integ: Integracao) -> int:
    """Devolve o código de saída de `ensaio --fechar e01`."""
    preparar_e_abrir_ensaio(integ)
    integ.avancar_ate_parar()
    revisar_tudo(integ)  # o cartão do ensaio de cada peça
    assert integ.executar("publicar", "--rodada", "e01") == 0
    for _ in range(8):  # as vagas do Opus, uma rodada de `erros` e `avancar` por vez
        assert integ.executar("erros", "--rodada", "e01") == 0
        if integ.existe("saida/erros/e01_amostras.json"):
            break
        integ.avancar_ate_parar(40)
    assert integ.existe("saida/erros/e01_amostras.json")
    revisar_tudo(integ)  # as amostras
    for _ in range(5):
        assert integ.executar("testar", "--rodada", "e01") == 0
        if integ.existe("saida/relatorios/teste_conferentes_ensaio_e01.json"):
            break
        integ.avancar_ate_parar(40)
    assert integ.existe("saida/relatorios/teste_conferentes_ensaio_e01.json")
    assert integ.executar("relatorio", "--rodada", "e01") == 0
    return integ.executar("ensaio", "--fechar", "e01")


def ensaio_aprovado(integ: Integracao) -> bool:
    lidas = integ.arquivos.ler_json("saida/rodadas.json", Rodadas)
    return next(r for r in lidas.rodadas if r.id == "e01").ensaio_aprovado


def test_ensaio_inteiro_aprovado(
    integ: Integracao, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", CHAVE_FALSA)
    assert ensaio_pelos_comandos(integ) == 0, capsys.readouterr().err
    assert ensaio_aprovado(integ)
    texto = integ.arquivos.ler_texto("saida/relatorios/relatorio_e01.md")
    assert "ensaio: sem valor de medida" in texto
    assert texto.rstrip().splitlines()[-1].startswith("A decisão de escalar é do responsável")
    for tipo in TIPOS:
        assert integ.arquivos.listar(f"saida/pacotes/ensaio_e01/{tipo}", "*.md")
    # A chave falsa não aparece em nenhum arquivo de saida/.
    for caminho in (integ.raiz / "saida").rglob("*"):
        if caminho.is_file():
            assert CHAVE_FALSA not in caminho.read_text("utf-8", errors="ignore"), caminho
    assert integ.tentativas_de_rede == []  # type: ignore[attr-defined]


def test_ensaio_com_resposta_do_opus_fora_do_formato_e_reprovado(
    integ: Integracao, capsys: pytest.CaptureFixture[str]
) -> None:
    integ.api.especiais[("plantar_erro_opus", MAN)] = [lambda textos: "isto não é JSON"]
    assert ensaio_pelos_comandos(integ) == 1
    assert "resposta fora do formato" in capsys.readouterr().err
    assert not ensaio_aprovado(integ)


def test_ensaio_com_pedido_local_acima_de_75_por_cento_e_reprovado(
    integ: Integracao, capsys: pytest.CaptureFixture[str]
) -> None:
    def redacao_longa(textos: list[str]) -> str:
        curto = integ.api._redacao(textos)
        peca_da_redacao = integ.api.rascunhos.pop(curto)
        longo = curto + "\n\n" + " ".join([*PALAVRAS] * 70) + "."
        integ.api.rascunhos[longo] = peca_da_redacao
        return longo

    integ.api.especiais[("redacao", EMB)] = [redacao_longa]
    assert ensaio_pelos_comandos(integ) == 1
    erro = capsys.readouterr().err
    assert "16.384" in erro and "32.768" in erro and "ensaio novo" in erro
    assert integ.ocorrencias(estado.ACIMA_DO_LIMITE)
    assert not ensaio_aprovado(integ)
