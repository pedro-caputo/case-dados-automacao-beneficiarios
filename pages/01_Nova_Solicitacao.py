"""
Página 1 — Entrada de Novas Solicitações com Validação Preventiva na Origem.
"""
import streamlit as st
import random
from src.config import DB_PATH, STATUS_ROTULOS
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.workflow import WorkflowService
from src.validators import (
    validar_cpf, validar_beneficiarios, format_cpf,
    format_phone, validar_email
)
from src.synthetic_data import gerar_cpf_valido, gerar_perfil_ficticio_completo
from src.ui_helpers import (
    apply_corporate_style, render_corporate_header,
    render_journey_stepper, get_status_badge_html,
    set_persistent_confirmation, render_persistent_confirmation
)

st.set_page_config(page_title="Nova Solicitação | Seguros PF", page_icon="📝", layout="wide")
apply_corporate_style()

init_db(DB_PATH)
repo = SolicitacaoRepository(DB_PATH)
workflow = WorkflowService(repo)

render_corporate_header(
    titulo="Nova Solicitação de Alteração de Beneficiários",
    subtitulo="Formulário estruturado com validação preventiva e conferência de integridade na entrada"
)

# Stepper da Jornada Operacional
render_journey_stepper(etapa_ativa=1)
render_persistent_confirmation()

# Inicializa sessão para lista de beneficiários
if "beneficiarios_form" not in st.session_state:
    st.session_state.beneficiarios_form = [
        {"nome": "", "cpf": "", "parentesco": "Cônjuge", "percentual": 100.0}
    ]

# Callbacks para aplicação de máscaras profissionais durante preenchimento
def formatar_cpf_titular():
    if "input_cpf_segurado" in st.session_state:
        st.session_state.input_cpf_segurado = format_cpf(st.session_state.input_cpf_segurado)

def formatar_tel_titular():
    if "input_tel_segurado" in st.session_state:
        st.session_state.input_tel_segurado = format_phone(st.session_state.input_tel_segurado)

# Caixa de Controles de Simulação (Separada dos campos reais do cliente)
with st.expander("🛠️ Ferramentas do Demonstrador / Injeção de Falhas de Teste", expanded=False):
    st.caption("Gere perfis fictícios variados ou injete falhas para testar os mecanismos de defesa preventiva:")
    sim_col1, sim_col2 = st.columns([2, 2])
    with sim_col1:
        if st.button("🎲 Gerar Novo Perfil Fictício Válido (Demonstração)", use_container_width=True):
            perfil = gerar_perfil_ficticio_completo()
            st.session_state.input_nome_segurado = perfil["titular"]["nome"]
            st.session_state.input_cpf_segurado = perfil["titular"]["cpf"]
            st.session_state.input_email_segurado = perfil["titular"]["email"]
            st.session_state.input_tel_segurado = perfil["titular"]["telefone"]
            st.session_state.beneficiarios_form = perfil["beneficiarios"]
            # Sincroniza chaves de formulário dinâmico
            for i, b in enumerate(perfil["beneficiarios"]):
                st.session_state[f"b_nome_{i}"] = b["nome"]
                st.session_state[f"b_cpf_{i}"] = b["cpf"]
                st.session_state[f"b_par_{i}"] = b["parentesco"]
                st.session_state[f"b_pct_{i}"] = b["percentual"]
            st.rerun()

    with sim_col2:
        simular_baixa_legibilidade = st.checkbox("Simular documento ilegível (gera exceção humana)", value=False)
        simular_anexo_ausente = st.checkbox("Simular anexo faltante (gera pendência com cliente)", value=False)

st.markdown("<br/>", unsafe_allow_html=True)

# -------------------------------------------------------------
# ETAPA A: DADOS DO SEGURADO
# -------------------------------------------------------------
st.markdown("### Etapa A • Dados do Segurado")
st.caption("Identificação do titular da apólice com máscaras automáticas e validação preventiva:")

col_c1, col_c2 = st.columns([1, 2])
with col_c1:
    canal = st.selectbox(
        "Canal de Atendimento:",
        ["APP", "AGENCIA", "EMAIL"],
        index=0,
        help="Canal por onde a solicitação foi originada"
    )
with col_c2:
    st.info("ℹ️ **Prioridade Operacional:** Definida automaticamente pelo sistema conforme regras da apólice (Padrão: Média).")

col_d1, col_d2 = st.columns(2)
with col_d1:
    nome_segurado = st.text_input(
        "Nome Completo do Segurado:",
        key="input_nome_segurado",
        placeholder="Ex: Mariana Alencar Ribeiro"
    )
    email_segurado = st.text_input(
        "E-mail de Contato:",
        key="input_email_segurado",
        placeholder="cliente@exemplo.com.br"
    )
    if email_segurado:
        val_em, mot_em = validar_email(email_segurado)
        if val_em:
            st.caption("✓ :green[E-mail com estrutura válida.]")
        else:
            st.caption(f"✕ :red[{mot_em}]")

with col_d2:
    cpf_segurado = st.text_input(
        "CPF do Segurado (Formatação automática):",
        key="input_cpf_segurado",
        on_change=formatar_cpf_titular,
        placeholder="000.000.000-00",
        help="Aceita números colados com ou sem pontuação; aplica máscara e validação matemática."
    )
    if cpf_segurado:
        val_cpf, mot_cpf = validar_cpf(cpf_segurado)
        if val_cpf:
            st.caption("✓ :green[CPF válido (dígitos verificadores corretos).]")
        else:
            st.caption(f"✕ :red[{mot_cpf}]")

    tel_segurado = st.text_input(
        "Telefone (Celular ou Fixo):",
        key="input_tel_segurado",
        on_change=formatar_tel_titular,
        placeholder="(11) 90000-0000"
    )

st.markdown("---")

# -------------------------------------------------------------
# ETAPA B: BENEFICIÁRIOS
# -------------------------------------------------------------
st.markdown("### Etapa B • Indicação de Beneficiários")
st.caption("Informe os beneficiários e verifique a validação preventiva da soma (exatamente 100,00%):")

# Garante estado dos beneficiários
if not st.session_state.beneficiarios_form:
    st.session_state.beneficiarios_form = [
        {"nome": "", "cpf": "", "parentesco": "Cônjuge", "percentual": 100.0}
    ]

soma_percentuais = sum(b.get("percentual", 0.0) for b in st.session_state.beneficiarios_form)
pct_valido = abs(soma_percentuais - 100.0) <= 0.01

col_b_info1, col_b_info2 = st.columns([2, 3])
with col_b_info1:
    cor_pct = "#15803D" if pct_valido else "#DC2626"
    st.markdown(f"**Soma das Participações:** <span style='font-size: 1.25rem; font-weight: 700; color: {cor_pct};'>{soma_percentuais:.2f}%</span> (Obrigatório: 100,00%)", unsafe_allow_html=True)
with col_b_info2:
    st.progress(min(1.0, max(0.0, soma_percentuais / 100.0)))

novos_beneficiarios = []
for idx, b in enumerate(st.session_state.beneficiarios_form):
    if f"b_nome_{idx}" not in st.session_state:
        st.session_state[f"b_nome_{idx}"] = b.get("nome", "")
    if f"b_cpf_{idx}" not in st.session_state:
        st.session_state[f"b_cpf_{idx}"] = b.get("cpf", "")
    if f"b_par_{idx}" not in st.session_state:
        st.session_state[f"b_par_{idx}"] = b.get("parentesco", "Cônjuge")
    if f"b_pct_{idx}" not in st.session_state:
        st.session_state[f"b_pct_{idx}"] = float(b.get("percentual", 0.0))

    with st.container():
        st.markdown(f"**Beneficiário #{idx + 1}**")
        b_col1, b_col2, b_col3, b_col4, b_col5 = st.columns([3, 2.5, 2, 2, 1])
        with b_col1:
            b_nome = st.text_input(f"Nome #{idx+1}", key=f"b_nome_{idx}")
        with b_col2:
            raw_b_cpf = st.text_input(f"CPF #{idx+1}", key=f"b_cpf_{idx}", placeholder="000.000.000-00")
            b_cpf = format_cpf(raw_b_cpf)
            if b_cpf:
                b_val_cpf, b_mot_cpf = validar_cpf(b_cpf)
                if b_val_cpf:
                    st.caption("✓ :green[Válido]")
                else:
                    st.caption(f"✕ :red[{b_mot_cpf}]")
        with b_col3:
            b_parentesco = st.selectbox(f"Parentesco #{idx+1}", ["Cônjuge", "Filho(a)", "Pai/Mãe", "Irmão(ã)", "Outro"], key=f"b_par_{idx}")
        with b_col4:
            b_pct = st.number_input(f"Participação % #{idx+1}", min_value=0.0, max_value=100.0, step=5.0, key=f"b_pct_{idx}")
        with b_col5:
            st.write("")
            st.write("")
            remover = st.button("🗑️", key=f"rem_{idx}", help="Remover beneficiário")

        if not remover:
            novos_beneficiarios.append({"nome": b_nome, "cpf": b_cpf, "parentesco": b_parentesco, "percentual": b_pct})

st.session_state.beneficiarios_form = novos_beneficiarios

if st.button("➕ Adicionar Outro Beneficiário"):
    new_idx = len(st.session_state.beneficiarios_form)
    st.session_state[f"b_nome_{new_idx}"] = ""
    st.session_state[f"b_cpf_{new_idx}"] = ""
    st.session_state[f"b_par_{new_idx}"] = "Filho(a)"
    st.session_state[f"b_pct_{new_idx}"] = 0.0
    st.session_state.beneficiarios_form.append({"nome": "", "cpf": "", "parentesco": "Filho(a)", "percentual": 0.0})
    st.rerun()

st.markdown("---")

# -------------------------------------------------------------
# ETAPA C: DOCUMENTAÇÃO OBRIGATÓRIA
# -------------------------------------------------------------
st.markdown("### Etapa C • Documentação Exigida")
st.caption("Checklist de anexos obrigatórios para conformidade regulatória da apólice:")

col_doc1, col_doc2 = st.columns(2)

with col_doc1:
    st.markdown(
        '<div style="background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 1rem; color: #F8FAFC;">'
        '<strong>1. Documento de Identificação Oficial (RG / CNH)</strong><br/>'
        '<span style="font-size: 0.85rem; color: #94A3B8;">Frente e verso legível com foto e CPF visíveis.</span><br/><br/>'
        '<span style="color: #4ADE80; font-weight: 600;">✓ Arquivo selecionado:</span> <code>documento_identificacao.pdf</code>'
        '</div>',
        unsafe_allow_html=True
    )

with col_doc2:
    if simular_anexo_ausente:
        st.markdown(
            '<div style="background-color: #2D1515; border: 1px solid #7F1D1D; border-left: 4px solid #EF4444; border-radius: 6px; padding: 1rem; color: #F8FAFC;">'
            '<strong>2. Formulário de Alteração Assinado</strong><br/>'
            '<span style="font-size: 0.85rem; color: #FCA5A5;">Com firma do titular do seguro.</span><br/><br/>'
            '<span style="color: #EF4444; font-weight: 600;">✕ Documento ausente (Simulado para teste de pendência)</span>'
            '</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            '<div style="background-color: #1E293B; border: 1px solid #334155; border-radius: 6px; padding: 1rem; color: #F8FAFC;">'
            '<strong>2. Formulário de Alteração Assinado</strong><br/>'
            '<span style="font-size: 0.85rem; color: #94A3B8;">Com firma do titular do seguro.</span><br/><br/>'
            '<span style="color: #4ADE80; font-weight: 600;">✓ Arquivo selecionado:</span> <code>formulario_alteracao_assinado.pdf</code>'
            '</div>',
            unsafe_allow_html=True
        )

st.markdown("<br/>", unsafe_allow_html=True)

# -------------------------------------------------------------
# BOTÃO DE SUBMISSÃO E VALIDAÇÃO PREVENTIVA
# -------------------------------------------------------------
if st.button("🚀 Submeter Solicitação com Validação Preventiva", type="primary", use_container_width=True):
    cpf_normalizado = format_cpf(cpf_segurado)
    tel_normalizado = format_phone(tel_segurado)
    email_limpo = (email_segurado or "").strip()

    cliente_dados = {
        "nome": (nome_segurado or "").strip(),
        "cpf": cpf_normalizado,
        "email": email_limpo,
        "telefone": tel_normalizado
    }

    # Normaliza CPFs dos beneficiários
    bens_normalizados = []
    for b in st.session_state.beneficiarios_form:
        bens_normalizados.append({
            "nome": (b.get("nome") or "").strip(),
            "cpf": format_cpf(b.get("cpf", "")),
            "parentesco": b.get("parentesco", "Outro"),
            "percentual": float(b.get("percentual", 0.0))
        })

    cpf_limpo = cpf_segurado.replace(".", "").replace("-", "") if cpf_segurado else "00000000000"
    documentos_dados = [
        {
            "tipo": "DOCUMENTO_IDENTIFICACAO",
            "nome_arquivo": f"identificacao_{cpf_limpo}.pdf",
            "presente": True,
            "formato": "pdf",
            "valido_sintatico": True,
            "legibilidade_simulada": True
        },
        {
            "tipo": "FORMULARIO_ALTERACAO",
            "nome_arquivo": f"formulario_alteracao_{cpf_limpo}.pdf" if not simular_anexo_ausente else "",
            "presente": not simular_anexo_ausente,
            "formato": "pdf",
            "valido_sintatico": True,
            "legibilidade_simulada": not simular_baixa_legibilidade
        }
    ]

    solic_id, protocolo, validacao = workflow.criar_solicitacao(
        canal=canal,
        cliente_dados=cliente_dados,
        beneficiarios_dados=bens_normalizados,
        documentos_dados=documentos_dados,
        prioridade="MEDIA",
        auto_validar=True
    )

    if not validacao.valido:
        st.error("⛔ **Solicitação Rejeitada pela Validação Preventiva:**")
        for err in validacao.erros:
            st.markdown(f"- ✕ {err}")
        st.warning("💡 **Garantia de Qualidade:** Nenhuma solicitação inconsistente entra na esteira operacional. Corrija os pontos acima para prosseguir.")
    else:
        solic_criada = workflow.repo.get_solicitacao(solic_id)
        status_result = solic_criada.get("status", "RECEBIDA")
        status_lbl = STATUS_ROTULOS.get(status_result, status_result)

        set_persistent_confirmation(
            protocolo=protocolo,
            acao="Entrada de Nova Solicitação via Formulário Estruturado",
            status_anterior="NOVO",
            status_novo=status_result,
            sla_impacto="SLA iniciado (contagem de 5 dias ativada)" if status_result != "AGUARDANDO_CLIENTE" else "SLA pausado imediatamente por pendência documental",
            proxima_etapa="CADASTRO" if status_result == "PRONTA_PARA_CADASTRO" else ("COMPLEMENTO" if status_result == "AGUARDANDO_CLIENTE" else "CONFERENCIA"),
            proxima_acao="Acessar a Fila Operacional para dar prosseguimento à esteira"
        )

        st.success(f"🎉 **Solicitação Recebida com Sucesso! Protocolo: `{protocolo}`**")

        st.markdown(
            '<div class="automation-banner">'
            '<div class="automation-title">Diagnóstico da Automação na Entrada</div>'
            '<div class="automation-item"><span class="automation-icon">✓</span> <strong>CPF do titular:</strong> formato e dígitos verificadores validados matematicamente.</div>'
            '<div class="automation-item"><span class="automation-icon">✓</span> <strong>Participação dos beneficiários:</strong> soma exatamente 100,00% sem duplicidade.</div>'
            f'<div class="automation-item"><span class="automation-icon">✓</span> <strong>Status Inicial Atribuído:</strong> {get_status_badge_html(status_result)}</div>'
            f'<div class="automation-item"><span class="automation-icon">✓</span> <strong>Comunicação Transacional:</strong> Notificação simulada de recebimento com protocolo enviada para <code>{email_segurado}</code>.</div>'
            '</div>',
            unsafe_allow_html=True
        )

        if status_result == "AGUARDANDO_CLIENTE":
            st.warning("⚠️ **Pendência Documental Detectada:** Como o formulário não foi anexado, o sistema abriu uma pendência e **pausou o relógio de SLA** até o retorno do cliente.")
        elif status_result == "EXCECAO":
            st.warning("⚠️ **Encaminhado para Análise Humana:** Documento com baixa legibilidade simulada foi encaminhado para a **Bancada do Analista**.")
        else:
            st.info("ℹ️ **Próxima Etapa:** O caso foi pré-validado e está na esteira pronto para conferência e efetivação de cadastro.")

        st.markdown("> **Nota Metodológica:** A validação bem-sucedida atesta a consistência dos dados de entrada, mas não equivale à conclusão da alteração na apólice, que requer a esteira operacional.")

        col_ir1, col_ir2 = st.columns(2)
        with col_ir1:
            if st.button("📋 Ir para a Fila Operacional", key="btn_pos_fila"):
                st.switch_page("pages/02_Fila_Operacional.py")
        with col_ir2:
            if status_result == "EXCECAO":
                if st.button("🧑‍💼 Analisar Exceção na Bancada", key="btn_pos_analise"):
                    st.switch_page("pages/03_Analise_Humana.py")
