"""
Página 4 — Dashboard Gerencial & Observabilidade Operacional.
Responde estruturadamente às 5 perguntas fundamentais da gestão com isolamento de cenários.
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from src.config import (
    DB_PATH, THEME_COLORS, STATUS_ROTULOS, ETAPA_ROTULOS,
    AS_IS_TOTAL_HORAS, AS_IS_SLA_NO_PRAZO, AS_IS_VOLUME_MENSAL
)
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.sla import calcular_metricas_sla
from src.ui_helpers import (
    apply_corporate_style, render_corporate_header,
    render_journey_stepper, render_universe_selector
)

st.set_page_config(page_title="Dashboard Gerencial | Seguros PF", page_icon="📊", layout="wide")
apply_corporate_style()

init_db(DB_PATH)
repo = SolicitacaoRepository(DB_PATH)

render_corporate_header(
    titulo="Dashboard Gerencial de Operações & Rastreabilidade",
    subtitulo="Visibilidade executiva em tempo real: backlog por etapa, controle de SLA e esforço humano"
)

render_journey_stepper(etapa_ativa=6)

# -------------------------------------------------------------
# SELEÇÃO EXPLÍCITA DO CENÁRIO (ISOLAMENTO DE DADOS)
# -------------------------------------------------------------
filtro_universo, filtro_run_id, origem_nome = render_universe_selector(repo, key_prefix="dashboard")

# Consulta métricas diretamente no SQLite respeitando o universo
metrics = repo.get_dashboard_metrics(universo=filtro_universo, run_id=filtro_run_id)

total_solic = metrics.get("total_solicitacoes", 0)
status_counts = metrics.get("status_counts", {})
etapa_counts = metrics.get("etapa_counts", {})
canal_counts = metrics.get("canal_counts", {})
tarefas_m = metrics.get("tarefas_metricas", {})
pendencias_t = metrics.get("pendencias_tipo", {})
pendencias_abertas_t = metrics.get("pendencias_abertas_tipo", {})
pendencias_resolvidas_t = metrics.get("pendencias_resolvidas_tipo", {})
total_pend_abertas = metrics.get("total_pendencias_abertas", 0)
total_pend_resolvidas = metrics.get("total_pendencias_resolvidas", 0)

concluidas = status_counts.get("CONCLUIDA", 0)
aguardando = status_counts.get("AGUARDANDO_CLIENTE", 0)
excecoes = status_counts.get("EXCECAO", 0)
prontas = status_counts.get("PRONTA_PARA_CADASTRO", 0) + status_counts.get("EM_CADASTRO", 0)
abertas = max(0, total_solic - concluidas - status_counts.get("REJEITADA", 0))

st.markdown("---")

# -------------------------------------------------------------
# PERGUNTA 1: QUAL É O VOLUME ATUAL?
# -------------------------------------------------------------
st.markdown("### 1. Qual é o volume atual da operação?")
st.caption("Visão geral quantitativa de entradas, estoque em andamento e desfechos:")

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: {THEME_COLORS['primary']};">
        <div class="kpi-title">Total Recebidas</div>
        <div class="kpi-value">{total_solic}</div>
        <div class="kpi-caption">Registros na base ativa</div>
    </div>
    """, unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: {THEME_COLORS['secondary']};">
        <div class="kpi-title">Backlog Aberto</div>
        <div class="kpi-value">{abertas}</div>
        <div class="kpi-caption">Casos em processamento</div>
    </div>
    """, unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: {THEME_COLORS['warning']};">
        <div class="kpi-title">Aguardando Cliente</div>
        <div class="kpi-value">{aguardando}</div>
        <div class="kpi-caption">SLA pausado (pendência)</div>
    </div>
    """, unsafe_allow_html=True)

with k4:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #D97706;">
        <div class="kpi-title">Exceções de Analista</div>
        <div class="kpi-value">{excecoes}</div>
        <div class="kpi-caption">Exigem intervenção humana</div>
    </div>
    """, unsafe_allow_html=True)

with k5:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: {THEME_COLORS['success']};">
        <div class="kpi-title">Concluídas</div>
        <div class="kpi-value">{concluidas}</div>
        <div class="kpi-caption">Efetivadas na apólice</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# -------------------------------------------------------------
# PERGUNTA 2: ONDE ESTÃO OS CASOS? (ETAPAS)
# -------------------------------------------------------------
st.markdown("### 2. Onde estão os casos na esteira operacional?")
st.caption("Distribuição do estoque entre as etapas do processo TO-BE:")

col_g1, col_g2 = st.columns([1.5, 1])

with col_g1:
    if etapa_counts:
        # Mapeia rótulos amigáveis
        df_etapas = pd.DataFrame([
            {"Etapa": ETAPA_ROTULOS.get(k, k), "Quantidade": v}
            for k, v in etapa_counts.items()
        ])
        fig_etapas = px.bar(
            df_etapas,
            x="Etapa",
            y="Quantidade",
            color="Etapa",
            color_discrete_sequence=["#0C2340", "#2F73D8", "#D97706", "#15803D", "#64748B"],
            text="Quantidade"
        )
        fig_etapas.update_traces(
            textfont=dict(color="#0F172A", size=13, weight="bold"),
            textposition="outside"
        )
        fig_etapas.update_layout(
            showlegend=False,
            margin=dict(l=15, r=15, t=15, b=15),
            height=280,
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(color="#0F172A", family="Inter, sans-serif", size=12)
        )
        fig_etapas.update_xaxes(
            title=dict(text="Etapa Operacional", font=dict(color="#0F172A", size=13, weight="bold")),
            tickfont=dict(color="#0F172A", size=12)
        )
        fig_etapas.update_yaxes(
            title=dict(text="Quantidade", font=dict(color="#0F172A", size=13, weight="bold")),
            tickfont=dict(color="#0F172A", size=12),
            gridcolor="#E2E8F0"
        )
        st.plotly_chart(fig_etapas, use_container_width=True)
    else:
        st.info("Nenhuma solicitação registrada nesta base para exibir distribuição por etapa.")

with col_g2:
    if status_counts:
        df_status = pd.DataFrame([
            {"Status": STATUS_ROTULOS.get(k, k), "Quantidade": v}
            for k, v in status_counts.items()
        ])
        fig_status = px.pie(
            df_status,
            names="Status",
            values="Quantidade",
            hole=0.45,
            color_discrete_sequence=["#1E3A8A", "#2563EB", "#D97706", "#059669", "#DC2626", "#7C3AED", "#64748B"]
        )
        fig_status.update_traces(
            textinfo="percent+label",
            textposition="inside",
            insidetextfont=dict(color="#FFFFFF", size=12, weight="bold"),
            outsidetextfont=dict(color="#0F172A", size=12, weight="bold"),
            marker=dict(line=dict(color="#FFFFFF", width=2))
        )
        fig_status.update_layout(
            margin=dict(l=15, r=15, t=15, b=15),
            height=280,
            paper_bgcolor="#FFFFFF",
            font=dict(color="#0F172A", family="Inter, sans-serif", size=12),
            legend=dict(
                font=dict(color="#0F172A", size=12),
                bgcolor="rgba(255,255,255,0.9)",
                bordercolor="#CBD5E1",
                borderwidth=1
            )
        )
        st.plotly_chart(fig_status, use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------
# PERGUNTA 3: O QUE EXIGE ATENÇÃO? (SLA E AGING)
# -------------------------------------------------------------
st.markdown("### 3. O que exige atenção imediata da gestão?")
st.caption("Indicadores de risco operacional, pontualidade e controle de prazos:")

# Busca solicitações no SQLite respeitando estritamente o universo
solics_universo = repo.list_solicitacoes(universo=filtro_universo, run_id=filtro_run_id, limit=2000)
sla_ok = 0
sla_alerta = 0
sla_expirado = 0
sla_pausado = 0
sla_encerrado_no_prazo = 0
sla_encerrado_fora_prazo = 0

for s in solics_universo:
    m = calcular_metricas_sla(s)
    if s["status"] in ["CONCLUIDA", "REJEITADA"] or s.get("data_conclusao"):
        if m.get("expirado"):
            sla_encerrado_fora_prazo += 1
        else:
            sla_encerrado_no_prazo += 1
    else:
        if m["estado"] == "PAUSADO":
            sla_pausado += 1
        elif m["expirado"]:
            sla_expirado += 1
        elif m["horas_restantes"] < 48:
            sla_alerta += 1
        else:
            sla_ok += 1

col_a1, col_a2, col_a3, col_a4 = st.columns(4)

with col_a1:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #15803D;">
        <div class="kpi-title">SLA Confortável Ativo (> 48h)</div>
        <div class="kpi-value">{sla_ok}</div>
        <div class="kpi-caption">Dentro do prazo regulamentar</div>
    </div>
    """, unsafe_allow_html=True)

with col_a2:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #B45309;">
        <div class="kpi-title">SLA em Alerta Ativo (< 48h)</div>
        <div class="kpi-value">{sla_alerta}</div>
        <div class="kpi-caption">Prioridade de atendimento</div>
    </div>
    """, unsafe_allow_html=True)

with col_a3:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #B91C1C;">
        <div class="kpi-title">SLA Expirado Ativo</div>
        <div class="kpi-value">{sla_expirado}</div>
        <div class="kpi-caption">Atraso operacional crítico</div>
    </div>
    """, unsafe_allow_html=True)

with col_a4:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #64748B;">
        <div class="kpi-title">Relógio de SLA Pausado</div>
        <div class="kpi-value">{sla_pausado}</div>
        <div class="kpi-caption">Aguardando cliente (sem prejuízo)</div>
    </div>
    """, unsafe_allow_html=True)

total_encerrados = sla_encerrado_no_prazo + sla_encerrado_fora_prazo
if total_encerrados > 0:
    pct_no_prazo = (sla_encerrado_no_prazo / total_encerrados) * 100
    st.markdown(
        f'<div style="background-color: #F0FDF4; border: 1px solid #BBF7D0; border-left: 4px solid #16A34A; padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.88rem; color: #166534; margin-top: 0.75rem;">'
        f'✓ <strong>SLA Encerrado (Casos Finalizados):</strong> <code>{total_encerrados}</code> solicitações concluídas — '
        f'<strong>{sla_encerrado_no_prazo} no prazo</strong> ({pct_no_prazo:.1f}%) e <strong>{sla_encerrado_fora_prazo} fora do prazo</strong>.'
        f'</div>',
        unsafe_allow_html=True
    )

st.markdown("<br/>", unsafe_allow_html=True)

# -------------------------------------------------------------
# PERGUNTA 4: ONDE ESTÃO OS PROBLEMAS? (INCONSISTÊNCIAS E CANAIS)
# -------------------------------------------------------------
st.markdown("### 4. Onde estão os problemas e motivos de pendência?")
st.caption("Diagnóstico de inconsistências documentais (distinguindo pendências em aberto de ocorrências históricas resolvidas) e volume por canal:")

col_p1, col_p2 = st.columns(2)

with col_p1:
    tab_p_abertas, tab_p_resolvidas = st.tabs([
        f"Pendências em Aberto ({total_pend_abertas})",
        f"Histórico Resolvido ({total_pend_resolvidas})"
    ])

    with tab_p_abertas:
        if pendencias_abertas_t:
            df_pa = pd.DataFrame([
                {"Tipo de Pendência": k.replace("_", " ").title(), "Quantidade": v}
                for k, v in pendencias_abertas_t.items()
            ])
            fig_pa = px.bar(
                df_pa,
                x="Quantidade",
                y="Tipo de Pendência",
                orientation="h",
                color="Tipo de Pendência",
                color_discrete_sequence=["#D97706", "#EA580C", "#B45309"],
                text="Quantidade"
            )
            fig_pa.update_traces(
                textfont=dict(color="#0F172A", size=12, weight="bold"),
                textposition="outside"
            )
            fig_pa.update_layout(
                showlegend=False,
                margin=dict(l=15, r=15, t=15, b=15),
                height=230,
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#F8FAFC",
                font=dict(color="#0F172A", family="Inter, sans-serif", size=12)
            )
            fig_pa.update_xaxes(
                title=dict(text="Quantidade", font=dict(color="#0F172A", size=12, weight="bold")),
                tickfont=dict(color="#0F172A", size=11),
                gridcolor="#E2E8F0"
            )
            fig_pa.update_yaxes(
                tickfont=dict(color="#0F172A", size=11, weight="bold")
            )
            st.plotly_chart(fig_pa, use_container_width=True)
        else:
            st.success("✓ **Nenhuma pendência ativa no momento.** Todas as solicitações estão regulares ou já tiveram complementos resolvidos.")

    with tab_p_resolvidas:
        if pendencias_resolvidas_t:
            df_pr = pd.DataFrame([
                {"Tipo de Pendência": k.replace("_", " ").title(), "Quantidade": v}
                for k, v in pendencias_resolvidas_t.items()
            ])
            fig_pr = px.bar(
                df_pr,
                x="Quantidade",
                y="Tipo de Pendência",
                orientation="h",
                color="Tipo de Pendência",
                color_discrete_sequence=["#059669", "#10B981", "#34D399"],
                text="Quantidade"
            )
            fig_pr.update_traces(
                textfont=dict(color="#0F172A", size=12, weight="bold"),
                textposition="outside"
            )
            fig_pr.update_layout(
                showlegend=False,
                margin=dict(l=15, r=15, t=15, b=15),
                height=230,
                paper_bgcolor="#FFFFFF",
                plot_bgcolor="#F8FAFC",
                font=dict(color="#0F172A", family="Inter, sans-serif", size=12)
            )
            fig_pr.update_xaxes(
                title=dict(text="Quantidade", font=dict(color="#0F172A", size=12, weight="bold")),
                tickfont=dict(color="#0F172A", size=11),
                gridcolor="#E2E8F0"
            )
            fig_pr.update_yaxes(
                tickfont=dict(color="#0F172A", size=11, weight="bold")
            )
            st.plotly_chart(fig_pr, use_container_width=True)
            st.caption("ℹ️ Ocorrências documentais históricas que foram complementadas e solucionadas com sucesso.")
        else:
            st.info("Nenhuma ocorrência documental histórica registrada.")

with col_p2:
    st.markdown("##### Volume por Canal de Entrada:")
    if canal_counts:
        df_c = pd.DataFrame(list(canal_counts.items()), columns=["Canal", "Quantidade"])
        fig_c = px.bar(
            df_c,
            x="Canal",
            y="Quantidade",
            color="Canal",
            color_discrete_map={"EMAIL": "#2F73D8", "AGENCIA": "#0C2340", "APP": "#15803D"},
            text="Quantidade"
        )
        fig_c.update_traces(
            textfont=dict(color="#0F172A", size=12, weight="bold"),
            textposition="outside"
        )
        fig_c.update_layout(
            showlegend=False,
            margin=dict(l=15, r=15, t=15, b=15),
            height=250,
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#F8FAFC",
            font=dict(color="#0F172A", family="Inter, sans-serif", size=12)
        )
        fig_c.update_xaxes(
            title=dict(text="Canal", font=dict(color="#0F172A", size=12, weight="bold")),
            tickfont=dict(color="#0F172A", size=12)
        )
        fig_c.update_yaxes(
            title=dict(text="Quantidade", font=dict(color="#0F172A", size=12, weight="bold")),
            tickfont=dict(color="#0F172A", size=12),
            gridcolor="#E2E8F0"
        )
        st.plotly_chart(fig_c, use_container_width=True)

st.markdown("---")

# -------------------------------------------------------------
# PERGUNTA 5: COMO A OPERAÇÃO EVOLUI? (ESFORÇO AUDITADO)
# -------------------------------------------------------------
st.markdown("### 5. Como a operação evolui? (Esforço Humano Auditado)")
st.caption("Tempo real de trabalho humano medido pelo cronômetro dos analistas na bancada:")

col_e1, col_e2, col_e3 = st.columns(3)
total_tarefas = tarefas_m.get("total_tarefas", 0)
tempo_total_s = tarefas_m.get("tempo_ativo_total_segundos", 0.0)
tempo_medio_s = tarefas_m.get("tempo_ativo_medio_segundos", 0.0)

with col_e1:
    st.metric("Total de Análises Humanas Gravadas", f"{total_tarefas} intervenções")

with col_e2:
    st.metric("Tempo Ativo Auditado no Banco", f"{tempo_total_s:.1f} s ({tempo_total_s/60:.1f} min)")

with col_e3:
    tempo_str = f"{tempo_medio_s:.1f} s / caso" if total_tarefas > 0 else "Sem medições"
    st.metric("Tempo Médio por Intervenção", tempo_str)

st.caption("🛡️ **Auditabilidade dos Indicadores:** Todos os números acima são extraídos por consultas relacionais diretamente do SQLite local, sem valores decorativos ou arbitrários.")
