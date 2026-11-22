"""Teste de aceite do brief 022: `fabrica/teste_conferentes.py` e o comando `testar`.

Banco, respostas das amostras e conferências falsas, escritos aqui numa pasta
temporária: as cópias e os gabaritos no formato do 019 e do 021, as respostas das
amostras no formato do 020 e os vereditos do teste no formato da decisão (018).
Nenhum modelo é chamado.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fabrica import __main__ as principal
from fabrica import estado
from fabrica import teste_conferentes as tc
from fabrica.comum.formatos import (
    Amostras,
    Conferencia,
    Descartada,
    Gabarito,
    Pedido,
    RespostasCartao,
    ResultadoTeste,
)
from fabrica.conferencia import extracao, local, semelhanca
from fabrica.conferencia.regras import MARCA
from fabrica.estado import RefPeca
from testes.test_conferencia_etapas import MAN, amb
from testes.test_fichas import RAIZ, Ambiente, preparar

__all__ = ["amb"]  # a fixture vem do teste do brief 017

INICIAL = "peticao_inicial_jec"
R = "r01"
A = f"{R}_{INICIAL}_001"  # original sem problema
B = f"{R}_{INICIAL}_002"  # original que já reprova em `cabimento`
ITENS = ("cabimento", "pedidos", "legitimidade", "coerencia_ficha", "fundamento")


# ---------------------------------------------------------------------------
# Banco falso
# ---------------------------------------------------------------------------


@pytest.fixture
def sint(tmp_path: Path) -> Ambiente:
    return Ambiente(preparar(tmp_path))


def gravar(amb_: Ambiente, caminho: str, texto: str) -> None:
    destino = amb_.raiz / caminho
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, "utf-8")


def original(amb_: Ambiente, peca: str) -> None:
    gravar(amb_, f"saida/rascunhos/{peca}_v1.md", f"{MARCA}\n\n## Fatos\n\nTexto de {peca}.\n")


def gabarito(
    amb_: Ambiente,
    copia: str,
    origem: str = "opus",
    tipo_erro: str = "cabimento",
    aceitos: tuple[str, ...] = ("cabimento", "pedidos"),
    sutil: bool = False,
) -> None:
    gravar(amb_, f"saida/erros/{copia}.md", f"{MARCA}\n\n## Fatos\n\nCópia {copia}.\n")
    dados = {
        "copia": copia,
        "original": f"{copia.split('_erro')[0]}_v1",
        "origem": origem,
        "tipo_erro": tipo_erro,
        "sutil": sutil,
        "item_principal": aceitos[0],
        "itens_aceitos": list(aceitos),
        "criador": "opus" if origem == "opus" else "programa",
        "verificador": "claude-sonnet-5-5" if origem == "opus" else None,
        "item_apontado_pelo_verificador": aceitos[0] if origem == "opus" else None,
        "amostra": None,
    }
    gravar(amb_, f"saida/erros/{copia}_gabarito.json", json.dumps(dados))


def descarte(amb_: Ambiente, copia: str, motivo: str | None = "nao_viu_erro") -> None:
    gravar(amb_, f"saida/erros/{copia}.md", f"{MARCA}\n\nDescartada {copia}.\n")
    dados = {
        "copia": copia,
        "original": f"{copia.split('_erro')[0]}_v1",
        "tipo_erro": "legitimidade",
        "sutil": True,
        "criador": "opus",
        "conferencia_que_falhou": "verificador",
        "item_apontado_pelo_verificador": None,
        "outro_problema": False,
        "motivo": motivo,
        "amostra": None,
    }
    gravar(amb_, f"saida/erros/{copia}_descartada.json", json.dumps(dados))


def sorteio(amb_: Ambiente, rodada: str, copias: list[str], descartadas: list[str]) -> None:
    dados = {
        "rodada": rodada,
        "copias": copias,
        "descartadas": descartadas,
        "sorteado_em": "2026-11-21T12:00:00+00:00",
    }
    gravar(amb_, f"saida/erros/{rodada}_amostras.json", json.dumps(dados))


def responder(amb_: Ambiente, identificador: str, tipo: str, amostra: list[dict[str, Any]]) -> None:
    dados = {
        "id_cartao": identificador,
        "tipo_cartao": tipo,
        "veredito_ficha": None,
        "veredito_peca": None,
        "dado_real": False,
        "dado_real_trecho": None,
        "citacoes_nao_resolvidas": [],
        "formato_certo": None,
        "formato_errado": None,
        "amostra": amostra,
        "data_confirmacao": "2026-11-21T13:00:00+00:00",
    }
    RespostasCartao.model_validate_json(json.dumps(dados))
    gravar(amb_, f"saida/cartoes/{identificador}_respostas.json", json.dumps(dados))


def resp_copia(copia: str, existe: bool = True, do_gabarito: bool | None = True) -> dict[str, Any]:
    return {"copia": copia, "erro_existe": existe, "erro_do_gabarito": do_gabarito}


def resp_descartada(copia: str, existe: bool) -> dict[str, Any]:
    return {"copia": copia, "erro_existe": existe, "erro_do_gabarito": None}


def responder_amostras(
    amb_: Ambiente, rodada: str, copias: list[dict[str, Any]], descartadas: list[dict[str, Any]]
) -> None:
    responder(amb_, f"{rodada}_amostra_copias", "amostra_copias", copias)
    responder(amb_, f"{rodada}_amostra_descartadas", "amostra_descartadas", descartadas)


# ---------------------------------------------------------------------------
# Conferências falsas do teste
# ---------------------------------------------------------------------------


def item(nome: str, final: str, *respostas: tuple[str, str]) -> dict[str, Any]:
    respostas = respostas or (("haiku", final),)
    return {
        "item": nome,
        "respostas": [
            {"item": nome, "resposta": r, "quem": q, "trecho": "", "divergencias": []}
            for q, r in respostas
        ],
        "regra": "falsa",
        "resposta_final": final,
        "quem_final": respostas[-1][0],
    }


def veredito(
    amb_: Ambiente, nome: str, final: str, caminho: dict[str, dict[str, Any]] | None = None
) -> None:
    caminho = caminho or {}
    itens = [caminho.get(i, item(i, "passa")) for i in ITENS]
    reprova = any(c["resposta_final"] == "nao_passa" for c in itens)
    assert (final != "aprovada") == reprova, "conferência falsa incoerente"
    dados = {
        "peca": f"{tc.PREFIXO}{nome}",
        "versao": 1,
        "extracao": None,
        "itens": [r for c in itens for r in c["respostas"]],
        "caminho": itens,
        "notas_estilo": None,
        "alertas": [],
        "veredito": final,
        "categoria_motivo": None if final == "aprovada" else "conteudo",
        "motivo": "" if final == "aprovada" else "falso",
        "semelhanca": None,
        "conferencia_local": None,
        "modo_teste": True,
    }
    gravar(amb_, f"saida/conferencias/{tc.PREFIXO}{nome}_v1.json", json.dumps(dados))


def formato(amb_: Ambiente, nome: str) -> None:
    gravar(amb_, f"saida/conducao/{tc.PREFIXO}{nome}_v1_destino.txt", f"{estado.COPIA_NAO_PEGA}\n")


# Cópias do banco da rodada r01 (o nome diz o que a conferência falsa faz com ela).
IA = {
    "c_haiku": f"{A}_erro2_1",  # pega pelo Haiku: conta com e sem o Opus
    "c_opus": f"{A}_erro3_1",  # pega só pelo Opus
    "c_outro": f"{A}_erro4_1",  # reprovada por item fora dos aceitos: não conta
    "c_orig": f"{B}_erro2_1",  # o item aceito já reprova na original: não conta
    "c_formato": f"{A}_erro5_1",  # terminou na categoria formato: não pega, listada
    "c_aprov": f"{B}_erro3_1",  # aprovada: não pega
}
JULG = [f"{A}_erro1_1", f"{B}_erro1_1"]  # funcao_trocada: uma pega
REGRA = f"{R}_{INICIAL}_003_erro1_1"  # valor_trocado: pega pelo programa
C = f"{R}_{INICIAL}_003"


def montar_banco(amb_: Ambiente) -> None:
    for p in (A, B, C):
        original(amb_, p)
    for copia in IA.values():
        gabarito(amb_, copia)
    gabarito(amb_, JULG[0], "programa_julgamento", "funcao_trocada", ("fundamento",))
    gabarito(amb_, JULG[1], "programa_julgamento", "funcao_trocada", ("fundamento",))
    gabarito(amb_, REGRA, "programa_regra", "valor_trocado", ("coerencia_ficha",))
    descarte(amb_, f"{B}_erro4_1")
    sorteio(amb_, R, [IA["c_haiku"], IA["c_opus"]], [f"{B}_erro4_1"])


def responder_tudo(amb_: Ambiente) -> None:
    responder_amostras(
        amb_,
        R,
        [resp_copia(IA["c_haiku"]), resp_copia(IA["c_opus"])],
        [resp_descartada(f"{B}_erro4_1", False)],
    )


def conferir_tudo(amb_: Ambiente) -> None:
    nao = "nao_passa"
    veredito(amb_, A, "aprovada")
    veredito(amb_, B, "refazer", {"cabimento": item("cabimento", nao)})
    veredito(amb_, C, "aprovada")
    veredito(amb_, IA["c_haiku"], "refazer", {"cabimento": item("cabimento", nao, ("haiku", nao))})
    veredito(
        amb_,
        IA["c_opus"],
        "refazer",
        {"pedidos": item("pedidos", nao, ("haiku", "passa"), ("local", "passa"), ("opus", nao))},
    )
    veredito(amb_, IA["c_outro"], "refazer", {"legitimidade": item("legitimidade", nao)})
    veredito(amb_, IA["c_orig"], "refazer", {"cabimento": item("cabimento", nao)})
    formato(amb_, IA["c_formato"])
    veredito(amb_, IA["c_aprov"], "aprovada")
    veredito(amb_, JULG[0], "refazer", {"fundamento": item("fundamento", nao, ("haiku", nao))})
    veredito(amb_, JULG[1], "aprovada")
    veredito(
        amb_,
        REGRA,
        "descartada",
        {"coerencia_ficha": item("coerencia_ficha", nao, ("programa", nao))},
    )


def resultado(amb_: Ambiente) -> ResultadoTeste:
    return amb_.arquivos.ler_json(tc.caminho_relatorio(R), ResultadoTeste)


# ---------------------------------------------------------------------------
# 1. Sem as duas amostras respondidas, `testar` recusa
# ---------------------------------------------------------------------------


def test_recusa_sem_as_amostras_respondidas(
    sint: Ambiente, capsys: pytest.CaptureFixture[str]
) -> None:
    assert sint.executar("testar") == 2
    montar_banco(sint)
    assert sint.executar("testar", "--rodada", R) == 1
    erro = capsys.readouterr().err
    assert "amostra de 10 cópias" in erro and "amostra das descartadas" in erro
    responder(sint, f"{R}_amostra_copias", "amostra_copias", [resp_copia(IA["c_haiku"])])
    assert sint.executar("testar", "--rodada", R) == 1
    erro = capsys.readouterr().err
    assert "amostra das descartadas" in erro and "amostra de 10 cópias" not in erro
    assert not sint.arquivos.existe(f"saida/erros/{R}_gabarito.json")
    # Sem o sorteio das amostras (o 021 não terminou), também recusa.
    (sint.raiz / f"saida/erros/{R}_amostras.json").unlink()
    assert sint.executar("testar", "--rodada", R) == 1
    assert "erros --rodada" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# 2. Fechamento do banco
# ---------------------------------------------------------------------------


def banco_com_amostras(amb_: Ambiente, rodada: str, rejeitadas: int, existentes: int) -> list[str]:
    copias = [f"{rodada}_{INICIAL}_001_erro{k}_1" for k in range(2, 6)]
    descartes = [f"{rodada}_{INICIAL}_002_erro{k}_1" for k in range(2, 5)]
    original(amb_, f"{rodada}_{INICIAL}_001")
    for c in copias:
        gabarito(amb_, c)
    for d in descartes:
        descarte(amb_, d)
    sorteio(amb_, rodada, copias[:3], descartes)
    respostas = [
        resp_copia(copias[0], False, None) if rejeitadas >= 1 else resp_copia(copias[0]),
        resp_copia(copias[1], True, False) if rejeitadas >= 2 else resp_copia(copias[1]),
        resp_copia(copias[2]),
    ]
    responder_amostras(
        amb_,
        rodada,
        respostas,
        [resp_descartada(d, i < existentes) for i, d in enumerate(descartes)],
    )
    return copias


def test_fechamento_marca_nao_confiavel_e_filtrado(sint: Ambiente) -> None:
    copias = banco_com_amostras(sint, R, rejeitadas=2, existentes=2)
    banco = tc.fechar_banco(R, sint.servicos)
    assert banco.nao_confiavel and banco.filtrado_pelo_verificador
    assert banco.rejeitadas == copias[:2]
    assert [g.copia for g in banco.no_banco] == copias[2:]
    lidos = json.loads(sint.arquivos.ler_texto(f"saida/erros/{R}_gabarito.json"))
    assert [g["amostra"] for g in lidos] == ["rejeitada", "rejeitada", "aceita", None]
    for g in lidos:
        Gabarito.model_validate_json(json.dumps(g))
    lidas = json.loads(sint.arquivos.ler_texto(f"saida/erros/{R}_descartadas.json"))
    assert [d["amostra"] for d in lidas] == ["erro_existe", "erro_existe", "erro_nao_existe"]
    for d in lidas:
        Descartada.model_validate_json(json.dumps(d))
    # Gravado uma vez: fechar de novo lê o que foi gravado e não regrava.
    antes = sint.arquivos.ler_texto(f"saida/erros/{R}_gabarito.json")
    assert tc.fechar_banco(R, sint.servicos) == banco
    assert sint.arquivos.ler_texto(f"saida/erros/{R}_gabarito.json") == antes
    # As descartadas não voltam ao banco: o teste só registra as cópias aceitas e as originais.
    refs = tc.registrar(R, sint.servicos)
    nomes = sorted(r.id.removeprefix(tc.PREFIXO) for r in refs)
    assert nomes == sorted([*copias[2:], f"{R}_{INICIAL}_001"])


def test_fechamento_sem_marca_abaixo_dos_limites(sint: Ambiente) -> None:
    banco_com_amostras(sint, R, rejeitadas=1, existentes=1)
    banco = tc.fechar_banco(R, sint.servicos)
    assert not banco.nao_confiavel and not banco.filtrado_pelo_verificador
    assert len(banco.rejeitadas) == 1 and len(banco.no_banco) == 3


def test_no_ensaio_as_marcas_nao_se_aplicam(sint: Ambiente) -> None:
    banco_com_amostras(sint, "e01", rejeitadas=2, existentes=2)
    banco = tc.fechar_banco("e01", sint.servicos)
    assert not banco.nao_confiavel and not banco.filtrado_pelo_verificador
    assert len(banco.rejeitadas) == 2  # a rejeitada sai do banco também no ensaio


# ---------------------------------------------------------------------------
# 3. A conferência do teste: modo de teste, sem refação, local segue a original
# ---------------------------------------------------------------------------


def test_conferencia_do_teste_em_modo_de_teste(amb: Ambiente) -> None:
    config_antes = (amb.raiz / "config/config.toml").read_bytes()
    teste = tc.servicos_do_teste(amb.servicos)
    assert teste.modo_teste and not amb.servicos.modo_teste
    copia = f"e01_{MAN}_001_erro2_1"
    ref = tc.ref_do_teste("e01", copia)
    assert (ref.rodada, ref.tipo, ref.numero, ref.id) == ("e01", MAN, 1, f"{tc.PREFIXO}{copia}")
    # A semelhança fica desligada sozinha.
    semelhanca.EtapaSemelhanca().pedir(ref, teste)
    lido = json.loads(amb.arquivos.ler_texto(extracao.caminho_etapa(ref, "semelhanca")))
    assert lido["desligada"] is True
    assert (amb.raiz / "config/config.toml").read_bytes() == config_antes
    # Sem refação: o veredito "refazer" encerra a peça do teste.
    veredito(amb, copia, "refazer", {"cabimento": item("cabimento", "nao_passa")})
    assert estado.ponto(ref, [], teste).acao == "refazer_em_teste"
    # Cada cópia segue a sua original no conferente local (risco baixo: 2 de 10).
    for n in range(1, 11):
        da_copia = tc.ref_do_teste("e01", f"e01_{MAN}_{n:03d}_erro2_1")
        assert local.EtapaLocal().se_aplica(da_copia, teste) == local.EtapaLocal().se_aplica(
            RefPeca("e01", MAN, n), amb.servicos
        )
    # Às cegas: o pedido da extração leva o texto, sem o nome da cópia nem o da original.
    gravar(amb, f"saida/rascunhos/{tc.PREFIXO}{copia}_v1.md", f"{MARCA}\n\nTexto da cópia.\n")
    caminho = extracao.EtapaExtracao().pedir(ref, teste)
    assert caminho is not None
    pedido = amb.arquivos.ler_json(caminho, Pedido)
    assert pedido.partes[-1].texto == f"{MARCA}\n\nTexto da cópia.\n"
    assert all("erro2" not in p.texto and "_001" not in p.texto for p in pedido.partes)


def test_etapas_do_teste_sao_as_da_conferencia_e_o_avancar_as_leva(
    sint: Ambiente, monkeypatch: pytest.MonkeyPatch
) -> None:
    montar_banco(sint)
    responder_tudo(sint)
    assert sint.executar("testar", "--rodada", R) == 0
    chamadas: list[tuple[Any, bool, list[RefPeca] | None]] = []

    def falso(etapas: Any, servicos: Any, pecas: Any = None) -> estado.ResumoAvanco:
        chamadas.append((etapas, servicos.modo_teste, pecas))
        return estado.ResumoAvanco()

    monkeypatch.setattr(estado, "avancar", falso)
    assert sint.executar("avancar") == 0
    do_teste = [c for c in chamadas if c[1]]
    assert len(do_teste) == 1
    etapas, _, pecas = do_teste[0]
    assert etapas is principal.ETAPAS
    assert pecas == tc.refs_do_teste(R, sint.servicos)
    assert len(pecas) == 3 + len(IA) + len(JULG) + 1  # as originais e as cópias do banco


# ---------------------------------------------------------------------------
# 4 a 8. Pego, as cinco taxas, o diagnóstico, a dependência do Opus e a retomada
# ---------------------------------------------------------------------------


def test_testar_retomavel_e_as_cinco_taxas(
    sint: Ambiente, capsys: pytest.CaptureFixture[str]
) -> None:
    montar_banco(sint)
    responder_tudo(sint)
    assert sint.executar("testar", "--rodada", R) == 0
    total = 3 + len(IA) + len(JULG) + 1
    assert f"faltam {total}" in capsys.readouterr().out
    assert sint.arquivos.existe(f"saida/erros/{R}_gabarito.json")
    for nome in [A, B, C, *IA.values(), *JULG, REGRA]:
        assert sint.arquivos.existe(f"saida/rascunhos/{tc.PREFIXO}{nome}_v1.md")
    assert sint.arquivos.ler_texto(f"saida/rascunhos/{tc.PREFIXO}{IA['c_opus']}_v1.md") == (
        sint.arquivos.ler_texto(f"saida/erros/{IA['c_opus']}.md")
    )
    veredito(sint, A, "aprovada")
    assert sint.executar("testar", "--rodada", R) == 0
    assert f"faltam {total - 1}" in capsys.readouterr().out
    assert not sint.arquivos.existe(tc.caminho_relatorio(R))
    conferir_tudo(sint)
    assert sint.executar("testar", "--rodada", R) == 0
    r = resultado(sint)
    por = {c.copia: c for c in r.copias}
    # 4. A regra do pego.
    assert por[IA["c_haiku"]].pego and por[IA["c_haiku"]].pego_sem_opus
    assert por[IA["c_opus"]].pego and not por[IA["c_opus"]].pego_sem_opus
    assert por[IA["c_opus"]].itens_pegos == ["pedidos"] and por[IA["c_opus"]].conferentes == [
        "opus"
    ]
    assert (
        not por[IA["c_outro"]].pego and not por[IA["c_orig"]].pego and not por[IA["c_aprov"]].pego
    )
    assert por[IA["c_formato"]].formato and not por[IA["c_formato"]].pego
    assert r.nao_pegas_formato == [IA["c_formato"]]
    # 5. As cinco taxas, com a margem de Wilson.
    assert (r.criterio_central.sucessos, r.criterio_central.total) == (2, 6)
    assert (r.sem_opus.sucessos, r.sem_opus.total) == (1, 6)
    assert r.criterio_central.inferior is not None and r.criterio_central.inferior < 2 / 6
    assert r.criterio_central.superior is not None and r.criterio_central.superior > 2 / 6
    assert (r.julgamento_programa.sucessos, r.julgamento_programa.total) == (1, 2)
    assert r.julgamento_inconclusivo  # menos de 5 cópias
    assert (r.regra_programa.sucessos, r.regra_programa.total) == (1, 1) and r.regra_sanidade_ok
    assert (r.reprovacao_pecas_boas.sucessos, r.reprovacao_pecas_boas.total) == (1, 3)
    assert r.decisao_criterio_central == "nao_passa"
    # 6. Diagnóstico por conferente, por tipo de erro e por origem.
    assert r.por_conferente["opus"].sucessos == 1 and r.por_conferente["haiku"].sucessos == 2
    assert r.por_conferente["programa"].sucessos == 1 and r.por_conferente["local"].sucessos == 0
    assert (r.por_tipo_erro["cabimento"].sucessos, r.por_tipo_erro["cabimento"].total) == (2, 6)
    assert (r.por_origem["opus"].sucessos, r.por_origem["opus"].total) == (2, 6)
    assert (r.por_origem["programa_regra"].sucessos, r.por_origem["programa_regra"].total) == (1, 1)
    # 7. Sem o Opus, 1/6 contra 2/6: mais de 15 pontos abaixo.
    assert r.dependente_do_opus
    # O banco foi fechado com as amostras: nenhuma rejeitada, nenhuma marca.
    assert not r.banco.nao_confiavel and not r.banco.filtrado_pelo_verificador
    assert r.banco.copias == len(IA) + len(JULG) + 1 and r.banco.copias_ia == len(IA)
    # 8. Rodar de novo não regrava.
    antes = sint.arquivos.ler_texto(tc.caminho_relatorio(R))
    assert sint.executar("testar", "--rodada", R) == 0
    assert sint.arquivos.ler_texto(tc.caminho_relatorio(R)) == antes


def test_taxa_sem_o_opus_nunca_maior_e_banco_nao_confiavel_nao_decide(sint: Ambiente) -> None:
    montar_banco(sint)
    responder_amostras(
        sint,
        R,
        [resp_copia(IA["c_haiku"], False, None), resp_copia(IA["c_opus"], True, False)],
        [resp_descartada(f"{B}_erro4_1", False)],
    )
    tc.registrar(R, sint.servicos)
    conferir_tudo(sint)
    assert tc.testar(R, principal.ETAPAS, sint.servicos).relatorio == tc.caminho_relatorio(R)
    r = resultado(sint)
    assert r.banco.nao_confiavel and r.banco.rejeitadas == [IA["c_haiku"], IA["c_opus"]]
    assert r.decisao_criterio_central == "nao_decide"
    assert r.criterio_central.total == len(IA) - 2 and r.criterio_central.sucessos == 0
    assert r.sem_opus.sucessos <= r.criterio_central.sucessos
    assert not r.dependente_do_opus


def test_criterio_central_passa_com_os_numeros_do_plano(sint: Ambiente) -> None:
    """32 de 40 dá 65,2% no limite inferior: passa (ARQUITETURA §5.12.6)."""
    original(sint, A)
    copias = [f"{A}_erro{k}_1" for k in range(2, 42)]
    for c in copias:
        gabarito(sint, c)
    sorteio(sint, R, copias[:10], [])
    responder(sint, f"{R}_amostra_copias", "amostra_copias", [resp_copia(c) for c in copias[:10]])
    tc.registrar(R, sint.servicos)
    veredito(sint, A, "aprovada")
    for n, c in enumerate(copias):
        if n < 32:
            veredito(sint, c, "refazer", {"cabimento": item("cabimento", "nao_passa")})
        else:
            veredito(sint, c, "aprovada")
    assert tc.testar(R, principal.ETAPAS, sint.servicos).relatorio is not None
    r = resultado(sint)
    assert (r.criterio_central.sucessos, r.criterio_central.total) == (32, 40)
    assert r.criterio_central.inferior is not None and r.criterio_central.inferior >= 0.65
    assert r.decisao_criterio_central == "passa"
    assert r.sem_opus.sucessos == 32 and not r.dependente_do_opus


def test_resultado_tem_modelo_em_formatos() -> None:
    assert "ResultadoTeste" in (RAIZ / "fabrica/comum/formatos.py").read_text("utf-8")
    assert tc.caminho_relatorio("r01") == "saida/relatorios/teste_conferentes.json"
    assert Amostras.__name__ == "Amostras" and Conferencia.__name__ == "Conferencia"
