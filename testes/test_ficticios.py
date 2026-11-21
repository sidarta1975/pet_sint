"""Teste de aceite do brief 009: `fabrica/ficticios.py`.

As listas de exemplo ficam aqui dentro; `dados/` só nasce no brief 014.
O teste tem o próprio cálculo de cada dígito verificador.
"""

from __future__ import annotations

import re

import pytest

from fabrica.comum.formatos import Cidade, Tribunal
from fabrica.ficticios import ErroFicticio, Ficticios

SEMENTE = 20261121
DDDS_INEXISTENTES = [20, 23, 25, 26, 29, 36, 39, 52, 56, 57, 58, 59, 72, 76, 78]
# Os 67 DDDs em uso (ARQUITETURA §5.2).
DDDS_EM_USO = (
    list(range(11, 20))
    + [21, 22, 24, 27, 28]
    + list(range(31, 36))
    + [37, 38]
    + list(range(41, 50))
    + [51]
    + list(range(53, 56))
    + list(range(61, 70))
    + [71]
    + list(range(73, 76))
    + [77, 79]
    + list(range(81, 90))
    + list(range(91, 100))
)
RUAS = ["Rua das Acácias Inventadas", "Avenida dos Ipês Fictícios", "Travessa do Exemplo"]
BAIRROS = ["Jardim Imaginário", "Vila Inventada", "Parque do Teste"]
CIDADES = [
    Cidade(
        nome="Campinas",
        uf="SP",
        cep_inicio="13000-001",
        cep_fim="13139-999",
        juizo_jec="Juizado Especial Cível da Comarca de Campinas",
        varas_civeis=[],
    ),
    Cidade(
        nome="Uberlândia",
        uf="MG",
        cep_inicio="38400-001",
        cep_fim="38415-999",
        juizo_jec="Juizado Especial Cível da Comarca de Uberlândia",
        varas_civeis=[],
    ),
    Cidade(
        nome="Joinville",
        uf="SC",
        cep_inicio="89200-001",
        cep_fim="89239-999",
        juizo_jec="Juizado Especial Cível da Comarca de Joinville",
        varas_civeis=[],
    ),
]
TRIBUNAIS = [
    Tribunal(uf="SP", codigo="26"),
    Tribunal(uf="MG", codigo="13"),
    Tribunal(uf="SC", codigo="24"),
]
PROFISSOES = ["professor(a)", "comerciante", "engenheiro(a)"]
# Lista oficial de exemplo (não vazia) de códigos de banco em uso.
CODIGOS_OFICIAIS = [f"{n:03d}" for n in range(1, 400, 3)]
N = 5_000


def gerador(semente: int = SEMENTE) -> Ficticios:
    return Ficticios(
        semente=semente,
        ddds=DDDS_INEXISTENTES,
        ruas=RUAS,
        bairros=BAIRROS,
        cidades=CIDADES,
        tribunais=TRIBUNAIS,
        profissoes=PROFISSOES,
    )


# --- cálculos próprios do teste --------------------------------------------


def _valor(caractere: str) -> int:
    return ord(caractere) - 48


def _dv_mod11(base: str, pesos: list[int]) -> str:
    soma = sum(_valor(c) * p for c, p in zip(base, pesos, strict=True))
    resto = soma % 11
    return "0" if resto < 2 else str(11 - resto)


def cpf_valido(cpf: str) -> bool:
    numeros = re.sub(r"\D", "", cpf)
    assert len(numeros) == 11
    d1 = _dv_mod11(numeros[:9], list(range(10, 1, -1)))
    d2 = _dv_mod11(numeros[:9] + d1, list(range(11, 1, -1)))
    return numeros[9:] == d1 + d2


def cnpj_valido(cnpj: str) -> bool:
    caracteres = re.sub(r"[./-]", "", cnpj)
    assert len(caracteres) == 14
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = _dv_mod11(caracteres[:12], pesos1)
    d2 = _dv_mod11(caracteres[:12] + d1, pesos2)
    return caracteres[12:] == d1 + d2


def dv_cnj_oficial(numero: str) -> str:
    m = re.fullmatch(r"(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})", numero)
    assert m, numero
    n, _, ano, j, tr, o = m.groups()
    resto = int(n + ano + j + tr + o + "00") % 97
    return f"{98 - resto:02d}"


# --- 1 ----------------------------------------------------------------------


def test_cpfs_com_digito_invalido() -> None:
    g = gerador()
    for _ in range(N):
        cpf = g.cpf()
        assert re.fullmatch(r"\d{3}\.\d{3}\.\d{3}-\d{2}", cpf)
        assert not cpf_valido(cpf)


def test_cnpjs_com_digito_invalido_inclusive_com_letras() -> None:
    g = gerador()
    com_letras = 0
    for _ in range(N):
        cnpj = g.cnpj()
        assert re.fullmatch(r"[0-9A-Z]{2}\.[0-9A-Z]{3}\.[0-9A-Z]{3}/[0-9A-Z]{4}-\d{2}", cnpj)
        assert not cnpj_valido(cnpj)
        com_letras += bool(re.search(r"[A-Z]", cnpj))
    assert com_letras > 0


def test_calculo_do_teste_confere_exemplos_conhecidos() -> None:
    # Exemplos públicos de documentação, só para conferir o cálculo do próprio teste.
    assert cpf_valido("529.982.247-25")
    assert cnpj_valido("11.222.333/0001-81")
    assert cnpj_valido("12.ABC.345/01DE-35")


# --- 2 ----------------------------------------------------------------------


def test_numeros_de_processo_com_digito_invalido() -> None:
    g = gerador()
    for indice in range(N):
        cidade = CIDADES[indice % len(CIDADES)]
        numero = g.numero_processo(uf=cidade.uf, ano=2026)
        m = re.fullmatch(r"\d{7}-(\d{2})\.2026\.8\.(\d{2})\.\d{4}", numero)
        assert m, numero
        assert m.group(2) == {"SP": "26", "MG": "13", "SC": "24"}[cidade.uf]
        assert m.group(1) != dv_cnj_oficial(numero)


def test_tribunal_desconhecido_recusado() -> None:
    with pytest.raises(ErroFicticio):
        gerador().numero_processo(uf="RJ", ano=2026)


# --- 3 a 7 ------------------------------------------------------------------


def test_telefones_com_ddd_inexistente() -> None:
    assert len(DDDS_EM_USO) == 67
    assert not set(DDDS_EM_USO) & set(DDDS_INEXISTENTES)
    g = gerador()
    for _ in range(N):
        telefone = g.telefone()
        m = re.fullmatch(r"\((\d{2})\) 9\d{4}-\d{4}", telefone)
        assert m, telefone
        assert int(m.group(1)) in DDDS_INEXISTENTES
        assert int(m.group(1)) not in DDDS_EM_USO


def test_ddd_em_uso_na_configuracao_recusado() -> None:
    with pytest.raises(ErroFicticio):
        Ficticios(SEMENTE, [11, 20], RUAS, BAIRROS, CIDADES, TRIBUNAIS, PROFISSOES)


@pytest.mark.parametrize("papel", ["autor", "reu", "advogado", "escritorio"])
def test_emails_terminam_em_example(papel: str) -> None:
    g = gerador()
    for _ in range(100):
        email = g.email(papel)
        assert email.endswith(".example")
        assert re.fullmatch(r"[a-z.]+@[a-z.]+\.example", email)


@pytest.mark.parametrize(
    ("papel", "categoria", "marcador"),
    [
        ("autor", "pessoa_fisica", "Nome e Sobrenome da Parte Autora"),
        ("reu", "pessoa_fisica", "Nome e Sobrenome da Parte Ré"),
        ("autor", "mei", "Razão Social da Parte Autora"),
        ("reu", "pessoa_juridica_privada", "Razão Social da Parte Ré"),
        ("reu", "microempresa", "Razão Social da Parte Ré"),
        ("autor", "empresa_pequeno_porte", "Razão Social da Parte Autora"),
    ],
)
def test_nomes_sao_os_marcadores(papel: str, categoria: str, marcador: str) -> None:
    assert gerador().nome(papel, categoria) == marcador  # type: ignore[arg-type]


def test_advogado_e_oab_marcadores() -> None:
    g = gerador()
    assert g.nome_advogado() == "Nome e Sobrenome do Advogado"
    assert g.oab() == "OAB/UF nº 000.000"


def test_enderecos_de_lista_com_cep_da_faixa() -> None:
    g = gerador()
    faixas = {c.nome: (c.uf, c.cep_inicio, c.cep_fim) for c in CIDADES}
    for _ in range(1_000):
        endereco = g.endereco()
        assert endereco.rua in RUAS
        assert endereco.bairro in BAIRROS
        uf, inicio, fim = faixas[endereco.cidade]
        assert endereco.estado == uf
        assert re.fullmatch(r"\d{5}-\d{3}", endereco.cep)
        assert inicio <= endereco.cep <= fim
        assert endereco.numero.isdigit()


def test_endereco_na_cidade_pedida() -> None:
    endereco = gerador().endereco(cidade="Joinville")
    assert (endereco.cidade, endereco.estado) == ("Joinville", "SC")


def test_identificadores_com_prefixo_sint() -> None:
    g = gerador()
    for _ in range(1_000):
        assert re.fullmatch(r"SINT-2026-\d{6}", g.identificador(2026))


# --- 8 ----------------------------------------------------------------------


def test_codigo_de_banco_fora_da_lista_oficial() -> None:
    assert CODIGOS_OFICIAIS
    g = gerador()
    for _ in range(1_000):
        codigo = g.codigo_banco(CODIGOS_OFICIAIS)
        assert re.fullmatch(r"\d{3}", codigo)
        assert codigo not in CODIGOS_OFICIAIS


def test_lista_oficial_vazia_recusada() -> None:
    with pytest.raises(ErroFicticio):
        gerador().codigo_banco([])


# --- 9 ----------------------------------------------------------------------


def _amostra(g: Ficticios) -> list[str]:
    dados = []
    for _ in range(50):
        dados += [g.cpf(), g.cnpj(), g.telefone(), g.numero_processo("SP", 2026)]
        dados += [g.identificador(2026), g.endereco().model_dump_json(), g.profissao()]
    return dados


def test_mesma_semente_mesmos_dados_e_sementes_diferentes_dados_diferentes() -> None:
    assert _amostra(gerador(1)) == _amostra(gerador(1))
    assert _amostra(gerador(1)) != _amostra(gerador(2))


def test_nao_usa_o_gerador_global() -> None:
    import random

    random.seed(5)
    antes = random.random()
    random.seed(5)
    _amostra(gerador())
    assert random.random() == antes


# --- nomes reservados do teste (conteúdo conferido; os nomes ficam só no arquivo) ---


def test_reais_reservados_valido_com_pelo_menos_20_nomes() -> None:
    from pathlib import Path

    from fabrica.comum.formatos import ReaisReservados

    caminho = Path(__file__).resolve().parent / "dados" / "reais_reservados.json"
    reservados = ReaisReservados.model_validate_json(caminho.read_text(encoding="utf-8"))
    assert len(reservados.nomes) >= 20
    societaria = re.compile(r"\b(S\.A\.|Ltda\.)")
    for item in reservados.nomes:
        maiusculas = [p for p in item.forma.split() if p[:1].isupper()]
        assert societaria.search(item.forma) or len(maiusculas) >= 2, item.forma
        assert item.forma not in {
            "Nome e Sobrenome da Parte Autora",
            "Nome e Sobrenome da Parte Ré",
            "Razão Social da Parte Autora",
            "Razão Social da Parte Ré",
        }
