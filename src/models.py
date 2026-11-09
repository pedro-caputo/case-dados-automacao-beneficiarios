"""
Modelos de dados, enums e estruturas para o processo TO-BE.
"""
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class Canal(str, Enum):
    EMAIL = "EMAIL"
    AGENCIA = "AGENCIA"
    APP = "APP"


class StatusSolicitacao(str, Enum):
    RECEBIDA = "RECEBIDA"
    EM_VALIDACAO = "EM_VALIDACAO"
    AGUARDANDO_CLIENTE = "AGUARDANDO_CLIENTE"
    PRONTA_PARA_CADASTRO = "PRONTA_PARA_CADASTRO"
    EM_CADASTRO = "EM_CADASTRO"
    CONCLUIDA = "CONCLUIDA"
    EXCECAO = "EXCECAO"
    REJEITADA = "REJEITADA"


class EtapaProcesso(str, Enum):
    TRIAGEM = "TRIAGEM"
    CONFERENCIA = "CONFERENCIA"
    COMPLEMENTO = "COMPLEMENTO"
    CADASTRO = "CADASTRO"
    RESPOSTA = "RESPOSTA"
    FINALIZADO = "FINALIZADO"


class Prioridade(str, Enum):
    BAIXA = "BAIXA"
    MEDIA = "MEDIA"
    ALTA = "ALTA"
    URGENTE = "URGENTE"


class TipoEvento(str, Enum):
    CRIACAO = "CRIACAO"
    VALIDACAO_INICIADA = "VALIDACAO_INICIADA"
    VALIDACAO_SUCESSO = "VALIDACAO_SUCESSO"
    VALIDACAO_FALHA = "VALIDACAO_FALHA"
    PENDENCIA_ABERTA = "PENDENCIA_ABERTA"
    PENDENCIA_FECHADA = "PENDENCIA_FECHADA"
    SLA_INICIADO = "SLA_INICIADO"
    SLA_PAUSADO = "SLA_PAUSADO"
    SLA_RETOMADO = "SLA_RETOMADO"
    SLA_ENCERRADO = "SLA_ENCERRADO"
    COMUNICACAO_ENVIADA = "COMUNICACAO_ENVIADA"
    COMUNICACAO_FALHA = "COMUNICACAO_FALHA"
    ANALISE_HUMANA_INICIADA = "ANALISE_HUMANA_INICIADA"
    ANALISE_HUMANA_CONCLUIDA = "ANALISE_HUMANA_CONCLUIDA"
    CADASTRO_EFETIVADO = "CADASTRO_EFETIVADO"
    SOLICITACAO_CONCLUIDA = "SOLICITACAO_CONCLUIDA"
    SOLICITACAO_REJEITADA = "SOLICITACAO_REJEITADA"


class TipoDocumento(str, Enum):
    DOCUMENTO_IDENTIFICACAO = "DOCUMENTO_IDENTIFICACAO"
    FORMULARIO_ALTERACAO = "FORMULARIO_ALTERACAO"
    COMPROVANTE_VINCULO = "COMPROVANTE_VINCULO"


class TipoPendencia(str, Enum):
    DOCUMENTO_AUSENTE = "DOCUMENTO_AUSENTE"
    DOCUMENTO_ILEGIVEL = "DOCUMENTO_ILEGIVEL"
    FORMATO_INVALIDO = "FORMATO_INVALIDO"
    DADOS_DIVERGENTES = "DADOS_DIVERGENTES"
    DADOS_INCOMPLETOS = "DADOS_INCOMPLETOS"


class EstadoComunicacao(str, Enum):
    PENDENTE = "PENDENTE"
    ENVIADA_SIMULADA = "ENVIADA_SIMULADA"
    FALHA_SIMULADA = "FALHA_SIMULADA"


class EstadoSLA(str, Enum):
    CORRENDO = "CORRENDO"
    PAUSADO = "PAUSADO"
    ENCERRADO = "ENCERRADO"


@dataclass
class Cliente:
    id: Optional[int] = None
    solicitacao_id: Optional[int] = None
    nome_ficticio: str = ""
    cpf_ficticio: str = ""
    email_ficticio: str = ""
    telefone_ficticio: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Beneficiario:
    id: Optional[int] = None
    solicitacao_id: Optional[int] = None
    nome_ficticio: str = ""
    cpf_ficticio: str = ""
    parentesco: str = "Outro"
    percentual: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Documento:
    id: Optional[int] = None
    solicitacao_id: Optional[int] = None
    tipo: TipoDocumento = TipoDocumento.DOCUMENTO_IDENTIFICACAO
    nome_arquivo: str = ""
    presente: bool = True
    formato: str = "pdf"
    valido_sintatico: bool = True
    legibilidade_simulada: bool = True
    metadados: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tipo"] = self.tipo.value if isinstance(self.tipo, TipoDocumento) else str(self.tipo)
        return d


@dataclass
class Pendencia:
    id: Optional[int] = None
    solicitacao_id: Optional[int] = None
    tipo: TipoPendencia = TipoPendencia.DOCUMENTO_AUSENTE
    descricao: str = ""
    aberta_em: str = field(default_factory=lambda: datetime.now().isoformat())
    fechada_em: Optional[str] = None
    resolucao: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tipo"] = self.tipo.value if isinstance(self.tipo, TipoPendencia) else str(self.tipo)
        return d


@dataclass
class TarefaHumana:
    id: Optional[int] = None
    solicitacao_id: Optional[int] = None
    tipo: str = "REVISAO_EXCECAO"
    atribuida_a: str = "Analista 1"
    estado: str = "PENDENTE"
    iniciada_em: Optional[str] = None
    encerrada_em: Optional[str] = None
    duracao_ativa_segundos: float = 0.0
    decisao: Optional[str] = None
    justificativa: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Evento:
    id: Optional[int] = None
    solicitacao_id: Optional[int] = None
    tipo_evento: TipoEvento = TipoEvento.CRIACAO
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    origem_ator: str = "SISTEMA"  # SISTEMA, ANALISTA, CLIENTE
    estado_anterior: Optional[str] = None
    estado_novo: Optional[str] = None
    detalhes_json: str = "{}"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["tipo_evento"] = self.tipo_evento.value if isinstance(self.tipo_evento, TipoEvento) else str(self.tipo_evento)
        return d


@dataclass
class Comunicacao:
    id: Optional[int] = None
    solicitacao_id: Optional[int] = None
    template: str = "CONFIRMACAO_RECEBIMENTO"
    destinatario: str = ""
    canal: str = "EMAIL"
    estado: EstadoComunicacao = EstadoComunicacao.PENDENTE
    tentativa: int = 1
    motivo_falha: Optional[str] = None
    criado_em: str = field(default_factory=lambda: datetime.now().isoformat())
    enviado_simulado_em: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["estado"] = self.estado.value if isinstance(self.estado, EstadoComunicacao) else str(self.estado)
        return d


@dataclass
class Solicitacao:
    id: Optional[int] = None
    protocolo: str = ""
    external_intent_id: Optional[str] = None
    run_id: Optional[str] = None
    universo: str = "INTERATIVO"
    canal: Canal = Canal.EMAIL
    data_criacao: str = field(default_factory=lambda: datetime.now().isoformat())
    status: StatusSolicitacao = StatusSolicitacao.RECEBIDA
    etapa: EtapaProcesso = EtapaProcesso.TRIAGEM
    prioridade: Prioridade = Prioridade.MEDIA
    responsavel: Optional[str] = None
    sla_dias: int = 5
    sla_inicio: Optional[str] = None
    sla_pausado_em: Optional[str] = None
    sla_pausa_acumulada_segundos: float = 0.0
    sla_estado: EstadoSLA = EstadoSLA.CORRENDO
    data_conclusao: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["canal"] = self.canal.value if isinstance(self.canal, Canal) else str(self.canal)
        d["status"] = self.status.value if isinstance(self.status, StatusSolicitacao) else str(self.status)
        d["etapa"] = self.etapa.value if isinstance(self.etapa, EtapaProcesso) else str(self.etapa)
        d["prioridade"] = self.prioridade.value if isinstance(self.prioridade, Prioridade) else str(self.prioridade)
        d["sla_estado"] = self.sla_estado.value if isinstance(self.sla_estado, EstadoSLA) else str(self.sla_estado)
        return d


@dataclass
class SimulationRun:
    id: Optional[str] = None
    seed: int = 20261108
    total_intents: int = 1000
    parametros_json: str = "{}"
    iniciado_em: str = field(default_factory=lambda: datetime.now().isoformat())
    concluido_em: Optional[str] = None
    metricas_json: str = "{}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RawIntent:
    id: str
    canal: str
    cliente_dados_json: str
    beneficiarios_json: str
    docs_json: str
    flags_json: str
    seed: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

