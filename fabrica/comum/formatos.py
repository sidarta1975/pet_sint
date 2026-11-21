"""Todos os contratos de dados da fábrica (ARQUITETURA §3 e Anexos A a E).

Cada modelo é estrito: campo faltando, campo a mais e tipo errado são recusados.
Dinheiro em centavos, inteiro; datas ano-mês-dia; horários com fuso.
Os mesmos modelos geram o esquema JSON das respostas estruturadas
(`esquema_resposta`).
"""

from __future__ import annotations

import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, RootModel, model_validator


class Modelo(BaseModel):
    """Base de todos os contratos: estrito, sem campo a mais e imutável."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)


# ---------------------------------------------------------------------------
# Listas fechadas (valores exatos dos canônicos)
# ---------------------------------------------------------------------------

RotuloTipo = Literal[
    "Petição Inicial em Juizado Especial Cível",
    "Embargos de Declaração",
    "Manifestação sobre Aviso de Recebimento Negativo",
]
NomeCurto = Literal["peticao_inicial_jec", "embargos_declaracao", "manifestacao_ar_negativo"]
ClasseRisco = Literal["baixo", "medio", "alto"]
Rito = Literal["juizado_especial_civel", "procedimento_comum"]
Categoria = Literal[
    "pessoa_fisica",
    "mei",
    "microempresa",
    "empresa_pequeno_porte",
    "pessoa_juridica_privada",
    "pessoa_juridica_direito_publico",
    "empresa_publica_uniao",
    "massa_falida",
]
Papel = Literal["autor", "reu"]
Complexidade = Literal["simples", "media"]
Estilo = Literal["conciso", "detalhado"]

NaturezaInicial = Literal[
    "citacao_reu",
    "inversao_onus",
    "tutela_urgencia",
    "danos_morais",
    "danos_materiais",
    "restituicao_simples",
    "restituicao_em_dobro",
    "obrigacao_fazer",
    "declaracao_inexistencia_debito",
    "exclusao_cadastro",
    "producao_provas",
]
NaturezaEmbargos = Literal[
    "acolhimento_embargos",
    "suprir_omissao",
    "eliminar_contradicao",
    "esclarecer_obscuridade",
    "corrigir_erro_material",
    "efeito_modificativo",
    "intimacao_parte_contraria",
]
NaturezaManifestacao = Literal[
    "nova_citacao_novo_endereco",
    "renovacao_mesmo_endereco",
    "ciencia",
    "concessao_prazo",
]
NaturezaQualquer = NaturezaInicial | NaturezaEmbargos | NaturezaManifestacao
NaturezaExtraida = NaturezaInicial | NaturezaEmbargos | NaturezaManifestacao | Literal["outro"]

TipoDefeito = Literal[
    "omissao_total", "omissao_parcial", "contradicao", "obscuridade", "erro_material"
]
OrigemAncora = Literal["decisao", "argumento"]
TipoDecisao = Literal["sentenca", "decisao_interlocutoria"]
PecaOrigemArgumento = Literal["inicial", "contestacao", "replica", "manifestacao"]
MotivoDevolucao = Literal[
    "mudou_se",
    "desconhecido",
    "endereco_insuficiente",
    "numero_inexistente",
    "ausente",
    "nao_procurado",
]
PedidoAR = Literal["informar_novo_endereco", "renovar_mesmo_endereco", "ciencia_e_prazo"]
MeioDiligencia = Literal["correio", "oficial_de_justica"]
Lugar = Literal["fatos", "pedido", "valor_causa", "outro"]
Funcao = Literal["requisito", "prazo", "competencia", "excecao", "consequencia", "definicao"]
Operacao = Literal[
    "igual", "diferente", "maior", "menor", "na_lista", "fora_da_lista", "vazio", "preenchido"
]
Efeito = Literal["proibe", "exige"]

ItemPrograma = Literal[
    "estrutura",
    "citacao_fora_da_tabela",
    "termos_inequivocos",
    "coerencia_ficha",
    "alcada",
    "prazo",
    "dado_real",
    "marca",
    "semelhanca",
]
ItemConferente = Literal[
    "cabimento",
    "competencia_enderecamento",
    "prazo_e_momento",
    "legitimidade",
    "pedidos",
    "fundamento",
    "coerencia",
    "pecas_anteriores",
    "argumentacao_suficiente",
    "texto_generico",
]
ItemConferencia = ItemPrograma | ItemConferente | Literal["estilo"]
ItemLocal = Literal["coerencia", "pecas_anteriores", "texto_generico"]

Veredito = Literal["aprovada", "refazer", "descartada"]
CategoriaMotivo = Literal["conteudo", "semelhanca", "ambos", "formato"]
RespostaItem = Literal["passa", "nao_passa"]
Conferente = Literal["programa", "haiku", "local", "opus"]

OrigemErro = Literal["programa_regra", "programa_julgamento", "opus"]
TipoErroRegra = Literal[
    "valor_trocado",
    "data_trocada",
    "fora_do_prazo",
    "acima_da_alcada",
    "citacao_fora_da_tabela",
    "juizo_trocado",
    "termo_inequivoco",
    "pedido_incompativel_com_rito",
]
TipoErroJulgamento = Literal["funcao_trocada"]
TipoErroOpus = Literal[
    "cabimento",
    "competencia",
    "prazo_e_momento",
    "legitimidade",
    "pedido_incompativel",
    "fundamento_nao_sustenta",
    "fato_contraditorio",
    "peca_anterior_distorcida",
    "argumentacao_generica",
    "texto_generico",
]
TipoErro = TipoErroRegra | TipoErroJulgamento | TipoErroOpus
MotivoDescarte = Literal["outro_problema", "outro_item", "nao_viu_erro"]
ConferenciaQueFalhou = Literal["programa", "verificador"]
AmostraGabarito = Literal["aceita", "rejeitada"]
AmostraDescartada = Literal["erro_existe", "erro_nao_existe"]

TipoCartao = Literal[
    "revisao", "ensaio", "amostra_copias", "amostra_descartadas", "leitura_publicacao"
]
EstadoRodada = Literal["aberta", "parada", "encerrada", "invalida"]
TipoOcorrencia = Literal["pausa", "parada", "intervencao", "contexto"]
ResultadoLocal = Literal["rodou", "esperou_e_rodou", "indisponivel"]
CausaIndisponivel = Literal["porteiro", "contexto", "janela", "falha"]
SituacaoResposta = Literal["ok", "fora_do_formato", "recusa", "cortada"]
TipoDocumento = Literal["cpf", "cnpj", "oab", "numero_processo", "protocolo", "contrato", "cep"]
PapelNome = Literal["autor", "reu", "advogado", "outro"]
TarefaRedacao = Literal["redacao_risco_baixo", "redacao_risco_medio", "redacao_risco_alto"]
Tarefa = Literal[
    "ficha",
    "redacao_risco_baixo",
    "redacao_risco_medio",
    "redacao_risco_alto",
    "extracao",
    "checklist",
    "conferencia_opus",
    "copia_com_erro",
    "verificacao_copia",
    "conferente_local",
]

ROTULO_POR_NOME: dict[str, str] = {
    "peticao_inicial_jec": "Petição Inicial em Juizado Especial Cível",
    "embargos_declaracao": "Embargos de Declaração",
    "manifestacao_ar_negativo": "Manifestação sobre Aviso de Recebimento Negativo",
}
NOME_POR_ROTULO: dict[str, str] = {rotulo: nome for nome, rotulo in ROTULO_POR_NOME.items()}

Centavos = Annotated[int, Field(ge=0)]
DataParcial = Annotated[str, Field(pattern=r"^\d{4}-\d{2}(-\d{2})?$")]
Nota = Annotated[int, Field(ge=1, le=5)]


# ---------------------------------------------------------------------------
# Ficha (Anexo A)
# ---------------------------------------------------------------------------


class Endereco(Modelo):
    rua: str
    numero: str
    complemento: str | None
    bairro: str
    cidade: str
    estado: str
    cep: str


class Parte(Modelo):
    id: str
    papel: Papel
    categoria: Categoria
    nome: str
    documento: str
    estado_civil: str | None
    profissao: str | None
    endereco: Endereco
    email: str
    telefone: str
    capaz: bool | None
    preso: bool | None


class Advogado(Modelo):
    nome: str
    oab: str
    email: str
    telefone: str
    endereco_escritorio: Endereco
    representa: str


class CasaMatriz(Modelo):
    materia: str
    tese: str
    polo: Papel
    complexidade: Complexidade
    momento: str
    estilo: Estilo


class Processo(Modelo):
    identificador_ficticio: str
    numero_cnj: str | None
    rito: Rito
    comarca: str
    uf: str
    juizo: str
    data_ajuizamento: datetime.date


class Fato(Modelo):
    data: datetime.date
    descricao: str
    valores: list[str]


class Valor(Modelo):
    id: str
    descricao: str
    centavos: Centavos
    data_referencia: datetime.date | None


class Prova(Modelo):
    id: str
    descricao: str
    identificador: str


class PedidoInicial(Modelo):
    id: str
    natureza: NaturezaInicial
    descricao: str
    valor: str | None


class PedidoEmbargos(Modelo):
    id: str
    natureza: NaturezaEmbargos
    descricao: str
    valor: str | None


class PedidoManifestacao(Modelo):
    id: str
    natureza: NaturezaManifestacao
    descricao: str
    valor: str | None


class PrazoProcessual(Modelo):
    inicio: datetime.date
    dias_uteis: int
    termo_final: datetime.date


class MomentoProcessual(Modelo):
    fase: str
    ultima_decisao: str
    prazo: PrazoProcessual | None


class PecaAnterior(Modelo):
    tipo: str
    data: datetime.date
    resumo: str
    texto: str | None


class TutelaUrgencia(Modelo):
    pedida: bool
    fundamento: str | None


class TentativaPrevia(Modelo):
    data: datetime.date
    protocolo: str


class DecisaoEmbargada(Modelo):
    tipo: TipoDecisao
    data: datetime.date
    data_intimacao: datetime.date
    juizo: str
    relatorio: str | None
    fundamentacao: str
    dispositivo: str


class Argumento(Modelo):
    id: str
    parte: str
    peca_de_origem: PecaOrigemArgumento
    texto: str


class Ancora(Modelo):
    origem: OrigemAncora
    argumento_id: str | None
    trecho_literal: str


class Defeito(Modelo):
    tipo: TipoDefeito
    ancora: Ancora
    trecho_mencao: str | None
    descricao: str
    efeito_modificativo: bool


class AvisoRecebimento(Modelo):
    data_juntada: datetime.date
    motivo_devolucao: MotivoDevolucao


class DeterminacaoJudicial(Modelo):
    data_intimacao: datetime.date
    prazo_dias_uteis: int


class FichaComum(Modelo):
    """Campos comuns a todos os tipos (Anexo A.1)."""

    id: str
    classe_risco: ClasseRisco
    casa_matriz: CasaMatriz
    semente: int
    processo: Processo
    partes: list[Parte]
    advogado: Advogado
    fatos: list[Fato]
    valores: list[Valor]
    provas: list[Prova]
    valor_causa: str | None
    fundamentos: list[str]
    momento_processual: MomentoProcessual
    pecas_anteriores: list[PecaAnterior]
    data_peca: datetime.date
    local_peca: str

    @model_validator(mode="after")
    def _um_autor_e_um_reu(self) -> FichaComum:
        papeis = sorted(parte.papel for parte in self.partes)
        if papeis != ["autor", "reu"]:
            raise ValueError("no MVP, partes tem exatamente uma parte autora e uma ré")
        return self


class FichaInicial(FichaComum):
    """Petição Inicial em Juizado Especial Cível (Anexo A.2)."""

    tipo: Literal["Petição Inicial em Juizado Especial Cível"]
    pedidos: list[PedidoInicial]
    materia: str
    relacao_consumo: bool
    inversao_onus_pedida: bool
    tutela_urgencia: TutelaUrgencia
    tentativa_previa: TentativaPrevia | None
    salario_minimo_referencia: Centavos

    @model_validator(mode="after")
    def _rito_do_juizado(self) -> FichaInicial:
        if self.processo.rito != "juizado_especial_civel":
            raise ValueError("a petição inicial do MVP é sempre juizado_especial_civel")
        return self


class FichaEmbargos(FichaComum):
    """Embargos de Declaração (Anexo A.3)."""

    tipo: Literal["Embargos de Declaração"]
    pedidos: list[PedidoEmbargos]
    embargante: str
    decisao_embargada: DecisaoEmbargada
    argumentos_das_partes: list[Argumento]
    defeito: Defeito

    @model_validator(mode="after")
    def _rito_comum(self) -> FichaEmbargos:
        if self.processo.rito != "procedimento_comum":
            raise ValueError("os embargos do MVP são sempre procedimento_comum")
        return self


class FichaManifestacao(FichaComum):
    """Manifestação sobre Aviso de Recebimento Negativo (Anexo A.4)."""

    tipo: Literal["Manifestação sobre Aviso de Recebimento Negativo"]
    pedidos: list[PedidoManifestacao]
    peticionante: str
    citando: str
    endereco_tentado: Endereco
    aviso_recebimento: AvisoRecebimento
    determinacao_judicial: DeterminacaoJudicial
    pedido_ar: PedidoAR
    novo_endereco: Endereco | None
    meio_nova_diligencia: MeioDiligencia | None
    prazo_pedido_dias: Annotated[int, Field(ge=10, le=30)] | None


FichaQualquer = FichaInicial | FichaEmbargos | FichaManifestacao


class Ficha(RootModel[Annotated[FichaQualquer, Field(discriminator="tipo")]]):
    """A ficha de qualquer tipo, escolhida pelo campo `tipo` (união discriminada)."""

    model_config = ConfigDict(strict=True, frozen=True)


# ---------------------------------------------------------------------------
# Base da ficha: o que o programa sorteia antes do pedido ao Haiku (brief 015)
# ---------------------------------------------------------------------------


class BaseFicha(Modelo):
    """Casa da matriz, combinação sorteada, dados fictícios e número da tentativa.

    Gravada em `saida/fichas/<peça>_base.json` antes do pedido. `casa` é a posição
    da casa no sorteio do tipo (1 a 10); `tentativa` é 1 na ficha original e 2 ou 3
    nas fichas novas da mesma casa.
    """

    peca: str
    rodada: str
    tipo: RotuloTipo
    classe_risco: ClasseRisco
    semente: int
    casa: Annotated[int, Field(ge=1)]
    tentativa: Annotated[int, Field(ge=1)]
    casa_matriz: CasaMatriz
    rito: Rito
    categoria_autor: Categoria
    categoria_reu: Categoria
    defeito: TipoDefeito | None
    tipo_decisao: TipoDecisao | None
    motivo_devolucao: MotivoDevolucao | None
    pedido_ar: PedidoAR | None
    processo: Processo
    partes: list[Parte]
    advogado: Advogado
    identificadores: list[str]
    salario_minimo_referencia: Centavos
    limite_fatos: datetime.date
    data_decisao: datetime.date | None
    data_intimacao: datetime.date | None
    data_juntada_aviso: datetime.date | None
    fase: str
    prazo: PrazoProcessual | None
    data_peca: datetime.date
    local_peca: str
    endereco_tentado: Endereco | None
    novo_endereco: Endereco | None
    meio_nova_diligencia: MeioDiligencia | None
    prazo_pedido_dias: Annotated[int, Field(ge=10, le=30)] | None


# ---------------------------------------------------------------------------
# Resposta do Haiku para a ficha (só a parte que o programa não sorteia)
# ---------------------------------------------------------------------------


class MomentoResposta(Modelo):
    ultima_decisao: str


class DecisaoEmbargadaResposta(Modelo):
    tipo: TipoDecisao
    data: datetime.date
    juizo: str
    relatorio: str | None
    fundamentacao: str
    dispositivo: str


class DefeitoResposta(Modelo):
    ancora: Ancora
    trecho_mencao: str | None
    descricao: str
    efeito_modificativo: bool


class RespostaFichaComum(Modelo):
    fatos: list[Fato]
    valores: list[Valor]
    provas: list[Prova]
    valor_causa: str | None
    fundamentos: list[str]
    momento_processual: MomentoResposta
    pecas_anteriores: list[PecaAnterior]


class RespostaFichaInicial(RespostaFichaComum):
    pedidos: list[PedidoInicial]
    relacao_consumo: bool
    inversao_onus_pedida: bool
    tutela_urgencia: TutelaUrgencia
    tentativa_previa: TentativaPrevia | None


class RespostaFichaEmbargos(RespostaFichaComum):
    pedidos: list[PedidoEmbargos]
    decisao_embargada: DecisaoEmbargadaResposta
    argumentos_das_partes: list[Argumento]
    defeito: DefeitoResposta


class RespostaFichaManifestacao(RespostaFichaComum):
    pedidos: list[PedidoManifestacao]


# ---------------------------------------------------------------------------
# Travas (Anexo A.5)
# ---------------------------------------------------------------------------


class VisaoTravas(Modelo):
    """Visão plana da ficha ou da combinação, com os nomes do Anexo A.5."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True, populate_by_name=True)

    tipo: RotuloTipo
    processo_rito: Rito | None = Field(alias="processo.rito")
    materia: str | None
    autor_categoria: Categoria | None = Field(alias="autor.categoria")
    autor_capaz: bool | None = Field(alias="autor.capaz")
    autor_preso: bool | None = Field(alias="autor.preso")
    reu_categoria: Categoria | None = Field(alias="reu.categoria")
    reu_capaz: bool | None = Field(alias="reu.capaz")
    reu_preso: bool | None = Field(alias="reu.preso")
    valor_causa_centavos: int | None
    alcada_centavos: int | None
    defeito_tipo: TipoDefeito | None = Field(alias="defeito.tipo")
    defeito_ancora_argumento_id: str | None = Field(alias="defeito.ancora.argumento_id")
    defeito_trecho_mencao: str | None = Field(alias="defeito.trecho_mencao")
    pedido_ar: PedidoAR | None
    aviso_recebimento_motivo_devolucao: MotivoDevolucao | None = Field(
        alias="aviso_recebimento.motivo_devolucao"
    )
    novo_endereco: str | None
    meio_nova_diligencia: MeioDiligencia | None
    nova_diligencia: bool | None


ValorCondicao = str | int | bool | list[str] | None


class Condicao(Modelo):
    campo: str
    op: Operacao
    valor: ValorCondicao
    outro_campo: str | None


class Trava(Modelo):
    condicoes: list[Condicao]
    efeito: Efeito
    campo_exigido: str | None
    base_legal: str
    dispositivos: list[str]


class Travas(Modelo):
    travas: list[Trava]


# ---------------------------------------------------------------------------
# Tabela de normas e citações
# ---------------------------------------------------------------------------


class Dispositivo(Modelo):
    id: str
    diploma: str
    artigo: str
    paragrafo: str
    assunto: str
    funcao: Funcao
    texto_vigente: str
    tipos: list[NomeCurto]
    fonte: str
    data_conferencia: datetime.date


class Diploma(Modelo):
    id: str
    nome: str
    formas: list[str]


class TabelaNormas(Modelo):
    versao: str
    diplomas: list[Diploma]
    dispositivos: list[Dispositivo]


class CitacaoResolvida(Modelo):
    diploma: str
    artigo: str
    paragrafo: str
    inciso: str | None
    alinea: str | None
    trecho: str
    posicao: int


class CitacaoNaoResolvida(Modelo):
    trecho: str
    posicao: int


# ---------------------------------------------------------------------------
# Formatos de dados/
# ---------------------------------------------------------------------------


class TipoCatalogo(Modelo):
    rotulo: RotuloTipo
    nome_curto: NomeCurto
    familia: str
    perfil: str
    classe_risco: ClasseRisco
    tarefa_redacao: TarefaRedacao
    quantidade: int
    depende_peca_anterior: bool
    itens_conferencia: list[ItemConferencia]


class CatalogoTipos(Modelo):
    tipos: list[TipoCatalogo]


class Bloco(Modelo):
    nome: str
    titulo: str
    ordem: int
    obrigatorio: bool
    descricao: str


class Familia(Modelo):
    id: str
    blocos: list[Bloco]


class Perfil(Modelo):
    id: str
    familia: str
    blocos: list[Bloco]
    retirar: list[str]
    ajustar: list[Bloco]
    pedidos_acessorios_padrao: list[str]


class Acrescimo(Modelo):
    tipo: NomeCurto
    blocos: list[Bloco]
    retirar: list[str]
    ajustar: list[Bloco]


class EstruturaMontada(Modelo):
    """Estrutura completa de um tipo, gravada em saida/preparacao/ (registro de decisão 001)."""

    tipo: NomeCurto
    familia: str
    perfil: str
    blocos: list[Bloco]
    pedidos_acessorios_padrao: list[str]


class Contagem(Modelo):
    valor: str
    quantidade: int


class EixoFixo(Modelo):
    eixo: Literal["complexidade", "estilo", "polo", "defeito", "tipo_decisao", "rito"]
    contagens: list[Contagem]


class MateriaMatriz(Modelo):
    materia: str
    teses: list[str]
    quantidade: int | None


class Matriz(Modelo):
    tipo: NomeCurto
    quantidade: int
    momento: str
    materias: list[MateriaMatriz]
    teto_por_materia: int
    eixos_fixos: list[EixoFixo]
    categorias_autor: list[Categoria]
    categorias_reu: list[Categoria]
    motivos_devolucao: list[MotivoDevolucao]
    pedidos_ar: list[PedidoAR]


class ItemLista(Modelo):
    item: ItemConferencia
    pergunta: str
    quem: list[Conferente]
    eliminatorio: bool
    tipos: list[NomeCurto]


class ListaConferencia(Modelo):
    itens: list[ItemLista]


class TermoInequivoco(Modelo):
    termo: str
    motivo: str
    norma: str


class TermosInequivocos(Modelo):
    termos: list[TermoInequivoco]


class PalavrasIgnoradas(Modelo):
    comuns: list[str]
    juridicas: list[str]


class Feriado(Modelo):
    data: datetime.date
    nome: str
    lei: str


class FeriadosNacionais(Modelo):
    feriados: list[Feriado]


class TipoErroCatalogo(Modelo):
    tipo_erro: TipoErro
    origem: OrigemErro
    tipos: list[NomeCurto]
    item_principal: ItemConferencia
    itens_aceitos: list[ItemConferencia]
    descricao: str


class CatalogoErros(Modelo):
    erros: list[TipoErroCatalogo]


class Cidade(Modelo):
    nome: str
    uf: str
    cep_inicio: str
    cep_fim: str
    juizo_jec: str
    varas_civeis: list[str]


class Tribunal(Modelo):
    uf: str
    codigo: str


class PedidoIncompativel(Modelo):
    tipo: NomeCurto
    rito: Rito | None
    texto: str


class ListasFicticias(Modelo):
    ruas: list[str]
    bairros: list[str]
    cidades: list[Cidade]
    profissoes: list[str]
    estados_civis: list[str]
    tribunais: list[Tribunal]
    pedidos_incompativeis: list[PedidoIncompativel]


class NomeReal(Modelo):
    nome: str
    categoria: str


class ReaisPermitidos(Modelo):
    nomes: list[NomeReal]


class ReaisProibidos(Modelo):
    nomes: list[NomeReal]


class NomeReservado(Modelo):
    nome: str
    forma: str


class ReaisReservados(Modelo):
    nomes: list[NomeReservado]


# ---------------------------------------------------------------------------
# Pedido e resposta (ARQUITETURA §3 e §7.1)
# ---------------------------------------------------------------------------


class ParteDoPedido(Modelo):
    nome: Literal["instrucoes", "estrutura", "trecho", "ficha", "motivo", "conteudo"]
    texto: str


class Pedido(Modelo):
    nome: str
    servico: Literal["claude", "local"]
    rodada: str
    peca: str
    versao: int | None
    tarefa: Tarefa
    tentativa: int
    modelo: str
    esforco: str | None
    teto_saida: int
    partes: list[ParteDoPedido]
    formato: str | None
    esquema: dict[str, Any] | None
    criado_em: datetime.datetime


class Tokens(Modelo):
    entrada: int
    cache: int
    raciocinio: int
    saida: int


class Resposta(Modelo):
    pedido: str
    modelo: str
    conteudo: str
    bruto: dict[str, Any] | None
    motivo_parada: str | None
    tokens: Tokens
    situacao: SituacaoResposta
    recebida_em: datetime.datetime


# ---------------------------------------------------------------------------
# Rascunho, extração e conferência
# ---------------------------------------------------------------------------


class Rascunho(Modelo):
    peca: str
    versao: int
    ficha: str
    estrutura: str
    versao_instrucoes: str
    modelo: str
    tarefa: TarefaRedacao
    resposta: str
    motivo_refacao: str | None


class NomeExtraido(Modelo):
    texto: str
    papel: PapelNome


class DocumentoExtraido(Modelo):
    tipo: TipoDocumento
    texto: str


class ValorExtraido(Modelo):
    texto: str
    centavos: int
    lugar: Lugar
    pedido: str | None


class DataExtraida(Modelo):
    texto: str
    data: DataParcial | None


class PedidoExtraido(Modelo):
    natureza: NaturezaExtraida
    texto: str


class Extracao(Modelo):
    nomes: list[NomeExtraido]
    documentos: list[DocumentoExtraido]
    valores: list[ValorExtraido]
    datas: list[DataExtraida]
    comarca: str | None
    juizo: str | None
    pedidos: list[PedidoExtraido]
    pecas_anteriores: list[str]
    data_peca: DataParcial | None


class Divergencia(Modelo):
    regra: str
    extraido: str
    ficha: str


class ResultadoItem(Modelo):
    item: ItemConferencia
    resposta: RespostaItem
    quem: Conferente
    trecho: str
    divergencias: list[Divergencia]


class Alerta(Modelo):
    item: ItemConferencia | None
    origem: str
    texto: str


class ResultadoProgramas(Modelo):
    """Itens de programa sobre o rascunho (`<peça>_v<k>_programas.json`)."""

    itens: list[ResultadoItem]
    alertas: list[Alerta]
    citacoes_resolvidas: list[CitacaoResolvida]
    citacoes_nao_resolvidas: list[CitacaoNaoResolvida]


class NotasEstilo(Modelo):
    clareza: Nota
    concisao: Nota
    linguagem_tecnica: Nota


class ItemChecklist(Modelo):
    item: ItemConferente
    resposta: RespostaItem
    trecho: str


class RespostaCitacao(Modelo):
    citacao: str
    resposta: RespostaItem
    trecho: str


class RespostaChecklist(Modelo):
    itens: list[ItemChecklist]
    citacoes: list[RespostaCitacao]
    notas: NotasEstilo


class ItemRespostaLocal(Modelo):
    item: ItemLocal
    resposta: RespostaItem
    trecho: str


class RespostaLocal(Modelo):
    itens: list[ItemRespostaLocal]


class ResultadoConferenteLocal(Modelo):
    """Resultado do conferente local (`<peça>_v<k>_local.json`)."""

    resultado: ResultadoLocal
    causa: CausaIndisponivel | None
    respostas: RespostaLocal | None
    fracao_contexto: float
    duracao_segundos: float


class ItemDesempate(Modelo):
    item: ItemConferente
    resposta: RespostaItem
    justificativa: str


class RespostaDesempate(Modelo):
    itens: list[ItemDesempate]


class ResultadoSemelhanca(Modelo):
    valor: float | None
    comparada_com: str | None
    limite: float
    reprova: bool
    desligada: bool


class CaminhoItem(Modelo):
    item: ItemConferencia
    respostas: list[ResultadoItem]
    regra: str
    resposta_final: RespostaItem
    quem_final: Conferente


class Conferencia(Modelo):
    """Veredito final de uma versão (`<peça>_v<k>.json`)."""

    peca: str
    versao: int
    extracao: Extracao | None
    itens: list[ResultadoItem]
    caminho: list[CaminhoItem]
    notas_estilo: NotasEstilo | None
    alertas: list[Alerta]
    veredito: Veredito
    categoria_motivo: CategoriaMotivo | None
    motivo: str
    semelhanca: float | None
    conferencia_local: ResultadoLocal | None
    modo_teste: bool


# ---------------------------------------------------------------------------
# Erros plantados e gabarito (Anexo C)
# ---------------------------------------------------------------------------


class CopiaComErro(Modelo):
    copia: str
    original: str
    trecho_original: str
    trecho_novo: str
    tipo_erro: TipoErro
    sutil: bool
    criador: Literal["programa", "opus"]


class Gabarito(Modelo):
    copia: str
    original: str
    origem: OrigemErro
    tipo_erro: TipoErro
    sutil: bool
    item_principal: ItemConferencia
    itens_aceitos: list[ItemConferencia]
    criador: Literal["programa", "opus"]
    verificador: str | None
    item_apontado_pelo_verificador: ItemConferencia | None
    amostra: AmostraGabarito | None


class Descartada(Modelo):
    copia: str
    original: str
    tipo_erro: TipoErro
    sutil: bool
    criador: Literal["programa", "opus"]
    conferencia_que_falhou: ConferenciaQueFalhou
    item_apontado_pelo_verificador: ItemConferencia | None
    outro_problema: bool
    motivo: MotivoDescarte | None
    amostra: AmostraDescartada | None


class RespostaCopiaOpus(Modelo):
    trecho_original: str
    trecho_novo: str


class RespostaVerificacao(Modelo):
    item_apontado: ItemConferencia | None
    descricao_erro: str
    outro_problema: bool
    descricao_outro_problema: str | None


# ---------------------------------------------------------------------------
# Cartões, rodada, registro e pacote
# ---------------------------------------------------------------------------


class Cartao(Modelo):
    id: str
    tipo_cartao: TipoCartao
    etapa: Literal[1, 2]
    conteudo: str


class RespostaAmostra(Modelo):
    copia: str
    erro_existe: bool
    erro_do_gabarito: bool | None


class RespostasCartao(Modelo):
    id_cartao: str
    tipo_cartao: TipoCartao
    veredito_ficha: Literal["aprovada", "reprovada"] | None
    veredito_peca: Literal["aprovada", "reprovada"] | None
    dado_real: bool
    dado_real_trecho: str | None
    citacoes_nao_resolvidas: list[str]
    formato_certo: bool | None
    formato_errado: str | None
    amostra: list[RespostaAmostra]
    data_confirmacao: datetime.datetime


class Amostras(Modelo):
    """As duas amostras sorteadas de uma rodada (`saida/erros/<rodada>_amostras.json`):
    gravado pelo brief 021, lido pelos cartões do brief 020."""

    rodada: str
    copias: list[str]
    descartadas: list[str]
    sorteado_em: datetime.datetime


class TaxaTeste(Modelo):
    """Uma taxa com a margem de Wilson; sem casos, taxa e margem ficam vazias."""

    sucessos: int
    total: int
    taxa: float | None
    inferior: float | None
    superior: float | None


class BancoTeste(Modelo):
    copias: int
    copias_ia: int
    rejeitadas: list[str]
    descartadas: int
    descartadas_com_erro: list[str]
    nao_confiavel: bool
    filtrado_pelo_verificador: bool


class CopiaTeste(Modelo):
    copia: str
    original: str
    origem: OrigemErro
    tipo_erro: TipoErro
    sutil: bool
    pego: bool
    pego_sem_opus: bool
    itens_pegos: list[ItemConferencia]
    conferentes: list[Conferente]
    formato: bool


class ResultadoTeste(Modelo):
    """O teste dos conferentes (`saida/relatorios/teste_conferentes.json`; brief 022)."""

    rodada: str
    gravado_em: datetime.datetime
    banco: BancoTeste
    criterio_central: TaxaTeste
    sem_opus: TaxaTeste
    julgamento_programa: TaxaTeste
    julgamento_inconclusivo: bool
    regra_programa: TaxaTeste
    regra_sanidade_ok: bool
    reprovacao_pecas_boas: TaxaTeste
    decisao_criterio_central: Literal["passa", "nao_passa", "inconclusivo", "nao_decide"]
    dependente_do_opus: bool
    nao_pegas_formato: list[str]
    copias: list[CopiaTeste]
    por_conferente: dict[str, TaxaTeste]
    por_tipo_erro: dict[str, TaxaTeste]
    por_origem: dict[str, TaxaTeste]


class Rodada(Modelo):
    id: Annotated[str, Field(pattern=r"^[er]\d{2}$")]
    semente: int
    impressoes: dict[str, str]
    ensaio_aprovado_origem: str | None
    estado: EstadoRodada
    aberta_em: datetime.datetime
    ensaio_aprovado: bool
    aprovado_em: datetime.datetime | None


class Rodadas(Modelo):
    rodadas: list[Rodada]


class Chamada(Modelo):
    rodada: str
    peca: str
    pedido: str
    tarefa: Tarefa
    modelo: str
    tokens_entrada: int
    tokens_cache: int
    tokens_raciocinio: int
    tokens_saida: int
    custo_milionesimos: int
    duracao_segundos: float
    momento: datetime.datetime


class Ocorrencia(Modelo):
    tipo: TipoOcorrencia
    causa: str
    inicio: datetime.datetime
    fim: datetime.datetime | None
    peca: str | None
    rodada: str | None
    detalhe: str


class ItemMetadados(Modelo):
    item: ItemConferencia
    resposta_final: RespostaItem
    quem_final: Conferente


class Metadados(Modelo):
    tipo: RotuloTipo
    classe_risco: ClasseRisco
    familia: str
    perfil: str
    materia: str
    tese: str
    polo: Papel
    complexidade: Complexidade
    estilo: Estilo
    ficha: Ficha
    identificador_processo: str
    semente: int
    modelo_redator: str
    esforco: str
    versao_instrucoes: str
    custo_milionesimos: int
    versao_tabela_normas: str
    conferencia: list[ItemMetadados]
    conferencia_local_rodou: bool
    marca_sintetico: Literal["DOCUMENTO SINTÉTICO — FICTÍCIO"]


# ---------------------------------------------------------------------------
# Esquema das respostas estruturadas
# ---------------------------------------------------------------------------

MODELOS_RESPOSTA: dict[str, type[Modelo]] = {
    "RespostaFichaInicial": RespostaFichaInicial,
    "RespostaFichaEmbargos": RespostaFichaEmbargos,
    "RespostaFichaManifestacao": RespostaFichaManifestacao,
    "Extracao": Extracao,
    "RespostaChecklist": RespostaChecklist,
    "RespostaLocal": RespostaLocal,
    "RespostaDesempate": RespostaDesempate,
    "RespostaCopiaOpus": RespostaCopiaOpus,
    "RespostaVerificacao": RespostaVerificacao,
}


def _proibir_campo_a_mais(no: Any) -> None:
    if isinstance(no, dict):
        if no.get("type") == "object" or "properties" in no:
            no["additionalProperties"] = False
        for valor in no.values():
            _proibir_campo_a_mais(valor)
    elif isinstance(no, list):
        for valor in no:
            _proibir_campo_a_mais(valor)


def esquema_resposta(modelo: type[BaseModel]) -> dict[str, Any]:
    """Esquema JSON do modelo, com campo a mais proibido em todos os níveis."""
    esquema = modelo.model_json_schema()
    _proibir_campo_a_mais(esquema)
    return esquema


# ---------------------------------------------------------------------------
# Configuração (brief 004): espelho exato de config/config.toml e config/gasto.toml
# ---------------------------------------------------------------------------


def _vazio_e_ausente(valor: Any) -> Any:
    """Valor pendente e vazio no config.toml é lido como ausente."""
    return None if valor == "" else valor


TextoOuAusente = Annotated[str | None, BeforeValidator(_vazio_e_ausente)]
NomeModelo = Literal["opus", "sonnet", "haiku"]
Esforco = Literal["low", "medium", "high", "xhigh", "max"]


class PrecoModelo(Modelo):
    id: str
    preco_entrada_centavos_por_milhao: Centavos
    preco_saida_centavos_por_milhao: Centavos


class PrecoModeloComFaixa(PrecoModelo):
    limite_entrada_tokens_do_preco: int
    preco_entrada_acima_do_limite_centavos_por_milhao: Centavos
    preco_saida_acima_do_limite_centavos_por_milhao: Centavos


class ConfigModelos(Modelo):
    data_conferencia: datetime.date
    opus: PrecoModelo
    sonnet: PrecoModelo
    haiku: PrecoModeloComFaixa


class ConfigTarefa(Modelo):
    modelo: NomeModelo
    esforco: Esforco
    teto_saida_tokens: int


class ConfigTarefas(Modelo):
    ficha: ConfigTarefa
    redacao_risco_baixo: ConfigTarefa
    extracao: ConfigTarefa
    checklist: ConfigTarefa
    redacao_risco_medio: ConfigTarefa
    redacao_risco_alto: ConfigTarefa
    conferencia_opus: ConfigTarefa
    copia_com_erro: ConfigTarefa
    verificacao_copia: ConfigTarefa


class ConfigApi(Modelo):
    modo_chamada: str
    esperas_novas_tentativas_segundos: list[int]


class ConfigVolume(Modelo):
    pecas_por_tipo: int
    copias_opus_por_peca_boa: int
    copias_programa_por_peca_boa: int
    fracao_copias_opus_sutis: float
    versoes_maximas: int


class ConfigPlanoB(Modelo):
    normal_a_partir_de_pecas_boas: int
    faixa_media_de: int
    faixa_media_ate: int
    copias_opus_por_peca_boa_faixa_media: int
    inconclusivo_abaixo_de: int


class ConfigSemelhanca(Modelo):
    limite: float
    palavras_por_trecho: int


class ConfigModeloLocal(Modelo):
    nome: str
    etiqueta_completa: TextoOuAusente
    digest: TextoOuAusente
    porta: int
    num_ctx: int
    num_ctx_alternativo: int
    fracao_limite_contexto_ensaio: float
    divisor_caracteres_por_token: int
    porteiro_intervalo_segundos: int
    porteiro_espera_maxima_minutos: int
    fracao_pecas_risco_baixo: float


class ConfigJanelaLocal(Modelo):
    inicio: datetime.time
    fim: datetime.time


class ConfigValvula(Modelo):
    espera_risco_medio_horas: int
    espera_risco_alto_dias: int
    fracao_sem_local_para_ressalva: float


class ConfigReferenciasLegais(Modelo):
    ano_das_fichas: int
    salario_minimo_centavos: Centavos
    salario_minimo_norma: str
    salario_minimo_data_conferencia: datetime.date
    alcada_em_salarios_minimos: int


class ConfigDdds(Modelo):
    inexistentes: list[int]
    data_conferencia: datetime.date


class ConfigCriterios(Modelo):
    taxa_minima: float
    limite_inferior_minimo: float
    confianca: float
    pontos_dependencia_opus: int
    minimo_copias_julgamento: int
    fracao_maxima_pecas_boas_reprovadas: float
    custo_marginal_maximo_centavos: Centavos
    piso_pecas_por_tipo: int
    fracao_fichas_reprovadas_por_tipo: float
    rejeitadas_para_banco_nao_confiavel: int
    existentes_para_banco_filtrado: int


class ConfigAmostras(Modelo):
    copias_aceitas: int
    descartadas_nao_viu_erro: int
    ensaio_copias_aceitas_maximo: int
    ensaio_descartadas_maximo: int


class ConfigMatriz(Modelo):
    tentativas_maximas: int
    fracao_maxima_por_materia: float
    dias_uteis_de_folga: int
    anos_maximos_dos_fatos: int


class ConfigFichas(Modelo):
    retornos_ao_haiku: int
    fichas_novas_por_casa: int


class ConfigTrecho(Modelo):
    teto_tokens: int


class ConfigAncora(Modelo):
    termos_minimos: int
    letras_do_radical: int
    letras_minimas: int
    fracao_maxima_fora_da_mencao: float
    palavras_maximas_mencao: int


class ConfigErros(Modelo):
    fracao_maxima_regiao: float
    diferenca_minima_valor_trocado: float


class ConfigComparacao(Modelo):
    diferenca_maxima_arredondamento: float


class Configuracao(Modelo):
    """Espelho exato de config/config.toml (brief 002)."""

    modelos: ConfigModelos
    tarefas: ConfigTarefas
    api: ConfigApi
    volume: ConfigVolume
    plano_b: ConfigPlanoB
    semelhanca: ConfigSemelhanca
    modelo_local: ConfigModeloLocal
    janela_local: ConfigJanelaLocal
    valvula: ConfigValvula
    referencias_legais: ConfigReferenciasLegais
    ddds: ConfigDdds
    criterios: ConfigCriterios
    amostras: ConfigAmostras
    matriz: ConfigMatriz
    fichas: ConfigFichas
    trecho: ConfigTrecho
    ancora: ConfigAncora
    erros: ConfigErros
    comparacao: ConfigComparacao


class Gasto(Modelo):
    """Espelho exato de config/gasto.toml (brief 002)."""

    alerta_centavos: Centavos
    corte_centavos: Centavos
