"""
Máquina de estados, validação de transições e orquestração do fluxo TO-BE.
"""
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
import uuid

from src.models import (
    Solicitacao, Cliente, Beneficiario, Documento, Pendencia,
    TarefaHumana, Evento, StatusSolicitacao, EtapaProcesso,
    Prioridade, TipoEvento, TipoPendencia, EstadoSLA, EstadoComunicacao
)
from src.repositories import SolicitacaoRepository
from src.validators import (
    validar_cpf, validar_beneficiarios, validar_documentos,
    validar_solicitacao_completa, ValidationResult
)
from src.notifications import NotificationService


TRANSICOES_VALIDAS = {
    StatusSolicitacao.RECEBIDA.value: [
        StatusSolicitacao.EM_VALIDACAO.value
    ],
    StatusSolicitacao.EM_VALIDACAO.value: [
        StatusSolicitacao.PRONTA_PARA_CADASTRO.value,
        StatusSolicitacao.AGUARDANDO_CLIENTE.value,
        StatusSolicitacao.EXCECAO.value
    ],
    StatusSolicitacao.AGUARDANDO_CLIENTE.value: [
        StatusSolicitacao.EM_VALIDACAO.value,
        StatusSolicitacao.EXCECAO.value
    ],
    StatusSolicitacao.PRONTA_PARA_CADASTRO.value: [
        StatusSolicitacao.EM_CADASTRO.value,
        StatusSolicitacao.EXCECAO.value
    ],
    StatusSolicitacao.EM_CADASTRO.value: [
        StatusSolicitacao.CONCLUIDA.value,
        StatusSolicitacao.EXCECAO.value
    ],
    StatusSolicitacao.EXCECAO.value: [
        StatusSolicitacao.PRONTA_PARA_CADASTRO.value,
        StatusSolicitacao.AGUARDANDO_CLIENTE.value,
        StatusSolicitacao.EM_CADASTRO.value,
        StatusSolicitacao.REJEITADA.value
    ],
    StatusSolicitacao.CONCLUIDA.value: [],
    StatusSolicitacao.REJEITADA.value: []
}


def gerar_protocolo_unico(data_dt: Optional[datetime] = None) -> str:
    """Gera um protocolo único humanamente legível no formato BEN-YYYYMMDD-XXXX."""
    dt = data_dt or datetime.now()
    hash_curto = uuid.uuid4().hex[:6].upper()
    return f"BEN-{dt.strftime('%Y%m%d')}-{hash_curto}"


class WorkflowService:
    def __init__(self, repo: SolicitacaoRepository):
        self.repo = repo
        self.notifications = NotificationService(repo)

    def validar_transicao(self, status_atual: str, novo_status: str) -> bool:
        """Garante conformidade com o grafo de transições permitido."""
        permitidos = TRANSICOES_VALIDAS.get(status_atual, [])
        return novo_status in permitidos

    def criar_solicitacao(
        self,
        canal: str,
        cliente_dados: Dict[str, Any],
        beneficiarios_dados: List[Dict[str, Any]],
        documentos_dados: List[Dict[str, Any]],
        prioridade: str = Prioridade.MEDIA.value,
        sla_dias: int = 5,
        external_intent_id: Optional[str] = None,
        run_id: Optional[str] = None,
        ator: str = "CANAL_ENTRADA",
        auto_validar: bool = True
    ) -> Tuple[Optional[int], Optional[str], ValidationResult]:
        """
        Recebe a solicitação no canal de entrada:
        1. Aplica validação preventiva (bloqueia na entrada se dados forem inconsistentes).
        2. Gera protocolo único.
        3. Persiste registro relacional com eventos auditáveis.
        4. Dispara comunicação simulada de confirmação de recebimento.
        5. Se auto_validar=True, avança para EM_VALIDACAO e avalia regras sistêmicas.
        """
        # Validação preventiva
        res_validacao = validar_solicitacao_completa(
            cliente=cliente_dados,
            beneficiarios=beneficiarios_dados,
            documentos=documentos_dados
        )

        if not res_validacao.valido:
            return None, None, res_validacao

        protocolo = gerar_protocolo_unico()
        now_iso = datetime.now().isoformat()

        solic = Solicitacao(
            protocolo=protocolo,
            external_intent_id=external_intent_id,
            run_id=run_id,
            canal=canal,
            data_criacao=now_iso,
            status=StatusSolicitacao.RECEBIDA,
            etapa=EtapaProcesso.TRIAGEM,
            prioridade=prioridade,
            sla_dias=sla_dias,
            sla_inicio=now_iso,
            sla_estado=EstadoSLA.CORRENDO
        )

        cliente = Cliente(
            nome_ficticio=cliente_dados.get("nome") or cliente_dados.get("nome_ficticio", ""),
            cpf_ficticio=cliente_dados.get("cpf") or cliente_dados.get("cpf_ficticio", ""),
            email_ficticio=cliente_dados.get("email") or cliente_dados.get("email_ficticio", ""),
            telefone_ficticio=cliente_dados.get("telefone") or cliente_dados.get("telefone_ficticio", "")
        )

        beneficiarios = [
            Beneficiario(
                nome_ficticio=b.get("nome") or b.get("nome_ficticio", ""),
                cpf_ficticio=b.get("cpf") or b.get("cpf_ficticio", ""),
                parentesco=b.get("parentesco", "Outro"),
                percentual=float(b.get("percentual", 0.0))
            )
            for b in beneficiarios_dados
        ]

        documentos = [
            Documento(
                tipo=d.get("tipo"),
                nome_arquivo=d.get("nome_arquivo", ""),
                presente=d.get("presente", True),
                formato=d.get("formato", "pdf"),
                valido_sintatico=d.get("valido_sintatico", True),
                legibilidade_simulada=d.get("legibilidade_simulada", True),
                metadados=d.get("metadados", {})
            )
            for d in documentos_dados
        ]

        solic_id = self.repo.create_solicitacao(solic, cliente, beneficiarios, documentos, ator=ator)

        # Comunicação de recebimento simulada
        self.notifications.enviar_comunicacao_simulada(
            solicitacao_id=solic_id,
            template_nome="CONFIRMACAO_RECEBIMENTO",
            destinatario=cliente.email_ficticio or cliente.telefone_ficticio or "cliente@exemplo.com",
            canal=canal,
            variaveis={"nome": cliente.nome_ficticio, "protocolo": protocolo, "sla_dias": sla_dias}
        )

        if auto_validar:
            self.executar_validacao_sistemica(solic_id, ator="SISTEMA")

        return solic_id, protocolo, res_validacao

    def executar_validacao_sistemica(self, solic_id: int, ator: str = "SISTEMA") -> Dict[str, Any]:
        """
        Executa conferência sistêmica de regras e documentos:
        - Se documentos ou dados estiverem faltantes/incompletos: gera pendência, transita para AGUARDANDO_CLIENTE e pausa SLA.
        - Se baixa legibilidade simulada ou erro grave: transita para EXCECAO para atuação do analista.
        - Se tudo consistente: transita para PRONTA_PARA_CADASTRO.
        """
        solic = self.repo.get_solicitacao(solic_id)
        if not solic:
            raise ValueError(f"Solicitação {solic_id} não encontrada.")

        status_atual = solic["status"]
        if status_atual != StatusSolicitacao.EM_VALIDACAO.value:
            if not self.validar_transicao(status_atual, StatusSolicitacao.EM_VALIDACAO.value):
                raise ValueError(f"Transição inválida de {status_atual} para EM_VALIDACAO.")
            self.repo.update_status(solic_id, StatusSolicitacao.EM_VALIDACAO, EtapaProcesso.CONFERENCIA, ator=ator)

        # Validação sistêmica documental
        docs = solic.get("documentos", [])
        res_docs = validar_documentos(docs)

        tem_pendencia = False
        tem_excecao = False
        motivo_pendencia = ""

        # Verifica documentos faltantes ou formatos errados
        for doc in docs:
            if not doc.get("presente", True) or not doc.get("nome_arquivo"):
                tem_pendencia = True
                motivo_pendencia = f"Documento obrigatório ausente: {doc.get('tipo')}."
                self.repo.add_pendencia(
                    Pendencia(
                        solicitacao_id=solic_id,
                        tipo=TipoPendencia.DOCUMENTO_AUSENTE,
                        descricao=motivo_pendencia
                    ),
                    ator=ator
                )
            elif not doc.get("valido_sintatico", True):
                tem_pendencia = True
                motivo_pendencia = f"Documento inválido ou corrompido: {doc.get('nome_arquivo')}."
                self.repo.add_pendencia(
                    Pendencia(
                        solicitacao_id=solic_id,
                        tipo=TipoPendencia.FORMATO_INVALIDO,
                        descricao=motivo_pendencia
                    ),
                    ator=ator
                )
            elif not doc.get("legibilidade_simulada", True):
                tem_excecao = True

        if tem_pendencia:
            # Transita para AGUARDANDO_CLIENTE e pausa SLA
            self.repo.update_status(
                solic_id,
                StatusSolicitacao.AGUARDANDO_CLIENTE,
                EtapaProcesso.COMPLEMENTO,
                ator=ator,
                justificativa=motivo_pendencia
            )
            # Notificação simulada de complemento
            cli = solic.get("cliente", {})
            self.notifications.enviar_comunicacao_simulada(
                solicitacao_id=solic_id,
                template_nome="SOLICITACAO_COMPLEMENTO",
                destinatario=cli.get("email_ficticio", "cliente@exemplo.com"),
                canal=solic.get("canal", "EMAIL"),
                variaveis={"nome": cli.get("nome_ficticio", ""), "protocolo": solic.get("protocolo", ""), "detalhe": motivo_pendencia}
            )
            # Pausa o SLA
            self.repo.update_sla_pause(solic_id, pausar=True)
            return {"status": StatusSolicitacao.AGUARDANDO_CLIENTE.value, "pendencia": motivo_pendencia}

        elif tem_excecao:
            # Transita para EXCECAO para revisão humana
            self.repo.update_status(
                solic_id,
                StatusSolicitacao.EXCECAO,
                EtapaProcesso.CONFERENCIA,
                ator=ator,
                justificativa="Documento com baixa legibilidade simulada detectada na conferência."
            )
            # Cria tarefa humana pendente
            self.repo.add_tarefa(TarefaHumana(
                solicitacao_id=solic_id,
                tipo="REVISAO_DOCUMENTAL",
                atribuida_a="Analista Operacional",
                estado="PENDENTE"
            ))
            return {"status": StatusSolicitacao.EXCECAO.value, "motivo": "Baixa legibilidade"}

        else:
            # Caso totalmente pronto para cadastro
            self.repo.update_status(
                solic_id,
                StatusSolicitacao.PRONTA_PARA_CADASTRO,
                EtapaProcesso.CADASTRO,
                ator=ator,
                justificativa="Validações preventiva e sistêmica concluídas com sucesso."
            )
            return {"status": StatusSolicitacao.PRONTA_PARA_CADASTRO.value}

    def registrar_complemento_cliente(
        self,
        solic_id: int,
        documentos_atualizados: List[Dict[str, Any]],
        resolucao: str = "Complemento documental anexado pelo cliente.",
        ator: str = "CLIENTE"
    ) -> bool:
        """
        Recebe complemento documental:
        1. Atualiza documentos no banco.
        2. Fecha pendências abertas.
        3. Retoma o relógio de SLA.
        4. Retorna para EM_VALIDACAO para reavaliação.
        """
        solic = self.repo.get_solicitacao(solic_id)
        if not solic:
            return False

        if solic["status"] != StatusSolicitacao.AGUARDANDO_CLIENTE.value:
            raise ValueError(f"Solicitação {solic_id} não está aguardando cliente (status atual: {solic['status']}).")

        # Fecha pendências abertas
        for p in solic.get("pendencias", []):
            if not p.get("fechada_em"):
                self.repo.close_pendencia(p["id"], resolucao=resolucao, ator=ator)

        # Retoma relógio de SLA
        self.repo.update_sla_pause(solic_id, pausar=False)

        # Transita para EM_VALIDACAO
        self.repo.update_status(
            solic_id,
            StatusSolicitacao.EM_VALIDACAO,
            EtapaProcesso.CONFERENCIA,
            ator=ator,
            justificativa=resolucao
        )

        # Atualiza documentos no banco
        conn = self.repo._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM documentos WHERE solicitacao_id = ?", (solic_id,))
        for d in documentos_atualizados:
            cursor.execute("""
                INSERT INTO documentos (solicitacao_id, tipo, nome_arquivo, presente, formato, valido_sintatico, legibilidade_simulada, metadados_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (solic_id, d["tipo"], d["nome_arquivo"], 1 if d.get("presente", True) else 0, d.get("formato", "pdf"), 1 if d.get("valido_sintatico", True) else 0, 1 if d.get("legibilidade_simulada", True) else 0, "{}"))
        conn.commit()
        conn.close()

        # Reexecuta validação sistêmica
        self.executar_validacao_sistemica(solic_id, ator="SISTEMA")
        return True

    def iniciar_cadastro(self, solic_id: int, ator: str = "ANALISTA") -> bool:
        """Coloca a solicitação em processo ativo de cadastro."""
        solic = self.repo.get_solicitacao(solic_id)
        if not solic:
            return False

        status_atual = solic["status"]
        if status_atual not in [StatusSolicitacao.PRONTA_PARA_CADASTRO.value, StatusSolicitacao.EXCECAO.value]:
            raise ValueError(f"Não é possível iniciar cadastro a partir do status '{status_atual}'.")

        self.repo.update_status(solic_id, StatusSolicitacao.EM_CADASTRO, EtapaProcesso.CADASTRO, ator=ator)
        return True

    def efetivar_cadastro_e_concluir(
        self,
        solic_id: int,
        ator: str = "ANALISTA",
        observacao: str = "Cadastro de beneficiários efetivado no sistema central."
    ) -> bool:
        """
        AC-10: Impede marcar conclusão sem confirmação explícita de efetivação do cadastro.
        Transita de EM_CADASTRO para CONCLUIDA e gera comunicação final.
        """
        solic = self.repo.get_solicitacao(solic_id)
        if not solic:
            return False

        if solic["status"] != StatusSolicitacao.EM_CADASTRO.value:
            raise ValueError(
                f"Tentativa de concluir solicitação sem efetivação prévia do cadastro. Status atual: {solic['status']}."
            )

        now_iso = datetime.now().isoformat()

        # Registra evento de efetivação cadastral
        self.repo.add_evento(Evento(
            solicitacao_id=solic_id,
            tipo_evento=TipoEvento.CADASTRO_EFETIVADO,
            origem_ator=ator,
            estado_anterior=StatusSolicitacao.EM_CADASTRO.value,
            estado_novo=StatusSolicitacao.CONCLUIDA.value,
            detalhes_json=json.dumps({"observacao": observacao})
        ))

        # Transita para CONCLUIDA
        self.repo.update_status(
            solic_id,
            StatusSolicitacao.CONCLUIDA,
            EtapaProcesso.FINALIZADO,
            ator=ator,
            justificativa=observacao
        )

        # Envia comunicação simulada de conclusão
        cli = solic.get("cliente", {})
        self.notifications.enviar_comunicacao_simulada(
            solicitacao_id=solic_id,
            template_nome="CONFIRMACAO_CONCLUSAO",
            destinatario=cli.get("email_ficticio", "cliente@exemplo.com"),
            canal=solic.get("canal", "EMAIL"),
            variaveis={"nome": cli.get("nome_ficticio", ""), "protocolo": solic.get("protocolo", "")}
        )

        return True

