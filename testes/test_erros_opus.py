"""Teste de aceite do brief 021: as cópias do Opus e a verificação do Sonnet em
`fabrica/erros_plantados.py`.

O Opus, o Haiku e o Sonnet são falsos (nenhum pedido sai da máquina): o falso
responde pela instrução que abre o pedido, lida de `instrucoes/`. As peças, as
extrações e as fichas são as do ensaio do `test_erros_programa.py`. O Opus falso
troca um trecho conhecido de cada peça; o Haiku falso devolve, para a cópia, a
extração da original; o Sonnet falso aponta o item principal do erro pedido.
"""

from __future__ import annotations

import json
import random
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import anthropic
import pytest

from fabrica import erros_plantados as ep
from fabrica.comum import config
from fabrica.comum.arquivos import Arquivos
from fabrica.comum.formatos import (
    Amostras,
    CatalogoErros,
    Descartada,
    Gabarito,
    Pedido,
    RespostaVerificacao,
    Rodada,
    Rodadas,
)
from fabrica.conferencia.regras import MARCA
from testes.test_conferencia_etapas import EMB, INICIAL, MAN, TIPOS, amb
from testes.test_erros_programa import cartao, gravar_peca, pecas
from testes.test_fichas import RAIZ, Ambiente

__all__ = ["amb", "pecas"]  # as fixtures vêm dos testes dos briefs 017 e 019

GERAL = config.carregar(Arquivos(RAIZ)).geral
CATALOGO = CatalogoErros.model_validate_json((RAIZ / ep.ERROS).read_text("utf-8"))
ENTRADAS = {e.tipo_erro: e for e in CATALOGO.erros}
DO_OPUS = {
    t: [e.tipo_erro for e in CATALOGO.erros if e.origem == "opus" and t in e.tipos] for t in TIPOS
}
PLANTAR = (RAIZ / "instrucoes/plantar_erro.md").read_text("utf-8")
SECAO_OPUS = ep.secao(PLANTAR, ep.TITULO_OPUS)
SECAO_SONNET = ep.secao(PLANTAR, ep.TITULO_SONNET)
EXTRACAO = (RAIZ / "instrucoes/extracao.md").read_text("utf-8")
# O trecho que o Opus falso troca em cada tipo (aparece uma vez no rascunho de exemplo).
TROCAS = {
    INICIAL: ("Requer a citação da parte ré.", "Requer a citação da parte ré, já citada."),
    EMB: ("para suprir a omissão apontada", "para rediscutir o mérito da decisão"),
    MAN: ("no novo endereço indicado", "no mesmo endereço já tentado"),
}


# ---------------------------------------------------------------------------
# Falsos
# ---------------------------------------------------------------------------


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
            "usage": {"input_tokens": 1000, "output_tokens": 100},
        }
    )


Responder = Callable[[str, dict[str, Any]], Any]


class FalsoBanco:
    """Opus, Haiku e Sonnet falsos, escolhidos pela instrução do pedido."""

    def __init__(self, amb: Ambiente) -> None:
        self.amb = amb
        self.originais = {
            amb.arquivos.ler_texto(c): c.removeprefix("saida/rascunhos/").removesuffix("_v1.md")
            for c in amb.arquivos.listar("saida/rascunhos", "*_v1.md")
        }
        self.copias: dict[str, tuple[str, dict[str, Any]]] = {}  # cópia -> (peça, pedido)
        self.chamadas: list[tuple[str, str, str]] = []  # (quem, peça, modelo)
        self.opus: list[Responder] = []
        self.extracao: list[Responder] = []
        self.sonnet: dict[str, list[Any]] = {}  # peça -> fila de respostas do Sonnet
        self.sonnet_padrao: dict[str, Any] = {}  # peça -> resposta fixa do Sonnet
        self.extracao_padrao: Responder | None = None
        self.messages = self

    def count_tokens(self, **argumentos: Any) -> anthropic.types.MessageTokensCount:
        return anthropic.types.MessageTokensCount(input_tokens=1000)

    def create(self, **argumentos: Any) -> anthropic.types.Message:
        textos = [b["text"] for b in argumentos["messages"][0]["content"]]
        modelo = argumentos["model"]
        if textos[0] == SECAO_OPUS:
            texto = self._opus(textos)
        elif textos[0] == EXTRACAO:
            texto = self._extracao(textos)
        elif textos[0] == SECAO_SONNET:
            texto = self._sonnet(textos)
        else:
            raise AssertionError("pedido que o teste não previu")
        return mensagem(texto, modelo)

    def _opus(self, textos: list[str]) -> str:
        pedido, original = json.loads(textos[1]), textos[-1]
        peca = self.originais[original]
        self.chamadas.append(("opus", peca, pedido["tipo_erro"]))
        responder = self.opus.pop(0) if self.opus else padrao_opus
        devolvido = responder(peca, pedido)
        if isinstance(devolvido, dict):
            velho, novo = devolvido["trecho_original"], devolvido["trecho_novo"]
            if original.count(velho) == 1:
                self.copias[original.replace(velho, novo)] = (peca, pedido)
            return json.dumps(devolvido, ensure_ascii=False)
        return str(devolvido)

    def _extracao(self, textos: list[str]) -> str:
        copia = textos[-1]
        peca, pedido = self.copias[copia]
        self.chamadas.append(("haiku", peca, pedido["tipo_erro"]))
        extracao = json.loads(
            self.amb.arquivos.ler_texto(f"saida/conferencias/{peca}_v1_extracao.json")
        )
        responder = self.extracao.pop(0) if self.extracao else self.extracao_padrao
        if responder is not None:
            return str(responder(peca, extracao))
        return json.dumps(extracao, ensure_ascii=False)

    def _sonnet(self, textos: list[str]) -> str:
        dados = json.loads(textos[-1])
        peca, pedido = self.copias[dados["copia"]]
        assert self.originais[dados["original"]] == peca
        self.chamadas.append(("sonnet", peca, pedido["tipo_erro"]))
        fila = self.sonnet.get(peca)
        resposta = fila.pop(0) if fila else self.sonnet_padrao.get(peca)
        if resposta is None:
            resposta = verificacao(ENTRADAS[pedido["tipo_erro"]].item_principal)
        return resposta if isinstance(resposta, str) else json.dumps(resposta, ensure_ascii=False)


def padrao_opus(peca: str, pedido: dict[str, Any]) -> dict[str, str]:
    tipo = next(t for t in TIPOS if f"_{t}_" in peca)
    velho, novo = TROCAS[tipo]
    return {"trecho_original": velho, "trecho_novo": novo}


def verificacao(item: str | None, outro: bool = False) -> dict[str, Any]:
    return {
        "item_apontado": item,
        "descricao_erro": "a troca muda o trecho" if item else "não achei erro",
        "outro_problema": outro,
        "descricao_outro_problema": "frase truncada" if outro else None,
    }


@pytest.fixture
def banco(pecas: Ambiente) -> tuple[Ambiente, FalsoBanco]:
    # Sem os pedidos de ficha, o `avancar` só vê as cópias do banco.
    for caminho in pecas.arquivos.listar("saida/pedidos", "*_ficha_t1.json"):
        (pecas.raiz / caminho).unlink()
    falso = FalsoBanco(pecas)
    pecas.cliente.messages = falso  # type: ignore[assignment]
    return pecas, falso


def rodar(amb: Ambiente, rodada: str = "e01") -> None:
    """`erros` e `avancar` alternados até o sorteio das amostras."""
    for _ in range(12):
        assert amb.executar("erros", "--rodada", rodada) == 0
        if amb.arquivos.existe(f"saida/erros/{rodada}_amostras.json"):
            return
        assert amb.executar("avancar") == 0
    raise AssertionError("as vagas não se resolveram")


def peca(tipo: str) -> str:
    return f"e01_{tipo}_001"


def gabarito(amb: Ambiente, nome: str) -> Gabarito:
    return amb.arquivos.ler_json(f"saida/erros/{nome}_gabarito.json", Gabarito)


def descartada(amb: Ambiente, nome: str) -> Descartada:
    return amb.arquivos.ler_json(f"saida/erros/{nome}_descartada.json", Descartada)


def pedido(amb: Ambiente, nome: str, tarefa: str) -> Pedido:
    return amb.arquivos.ler_json(f"saida/pedidos/{nome}_banco_v1_{tarefa}_t1.json", Pedido)


def amostras(amb: Ambiente, rodada: str = "e01") -> Amostras:
    return amb.arquivos.ler_json(f"saida/erros/{rodada}_amostras.json", Amostras)


# ---------------------------------------------------------------------------
# 1. Vagas, plano B e sorteio dos tipos
# ---------------------------------------------------------------------------


def lista(n: int, tipos: tuple[str, ...] = TIPOS, rodada: str = "r01") -> list[tuple[str, str]]:
    return [
        (f"{rodada}_{tipos[i % len(tipos)]}_{i + 1:03d}", tipos[i % len(tipos)]) for i in range(n)
    ]


@pytest.mark.parametrize(
    ("boas", "situacao", "por_peca"),
    [
        (25, "normal", 4),
        (20, "normal", 4),
        (19, "faixa_media", 6),
        (14, "faixa_media", 6),
        (13, "inconclusivo", 0),
        (1, "inconclusivo", 0),
    ],
)
def test_vagas_pelo_plano_b(boas: int, situacao: str, por_peca: int) -> None:
    plano = ep.planejar("r01", 7, lista(boas), DO_OPUS, GERAL)
    assert (plano.situacao, plano.pecas_boas) == (situacao, boas)
    assert len(plano.vagas) == boas * por_peca
    for nome, tipo in lista(boas):
        vagas = [v for v in plano.vagas if v.peca == nome]
        assert [v.k for v in vagas] == list(range(2, por_peca + 2))
        assert len({v.tipo_erro for v in vagas}) == por_peca  # tipos diferentes entre si
        assert all(v.tipo_erro in DO_OPUS[tipo] and v.tipo == tipo for v in vagas)
        assert sum(v.sutil for v in vagas) == por_peca // 2  # metade sutis


def test_ensaio_uma_vaga_por_peca() -> None:
    plano = ep.planejar("e01", 7, lista(3, rodada="e01"), DO_OPUS, GERAL)
    assert plano.situacao == "ensaio"
    assert [v.k for v in plano.vagas] == [2, 2, 2]
    assert sum(v.sutil for v in plano.vagas) == 1  # metade de 3, arredondada para baixo


def test_sorteio_equilibra_os_tipos_e_repete_com_a_semente() -> None:
    pecas_ = lista(20, (INICIAL,))
    plano = ep.planejar("r01", 7, pecas_, DO_OPUS, GERAL)
    contagem = Counter(v.tipo_erro for v in plano.vagas)
    assert set(contagem) == set(DO_OPUS[INICIAL])
    assert max(contagem.values()) - min(contagem.values()) <= 1
    for tipo_erro in contagem:
        sutis = sum(v.sutil for v in plano.vagas if v.tipo_erro == tipo_erro)
        assert abs(2 * sutis - contagem[tipo_erro]) <= 1  # sutil e direto equilibrados
    assert ep.planejar("r01", 7, pecas_, DO_OPUS, GERAL) == plano
    assert any(ep.planejar("r01", s, pecas_, DO_OPUS, GERAL) != plano for s in range(8, 12))
    # Os três tipos juntos: o sorteio equilibra no conjunto.
    misto = ep.planejar("r01", 3, lista(21), DO_OPUS, GERAL)
    contagem = Counter(v.tipo_erro for v in misto.vagas)
    assert max(contagem.values()) - min(contagem.values()) <= 2


def rodada_com_boas(amb: Ambiente, boas: int) -> None:
    arquivos = amb.arquivos
    lidas = arquivos.ler_json("saida/rodadas.json", Rodadas).rodadas
    r01 = Rodada.model_validate_json(
        lidas[0].model_copy(update={"id": "r01", "ensaio_aprovado_origem": "e01"}).model_dump_json()
    )
    arquivos.regravar_rodadas(Rodadas(rodadas=[*lidas, r01]))
    for n in range(1, boas + 1):
        nome = f"r01_{INICIAL}_{n:03d}"
        for sufixo in (".json", "_base.json"):
            origem = amb.raiz / f"saida/fichas/e01_{INICIAL}_001{sufixo}"
            (amb.raiz / f"saida/fichas/{nome}{sufixo}").write_text(origem.read_text("utf-8"))
        gravar_peca(amb, INICIAL, nome)
        cartao(amb, nome, "aprovada", "aprovada")


def test_menos_de_14_boas_e_inconclusivo_sem_pedido(banco: tuple[Ambiente, FalsoBanco]) -> None:
    amb, falso = banco
    rodada_com_boas(amb, 2)
    assert amb.executar("erros", "--rodada", "r01") == 0
    assert amb.arquivos.listar("saida/pedidos", "r01_*copia_com_erro*") == []
    assert any(
        o.causa == ep.INCONCLUSIVO and o.rodada == "r01"
        for o in amb.servicos.registro.ocorrencias()
    )
    assert amb.executar("avancar") == 0
    assert falso.chamadas == []
    assert not amb.arquivos.existe("saida/erros/r01_amostras.json")
    # A cópia por programa (019) continua.
    assert amb.arquivos.existe(f"saida/erros/r01_{INICIAL}_001_erro1_1.md")


# ---------------------------------------------------------------------------
# 2. A troca feita pelo programa e a conferência de programa
# ---------------------------------------------------------------------------

ORIGINAL = (
    f"{MARCA}\n\n## Fatos\n\nA parte autora contratou o serviço em março.\n\n"
    "## Fundamentos\n\nO fornecedor responde pelos danos causados ao consumidor.\n\n"
    "## Pedidos\n\nRequer a condenação da parte ré ao pagamento da indenização pedida.\n"
)


def test_troca_feita_pelo_programa() -> None:
    fracao = GERAL.erros.fracao_maxima_regiao
    certa = ep.trocar(
        ORIGINAL, "contratou o serviço em março", "contratou o serviço em maio", fracao
    )
    assert certa.falha is None and certa.texto is not None
    assert certa.texto == ORIGINAL.replace("em março", "em maio")
    i = ORIGINAL.index("contratou")
    assert certa.texto[:i] == ORIGINAL[:i]
    assert certa.texto.endswith(ORIGINAL[i + len("contratou o serviço em março") :])
    casos = {
        "não aparece": ("contratou o produto", "x"),
        "mais de uma vez": ("parte", "pessoa"),
        "vazio": ("", "algo"),
        "sem mudança": ("em março", "em março"),
        "duas regiões": (
            "em março.\n\n## Fundamentos\n\nO fornecedor responde",
            "em maio.\n\n## Fundamentos\n\nO fabricante responde",
        ),
        "mais de um quarto": (
            "O fornecedor responde pelos danos causados ao consumidor.",
            "Texto novo e longo. " * 12,
        ),
    }
    for caso, (velho, novo) in casos.items():
        troca = ep.trocar(ORIGINAL, velho, novo, fracao)
        assert troca.texto is None and troca.falha, caso


def test_trecho_que_nao_aparece_descarta_na_conferencia_de_programa(
    banco: tuple[Ambiente, FalsoBanco],
) -> None:
    amb, falso = banco
    # O primeiro pedido (embargos, na ordem das peças) devolve um trecho que não está na peça.
    falso.opus = [lambda p, d: {"trecho_original": "trecho que não existe", "trecho_novo": "x"}]
    rodar(amb)
    nome = f"{peca(EMB)}_erro2_1"
    d = descartada(amb, nome)
    assert (d.conferencia_que_falhou, d.motivo, d.item_apontado_pelo_verificador) == (
        "programa",
        None,
        None,
    )
    assert (d.criador, d.original) == ("opus", f"{peca(EMB)}_v1")
    assert not amb.arquivos.existe(f"saida/erros/{nome}.md")
    # Nada foi pedido ao Haiku nem ao Sonnet para a descartada; a refação foi aceita.
    assert [c[0] for c in falso.chamadas if c[1] == peca(EMB)] == [
        "opus",
        "opus",
        "haiku",
        "sonnet",
    ]
    assert gabarito(amb, f"{peca(EMB)}_erro2_2").tipo_erro == d.tipo_erro


def test_programa_reprova_item_fora_dos_aceitos(banco: tuple[Ambiente, FalsoBanco]) -> None:
    amb, falso = banco

    def juizo_errado(p: str, extracao: dict[str, Any]) -> str:
        return json.dumps({**extracao, "juizo": "Juízo que não é o da ficha"}, ensure_ascii=False)

    falso.extracao_padrao = juizo_errado  # `coerencia_ficha` reprova em toda cópia
    rodar(amb)
    gabaritos = [
        gabarito(amb, c.removesuffix("_gabarito.json").removeprefix("saida/erros/"))
        for c in amb.arquivos.listar("saida/erros", "e01_*_erro2_*_gabarito.json")
    ]
    descartes = [
        Descartada.model_validate_json((amb.raiz / c).read_text("utf-8"))
        for c in amb.arquivos.listar("saida/erros", "e01_*_erro2_*_descartada.json")
    ]
    assert descartes, "algum erro pedido não aceita coerencia_ficha"
    for d in descartes:
        assert (d.conferencia_que_falhou, d.motivo) == ("programa", None)
        assert "coerencia_ficha" not in ENTRADAS[d.tipo_erro].itens_aceitos
        assert amb.arquivos.existe(f"saida/erros/{d.copia}.md")  # a cópia existe; o resto, não
    for g in gabaritos:
        assert "coerencia_ficha" in g.itens_aceitos
    # Só as cópias que passaram na conferência de programa foram ao Sonnet.
    assert sum(c[0] == "sonnet" for c in falso.chamadas) == len(gabaritos)


# ---------------------------------------------------------------------------
# 2 e 3. O caminho inteiro no ensaio: pedidos, troca, extração, Sonnet e gabarito
# ---------------------------------------------------------------------------


def test_ensaio_as_tres_copias_aceitas(banco: tuple[Ambiente, FalsoBanco]) -> None:
    amb, falso = banco
    rodar(amb)
    arquivos = amb.arquivos
    gasto = amb.servicos.gasto
    plano = ep.plano_da_rodada("e01", amb.servicos)
    assert sum(v.sutil for v in plano.vagas) == 1
    for vaga in plano.vagas:
        nome = f"{vaga.peca}_erro2_1"
        original = arquivos.ler_texto(f"saida/rascunhos/{vaga.peca}_v1.md")
        velho, novo = TROCAS[vaga.tipo]
        copia = arquivos.ler_texto(f"saida/erros/{nome}.md")
        assert copia == original.replace(velho, novo) and copia.splitlines()[0] == MARCA
        g = gabarito(amb, nome)
        entrada = ENTRADAS[vaga.tipo_erro]
        assert (g.copia, g.original, g.origem, g.criador) == (
            nome,
            f"{vaga.peca}_v1",
            "opus",
            "opus",
        )
        assert (g.tipo_erro, g.sutil) == (vaga.tipo_erro, vaga.sutil)
        assert (g.item_principal, g.itens_aceitos) == (
            entrada.item_principal,
            entrada.itens_aceitos,
        )
        assert g.item_apontado_pelo_verificador == entrada.item_principal
        assert g.verificador == gasto.modelo_da_tarefa("verificacao_copia") and g.amostra is None
        # Pedido ao Opus: a instrução lida do arquivo, o erro pedido e a original.
        p = pedido(amb, nome, "copia_com_erro")
        assert (p.tarefa, p.modelo, p.formato) == (
            "copia_com_erro",
            gasto.modelo_da_tarefa("copia_com_erro"),
            "RespostaCopiaOpus",
        )
        assert [x.nome for x in p.partes] == ["instrucoes", "estrutura", "conteudo"]
        assert p.partes[0].texto == SECAO_OPUS and p.partes[2].texto == original
        erro = json.loads(p.partes[1].texto)
        assert (erro["tipo_erro"], erro["sutil"]) == (vaga.tipo_erro, vaga.sutil)
        # Extração da cópia: mesma instrução e mesma tarefa da extração (017).
        p = pedido(amb, nome, "extracao")
        assert p.partes[0].texto == EXTRACAO and p.partes[-1].texto == copia
        assert p.modelo == gasto.modelo_da_tarefa("extracao")
        # Sonnet: a original e a cópia, sem o erro pedido, e só os itens do tipo.
        p = pedido(amb, nome, "verificacao_copia")
        assert (p.tarefa, p.modelo, p.formato) == (
            "verificacao_copia",
            gasto.modelo_da_tarefa("verificacao_copia"),
            "RespostaVerificacao",
        )
        assert p.partes[0].texto == SECAO_SONNET
        itens = [i["item"] for i in json.loads(p.partes[1].texto)["itens"]]
        catalogo = ep.material(ep.ref_da_peca("e01", vaga.peca), amb.servicos).catalogo
        assert itens == [i for i in catalogo.itens_conferencia if i not in ("semelhanca", "marca")]
        assert json.loads(p.partes[-1].texto) == {"original": original, "copia": copia}
        enviado = "\n".join(x.texto for x in p.partes)
        assert entrada.descricao not in enviado and '"tipo_erro"' not in enviado
    a = amostras(amb)
    assert sorted(a.copias) == sorted(f"{v.peca}_erro2_1" for v in plano.vagas)
    assert a.descartadas == [] and a.rodada == "e01"
    assert [c[0] for c in falso.chamadas].count("opus") == 3 and len(falso.chamadas) == 9
    # Nenhum arquivo fora de saida/.
    assert not any(Path(c).parts[0] != "saida" for c in arquivos.listar("saida", "**/*"))
    # Retomável: rodar de novo não pede nada nem muda o sorteio.
    antes = amostras(amb)
    assert amb.executar("erros", "--rodada", "e01") == 0 and amb.executar("avancar") == 0
    assert amostras(amb) == antes and len(falso.chamadas) == 9


# ---------------------------------------------------------------------------
# 3 e 4. O Sonnet decide; o programa dá o motivo
# ---------------------------------------------------------------------------


def resposta(item: str | None, outro: bool) -> RespostaVerificacao:
    return RespostaVerificacao.model_validate_json(json.dumps(verificacao(item, outro)))


def test_motivo_do_descarte_por_programa() -> None:
    aceitos = ["cabimento", "pedidos"]
    assert ep.motivo_do_descarte(resposta(None, False), aceitos) == "nao_viu_erro"
    assert ep.motivo_do_descarte(resposta(None, True), aceitos) == "nao_viu_erro"
    assert ep.motivo_do_descarte(resposta("cabimento", True), aceitos) == "outro_problema"
    assert ep.motivo_do_descarte(resposta("legitimidade", True), aceitos) == "outro_problema"
    assert ep.motivo_do_descarte(resposta("legitimidade", False), aceitos) == "outro_item"
    assert ep.motivo_do_descarte(resposta("pedidos", False), aceitos) is None  # passa


def test_sonnet_decide_e_a_descartada_e_refeita(banco: tuple[Ambiente, FalsoBanco]) -> None:
    amb, falso = banco
    plano = {v.tipo: v for v in ep.plano_da_rodada("e01", amb.servicos).vagas}
    fora = {
        t: next(
            i
            for i in ("estrutura", "dado_real")
            if i not in ENTRADAS[plano[t].tipo_erro].itens_aceitos
        )
        for t in TIPOS
    }
    falso.sonnet = {
        peca(EMB): [verificacao(None, True)],
        peca(MAN): [verificacao(ENTRADAS[plano[MAN].tipo_erro].item_principal, True)],
        peca(INICIAL): [verificacao(fora[INICIAL])],
    }
    rodar(amb)
    esperado = {
        EMB: ("nao_viu_erro", None, True),
        MAN: ("outro_problema", ENTRADAS[plano[MAN].tipo_erro].item_principal, True),
        INICIAL: ("outro_item", fora[INICIAL], False),
    }
    for tipo, (motivo, item, outro) in esperado.items():
        d = descartada(amb, f"{peca(tipo)}_erro2_1")
        assert (d.conferencia_que_falhou, d.motivo) == ("verificador", motivo)
        assert (d.item_apontado_pelo_verificador, d.outro_problema) == (item, outro)
        assert (d.tipo_erro, d.sutil, d.criador) == (
            plano[tipo].tipo_erro,
            plano[tipo].sutil,
            "opus",
        )
        # Refeita uma vez, com o mesmo tipo de erro, e aceita.
        g = gabarito(amb, f"{peca(tipo)}_erro2_2")
        assert (g.tipo_erro, g.sutil) == (plano[tipo].tipo_erro, plano[tipo].sutil)
    a = amostras(amb)
    assert sorted(a.copias) == sorted(f"{peca(t)}_erro2_2" for t in TIPOS)
    assert a.descartadas == [f"{peca(EMB)}_erro2_1"]  # só a de nao_viu_erro


def test_segunda_falha_troca_o_tipo_e_custo_a_parte(banco: tuple[Ambiente, FalsoBanco]) -> None:
    amb, falso = banco
    plano = {v.tipo: v for v in ep.plano_da_rodada("e01", amb.servicos).vagas}
    # Embargos: as duas tentativas do tipo sorteado falham; a vaga troca de tipo e passa.
    falso.sonnet = {peca(EMB): [verificacao(None), verificacao(None)]}
    # Manifestação: o Sonnet nunca vê erro; a vaga fica perdida depois da troca.
    falso.sonnet_padrao = {peca(MAN): verificacao(None)}
    rodar(amb)
    primeiro = plano[EMB].tipo_erro
    assert descartada(amb, f"{peca(EMB)}_erro2_1").tipo_erro == primeiro
    assert descartada(amb, f"{peca(EMB)}_erro2_2").tipo_erro == primeiro
    novo = gabarito(amb, f"{peca(EMB)}_erro2_3")
    assert novo.tipo_erro != primeiro and novo.tipo_erro in DO_OPUS[EMB]
    assert novo.sutil == plano[EMB].sutil
    for t in (1, 2, 3, 4):
        assert amb.arquivos.existe(f"saida/erros/{peca(MAN)}_erro2_{t}_descartada.json")
    assert not amb.arquivos.existe(f"saida/erros/{peca(MAN)}_erro2_5.md")
    resumo = ep.resumo_do_banco("e01", amb.servicos)
    assert (resumo.vagas, resumo.aceitas, resumo.perdidas, resumo.pendentes) == (3, 2, 1, 0)
    assert resumo.trocaram_de_tipo == 2 and resumo.descartadas == 6
    # O custo de cada descartada fica marcado à parte no registro.
    chamadas = amb.servicos.registro.chamadas()
    marcas = [o for o in amb.servicos.registro.ocorrencias() if o.causa == ep.CUSTO_DESCARTADA]
    assert len(marcas) == 6
    for o in marcas:
        assert o.peca is not None
        custo = sum(
            c.custo_milionesimos for c in chamadas if c.peca == f"{o.peca}{ep.SUFIXO_BANCO}"
        )
        assert custo > 0 and o.detalhe.startswith(f"{custo} ")
    a = amostras(amb)
    assert sorted(a.copias) == sorted([f"{peca(EMB)}_erro2_3", f"{peca(INICIAL)}_erro2_1"])
    assert len(a.descartadas) == 1  # no ensaio, até 1 das de nao_viu_erro
    assert descartada(amb, a.descartadas[0]).motivo == "nao_viu_erro"


def test_resposta_fora_do_formato_duas_vezes_descarta(banco: tuple[Ambiente, FalsoBanco]) -> None:
    amb, falso = banco
    falso.opus = [lambda p, d: "isto não é JSON", lambda p, d: "nem isto"]
    rodar(amb)
    d = descartada(amb, f"{peca(EMB)}_erro2_1")
    assert (d.conferencia_que_falhou, d.motivo) == ("programa", None)
    assert gabarito(amb, f"{peca(EMB)}_erro2_2").criador == "opus"


# ---------------------------------------------------------------------------
# 6. As amostras
# ---------------------------------------------------------------------------


def test_sorteio_das_amostras() -> None:
    a = GERAL.amostras
    aceitas = [f"c{i:02d}" for i in range(30)]
    nao_viu = [f"d{i}" for i in range(8)]
    copias, descartes = ep.sortear_amostras("r01", 7, aceitas, nao_viu, a)
    assert len(copias) == a.copias_aceitas == 10 and set(copias) <= set(aceitas)
    assert len(descartes) == a.descartadas_nao_viu_erro == 5 and set(descartes) <= set(nao_viu)
    assert ep.sortear_amostras("r01", 7, aceitas, nao_viu, a) == (copias, descartes)
    assert ep.sortear_amostras("r01", 7, aceitas, nao_viu[:3], a)[1] == sorted(nao_viu[:3])
    assert ep.sortear_amostras("r01", 7, aceitas[:4], [], a) == (sorted(aceitas[:4]), [])
    # Ensaio: todas as aceitas, até 3, e até 1 descartada.
    copias, descartes = ep.sortear_amostras("e01", 7, aceitas[:2], nao_viu, a)
    assert copias == aceitas[:2] and len(descartes) == 1
    copias, _ = ep.sortear_amostras("e01", 7, aceitas[:5], [], a)
    assert len(copias) == 3 and set(copias) <= set(aceitas[:5])


def test_amostras_so_depois_de_resolvidas_todas_as_vagas(
    banco: tuple[Ambiente, FalsoBanco],
) -> None:
    amb, falso = banco
    assert amb.executar("erros", "--rodada", "e01") == 0
    # Os pedidos ao Opus estão gravados, mas ninguém coletou: nada de sorteio.
    assert len(amb.arquivos.listar("saida/pedidos", "e01_*_banco_v1_copia_com_erro_t1.json")) == 3
    assert falso.chamadas == []
    assert ep.gravar_amostras("e01", amb.servicos) is None
    assert not amb.arquivos.existe("saida/erros/e01_amostras.json")
    rodar(amb)
    assert amostras(amb).copias


# ---------------------------------------------------------------------------
# 7. Nenhum texto da instrução no código
# ---------------------------------------------------------------------------


def test_frase_de_plantar_erro_nao_esta_no_codigo() -> None:
    assert SECAO_OPUS.startswith(f"# {ep.TITULO_OPUS}") and ep.TITULO_SONNET not in SECAO_OPUS
    assert SECAO_SONNET.startswith(f"# {ep.TITULO_SONNET}")
    frases = [f.strip() for f in PLANTAR.replace("\n", " ").split(".") if len(f.strip()) > 40]
    assert len(frases) >= 10
    codigo = "\n".join(p.read_text("utf-8") for p in (RAIZ / "fabrica").rglob("*.py"))
    for frase in frases:
        assert frase not in codigo, frase


def test_semente_das_vagas_nao_depende_da_ordem_de_entrada() -> None:
    pecas_ = lista(20)
    embaralhadas = list(pecas_)
    random.Random(1).shuffle(embaralhadas)
    assert ep.planejar("r01", 7, embaralhadas, DO_OPUS, GERAL) == ep.planejar(
        "r01", 7, pecas_, DO_OPUS, GERAL
    )
