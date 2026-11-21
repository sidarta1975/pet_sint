"""Teste de aceite do brief 010: `fabrica/conferencia/dados_reais.py`.

A peça de exemplo usa só dados de `ficticios.py` e os marcadores. As listas de
permitidos e de proibidos são de exemplo, escritas aqui. Os nomes reservados
são lidos de `testes/dados/reais_reservados.json` e nunca copiados para cá.
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pytest

from fabrica.comum.formatos import Cidade, ReaisReservados, Tribunal
from fabrica.conferencia.dados_reais import Detector
from fabrica.ficticios import Ficticios

RAIZ = Path(__file__).resolve().parent.parent
DDDS = [20, 23, 25, 26, 29, 36, 39, 52, 56, 57, 58, 59, 72, 76, 78]
MARCADORES = [
    "Nome e Sobrenome da Parte Autora",
    "Razão Social da Parte Ré",
    "Nome e Sobrenome do Advogado",
]
PERMITIDOS = [
    "SISBAJUD",
    "Serasa",
    "CNJ",
    "data venia",
    "inaudita altera pars",
    "Tribunal de Justiça do Estado de São Paulo",
    "Juizado Especial Cível da Comarca de Campinas",
    "Excelentíssimo Senhor Doutor Juiz de Direito",
    "Representante Legal",
    "Requerente",
    "Embargante",
]
PROIBIDOS = ["Itaú", "Latam"]
TITULOS = ["Dos Fatos", "Dos Pedidos"]
CODIGOS_OFICIAIS = ["001", "033", "104", "237", "341"]
MARCA = "DOCUMENTO SINTÉTICO — FICTÍCIO"

CIDADE = Cidade(
    nome="Campinas",
    uf="SP",
    cep_inicio="13000-001",
    cep_fim="13139-999",
    juizo_jec="Juizado Especial Cível da Comarca de Campinas",
    varas_civeis=[],
)
FICTICIOS = Ficticios(
    semente=11,
    ddds=DDDS,
    ruas=["Rua das Acácias Inventadas"],
    bairros=["Jardim Imaginário"],
    cidades=[CIDADE],
    tribunais=[Tribunal(uf="SP", codigo="26")],
    profissoes=["professora"],
)
ENDERECO = FICTICIOS.endereco()


def _peca(plantado: str = "") -> str:
    f = FICTICIOS
    return f"""{MARCA}

Excelentíssimo Senhor Doutor Juiz de Direito do Juizado Especial Cível da Comarca de Campinas

Nome e Sobrenome da Parte Autora, solteira, professora, inscrita no CPF sob o nº {f.cpf()}, \
residente na {ENDERECO.rua}, {ENDERECO.numero}, {ENDERECO.bairro}, {ENDERECO.cidade}/\
{ENDERECO.estado}, CEP {ENDERECO.cep}, telefone {f.telefone()}, e-mail {f.email("autor")}, \
por seu advogado, Nome e Sobrenome do Advogado, {f.oab()}, e-mail {f.email("escritorio")}, \
vem propor ação em face de Razão Social da Parte Ré, inscrita no CNPJ sob o nº {f.cnpj()}, \
pelos fatos a seguir.

Dos Fatos

A Parte Autora celebrou o contrato nº {f.identificador(2026)} e registrou o protocolo \
{f.identificador(2026)}. O bloqueio foi pedido pelo SISBAJUD e a negativação constou no Serasa, \
conforme o CNJ. Data venia, requer a medida inaudita altera pars. O processo \
{f.numero_processo("SP", 2026)} tramita no Tribunal de Justiça do Estado de São Paulo. \
O advogado da Parte Autora, em face da Razão Social da Parte Ré, pede a intimação. \
A Requerente e o Embargante citados por seu Representante Legal concordam.{plantado}

Dos Pedidos

Diante do exposto, requer a procedência. Nestes termos, pede deferimento.
"""


def detector(proibidos: list[str] | None = None) -> Detector:
    return Detector(
        marcadores=MARCADORES,
        ruas=[ENDERECO.rua],
        termos_da_ficha=[ENDERECO.bairro, ENDERECO.cidade],
        permitidos=PERMITIDOS,
        proibidos=PROIBIDOS if proibidos is None else proibidos,
        titulos=TITULOS,
        ddds=DDDS,
        codigos_banco=CODIGOS_OFICIAIS,
    )


# --- cálculos próprios do teste, para plantar documentos válidos -----------------


def _dv11(base: str, pesos: list[int]) -> str:
    resto = sum((ord(c) - 48) * p for c, p in zip(base, pesos, strict=True)) % 11
    return "0" if resto < 2 else str(11 - resto)


def cnpj_valido(base: str) -> str:
    d1 = _dv11(base, [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    d2 = _dv11(base + d1, [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2])
    return f"{base[:2]}.{base[2:5]}.{base[5:8]}/{base[8:12]}-{d1}{d2}"


def processo_valido(n: str, ano: str, tr: str, o: str) -> str:
    dv = 98 - int(n + ano + "8" + tr + o + "00") % 97
    return f"{n}-{dv:02d}.{ano}.8.{tr}.{o}"


# 1 -----------------------------------------------------------------------------


def test_peca_limpa_sem_achado() -> None:
    assert detector().detectar(_peca()) == []


# 2 -----------------------------------------------------------------------------

PLANTADOS = [
    ("cpf", " O CPF 529.982.247-25 foi citado."),
    ("cnpj", f" O CNPJ {cnpj_valido('11222333000181'[:12])} foi citado."),
    ("cnpj", f" O CNPJ {cnpj_valido('12ABC34501DE')} foi citado."),
    ("numero_processo", f" Consta o processo {processo_valido('0001234', '2026', '26', '0100')}."),
    ("oab", " Assina também o advogado inscrito na OAB/SP nº 123.456."),
    ("nome", " Consta ainda que Fulana de Tal participou."),
    ("nome", " Consta ainda que o Sr. Sicrano participou."),
    ("nome", " Consta ainda que a Dra. Beltrana participou."),
    ("nome", " Consta ainda que a empresa Exemplar Ltda. participou."),
    ("nome", " Consta ainda que a empresa Modelo S.A. participou."),
    ("nome", " Consta ainda que a empresa Fictícia ME participou."),
    ("nome", " Consta ainda que a empresa Inventada EIRELI participou."),
    ("nome", " Consta ainda que o Banco Imaginado participou."),
    ("nome", " Consta ainda que a Companhia Sonhada participou."),
    ("nome", " Consta ainda que a Parte Autora Fulana de Tal participou."),
    ("nome_proibido", " Consta ainda que o itaú participou."),
    ("nome_proibido", " Consta ainda que a Latam participou."),
    ("telefone", " Ligue para (11) 91234-5678."),
    ("email", " Escreva para contato@empresa.com.br hoje."),
    ("rua", " A correspondência foi para a Rua das Palmeiras Esquecidas, 10."),
    ("contrato_protocolo", " Foi firmado o contrato nº 123456 entre as partes."),
    ("contrato_protocolo", " Foi aberto o protocolo 2026-0001 no atendimento."),
    ("codigo_banco", " O depósito foi feito no código do banco 341."),
    ("nome_ao_lado_do_cargo", " O juiz Sicrano despachou."),
    ("nome_ao_lado_do_cargo", " A escrivã Beltrana certificou."),
]


@pytest.mark.parametrize(("tipo", "plantado"), PLANTADOS, ids=[p[1].strip() for p in PLANTADOS])
def test_cada_dado_real_plantado_e_pego(tipo: str, plantado: str) -> None:
    achados = detector().detectar(_peca(plantado))
    assert achados, plantado
    assert tipo in {achado.tipo for achado in achados}
    texto = _peca(plantado)
    for achado in achados:
        assert texto[achado.posicao : achado.posicao + len(achado.trecho)] == achado.trecho


def test_valido_e_invalido_pelo_digito() -> None:
    assert detector().detectar(" O CPF 529.982.247-26 foi citado.") == []
    assert detector().detectar(" O CPF 529.982.247-25 foi citado.")[0].tipo == "cpf"


def test_lista_oficial_vazia_nao_acusa_codigo() -> None:
    vazio = Detector(MARCADORES, [ENDERECO.rua], [], PERMITIDOS, [], TITULOS, DDDS, [])
    assert vazio.detectar(" O depósito foi feito no código do banco 341.") == []


# 3 -----------------------------------------------------------------------------


def _reservados() -> ReaisReservados:
    caminho = RAIZ / "testes/dados/reais_reservados.json"
    return ReaisReservados.model_validate_json(caminho.read_text(encoding="utf-8"))


def test_pega_100_por_cento_dos_reservados_com_proibidos_vazio() -> None:
    vazio = detector(proibidos=[])
    reservados = _reservados().nomes
    pegos = 0
    for item in reservados:
        texto = _peca(f" Consta ainda que {item.forma} participou do caso.")
        inicio = texto.index(item.forma)
        fim = inicio + len(item.forma)
        achados = [a for a in vazio.detectar(texto) if a.tipo == "nome"]
        if any(a.posicao < fim and a.posicao + len(a.trecho) > inicio for a in achados):
            pegos += 1
    assert pegos == len(reservados), f"{pegos} de {len(reservados)} pegos"


# 4 -----------------------------------------------------------------------------


def _normal(texto: str) -> str:
    sem = unicodedata.normalize("NFD", texto)
    return "".join(c for c in sem if unicodedata.category(c) != "Mn").casefold()


def test_nenhum_reservado_no_codigo_nem_nos_dados() -> None:
    pastas = [RAIZ / "fabrica"]
    if (RAIZ / "dados").is_dir():
        pastas.append(RAIZ / "dados")
        aviso = ""
    else:
        aviso = " (dados/ ainda não existe: conferido só fabrica/)"
    arquivos = [
        p
        for pasta in pastas
        for p in pasta.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    ]
    assert arquivos
    textos = {p: _normal(p.read_text(encoding="utf-8", errors="ignore")) for p in arquivos}
    vazados = []
    for item in _reservados().nomes:
        alvo = re.compile(r"(?<!\w)" + re.escape(_normal(item.forma)) + r"(?!\w)")
        vazados += [str(p.relative_to(RAIZ)) for p, t in textos.items() if alvo.search(t)]
    assert vazados == [], f"nome reservado encontrado em {vazados}{aviso}"


# 5 -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "texto",
    [
        " O bloqueio pelo SISBAJUD e a consulta ao Serasa seguiram a regra do CNJ.",
        " Data venia, a tutela foi pedida inaudita altera pars.",
        " O recurso irá ao Tribunal de Justiça do Estado de São Paulo.",
        " A causa corre no Juizado Especial Cível da Comarca de Campinas.",
        " Dirige-se ao Excelentíssimo Senhor Doutor Juiz de Direito.",
        " O advogado da Parte Autora falou.",
        " O pedido foi feito em face da Razão Social da Parte Ré.",
        " A Requerente, por seu Representante Legal, concorda com o Embargante.",
        " Dos Fatos",
        " Contudo, nada mais. Portanto, Assim decidiu-se. Ademais, Nada consta.",
        " Juntou cópia do CPF e CNPJ e do RG.",
    ],
)
def test_termos_juridicos_e_permitidos_nao_sao_acusados(texto: str) -> None:
    assert detector().detectar(_peca(texto)) == []


def test_marca_e_titulos_ignorados() -> None:
    assert detector().detectar(f"{MARCA}\n\nDos Fatos\n\nDos Pedidos\n") == []
