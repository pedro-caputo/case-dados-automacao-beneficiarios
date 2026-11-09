"""
Módulo de comunicações simuladas com rastreamento de tentativas, templates e escalonamento.
AVISO: Este sistema opera exclusivamente em modo simulado; nenhum e-mail real é transmitido.
"""
from typing import Dict, Any, Optional
from datetime import datetime
from src.models import Comunicacao, EstadoComunicacao, TipoEvento, Evento
from src.repositories import SolicitacaoRepository
from src.config import MAX_RETRY_COMUNICACOES


TEMPLATES = {
    "CONFIRMACAO_RECEBIMENTO": "Prezado(a) {nome}, sua solicitação de alteração de beneficiários foi recebida com sucesso sob o protocolo {protocolo}. Prazo estimado de análise: {sla_dias} dias.",
    "SOLICITACAO_COMPLEMENTO": "Prezado(a) {nome}, identificamos uma pendência no protocolo {protocolo}: {detalhe}. O relógio de SLA está pausado até o recebimento do complemento solicitado.",
    "CONFIRMACAO_CONCLUSAO": "Prezado(a) {nome}, informamos que a alteração de beneficiários do protocolo {protocolo} foi concluída e cadastrada com sucesso.",
    "AVISO_EXCECAO": "Prezado(a) {nome}, sua solicitação {protocolo} está sob análise de nossa equipe especializada. Você receberá atualizações em breve."
}


class NotificationService:
    def __init__(self, repo: SolicitacaoRepository):
        self.repo = repo

    def enviar_comunicacao_simulada(
        self,
        solicitacao_id: int,
        template_nome: str,
        destinatario: str,
        canal: str = "EMAIL",
        variaveis: Optional[Dict[str, Any]] = None,
        forcar_falha: bool = False
    ) -> Comunicacao:
        """
        Executa disparo simulado de notificação e registra evento de auditoria.
        Se falhar intencionalmente, gerencia retries e escalonamento sem perder o caso.
        """
        now_iso = datetime.now().isoformat()
        com = Comunicacao(
            solicitacao_id=solicitacao_id,
            template=template_nome,
            destinatario=destinatario,
            canal=canal,
            estado=EstadoComunicacao.PENDENTE,
            tentativa=1,
            criado_em=now_iso
        )
        com_id = self.repo.add_comunicacao(com)
        com.id = com_id

        if forcar_falha:
            # Falha simulada
            motivo = "Falha simulada de conexão no gateway do canal."
            self.repo.update_comunicacao(
                com_id=com_id,
                estado=EstadoComunicacao.FALHA_SIMULADA,
                tentativa=1,
                motivo_falha=motivo
            )
            com.estado = EstadoComunicacao.FALHA_SIMULADA
            com.motivo_falha = motivo

            # Registra evento de auditoria de falha
            self.repo.add_evento(Evento(
                solicitacao_id=solicitacao_id,
                tipo_evento=TipoEvento.COMUNICACAO_FALHA,
                origem_ator="SISTEMA",
                estado_anterior=EstadoComunicacao.PENDENTE.value,
                estado_novo=EstadoComunicacao.FALHA_SIMULADA.value,
                detalhes_json=f'{{"comunicacao_id": {com_id}, "motivo": "{motivo}", "template": "{template_nome}"}}'
            ))
        else:
            # Sucesso simulado
            self.repo.update_comunicacao(
                com_id=com_id,
                estado=EstadoComunicacao.ENVIADA_SIMULADA,
                tentativa=1,
                enviado_em=now_iso
            )
            com.estado = EstadoComunicacao.ENVIADA_SIMULADA
            com.enviado_simulado_em = now_iso

            # Registra evento de auditoria de envio
            self.repo.add_evento(Evento(
                solicitacao_id=solicitacao_id,
                tipo_evento=TipoEvento.COMUNICACAO_ENVIADA,
                origem_ator="SISTEMA",
                estado_anterior=EstadoComunicacao.PENDENTE.value,
                estado_novo=EstadoComunicacao.ENVIADA_SIMULADA.value,
                detalhes_json=f'{{"comunicacao_id": {com_id}, "template": "{template_nome}", "destinatario": "{destinatario}"}}'
            ))

        return com

