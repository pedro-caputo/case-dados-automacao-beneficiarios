"""
Página 3 — Bancada do Analista — Revisões e Cadastro (Human-in-the-Loop).
Conduz o analista em 5 etapas lógicas com cronômetro auditado e alto contraste visual.
"""
import streamlit as st
import time
from datetime import datetime
import pandas as pd
from src.config import DB_PATH, STATUS_ROTULOS, ETAPA_ROTULOS
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.workflow import WorkflowService
from src.sla import calcular_metricas_sla
from src.models import TarefaHumana, StatusSolicitacao, EtapaProcesso, TipoPendencia, Pendencia
from src.ui_helpers import (
    apply_corporate_style, render_corporate_header,
    render_journey_stepper, get_status_badge_html,
    get_sla_badge_html, render_document_card, render_timeline,
    set_persistent_confirmation, render_persistent_confirmation,
    render_universe_selector
)

st.set_page_config(page_title="Bancada do Analista | Seguros PF", page_icon="🧑‍💼", layout="wide")
apply_corporate_style()

init_db(DB_PATH)
repo = SolicitacaoRepository(DB_PATH)
workflow = WorkflowService(repo)

render_corporate_header(
    titulo="Bancada do Analista — Revisões e Cadastro",
    subtitulo="Atuação humana especializada sobre exceções, inconsistências e efetivação cadastral"
)

render_journey_stepper(etapa_ativa=4)

# Banner de Confirmação Persistente (sobrevive a reruns e redirecionamentos)
render_persistent_confirmation()

# Sincronização prévia se veio redirecionado da Fila Operacional
if "caso_para_analisar_id" in st.session_state and st.session_state.caso_para_analisar_id:
    solic_redirecionada = repo.get_solicitacao(st.session_state.caso_para_analisar_id)
    if solic_redirecionada:
        st.session_state.universo_selecionado = solic_redirecionada.get("universo", "INTERATIVO")
        st.session_state.run_id_selecionado = solic_redirecionada.get("run_id")
        st.session_state.caso_analise_id = solic_redirecionada["id"]
    st.session_state.caso_para_analisar_id = None

# Seletor do Universo de Dados (Garante que Bancada opera estritamente no universo escolhido)
universo, run_id, universo_nome = render_universe_selector(repo, key_prefix="bancada")

# Inicializa sessão para cronômetro
if "cronometro_ativo" not in st.session_state:
    st.session_state.cronometro_ativo = False
if "cronometro_inicio" not in st.session_state:
    st.session_state.cronometro_inicio = 0.0
if "cronometro_acumulado" not in st.session_state:
    st.session_state.cronometro_acumulado = 0.0
if "caso_analise_id" not in st.session_state:
    st.session_state.caso_analise_id = None

# Busca casos que exigem atenção humana filtrados RIGOROSAMENTE pelo universo selecionado
casos_excecao = repo.list_solicitacoes(status="EXCECAO", universo=universo, run_id=run_id, limit=200)
casos_cadastro = repo.list_solicitacoes(status="EM_CADASTRO", universo=universo, run_id=run_id, limit=200)
casos_para_analise = casos_excecao + casos_cadastro

# Se existe um caso selecionado mas ele não veio na lista de exceção/cadastro, inclui explicitamente
if st.session_state.caso_analise_id:
    if not any(c["id"] == st.session_state.caso_analise_id for c in casos_para_analise):
        solic_ativa = repo.get_solicitacao(st.session_state.caso_analise_id)
        if solic_ativa:
            univ_ativa = solic_ativa.get("universo", "INTERATIVO")
            if univ_ativa == universo and (not run_id or solic_ativa.get("run_id") == run_id):
                casos_para_analise.insert(0, solic_ativa)

# KPIs da Bancada restritos ao universo selecionado
kpi1, kpi2, kpi3 = st.columns(3)
metrics = repo.get_dashboard_metrics(universo=universo, run_id=run_id)
tarefas_m = metrics.get("tarefas_metricas", {})
total_tarefas = tarefas_m.get("total_tarefas", 0)
tempo_medio = tarefas_m.get("tempo_ativo_medio_segundos", 0.0)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #D97706;">
        <div class="kpi-title">Exceções Documentais Pendentes</div>
        <div class="kpi-value">{len(casos_excecao)}</div>
        <div class="kpi-caption">Exigem discernimento do analista</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #2F73D8;">
        <div class="kpi-title">Em Cadastro Ativo</div>
        <div class="kpi-value">{len(casos_cadastro)}</div>
        <div class="kpi-caption">Aguardando confirmação final</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    valor_medio_str = f"{tempo_medio:.1f} s" if total_tarefas > 0 else "Sem medições"
    legenda_str = f"Baseado em {total_tarefas} análises auditadas" if total_tarefas > 0 else "Nenhuma intervenção gravada ainda"
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #15803D;">
        <div class="kpi-title">Média de Esforço Humano</div>
        <div class="kpi-value">{valor_medio_str}</div>
        <div class="kpi-caption">{legenda_str}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

if not casos_para_analise:
    st.info("✓ Nenhuma exceção ou tarefa pendente na fila no momento! Todas as solicitações válidas foram processadas sem pendência de analista.")
    st.caption("Para testar esta bancada, registre uma solicitação com baixa legibilidade simulada na aba 'Nova Solicitação' ou selecione um caso na 'Fila Operacional'.")
else:
    # Seleção de caso
    opcoes = [f"#{c['id']} — {c['protocolo']} ({c.get('cliente_nome', 'N/D')}) | Status: {STATUS_ROTULOS.get(c['status'], c['status'])}" for c in casos_para_analise]
    
    idx_default = 0
    if st.session_state.caso_analise_id:
        for idx, item in enumerate(opcoes):
            if f"#{st.session_state.caso_analise_id} " in item:
                idx_default = idx
                break

    escolha_caso = st.selectbox("Selecione a solicitação para atuar:", opcoes, index=idx_default)
    caso_id = int(escolha_caso.split("—")[0].replace("#", "").strip())
    
    solic = repo.get_solicitacao(caso_id)
    if solic:
        sla_m = calcular_metricas_sla(solic)
        status_atual = solic["status"]

        # Se trocou de caso, reinicia cronômetro
        if st.session_state.caso_analise_id != caso_id:
            st.session_state.caso_analise_id = caso_id
            st.session_state.cronometro_ativo = False
            st.session_state.cronometro_acumulado = 0.0
            st.session_state.cronometro_inicio = 0.0

        # -------------------------------------------------------------
        # CRONÔMETRO DE ESFORÇO HUMANO ATIVO
        # -------------------------------------------------------------
        st.markdown("#### ⏱️ Medição de Esforço Humano Ativo (Cronômetro do Analista)")
        st.caption("O cronômetro registra exclusivamente o tempo em que o analista está avaliando o caso, distinguindo esforço humano de tempo de software.")

        col_t1, col_t2, col_t3, col_t4 = st.columns([2, 1.5, 1.5, 3])

        with col_t1:
            if not st.session_state.cronometro_ativo:
                if st.button("▶️ Iniciar Análise", type="primary", use_container_width=True):
                    st.session_state.cronometro_ativo = True
                    st.session_state.cronometro_inicio = time.time()
                    st.rerun()
            else:
                if st.button("⏸️ Pausar Análise", use_container_width=True):
                    decorrido = time.time() - st.session_state.cronometro_inicio
                    st.session_state.cronometro_acumulado += decorrido
                    st.session_state.cronometro_ativo = False
                    st.rerun()

        with col_t2:
            if st.button("🔄 Zerar Tempo", use_container_width=True):
                st.session_state.cronometro_ativo = False
                st.session_state.cronometro_acumulado = 0.0
                st.session_state.cronometro_inicio = 0.0
                st.rerun()

        tempo_exibicao = st.session_state.cronometro_acumulado
        if st.session_state.cronometro_ativo:
            tempo_exibicao += (time.time() - st.session_state.cronometro_inicio)

        with col_t3:
            st.metric(
                label="Tempo em Atividade",
                value=f"{tempo_exibicao:.1f} s",
                delta="Gravando esforço..." if st.session_state.cronometro_ativo else "Pausado"
            )

        with col_t4:
            st.caption("O tempo apurado será registrado formalmente no banco ao concluir sua decisão.")

        st.markdown("---")

        # -------------------------------------------------------------
        # ETAPA 1 — IDENTIFICAÇÃO DO CASO
        # -------------------------------------------------------------
        st.markdown("### Etapa 1 • Identificação do Caso")
        cli = solic.get("cliente", {})
        
        motivo_encaminhamento = "Documento com baixa legibilidade simulada na entrada" if status_atual == "EXCECAO" else "Solicitação pré-validada aguardando confirmação cadastral"

        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        with col_i1:
            st.markdown(f"**Protocolo:** `{solic['protocolo']}`")
            st.markdown(f"**Segurado:** {cli.get('nome_ficticio')}")
        with col_i2:
            st.markdown(f"**Canal de Origem:** `{solic['canal']}`")
            st.markdown(f"**Status Atual:** {get_status_badge_html(status_atual)}", unsafe_allow_html=True)
        with col_i3:
            st.markdown(f"**SLA:** {get_sla_badge_html(sla_m)}", unsafe_allow_html=True)
            st.markdown(f"**Lead Time:** `{sla_m['lead_time_bruto_horas']}h`")
        with col_i4:
            st.markdown(f"**Motivo do Encaminhamento:**")
            st.markdown(f"<span style='color: #B91C1C; font-weight: 600;'>{motivo_encaminhamento}</span>", unsafe_allow_html=True)

        st.markdown("---")

        # -------------------------------------------------------------
        # ETAPA 2 — DADOS E DOCUMENTAÇÃO
        # -------------------------------------------------------------
        st.markdown("### Etapa 2 • Dados do Segurado e Beneficiários")
        
        col_d_seg, col_d_ben = st.columns([1, 1.3])
        with col_d_seg:
            st.markdown(f"""
            <div style="background-color: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 6px; padding: 1rem; color: #0F172A;">
                <strong style="color: #0C2340; font-size: 0.95rem;">Dados do Titular:</strong><br/>
                • <strong>Nome:</strong> {cli.get('nome_ficticio')}<br/>
                • <strong>CPF:</strong> <code>{cli.get('cpf_ficticio')}</code><br/>
                • <strong>E-mail:</strong> {cli.get('email_ficticio')}<br/>
                • <strong>Telefone:</strong> {cli.get('telefone_ficticio')}
            </div>
            """, unsafe_allow_html=True)

        with col_d_ben:
            bens = solic.get("beneficiarios", [])
            df_b = pd.DataFrame([{
                "Nome": b.get("nome_ficticio"),
                "CPF": b.get("cpf_ficticio"),
                "Parentesco": b.get("parentesco"),
                "Participação (%)": f"{b.get('percentual', 0):.2f}%"
            } for b in bens])
            st.dataframe(df_b, use_container_width=True, hide_index=True)

        st.markdown("---")

        # -------------------------------------------------------------
        # ETAPA 3 — DIAGNÓSTICO DA AUTOMAÇÃO
        # -------------------------------------------------------------
        st.markdown("### Etapa 3 • Diagnóstico da Automação")
        st.caption("Transparência do processo: veja exatamente o que as regras de software avaliaram automaticamente:")

        st.markdown("""
        <div class="automation-banner">
            <div class="automation-title">O que o sistema verificou automaticamente?</div>
            <div class="automation-item"><span class="automation-icon" style="color: #15803D;">✓</span> <strong>CPF do segurado:</strong> dígitos verificadores matemáticos válidos (sem erro de digitação).</div>
            <div class="automation-item"><span class="automation-icon" style="color: #15803D;">✓</span> <strong>Participação dos beneficiários:</strong> soma exatamente 100,00% sem CPFs duplicados.</div>
            <div class="automation-item"><span class="automation-icon" style="color: #15803D;">✓</span> <strong>Campos obrigatórios:</strong> nome, contato e parentesco preenchidos na entrada.</div>
            <div class="automation-item"><span class="automation-icon" style="color: #B45309;">⚠</span> <strong>O que NÃO pode ser concluído automaticamente:</strong> Legibilidade de imagens escaneadas, integridade visual de assinaturas e autenticidade documental exigem análise humana.</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("##### Documentação Anexada e Diagnóstico:")
        docs = solic.get("documentos", [])
        for d in docs:
            render_document_card(d)

        st.markdown("---")

        # -------------------------------------------------------------
        # ETAPA 4 — DECISÃO HUMANA CONTEXTUALIZADA
        # -------------------------------------------------------------
        st.markdown("### Etapa 4 • Decisão Fundamentada do Analista")
        st.caption("Selecione a ação autorizada para o estado atual da solicitação:")

        if status_atual == "EXCECAO":
            opcoes_decisao = [
                "Aprovar Análise e Encaminhar para Cadastro (Superar Exceção)",
                "Solicitar Complemento ao Cliente (Abrir Pendência e Pausar SLA)",
                "Rejeitar Solicitação com Justificativa"
            ]
        elif status_atual == "EM_CADASTRO":
            opcoes_decisao = [
                "Confirmar Efetivação Cadastral e Concluir Processo",
                "Devolver para Análise de Exceção Documental",
                "Rejeitar Solicitação com Justificativa"
            ]
        else:
            opcoes_decisao = [
                "Aprovar para Próxima Etapa",
                "Solicitar Complemento ao Cliente",
                "Rejeitar Solicitação"
            ]

        decisao = st.radio("Desfecho da análise:", opcoes_decisao, index=0)

        motivo_pend_sel = None
        if "Solicitar Complemento" in decisao:
            motivo_pend_sel = st.selectbox(
                "Causa estruturada da pendência:",
                [
                    "DOCUMENTO_ILEGIVEL — Aguardando reenvio de documento com legibilidade adequada",
                    "DOCUMENTO_AUSENTE — Aguardando envio do documento obrigatório",
                    "DADOS_DIVERGENTES — Aguardando correção das informações identificadas"
                ],
                index=0
            )

        justificativa = st.text_area(
            "Justificativa Formal da Decisão (Obrigatória para auditoria):",
            placeholder="Ex: Documento inspecionado visualmente e aceito conforme diretrizes da apólice; ou ilegível necessitando de novo envio pelo segurado."
        )

        col_dec_btn1, col_dec_btn2 = st.columns([2, 1])
        with col_dec_btn1:
            if st.button("💾 Gravar Decisão e Finalizar Tarefa", type="primary", use_container_width=True):
                if not justificativa.strip():
                    st.error("⛔ A justificativa formal é obrigatória para qualquer decisão do analista.")
                else:
                    # Idempotência: verifica se o caso ainda está no mesmo status antes de gravar
                    caso_atualizado = repo.get_solicitacao(caso_id)
                    if not caso_atualizado or caso_atualizado["status"] != status_atual:
                        st.warning("⚠️ Esta solicitação já foi modificada ou processada previamente. Recarregue a página.")
                    else:
                        # Tempo apurado
                        tempo_final_segundos = st.session_state.cronometro_acumulado
                        if st.session_state.cronometro_ativo:
                            tempo_final_segundos += (time.time() - st.session_state.cronometro_inicio)

                        # Validação de integridade atômica no backend antes de persistir a decisão
                        atual_db = repo.get_solicitacao(caso_id)
                        if not atual_db or atual_db["id"] != caso_id:
                            st.error("Erro crítico de consistência: a solicitação não foi encontrada no banco.")
                            st.stop()
                        if atual_db["protocolo"] != solic.get("protocolo"):
                            st.error(f"Bloqueio de Integridade: Protocolo da tela ({solic.get('protocolo')}) difere do banco ({atual_db['protocolo']}). Ação cancelada.")
                            st.stop()
                        if atual_db["status"] != status_atual:
                            st.warning(f"O status deste caso foi alterado para '{atual_db['status']}' por outra rotina. Recarregando...")
                            st.rerun()

                        # Registra tarefa no banco
                        repo.add_tarefa(TarefaHumana(
                            solicitacao_id=caso_id,
                            tipo="REVISAO_EXCECAO" if status_atual == "EXCECAO" else "CONFIRMACAO_CADASTRO",
                            atribuida_a="Analista Operacional",
                            estado="CONCLUIDA",
                            iniciada_em=datetime.now().isoformat(),
                            encerrada_em=datetime.now().isoformat(),
                            duracao_ativa_segundos=round(tempo_final_segundos, 1),
                            decisao=decisao,
                            justificativa=justificativa
                        ))

                        protocolo_caso = solic.get("protocolo", "")

                        # Executa transições de estado com confirmações persistentes
                        if "Aprovar" in decisao or "Encaminhar para Cadastro" in decisao:
                            workflow.iniciar_cadastro(caso_id, ator="ANALISTA")
                            set_persistent_confirmation(
                                protocolo=protocolo_caso,
                                acao="Superação de Exceção Documental e Encaminhamento para Cadastro",
                                status_anterior=status_atual,
                                status_novo="EM_CADASTRO",
                                sla_impacto="SLA mantido ativo (consumo normal de prazo interno)",
                                proxima_etapa="CADASTRO",
                                proxima_acao="Confirmar efetivação cadastral no sistema"
                            )
                        elif "Solicitar Complemento" in decisao:
                            tipo_enum = TipoPendencia.DOCUMENTO_ILEGIVEL
                            msg_causa = "Aguardando reenvio de documento com legibilidade adequada."
                            if motivo_pend_sel and "DOCUMENTO_AUSENTE" in motivo_pend_sel:
                                tipo_enum = TipoPendencia.DOCUMENTO_AUSENTE
                                msg_causa = "Aguardando envio do documento obrigatório."
                            elif motivo_pend_sel and "DADOS_DIVERGENTES" in motivo_pend_sel:
                                tipo_enum = TipoPendencia.DADOS_DIVERGENTES
                                msg_causa = "Aguardando correção das informações identificadas."

                            repo.add_pendencia(
                                Pendencia(
                                    solicitacao_id=caso_id,
                                    tipo=tipo_enum,
                                    descricao=f"{msg_causa} Detalhe formal: {justificativa}"
                                ),
                                ator="ANALISTA"
                            )
                            repo.update_status(
                                caso_id,
                                novo_status=StatusSolicitacao.AGUARDANDO_CLIENTE,
                                nova_etapa=EtapaProcesso.COMPLEMENTO,
                                ator="ANALISTA",
                                justificativa=justificativa
                            )
                            repo.update_sla_pause(caso_id, pausar=True)
                            workflow.notifications.enviar_comunicacao_simulada(
                                solicitacao_id=caso_id,
                                template_nome="SOLICITACAO_COMPLEMENTO",
                                destinatario=cli.get("email_ficticio", "cliente@exemplo.com"),
                                canal=solic.get("canal", "EMAIL"),
                                variaveis={"nome": cli.get("nome_ficticio", ""), "protocolo": protocolo_caso, "detalhe": f"{msg_causa} {justificativa}"}
                            )
                            set_persistent_confirmation(
                                protocolo=protocolo_caso,
                                acao="Abertura de Pendência com Cliente",
                                status_anterior=status_atual,
                                status_novo="AGUARDANDO_CLIENTE",
                                sla_impacto="SLA pausado imediatamente (relógio congelado até envio do complemento)",
                                proxima_etapa="COMPLEMENTO",
                                proxima_acao="Aguardar envio de anexo pelo segurado via portal/e-mail"
                            )
                        elif "Confirmar Efetivação Cadastral" in decisao:
                            if status_atual != StatusSolicitacao.EM_CADASTRO.value:
                                workflow.iniciar_cadastro(caso_id, ator="ANALISTA")
                            workflow.efetivar_cadastro_e_concluir(caso_id, ator="ANALISTA", observacao=justificativa)
                            set_persistent_confirmation(
                                protocolo=protocolo_caso,
                                acao="Confirmação de Efetivação Cadastral e Averbação",
                                status_anterior=status_atual,
                                status_novo="CONCLUIDA",
                                sla_impacto="SLA encerrado com sucesso (apólice concluída)",
                                proxima_etapa="FINALIZADO",
                                proxima_acao="Processo concluído com êxito; nenhuma ação pendente"
                            )
                        elif "Rejeitar" in decisao:
                            repo.update_status(
                                caso_id,
                                novo_status=StatusSolicitacao.REJEITADA,
                                nova_etapa=EtapaProcesso.FINALIZADO,
                                ator="ANALISTA",
                                justificativa=justificativa
                            )
                            set_persistent_confirmation(
                                protocolo=protocolo_caso,
                                acao="Rejeição Formal da Solicitação",
                                status_anterior=status_atual,
                                status_novo="REJEITADA",
                                sla_impacto="SLA encerrado por indeferimento",
                                proxima_etapa="FINALIZADO",
                                proxima_acao="Processo arquivado; notificação enviada"
                            )

                        # Reseta cronômetro e recarrega tela com confirmação visível
                        st.session_state.cronometro_ativo = False
                        st.session_state.cronometro_acumulado = 0.0
                        st.session_state.cronometro_inicio = 0.0
                        st.rerun()

        st.markdown("---")

        # -------------------------------------------------------------
        # ETAPA 5 — HISTÓRICO DE AUDITORIA COMPLETO
        # -------------------------------------------------------------
        st.markdown("### Etapa 5 • Histórico de Auditoria & Trilha de Eventos")
        render_timeline(solic.get("eventos", []))
