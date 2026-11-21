"""Teste de aceite do brief 003: contratos de dados de `fabrica/comum/formatos.py`.

Para cada contrato: um exemplo válido passa; o mesmo exemplo com campo faltando,
com campo a mais e com tipo errado é recusado. Todos os dados são fictícios.
"""

import copy
import json
from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from fabrica.comum import formatos as f

# ---------------------------------------------------------------------------
# Exemplos válidos (dados fictícios, com os marcadores fixos)
# ---------------------------------------------------------------------------


def endereco(rua: str = "Rua das Acácias Inventadas") -> dict[str, Any]:
    return {
        "rua": rua,
        "numero": "100",
        "complemento": None,
        "bairro": "Jardim Imaginário",
        "cidade": "Campinas",
        "estado": "SP",
        "cep": "13010-111",
    }


def parte(papel: str, categoria: str = "pessoa_fisica") -> dict[str, Any]:
    pessoa = categoria == "pessoa_fisica"
    if papel == "autor":
        nome = "Nome e Sobrenome da Parte Autora" if pessoa else "Razão Social da Parte Autora"
    else:
        nome = "Nome e Sobrenome da Parte Ré" if pessoa else "Razão Social da Parte Ré"
    return {
        "id": papel,
        "papel": papel,
        "categoria": categoria,
        "nome": nome,
        "documento": "123.456.789-00" if pessoa else "11.222.333/0001-80",
        "estado_civil": "solteiro(a)" if pessoa else None,
        "profissao": "professor(a)" if pessoa else None,
        "endereco": endereco(),
        "email": f"parte.{papel}@ficticio.example",
        "telefone": "(20) 91234-5678",
        "capaz": True if pessoa else None,
        "preso": False if pessoa else None,
    }


def ficha_comum(rotulo: str, rito: str, classe: str) -> dict[str, Any]:
    return {
        "id": "e01_peticao_inicial_jec_001",
        "tipo": rotulo,
        "classe_risco": classe,
        "casa_matriz": {
            "materia": "negativacao_indevida",
            "tese": "inscrição sem débito",
            "polo": "autor",
            "complexidade": "media",
            "momento": "antes da citação",
            "estilo": "detalhado",
        },
        "semente": 42,
        "processo": {
            "identificador_ficticio": "SINT-PROC-0001",
            "numero_cnj": None,
            "rito": rito,
            "comarca": "Campinas",
            "uf": "SP",
            "juizo": "Juizado Especial Cível da Comarca de Campinas",
            "data_ajuizamento": "2026-06-10",
        },
        "partes": [parte("autor"), parte("reu", "pessoa_juridica_privada")],
        "advogado": {
            "nome": "Nome e Sobrenome do Advogado",
            "oab": "OAB/UF nº 000.000",
            "email": "escritorio@ficticio.example",
            "telefone": "(20) 93456-7890",
            "endereco_escritorio": endereco("Avenida dos Ipês Fictícios"),
            "representa": "autor",
        },
        "fatos": [{"data": "2026-03-15", "descricao": "Fato fictício.", "valores": ["v1"]}],
        "valores": [
            {
                "id": "v1",
                "descricao": "danos materiais",
                "centavos": 150000,
                "data_referencia": None,
            }
        ],
        "provas": [{"id": "d1", "descricao": "extrato", "identificador": "SINT-2026-000001"}],
        "valor_causa": "v1",
        "fundamentos": ["cdc_art_14"],
        "momento_processual": {"fase": "inicial", "ultima_decisao": "nenhuma", "prazo": None},
        "pecas_anteriores": [],
        "data_peca": "2026-06-10",
        "local_peca": "Campinas",
    }


def ficha_inicial() -> dict[str, Any]:
    ficha = ficha_comum(
        "Petição Inicial em Juizado Especial Cível", "juizado_especial_civel", "medio"
    )
    ficha.update(
        {
            "pedidos": [
                {"id": "p1", "natureza": "danos_materiais", "descricao": "danos", "valor": "v1"}
            ],
            "materia": "negativacao_indevida",
            "relacao_consumo": True,
            "inversao_onus_pedida": False,
            "tutela_urgencia": {"pedida": False, "fundamento": None},
            "tentativa_previa": {"data": "2026-04-10", "protocolo": "SINT-2026-000123"},
            "salario_minimo_referencia": 162100,
        }
    )
    return ficha


def ficha_embargos() -> dict[str, Any]:
    ficha = ficha_comum("Embargos de Declaração", "procedimento_comum", "alto")
    ficha["processo"]["numero_cnj"] = "0001234-04.2026.8.26.0100"
    ficha["valor_causa"] = None
    ficha["momento_processual"] = {
        "fase": "depois da sentença",
        "ultima_decisao": "sentença de improcedência",
        "prazo": {"inicio": "2026-07-01", "dias_uteis": 5, "termo_final": "2026-07-08"},
    }
    ficha.update(
        {
            "pedidos": [
                {"id": "p1", "natureza": "suprir_omissao", "descricao": "suprir", "valor": None}
            ],
            "embargante": "autor",
            "decisao_embargada": {
                "tipo": "sentenca",
                "data": "2026-06-25",
                "data_intimacao": "2026-07-01",
                "juizo": "2ª Vara Cível da Comarca de Campinas",
                "relatorio": "Relatório fictício.",
                "fundamentacao": "Fundamentação fictícia.",
                "dispositivo": "Julgo improcedente.",
            },
            "argumentos_das_partes": [
                {"id": f"a{i}", "parte": "autor", "peca_de_origem": "inicial", "texto": "Texto."}
                for i in range(1, 4)
            ],
            "defeito": {
                "tipo": "omissao_total",
                "ancora": {
                    "origem": "argumento",
                    "argumento_id": "a1",
                    "trecho_literal": "Texto.",
                },
                "trecho_mencao": None,
                "descricao": "A sentença não enfrentou o argumento a1.",
                "efeito_modificativo": True,
            },
        }
    )
    return ficha


def ficha_manifestacao() -> dict[str, Any]:
    ficha = ficha_comum(
        "Manifestação sobre Aviso de Recebimento Negativo", "procedimento_comum", "baixo"
    )
    ficha["valor_causa"] = None
    ficha.update(
        {
            "pedidos": [
                {
                    "id": "p1",
                    "natureza": "nova_citacao_novo_endereco",
                    "descricao": "nova citação",
                    "valor": None,
                }
            ],
            "peticionante": "autor",
            "citando": "reu",
            "endereco_tentado": endereco(),
            "aviso_recebimento": {"data_juntada": "2026-07-01", "motivo_devolucao": "mudou_se"},
            "determinacao_judicial": {"data_intimacao": "2026-07-02", "prazo_dias_uteis": 5},
            "pedido_ar": "informar_novo_endereco",
            "novo_endereco": endereco("Travessa das Bromélias Imaginárias"),
            "meio_nova_diligencia": "correio",
            "prazo_pedido_dias": None,
        }
    )
    return ficha


def resposta_ficha_comum() -> dict[str, Any]:
    ficha = ficha_inicial()
    return {
        "fatos": ficha["fatos"],
        "valores": ficha["valores"],
        "provas": ficha["provas"],
        "valor_causa": "v1",
        "fundamentos": ["cdc_art_14"],
        "momento_processual": {"ultima_decisao": "nenhuma"},
        "pecas_anteriores": [],
    }


def resposta_ficha_inicial() -> dict[str, Any]:
    ficha = ficha_inicial()
    dados = resposta_ficha_comum()
    for campo in (
        "pedidos",
        "relacao_consumo",
        "inversao_onus_pedida",
        "tutela_urgencia",
        "tentativa_previa",
    ):
        dados[campo] = ficha[campo]
    return dados


def resposta_ficha_embargos() -> dict[str, Any]:
    ficha = ficha_embargos()
    dados = resposta_ficha_comum()
    decisao = dict(ficha["decisao_embargada"])
    del decisao["data_intimacao"]
    defeito = dict(ficha["defeito"])
    del defeito["tipo"]
    dados.update(
        {
            "pedidos": ficha["pedidos"],
            "decisao_embargada": decisao,
            "argumentos_das_partes": ficha["argumentos_das_partes"],
            "defeito": defeito,
        }
    )
    return dados


def resposta_ficha_manifestacao() -> dict[str, Any]:
    dados = resposta_ficha_comum()
    dados["pedidos"] = ficha_manifestacao()["pedidos"]
    return dados


def visao_travas() -> dict[str, Any]:
    return {
        "tipo": "Petição Inicial em Juizado Especial Cível",
        "processo.rito": "juizado_especial_civel",
        "materia": "negativacao_indevida",
        "autor.categoria": "pessoa_fisica",
        "autor.capaz": True,
        "autor.preso": False,
        "reu.categoria": "pessoa_juridica_privada",
        "reu.capaz": None,
        "reu.preso": None,
        "valor_causa_centavos": 150000,
        "alcada_centavos": 6484000,
        "defeito.tipo": None,
        "defeito.ancora.argumento_id": None,
        "defeito.trecho_mencao": None,
        "pedido_ar": None,
        "aviso_recebimento.motivo_devolucao": None,
        "novo_endereco": None,
        "meio_nova_diligencia": None,
        "nova_diligencia": None,
    }


def condicao() -> dict[str, Any]:
    return {
        "campo": "processo.rito",
        "op": "igual",
        "valor": "juizado_especial_civel",
        "outro_campo": None,
    }


def trava() -> dict[str, Any]:
    return {
        "condicoes": [condicao()],
        "efeito": "proibe",
        "campo_exigido": None,
        "base_legal": "Art. 8º, § 1º, da Lei 9.099/1995",
        "dispositivos": ["lei_9099_art_8_p1"],
    }


def dispositivo() -> dict[str, Any]:
    return {
        "id": "cdc_art_14",
        "diploma": "cdc",
        "artigo": "14",
        "paragrafo": "caput",
        "assunto": "responsabilidade pelo fato do serviço",
        "funcao": "consequencia",
        "texto_vigente": "Texto do dispositivo.",
        "tipos": ["peticao_inicial_jec"],
        "fonte": "https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm",
        "data_conferencia": "2026-11-21",
    }


def tabela_normas() -> dict[str, Any]:
    return {
        "versao": "2026-11-21",
        "diplomas": [{"id": "cdc", "nome": "Código de Defesa do Consumidor", "formas": ["CDC"]}],
        "dispositivos": [dispositivo()],
    }


def bloco(nome: str = "fatos", ordem: int = 1) -> dict[str, Any]:
    return {
        "nome": nome,
        "titulo": "Dos Fatos",
        "ordem": ordem,
        "obrigatorio": True,
        "descricao": "Narrativa dos fatos.",
    }


def tipo_catalogo() -> dict[str, Any]:
    return {
        "rotulo": "Petição Inicial em Juizado Especial Cível",
        "nome_curto": "peticao_inicial_jec",
        "familia": "peticao_inicial",
        "perfil": "juizado_especial_civel",
        "classe_risco": "medio",
        "tarefa_redacao": "redacao_risco_medio",
        "quantidade": 10,
        "depende_peca_anterior": False,
        "itens_conferencia": ["cabimento", "coerencia"],
    }


def matriz() -> dict[str, Any]:
    return {
        "tipo": "peticao_inicial_jec",
        "quantidade": 10,
        "momento": "antes da citação",
        "materias": [{"materia": "voo", "teses": ["atraso"], "quantidade": 2}],
        "teto_por_materia": 2,
        "eixos_fixos": [
            {
                "eixo": "complexidade",
                "contagens": [
                    {"valor": "simples", "quantidade": 5},
                    {"valor": "media", "quantidade": 5},
                ],
            }
        ],
        "categorias_autor": ["pessoa_fisica"],
        "categorias_reu": ["pessoa_juridica_privada"],
        "motivos_devolucao": [],
        "pedidos_ar": [],
    }


def pedido_api() -> dict[str, Any]:
    return {
        "nome": "e01_peticao_inicial_jec_001_v1_extracao_t1",
        "servico": "claude",
        "rodada": "e01",
        "peca": "e01_peticao_inicial_jec_001",
        "versao": 1,
        "tarefa": "extracao",
        "tentativa": 1,
        "modelo": "claude-haiku-5-5",
        "esforco": "low",
        "teto_saida": 8000,
        "partes": [{"nome": "instrucoes", "texto": "Instruções."}],
        "formato": "Extracao",
        "esquema": {"type": "object"},
        "criado_em": "2026-11-21T10:00:00+00:00",
    }


def resposta_api() -> dict[str, Any]:
    return {
        "pedido": "e01_peticao_inicial_jec_001_v1_extracao_t1",
        "modelo": "claude-haiku-5-5",
        "conteudo": "{}",
        "bruto": None,
        "motivo_parada": "end_turn",
        "tokens": {"entrada": 100, "cache": 0, "raciocinio": 0, "saida": 50},
        "situacao": "ok",
        "recebida_em": "2026-11-21T10:00:05+00:00",
    }


def extracao() -> dict[str, Any]:
    return {
        "nomes": [{"texto": "Nome e Sobrenome da Parte Autora", "papel": "autor"}],
        "documentos": [{"tipo": "cep", "texto": "13010-111"}],
        "valores": [
            {"texto": "R$ 1.500,00", "centavos": 150000, "lugar": "pedido", "pedido": "p1"}
        ],
        "datas": [{"texto": "março de 2026", "data": "2026-03"}],
        "comarca": "Campinas",
        "juizo": "Juizado Especial Cível da Comarca de Campinas",
        "pedidos": [{"natureza": "outro", "texto": "honorários"}],
        "pecas_anteriores": [],
        "data_peca": "2026-06-10",
    }


def resultado_item() -> dict[str, Any]:
    return {
        "item": "coerencia_ficha",
        "resposta": "passa",
        "quem": "programa",
        "trecho": "",
        "divergencias": [],
    }


def notas() -> dict[str, Any]:
    return {"clareza": 4, "concisao": 3, "linguagem_tecnica": 5}


def conferencia() -> dict[str, Any]:
    return {
        "peca": "e01_peticao_inicial_jec_001",
        "versao": 1,
        "extracao": extracao(),
        "itens": [resultado_item()],
        "caminho": [
            {
                "item": "coerencia_ficha",
                "respostas": [resultado_item()],
                "regra": "item de programa",
                "resposta_final": "passa",
                "quem_final": "programa",
            }
        ],
        "notas_estilo": notas(),
        "alertas": [],
        "veredito": "aprovada",
        "categoria_motivo": None,
        "motivo": "",
        "semelhanca": 0.1,
        "conferencia_local": "rodou",
        "modo_teste": False,
    }


def gabarito() -> dict[str, Any]:
    return {
        "copia": "r01_peticao_inicial_jec_001_erro1_1",
        "original": "r01_peticao_inicial_jec_001",
        "origem": "programa_regra",
        "tipo_erro": "valor_trocado",
        "sutil": False,
        "item_principal": "coerencia_ficha",
        "itens_aceitos": ["coerencia_ficha"],
        "criador": "programa",
        "verificador": None,
        "item_apontado_pelo_verificador": None,
        "amostra": None,
    }


def descartada() -> dict[str, Any]:
    return {
        "copia": "r01_peticao_inicial_jec_001_erro2_1",
        "original": "r01_peticao_inicial_jec_001",
        "tipo_erro": "cabimento",
        "sutil": True,
        "criador": "opus",
        "conferencia_que_falhou": "verificador",
        "item_apontado_pelo_verificador": None,
        "outro_problema": False,
        "motivo": "nao_viu_erro",
        "amostra": None,
    }


def rodada() -> dict[str, Any]:
    return {
        "id": "e01",
        "semente": 7,
        "impressoes": {"config/config.toml": "abc"},
        "ensaio_aprovado_origem": None,
        "estado": "aberta",
        "aberta_em": "2026-11-21T10:00:00+00:00",
        "ensaio_aprovado": False,
        "aprovado_em": None,
    }


def chamada() -> dict[str, Any]:
    return {
        "rodada": "e01",
        "peca": "e01_peticao_inicial_jec_001",
        "pedido": "e01_peticao_inicial_jec_001_v1_extracao_t1",
        "tarefa": "extracao",
        "modelo": "claude-haiku-5-5",
        "tokens_entrada": 100,
        "tokens_cache": 0,
        "tokens_raciocinio": 0,
        "tokens_saida": 50,
        "custo_milionesimos": 3500,
        "duracao_segundos": 1.5,
        "momento": "2026-11-21T10:00:05+00:00",
    }


def ocorrencia() -> dict[str, Any]:
    return {
        "tipo": "pausa",
        "causa": "api",
        "inicio": "2026-11-21T10:00:00+00:00",
        "fim": None,
        "peca": None,
        "rodada": "e01",
        "detalhe": "",
    }


def metadados() -> dict[str, Any]:
    return {
        "tipo": "Petição Inicial em Juizado Especial Cível",
        "classe_risco": "medio",
        "familia": "peticao_inicial",
        "perfil": "juizado_especial_civel",
        "materia": "negativacao_indevida",
        "tese": "inscrição sem débito",
        "polo": "autor",
        "complexidade": "media",
        "estilo": "detalhado",
        "ficha": ficha_inicial(),
        "identificador_processo": "SINT-PROC-0001",
        "semente": 42,
        "modelo_redator": "claude-sonnet-5-5",
        "esforco": "low",
        "versao_instrucoes": "abc",
        "custo_milionesimos": 1000,
        "versao_tabela_normas": "2026-11-21",
        "conferencia": [
            {"item": "coerencia_ficha", "resposta_final": "passa", "quem_final": "programa"}
        ],
        "conferencia_local_rodou": True,
        "marca_sintetico": "DOCUMENTO SINTÉTICO — FICTÍCIO",
    }


EXEMPLOS: list[tuple[type[BaseModel], Any]] = [
    (f.FichaInicial, ficha_inicial),
    (f.FichaEmbargos, ficha_embargos),
    (f.FichaManifestacao, ficha_manifestacao),
    (f.RespostaFichaInicial, resposta_ficha_inicial),
    (f.RespostaFichaEmbargos, resposta_ficha_embargos),
    (f.RespostaFichaManifestacao, resposta_ficha_manifestacao),
    (f.VisaoTravas, visao_travas),
    (f.Condicao, condicao),
    (f.Trava, trava),
    (f.Travas, lambda: {"travas": [trava()]}),
    (f.Dispositivo, dispositivo),
    (f.TabelaNormas, tabela_normas),
    (f.CatalogoTipos, lambda: {"tipos": [tipo_catalogo()]}),
    (f.Familia, lambda: {"id": "peticao_inicial", "blocos": [bloco()]}),
    (
        f.Perfil,
        lambda: {
            "id": "juizado_especial_civel",
            "familia": "peticao_inicial",
            "blocos": [bloco("alcada", 5)],
            "retirar": [],
            "ajustar": [],
            "pedidos_acessorios_padrao": ["citacao_reu"],
        },
    ),
    (
        f.Acrescimo,
        lambda: {"tipo": "embargos_declaracao", "blocos": [bloco()], "retirar": [], "ajustar": []},
    ),
    (
        f.EstruturaMontada,
        lambda: {
            "tipo": "peticao_inicial_jec",
            "familia": "peticao_inicial",
            "perfil": "juizado_especial_civel",
            "blocos": [bloco()],
            "pedidos_acessorios_padrao": ["citacao_reu"],
        },
    ),
    (f.Matriz, matriz),
    (
        f.ListaConferencia,
        lambda: {
            "itens": [
                {
                    "item": "cabimento",
                    "pergunta": "A peça é o instrumento certo?",
                    "quem": ["haiku"],
                    "eliminatorio": True,
                    "tipos": ["peticao_inicial_jec"],
                }
            ]
        },
    ),
    (
        f.TermosInequivocos,
        lambda: {"termos": [{"termo": "prazo em quádruplo", "motivo": "m", "norma": "n"}]},
    ),
    (f.PalavrasIgnoradas, lambda: {"comuns": ["de"], "juridicas": ["autor"]}),
    (
        f.FeriadosNacionais,
        lambda: {"feriados": [{"data": "2026-09-07", "nome": "Independência", "lei": "Lei"}]},
    ),
    (
        f.CatalogoErros,
        lambda: {
            "erros": [
                {
                    "tipo_erro": "valor_trocado",
                    "origem": "programa_regra",
                    "tipos": ["peticao_inicial_jec"],
                    "item_principal": "coerencia_ficha",
                    "itens_aceitos": ["coerencia_ficha"],
                    "descricao": "Troca um valor.",
                }
            ]
        },
    ),
    (
        f.ListasFicticias,
        lambda: {
            "ruas": ["Rua das Acácias Inventadas"],
            "bairros": ["Jardim Imaginário"],
            "cidades": [
                {
                    "nome": "Campinas",
                    "uf": "SP",
                    "cep_inicio": "13000-001",
                    "cep_fim": "13139-999",
                    "juizo_jec": "Juizado Especial Cível da Comarca de Campinas",
                    "varas_civeis": ["1ª Vara Cível da Comarca de Campinas"],
                }
            ],
            "profissoes": ["professor(a)"],
            "estados_civis": ["solteiro(a)"],
            "tribunais": [{"uf": "SP", "codigo": "26"}],
            "pedidos_incompativeis": [
                {"tipo": "peticao_inicial_jec", "rito": None, "texto": "citação por edital"}
            ],
        },
    ),
    (f.ReaisPermitidos, lambda: {"nomes": [{"nome": "SISBAJUD", "categoria": "sistema"}]}),
    (f.ReaisProibidos, lambda: {"nomes": [{"nome": "Empresa Exemplo", "categoria": "banco"}]}),
    (f.ReaisReservados, lambda: {"nomes": [{"nome": "Exemplo", "forma": "Exemplo S.A."}]}),
    (f.Pedido, pedido_api),
    (f.Resposta, resposta_api),
    (
        f.Rascunho,
        lambda: {
            "peca": "e01_peticao_inicial_jec_001",
            "versao": 1,
            "ficha": "e01_peticao_inicial_jec_001",
            "estrutura": "abc",
            "versao_instrucoes": "def",
            "modelo": "claude-sonnet-5-5",
            "tarefa": "redacao_risco_medio",
            "resposta": "e01_peticao_inicial_jec_001_v1_redacao_risco_medio_t1",
            "motivo_refacao": None,
        },
    ),
    (f.Extracao, extracao),
    (f.ResultadoItem, resultado_item),
    (
        f.ResultadoProgramas,
        lambda: {
            "itens": [resultado_item()],
            "alertas": [{"item": None, "origem": "citacoes", "texto": "art. 5º"}],
            "citacoes_resolvidas": [
                {
                    "diploma": "cdc",
                    "artigo": "14",
                    "paragrafo": "caput",
                    "inciso": None,
                    "alinea": None,
                    "trecho": "art. 14 do CDC",
                    "posicao": 3,
                }
            ],
            "citacoes_nao_resolvidas": [{"trecho": "art. 5º", "posicao": 40}],
        },
    ),
    (
        f.RespostaChecklist,
        lambda: {
            "itens": [{"item": "cabimento", "resposta": "passa", "trecho": "t"}],
            "citacoes": [{"citacao": "art. 5º", "resposta": "passa", "trecho": "t"}],
            "notas": notas(),
        },
    ),
    (
        f.RespostaLocal,
        lambda: {"itens": [{"item": "coerencia", "resposta": "passa", "trecho": "t"}]},
    ),
    (
        f.ResultadoConferenteLocal,
        lambda: {
            "resultado": "indisponivel",
            "causa": "porteiro",
            "respostas": None,
            "fracao_contexto": 0.4,
            "duracao_segundos": 0.0,
        },
    ),
    (
        f.RespostaDesempate,
        lambda: {"itens": [{"item": "coerencia", "resposta": "passa", "justificativa": "j"}]},
    ),
    (
        f.ResultadoSemelhanca,
        lambda: {
            "valor": 0.2,
            "comparada_com": None,
            "limite": 0.85,
            "reprova": False,
            "desligada": False,
        },
    ),
    (f.Conferencia, conferencia),
    (
        f.CopiaComErro,
        lambda: {
            "copia": "r01_peticao_inicial_jec_001_erro1_1",
            "original": "r01_peticao_inicial_jec_001",
            "trecho_original": "R$ 1.500,00",
            "trecho_novo": "R$ 1.980,00",
            "tipo_erro": "valor_trocado",
            "sutil": False,
            "criador": "programa",
        },
    ),
    (f.Gabarito, gabarito),
    (f.Descartada, descartada),
    (f.RespostaCopiaOpus, lambda: {"trecho_original": "a", "trecho_novo": "b"}),
    (
        f.RespostaVerificacao,
        lambda: {
            "item_apontado": "cabimento",
            "descricao_erro": "d",
            "outro_problema": False,
            "descricao_outro_problema": None,
        },
    ),
    (
        f.Cartao,
        lambda: {
            "id": "e01_peticao_inicial_jec_001",
            "tipo_cartao": "ensaio",
            "etapa": 1,
            "conteudo": "c",
        },
    ),
    (
        f.RespostasCartao,
        lambda: {
            "id_cartao": "e01_peticao_inicial_jec_001",
            "tipo_cartao": "revisao",
            "veredito_ficha": "aprovada",
            "veredito_peca": "reprovada",
            "dado_real": False,
            "dado_real_trecho": None,
            "citacoes_nao_resolvidas": [],
            "formato_certo": None,
            "formato_errado": None,
            "amostra": [],
            "data_confirmacao": "2026-11-21T10:00:00+00:00",
        },
    ),
    (f.Rodada, rodada),
    (f.Rodadas, lambda: {"rodadas": [rodada()]}),
    (f.Chamada, chamada),
    (f.Ocorrencia, ocorrencia),
    (f.Metadados, metadados),
]

IDS = [modelo.__name__ for modelo, _ in EXEMPLOS]


def _json(dados: Any) -> str:
    return json.dumps(dados, ensure_ascii=False)


@pytest.mark.parametrize(("modelo", "exemplo"), EXEMPLOS, ids=IDS)
def test_exemplo_valido_passa(modelo: type[BaseModel], exemplo: Any) -> None:
    modelo.model_validate_json(_json(exemplo()))


@pytest.mark.parametrize(("modelo", "exemplo"), EXEMPLOS, ids=IDS)
def test_campo_faltando_recusado(modelo: type[BaseModel], exemplo: Any) -> None:
    for campo in list(exemplo()):
        dados = exemplo()
        del dados[campo]
        with pytest.raises(ValidationError):
            modelo.model_validate_json(_json(dados))


@pytest.mark.parametrize(("modelo", "exemplo"), EXEMPLOS, ids=IDS)
def test_campo_a_mais_recusado(modelo: type[BaseModel], exemplo: Any) -> None:
    dados = exemplo()
    dados["campo_inventado"] = "x"
    with pytest.raises(ValidationError):
        modelo.model_validate_json(_json(dados))


# Campos que aceitam texto ou número por desenho (o valor comparado numa trava).
CAMPOS_LIVRES = {"valor"}


def _trocar_tipos(dados: dict[str, Any], livres: set[str] = frozenset()) -> list[dict[str, Any]]:
    """Uma cópia por campo de texto (vira número) e por campo de número (vira texto)."""
    copias = []
    for campo, valor in dados.items():
        if isinstance(valor, bool) or valor is None or campo in livres:
            continue
        if isinstance(valor, str):
            copia = copy.deepcopy(dados)
            copia[campo] = 123
            copias.append(copia)
        elif isinstance(valor, int | float):
            copia = copy.deepcopy(dados)
            copia[campo] = "123"
            copias.append(copia)
    return copias


@pytest.mark.parametrize(("modelo", "exemplo"), EXEMPLOS, ids=IDS)
def test_tipo_errado_recusado(modelo: type[BaseModel], exemplo: Any) -> None:
    livres = CAMPOS_LIVRES if modelo is f.Condicao else set()
    copias = _trocar_tipos(exemplo(), livres)
    for dados in copias:
        with pytest.raises(ValidationError):
            modelo.model_validate_json(_json(dados))


def test_todo_contrato_tem_exemplo_com_texto_ou_inteiro() -> None:
    sem_troca = [m.__name__ for m, e in EXEMPLOS if not _trocar_tipos(e())]
    # Estes só têm listas ou objetos no primeiro nível; o tipo errado é testado por dentro.
    assert set(sem_troca) <= {
        "Travas",
        "CatalogoTipos",
        "ListaConferencia",
        "TermosInequivocos",
        "PalavrasIgnoradas",
        "FeriadosNacionais",
        "CatalogoErros",
        "ListasFicticias",
        "ReaisPermitidos",
        "ReaisProibidos",
        "ReaisReservados",
        "ResultadoProgramas",
        "RespostaChecklist",
        "RespostaLocal",
        "RespostaDesempate",
        "Rodadas",
        "RespostaFichaManifestacao",
    }


def test_tipo_errado_dentro_de_lista() -> None:
    dados = {"travas": [trava()]}
    dados["travas"][0]["base_legal"] = 9
    with pytest.raises(ValidationError):
        f.Travas.model_validate_json(_json(dados))


@pytest.mark.parametrize("data", ["15/03/2026", "2026-3-15", "20260315", "2026-13-01"])
def test_data_fora_do_formato_recusada(data: str) -> None:
    dados = ficha_inicial()
    dados["data_peca"] = data
    with pytest.raises(ValidationError):
        f.FichaInicial.model_validate_json(_json(dados))


def test_dinheiro_com_casas_decimais_recusado() -> None:
    dados = ficha_inicial()
    dados["valores"][0]["centavos"] = 1500.50
    with pytest.raises(ValidationError):
        f.FichaInicial.model_validate_json(_json(dados))
    dados = extracao()
    dados["valores"][0]["centavos"] = 1500.0
    with pytest.raises(ValidationError):
        f.Extracao.model_validate_json(_json(dados))


@pytest.mark.parametrize(
    ("modelo", "exemplo", "caminho", "valor"),
    [
        (f.FichaInicial, ficha_inicial, ("partes", 0, "categoria"), "pessoa_estrangeira"),
        (f.FichaInicial, ficha_inicial, ("pedidos", 0, "natureza"), "suprir_omissao"),
        (f.FichaInicial, ficha_inicial, ("pedidos", 0, "natureza"), "outro"),
        (f.FichaEmbargos, ficha_embargos, ("pedidos", 0, "natureza"), "danos_morais"),
        (f.FichaEmbargos, ficha_embargos, ("defeito", "tipo"), "omissao"),
        (f.FichaEmbargos, ficha_embargos, ("defeito", "ancora", "origem"), "sentenca"),
        (f.FichaEmbargos, ficha_embargos, ("decisao_embargada", "tipo"), "acordao"),
        (
            f.FichaEmbargos,
            ficha_embargos,
            ("argumentos_das_partes", 0, "peca_de_origem"),
            "apelacao",
        ),
        (f.FichaManifestacao, ficha_manifestacao, ("pedido_ar",), "citacao_por_edital"),
        (
            f.FichaManifestacao,
            ficha_manifestacao,
            ("aviso_recebimento", "motivo_devolucao"),
            "recusado",
        ),
        (f.FichaManifestacao, ficha_manifestacao, ("meio_nova_diligencia",), "edital"),
        (f.FichaManifestacao, ficha_manifestacao, ("prazo_pedido_dias",), 5),
        (f.Extracao, extracao, ("valores", 0, "lugar"), "fundamentacao"),
        (f.Extracao, extracao, ("pedidos", 0, "natureza"), "honorarios"),
        (f.Extracao, extracao, ("documentos", 0, "tipo"), "rg"),
        (f.Extracao, extracao, ("nomes", 0, "papel"), "juiz"),
        (f.Dispositivo, dispositivo, ("funcao",), "regra"),
        (f.Condicao, condicao, ("op",), "contem"),
        (f.Trava, trava, ("efeito",), "permite"),
        (f.Conferencia, conferencia, ("veredito",), "reprovada"),
        (f.Conferencia, conferencia, ("categoria_motivo",), "estilo"),
        (f.Conferencia, conferencia, ("itens", 0, "item"), "ortografia"),
        (f.Gabarito, gabarito, ("origem",), "sonnet"),
        (f.Gabarito, gabarito, ("tipo_erro",), "erro_qualquer"),
        (f.Gabarito, gabarito, ("amostra",), "talvez"),
        (f.Descartada, descartada, ("motivo",), "nao_gostou"),
        (f.Descartada, descartada, ("conferencia_que_falhou",), "haiku"),
        (f.Descartada, descartada, ("amostra",), "aceita"),
        (f.Rodada, rodada, ("estado",), "pausada"),
        (f.Rodada, rodada, ("id",), "x01"),
        (f.Ocorrencia, ocorrencia, ("tipo",), "erro"),
        (f.Resposta, resposta_api, ("situacao",), "estranha"),
        (
            f.ResultadoConferenteLocal,
            lambda: {
                "resultado": "rodou",
                "causa": None,
                "respostas": None,
                "fracao_contexto": 0.1,
                "duracao_segundos": 1.0,
            },
            ("resultado",),
            "caiu",
        ),
        (
            f.ResultadoConferenteLocal,
            lambda: {
                "resultado": "indisponivel",
                "causa": "porteiro",
                "respostas": None,
                "fracao_contexto": 0.1,
                "duracao_segundos": 1.0,
            },
            ("causa",),
            "luz",
        ),
        (f.Metadados, metadados, ("marca_sintetico",), "documento"),
        (f.TipoCatalogo, tipo_catalogo, ("rotulo",), "Petição Inicial"),
        (f.TipoCatalogo, tipo_catalogo, ("nome_curto",), "inicial"),
        (f.TipoCatalogo, tipo_catalogo, ("classe_risco",), "altissimo"),
        (
            f.RespostaChecklist,
            lambda: {
                "itens": [],
                "citacoes": [],
                "notas": notas(),
            },
            ("notas", "clareza"),
            6,
        ),
    ],
)
def test_lista_fechada_recusa_valor_de_fora(
    modelo: type[BaseModel], exemplo: Any, caminho: tuple[Any, ...], valor: Any
) -> None:
    dados = exemplo()
    alvo = dados
    for chave in caminho[:-1]:
        alvo = alvo[chave]
    alvo[caminho[-1]] = valor
    with pytest.raises(ValidationError):
        modelo.model_validate_json(_json(dados))


def test_inicial_recusa_rito_comum_e_embargos_recusa_juizado() -> None:
    dados = ficha_inicial()
    dados["processo"]["rito"] = "procedimento_comum"
    with pytest.raises(ValidationError):
        f.FichaInicial.model_validate_json(_json(dados))
    dados = ficha_embargos()
    dados["processo"]["rito"] = "juizado_especial_civel"
    with pytest.raises(ValidationError):
        f.FichaEmbargos.model_validate_json(_json(dados))


def test_ficha_escolhida_pelo_tipo() -> None:
    for exemplo, classe in (
        (ficha_inicial, f.FichaInicial),
        (ficha_embargos, f.FichaEmbargos),
        (ficha_manifestacao, f.FichaManifestacao),
    ):
        ficha = f.Ficha.model_validate_json(_json(exemplo()))
        assert isinstance(ficha.root, classe)
    dados = ficha_inicial()
    dados["tipo"] = "Embargos de Declaração"
    with pytest.raises(ValidationError):
        f.Ficha.model_validate_json(_json(dados))


def test_ficha_exige_um_autor_e_um_reu() -> None:
    dados = ficha_inicial()
    dados["partes"] = [parte("autor"), parte("autor")]
    with pytest.raises(ValidationError):
        f.FichaInicial.model_validate_json(_json(dados))


def _objetos(no: Any) -> list[dict[str, Any]]:
    achados: list[dict[str, Any]] = []
    if isinstance(no, dict):
        if no.get("type") == "object" or "properties" in no:
            achados.append(no)
        for valor in no.values():
            achados.extend(_objetos(valor))
    elif isinstance(no, list):
        for valor in no:
            achados.extend(_objetos(valor))
    return achados


@pytest.mark.parametrize("nome", sorted(f.MODELOS_RESPOSTA))
def test_esquema_das_respostas_proibe_campo_a_mais(nome: str) -> None:
    esquema = f.esquema_resposta(f.MODELOS_RESPOSTA[nome])
    objetos = _objetos(esquema)
    assert objetos
    assert all(objeto.get("additionalProperties") is False for objeto in objetos)
