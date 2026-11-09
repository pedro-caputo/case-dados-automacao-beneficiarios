"""
Página 2 — Fila Operacional de Atendimento com Ações Contextualizadas e SLA.
"""
import streamlit as st
import pandas as pd
from src.config import DB_PATH, STATUS_ROTULOS, ETAPA_ROTULOS
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.workflow import WorkflowService
from src.sla import calcular_metricas_sla
from src.ui_helpers import (
    apply_corporate_style, render_corporate_header,
    render_journey_stepper, get_status_badge_html,
    get_sla_badge_html, render_timeline, render_document_card,
    set_persistent_confirmation, render_persistent_confirmation,
    render_universe_selector
)

st.set_page_config(page_title="Fila Operacional | Seguros PF", page_icon="📋", layout="wide")
apply_corporate_style()

init_db(DB_PATH)
repo = SolicitacaoRepository(DB_PATH)
workflow = WorkflowService(repo)

render_corporate_header(
    titulo="Fila Operacional de Atendimento",
    subtitulo="Bancada de triagem e distribuição com priorização por criticidade e controle de SLA"
)

render_journey_stepper(etapa_ativa=3)

# Banner de Confirmação Persistente (sobrevive a reruns e redirecionamentos)
render_persistent_confirmation()

# Seletor do Universo de Dados (Isolamento entre Operação Interativa e Simulação Experimental)
universo, run_id, universo_nome = render_universe_selector(repo, key_prefix="fila")

# -------------------------------------------------------------
# FILTROS OBJETIVOS
# -------------------------------------------------------------
st.markdown("#### Filtros e Localização de Casos")
f_col1, f_col2, f_col3, f_col4 = st.columns([2.5, 2, 2, 3.5])

with f_col1:
    opcoes_status = [
        "Apenas Casos Ativos (Padrão)",
        "Todos os Status (Inclusive Concluídos)"
    ] + list(STATUS_ROTULOS.values())
    escolha_status_lbl = st.selectbox("Filtrar por Status:", opcoes_status, index=0)

    filtro_status_key = None
    apenas_ativas = False

    if escolha_status_lbl == "Apenas Casos Ativos (Padrão)":
        apenas_ativas = True
    elif escolha_status_lbl == "Todos os Status (Inclusive Concluídos)":
        apenas_ativas = False
    else:
        for k, v in STATUS_ROTULOS.items():
            if v == escolha_status_lbl:
                filtro_status_key = k
                break

with f_col2:
    opcoes_etapas = ["Todas as Etapas"] + list(ETAPA_ROTULOS.values())
    escolha_etapa_lbl = st.selectbox("Filtrar por Etapa:", opcoes_etapas, index=0)
    filtro_etapa_key = None
    if escolha_etapa_lbl != "Todas as Etapas":
        for k, v in ETAPA_ROTULOS.items():
            if v == escolha_etapa_lbl:
                filtro_etapa_key = k
                break

with f_col3:
    canal_filtro = st.selectbox("Filtrar por Canal:", ["Todos os Canais", "APP", "AGENCIA", "EMAIL"], index=0)
    filtro_canal = None if canal_filtro == "Todos os Canais" else canal_filtro

with f_col4:
    busca_protocolo = st.text_input("Buscar por Protocolo ou Segurado:", placeholder="Digite o protocolo (BEN-...) ou nome...")

# Busca solicitações no SQLite com suporte a filtro de casos ativos e universo isolado
solicitacoes = repo.list_solicitacoes(
    status=filtro_status_key,
    etapa=filtro_etapa_key,
    canal=filtro_canal,
    universo=universo,
    run_id=run_id,
    search_protocol=busca_protocolo if busca_protocolo else None,
    apenas_ativas=apenas_ativas,
    limit=500
)

# -------------------------------------------------------------
# TABELA PRINCIPAL DA FILA OPERACIONAL
# -------------------------------------------------------------
st.markdown(f"**Total de Casos na Fila:** `{len(solicitacoes)}`")

if not solicitacoes:
    st.info("Nenhuma solicitação localizada com os filtros informados. Você pode registrar uma nova na aba 'Nova Solicitação' ou gerar o lote de 1.000 casos no 'Laboratório'.")
else:
    # Mapeia próxima ação recomendada por estado
    def proxima_acao_recomendada(status: str) -> str:
        if status == "PRONTA_PARA_CADASTRO":
            return "Iniciar cadastro sistêmico"
        if status == "EM_CADASTRO":
            return "Confirmar efetivação cadastral"
        if status == "AGUARDANDO_CLIENTE":
            return "Aguardando complemento (SLA pausado)"
        if status == "EXCECAO":
            return "Revisão na Bancada do Analista"
        if status == "CONCLUIDA":
            return "Processo finalizado com sucesso"
        if status == "RECEBIDA":
            return "Executar validação sistêmica"
        return "Em processamento"

    dados_tabela = []
    for s in solicitacoes:
        sla_m = calcular_metricas_sla(s)
        dt_criacao = s.get("data_criacao", "")[:16].replace("T", " ")
        status_raw = s["status"]
        status_amigavel = STATUS_ROTULOS.get(status_raw, status_raw)
        etapa_amigavel = ETAPA_ROTULOS.get(s["etapa"], s["etapa"])

        sla_restante_str = f"{sla_m['horas_restantes']}h" if not sla_m["concluido"] else f"Encerrado ({sla_m.get('lead_time_liquido_horas', 0.0)}h)"
        sla_estado_str = "✓ SLA Encerrado" if sla_m["concluido"] else ("⏸️ Pausado" if sla_m["estado"] == "PAUSADO" else ("⚠️ Expirado" if sla_m["expirado"] else "Normal"))

        dados_tabela.append({
            "ID": s["id"],
            "Protocolo": s["protocolo"],
            "Segurado": s.get("cliente_nome", "N/D"),
            "Canal": s["canal"],
            "Status": status_amigavel,
            "Etapa": etapa_amigavel,
            "Prioridade": s["prioridade"],
            "Prazo SLA": sla_restante_str,
            "SLA Estado": sla_estado_str,
            "Próxima Ação": proxima_acao_recomendada(status_raw),
            "Responsável": s.get("responsavel") or "Fila Geral"
        })

    df = pd.DataFrame(dados_tabela)
    st.dataframe(
        df[["Protocolo", "Segurado", "Canal", "Status", "Etapa", "Prioridade", "Prazo SLA", "SLA Estado", "Próxima Ação", "Responsável"]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    # -------------------------------------------------------------
    # DETALHAMENTO DO CASO SELECIONADO & AÇÕES CONTEXTUAIS
    # -------------------------------------------------------------
    st.markdown("#### Detalhes do Caso Selecionado")

    lista_opcoes = [f"#{s['id']} — {s['protocolo']} ({s.get('cliente_nome', 'N/D')}) | Status: {STATUS_ROTULOS.get(s['status'], s['status'])}" for s in solicitacoes]
    escolha = st.selectbox("Selecione o caso que deseja inspecionar:", lista_opcoes, index=0)

    solic_id_selecionado = int(escolha.split("—")[0].replace("#", "").strip())
    detalhes = repo.get_solicitacao(solic_id_selecionado)

    if detalhes:
        sla_info = calcular_metricas_sla(detalhes)
        status_atual = detalhes["status"]
        status_lbl = STATUS_ROTULOS.get(status_atual, status_atual)
        lead_liq = sla_info.get("lead_time_liquido_horas", sla_info["lead_time_bruto_horas"])

        # Cabeçalho do Caso
        c_top1, c_top2, c_top3, c_top4 = st.columns(4)
        with c_top1:
            st.markdown(f"**Protocolo:** `{detalhes['protocolo']}`")
            st.markdown(f"**Canal de Origem:** `{detalhes['canal']}`")
        with c_top2:
            st.markdown(f"**Status:** {get_status_badge_html(status_atual)}", unsafe_allow_html=True)
            st.markdown(f"**Etapa Atual:** `{ETAPA_ROTULOS.get(detalhes['etapa'], detalhes['etapa'])}`")
        with c_top3:
            st.markdown(f"**Controle de SLA:** {get_sla_badge_html(sla_info, status=status_atual)}", unsafe_allow_html=True)
            st.markdown(f"**Lead Time Líquido:** `{lead_liq}h` (Bruto: `{sla_info['lead_time_bruto_horas']}h`)")
        with c_top4:
            st.markdown(f"**Pausa Acumulada:** `{sla_info['pausa_acumulada_horas']}h`")
            st.markdown(f"**Responsável Atual:** `{detalhes.get('responsavel') or 'Fila Geral'}`")

        st.markdown("<br/>", unsafe_allow_html=True)

        # Painel de Ações Contextuais (Apenas ações válidas para o estado!)
        st.markdown("##### Ações Contextuais para este Caso:")
        
        act_box = st.container()
        with act_box:
            col_b1, col_b2, col_b3 = st.columns(3)

            with col_b1:
                if status_atual == "PRONTA_PARA_CADASTRO":
                    if st.button("Iniciar Processo de Cadastro ➔", type="primary", use_container_width=True):
                        workflow.iniciar_cadastro(detalhes["id"], ator="ANALISTA")
                        set_persistent_confirmation(
                            protocolo=detalhes["protocolo"],
                            acao="Início de Cadastro Sistêmico",
                            status_anterior=status_atual,
                            status_novo="EM_CADASTRO",
                            sla_impacto="SLA mantido ativo (consumo normal de prazo interno)",
                            proxima_etapa="CADASTRO",
                            proxima_acao="Confirmar efetivação cadastral no sistema"
                        )
                        st.rerun()

                elif status_atual == "EM_CADASTRO":
                    if st.button("Confirmar Efetivação Cadastral ➔", type="primary", use_container_width=True):
                        workflow.efetivar_cadastro_e_concluir(
                            detalhes["id"],
                            ator="ANALISTA",
                            observacao="Cadastro confirmado no sistema central e apólice averbada."
                        )
                        set_persistent_confirmation(
                            protocolo=detalhes["protocolo"],
                            acao="Efetivação Cadastral e Averbação na Apólice",
                            status_anterior=status_atual,
                            status_novo="CONCLUIDA",
                            sla_impacto="SLA encerrado com sucesso (apólice emitida)",
                            proxima_etapa="FINALIZADO",
                            proxima_acao="Processo concluído com êxito; nenhuma ação pendente"
                        )
                        st.rerun()

                elif status_atual == "EXCECAO":
                    st.info("⚠️ Este caso está retido para análise de inconsistências documentais.")
                    if st.button("Abrir na Bancada do Analista ➔", type="primary", use_container_width=True):
                        st.session_state.caso_para_analisar_id = detalhes["id"]
                        st.session_state.universo_selecionado = detalhes.get("universo", "INTERATIVO")
                        st.session_state.run_id_selecionado = detalhes.get("run_id")
                        st.switch_page("pages/03_Analise_Humana.py")

                elif status_atual == "AGUARDANDO_CLIENTE":
                    st.warning("⏸️ O relógio de SLA está pausado aguardando o envio de documento complementar.")
                    if st.button("📥 Simular Recebimento de Complemento do Cliente", use_container_width=True):
                        # Simulação com sequência transparente de revalidação
                        novos_docs = [
                            {"tipo": "DOCUMENTO_IDENTIFICACAO", "nome_arquivo": "rg_conforme.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True},
                            {"tipo": "FORMULARIO_ALTERACAO", "nome_arquivo": "formulario_assinado_valido.pdf", "presente": True, "formato": "pdf", "valido_sintatico": True, "legibilidade_simulada": True}
                        ]
                        workflow.registrar_complemento_cliente(
                            solic_id=detalhes["id"],
                            documentos_atualizados=novos_docs,
                            resolucao="Complemento recebido pelo canal digital; documentos simulados como conformes.",
                            ator="CLIENTE"
                        )
                        set_persistent_confirmation(
                            protocolo=detalhes["protocolo"],
                            acao="Recepção e Revalidação de Complemento Documental",
                            status_anterior=status_atual,
                            status_novo="PRONTA_PARA_CADASTRO",
                            sla_impacto="SLA retomado (relógio desbloqueado após complemento)",
                            proxima_etapa="CADASTRO",
                            proxima_acao="Iniciar cadastro sistêmico no menu contextual"
                        )
                        st.rerun()

                elif status_atual == "CONCLUIDA":
                    st.success("✓ Este caso já foi finalizado e cadastrado com sucesso. Nenhuma ação pendente.")

            with col_b2:
                if status_atual in ["RECEBIDA", "EM_VALIDACAO"]:
                    if st.button("Executar Validação Sistêmica ➔", use_container_width=True):
                        workflow.executar_validacao_sistemica(detalhes["id"], ator="ANALISTA")
                        set_persistent_confirmation(
                            protocolo=detalhes["protocolo"],
                            acao="Execução de Validação Sistêmica",
                            status_anterior=status_atual,
                            status_novo="PRONTA_PARA_CADASTRO",
                            sla_impacto="SLA mantido ativo",
                            proxima_etapa="CADASTRO",
                            proxima_acao="Prosseguir para a efetivação cadastral"
                        )
                        st.rerun()

            with col_b3:
                if status_atual not in ["CONCLUIDA", "REJEITADA", "EXCECAO"]:
                    if st.button("Encaminhar para Análise de Exceção", use_container_width=True):
                        repo.update_status(
                            detalhes["id"],
                            novo_status="EXCECAO",
                            nova_etapa="CONFERENCIA",
                            ator="ANALISTA",
                            justificativa="Encaminhado manualmente para verificação de exceção."
                        )
                        set_persistent_confirmation(
                            protocolo=detalhes["protocolo"],
                            acao="Encaminhamento Manual para Bancada do Analista",
                            status_anterior=status_atual,
                            status_novo="EXCECAO",
                            sla_impacto="SLA mantido ativo (prazo de análise correndo)",
                            proxima_etapa="CONFERENCIA",
                            proxima_acao="Abrir caso na Bancada do Analista para decisão"
                        )
                        st.rerun()

        st.markdown("<br/>", unsafe_allow_html=True)

        # Abas de visualização detalhada
        tab_dados, tab_docs, tab_timeline = st.tabs([
            "Dados do Segurado & Beneficiários",
            "Documentos & Diagnóstico de Conformidade",
            "Histórico de Auditoria & Eventos"
        ])

        with tab_dados:
            cli = detalhes.get("cliente", {})
            st.markdown(f"""
            - **Segurado:** {cli.get('nome_ficticio')}
            - **CPF:** `{cli.get('cpf_ficticio')}`
            - **E-mail:** {cli.get('email_ficticio')}
            - **Telefone:** {cli.get('telefone_ficticio')}
            """)

            st.markdown("##### Beneficiários Indicados:")
            bens = detalhes.get("beneficiarios", [])
            df_b = pd.DataFrame([{
                "Nome": b.get("nome_ficticio"),
                "CPF": b.get("cpf_ficticio"),
                "Parentesco": b.get("parentesco"),
                "Participação (%)": f"{b.get('percentual', 0):.2f}%"
            } for b in bens])
            st.dataframe(df_b, use_container_width=True, hide_index=True)

        with tab_docs:
            st.markdown("##### Anexos Registrados:")
            for d in detalhes.get("documentos", []):
                render_document_card(d)

            pends = detalhes.get("pendencias", [])
            if pends:
                st.markdown("##### Pendências Operacionais Registradas:")
                for p in pends:
                    status_p = "🔴 Aberta" if not p.get("fechada_em") else f"🟢 Resolvida ({p.get('fechada_em')[:16]})"
                    st.markdown(f"- **Tipo:** `{p.get('tipo')}` | Status: **{status_p}**")
                    st.markdown(f"  *Descrição:* {p.get('descricao')}")
                    if p.get("resolucao"):
                        st.markdown(f"  *Resolução:* {p.get('resolucao')}")

        with tab_timeline:
            render_timeline(detalhes.get("eventos", []))
