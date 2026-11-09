"""
Central de Operações — Ponto de Entrada da Gestão de Alteração de Beneficiários.
"""
import sys
import importlib
import streamlit as st

# Recarrega dinamicamente submódulos locais para evitar cache em disco durante atualizações
for _mod_name in list(sys.modules.keys()):
    if _mod_name.startswith("src.") and _mod_name in sys.modules:
        try:
            importlib.reload(sys.modules[_mod_name])
        except Exception:
            pass

from src.config import DB_PATH, DEFAULT_SEED
from src.database import init_db, reset_operational_data
from src.repositories import SolicitacaoRepository
from src.ui_helpers import (
    apply_corporate_style, render_corporate_header,
    render_journey_stepper, render_persistent_confirmation
)

st.set_page_config(
    page_title="Central de Operações | Beneficiários Seguros PF",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_corporate_style()
init_db(DB_PATH)
repo = SolicitacaoRepository(DB_PATH)

render_corporate_header(
    titulo="Central de Operações — Alteração de Beneficiários",
    subtitulo="Plataforma Integrada de Gestão de Solicitações, Automação Preventiva e Controle de SLA"
)

# Stepper da Jornada
render_journey_stepper(etapa_ativa=1)
render_persistent_confirmation()

# Seção de Entrada Rápida: O que fazer e por onde começar?
st.markdown("### Por onde você deseja começar?")
st.markdown("Selecione uma das três ações principais abaixo para navegar pela esteira operacional:")

col_act1, col_act2, col_act3 = st.columns(3)

with col_act1:
    st.markdown("""
    <div class="kpi-card" style="border-top-color: #2F73D8; min-height: 195px;">
        <div class="kpi-title">Ação 1 • Entrada de Dados</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #0C2340; margin: 0.4rem 0;">Nova Solicitação</div>
        <div class="kpi-caption" style="margin-bottom: 1rem;">
            Preencha um formulário simulado e teste a validação preventiva na origem (bloqueio de CPF incorreto e soma diferente de 100%).
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Criar Nova Solicitação ➔", key="btn_ir_nova", type="primary", use_container_width=True):
        st.switch_page("pages/01_Nova_Solicitacao.py")

with col_act2:
    st.markdown("""
    <div class="kpi-card" style="border-top-color: #0C2340; min-height: 195px;">
        <div class="kpi-title">Ação 2 • Gestão Operacional</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #0C2340; margin: 0.4rem 0;">Fila de Trabalho</div>
        <div class="kpi-caption" style="margin-bottom: 1rem;">
            Consulte as solicitações em andamento, acompanhe o relógio de SLA em tempo real e trate pendências com clientes.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Acessar Fila Operacional ➔", key="btn_ir_fila", use_container_width=True):
        st.switch_page("pages/02_Fila_Operacional.py")

with col_act3:
    st.markdown("""
    <div class="kpi-card" style="border-top-color: #F28C28; min-height: 195px;">
        <div class="kpi-title">Ação 3 • Simulação & Métricas</div>
        <div style="font-size: 1.15rem; font-weight: 700; color: #0C2340; margin: 0.4rem 0;">Laboratório de Simulação</div>
        <div class="kpi-caption" style="margin-bottom: 1rem;">
            Execute o lote de 1.000 intenções sintéticas com medição computacional de alta resolução e síntese para o Slide 10.
        </div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Abrir Laboratório ➔", key="btn_ir_lab", use_container_width=True):
        st.switch_page("pages/05_Laboratorio.py")

st.markdown("<br/>", unsafe_allow_html=True)

# Indicadores Rápidos da Operação Interativa (Exclusivo Demonstração Manual)
st.markdown("### Situação Atual da Operação Interativa")
metrics = repo.get_dashboard_metrics(universo="INTERATIVO")
status_counts = metrics.get("status_counts", {})
total_solic = metrics.get("total_solicitacoes", 0)

kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

with kpi1:
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #0C2340;">
        <div class="kpi-title">Total Recebidas</div>
        <div class="kpi-value">{total_solic}</div>
        <div class="kpi-caption">Registros operacionais</div>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    prontas = status_counts.get("PRONTA_PARA_CADASTRO", 0)
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #15803D;">
        <div class="kpi-title">Prontas p/ Cadastro</div>
        <div class="kpi-value">{prontas}</div>
        <div class="kpi-caption">Aptas para efetivação</div>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    pendentes = status_counts.get("AGUARDANDO_CLIENTE", 0)
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #B45309;">
        <div class="kpi-title">Aguardando Cliente</div>
        <div class="kpi-value">{pendentes}</div>
        <div class="kpi-caption">SLA pausado</div>
    </div>
    """, unsafe_allow_html=True)

with kpi4:
    excecoes = status_counts.get("EXCECAO", 0)
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #D97706;">
        <div class="kpi-title">Em Análise Humana</div>
        <div class="kpi-value">{excecoes}</div>
        <div class="kpi-caption">Exceções e dúvidas</div>
    </div>
    """, unsafe_allow_html=True)

with kpi5:
    concluidas = status_counts.get("CONCLUIDA", 0)
    st.markdown(f"""
    <div class="kpi-card" style="border-top-color: #2F73D8;">
        <div class="kpi-title">Concluídas</div>
        <div class="kpi-value">{concluidas}</div>
        <div class="kpi-caption">Efetivadas na apólice</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br/>", unsafe_allow_html=True)

# Seção de Manutenção da Demonstração
with st.expander("⚙️ Gestão de Demonstração e Base de Dados", expanded=False):
    col_d1, col_d2 = st.columns([3, 1])
    with col_d1:
        total_int = repo.count_raw_intents(DEFAULT_SEED)
        st.write(f"• **Base Sintética de Intenções:** `{total_int}` registros determinísticos (Seed: `{DEFAULT_SEED}`).")
        st.write("• **Banco de Dados Relacional:** SQLite local com integridade referencial ativa.")
    with col_d2:
        if st.button("Reiniciar Dados Demo", help="Limpa casos criados manualmente na interface sem afetar a base sintética"):
            reset_operational_data(DB_PATH)
            st.success("Dados operacionais reiniciados!")
            st.rerun()
