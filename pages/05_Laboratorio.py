"""
Página 5 — Laboratório de Experimentos & Simulação Comparativa AS-IS vs TO-BE.
Organizado em 4 etapas lógicas com auditoria metodológica rigorosa da redução de esforço.
"""
import streamlit as st
import json
import pandas as pd
from pathlib import Path
from src.config import (
    DB_PATH, DEFAULT_SEED, DATA_DIR, OUTPUTS_DIR,
    AS_IS_TOTAL_HORAS, AS_IS_TOTAL_MINUTOS, AS_IS_VOLUME_MENSAL
)
from src.database import init_db
from src.repositories import SolicitacaoRepository
from src.simulation import SimulationEngine
from src.metrics import gerar_relatorio_markdown, gerar_tabela_slide10
from src.ui_helpers import (
    apply_corporate_style, render_corporate_header,
    render_journey_stepper
)

st.set_page_config(page_title="Laboratório de Simulação | Seguros PF", page_icon="🧪", layout="wide")
apply_corporate_style()

init_db(DB_PATH)
repo = SolicitacaoRepository(DB_PATH)
engine = SimulationEngine(repo)

render_corporate_header(
    titulo="Laboratório de Experimentos & Comparação TO-BE",
    subtitulo="Simulação de 1.000 solicitações com medição computacional e auditoria metodológica do esforço humano"
)

render_journey_stepper(etapa_ativa=5)

if "ultimas_metricas_simulacao" not in st.session_state:
    st.session_state.ultimas_metricas_simulacao = None

# -------------------------------------------------------------
# ETAPA 1 — CONFIGURAR O EXPERIMENTO
# -------------------------------------------------------------
st.markdown("### Etapa 1 • Configuração do Cenário Experimental")
st.caption("O laboratório utiliza a distribuição factual documentada no case com semente reproduzível:")

col_c1, col_c2 = st.columns([2, 1])

with col_c1:
    st.markdown(
        '<div style="background-color: #1E293B; border: 1px solid #334155; border-left: 4px solid #38BDF8; border-radius: 6px; padding: 1rem; color: #F8FAFC;">'
        '<strong>Parâmetros Padrão do Case Seguros PF:</strong><br/>'
        '• <strong>Volume Testado:</strong> 1.000 intenções sintéticas mensais.<br/>'
        '• <strong>Canais Factuais:</strong> E-mail (550), Agência (300), Aplicativo (150).<br/>'
        '• <strong>Inadequação Documental Inicial:</strong> exatamente 250 casos (25%).<br/>'
        '• <strong>Clientes em Atraso (> 5 dias):</strong> exatamente 100 casos (40% de 250).<br/>'
        '• <strong>Semente Determinística:</strong> <code>20261108</code> (garante reprodutibilidade idêntica).'
        '</div>',
        unsafe_allow_html=True
    )

with col_c2:
    seed_input = st.number_input("Semente (Seed):", value=DEFAULT_SEED, step=1, help="Garante que as 1.000 intenções sejam geradas de forma determinística")

with st.expander("⚙️ Parâmetros Avançados da Projeção Operacional Humana", expanded=False):
    st.caption("Hipóteses de tempo humano adotadas para as atividades que NÃO são 100% automatizadas:")
    p_col1, p_col2, p_col3 = st.columns(3)
    with p_col1:
        tempo_excecao = st.slider("Tempo por Exceção (min):", 3.0, 10.0, 6.0, 0.5, help="Análise de documentos ilegíveis ou divergentes")
    with p_col2:
        tempo_comp = st.slider("Tempo p/ Reanálise de Complemento (min):", 2.0, 8.0, 4.0, 0.5, help="Conferência do anexo reenviado pelo segurado")
    with p_col3:
        tempo_cad = st.slider("Supervisão de Cadastro em Lote (min/caso):", 0.2, 2.0, 0.5, 0.1, help="Supervisão humana de lotes cadastrais pré-validados")

st.markdown("---")

# -------------------------------------------------------------
# GERENCIAMENTO DE EXECUÇÕES EXPERIMENTAIS
# -------------------------------------------------------------
with st.expander("📂 Gerenciamento de Execuções Experimentais Salvas no Banco", expanded=False):
    runs_existentes = repo.list_simulation_runs()
    if not runs_existentes:
        st.info("Nenhuma execução experimental registrada no banco.")
    else:
        df_runs = pd.DataFrame([{
            "ID do Lote": r["id"],
            "Semente": r["seed"],
            "Intenções": r["total_intents"],
            "Casos no Banco": r.get("total_solicitacoes", 0),
            "Iniciado Em": r.get("iniciado_em", "")[:19].replace("T", " "),
            "Concluído Em": (r.get("concluido_em") or "")[:19].replace("T", " ")
        } for r in runs_existentes])
        st.dataframe(df_runs, use_container_width=True, hide_index=True)

        col_sel_run, col_del_run = st.columns([2, 1])
        with col_sel_run:
            opcoes_run_sel = [f"{r['id']} (Semente: {r['seed']} — {r.get('total_solicitacoes', 0)} casos)" for r in runs_existentes]
            run_escolhido_str = st.selectbox("Carregar execução para análise detalhada:", opcoes_run_sel, key="sb_carregar_run")
            id_run_carregar = run_escolhido_str.split(" ")[0].strip()

            if st.button("👁️ Carregar Resultados Deste Lote", key="btn_load_run"):
                run_obj = next((r for r in runs_existentes if r["id"] == id_run_carregar), None)
                if run_obj and run_obj.get("metricas_json"):
                    st.session_state.ultimas_metricas_simulacao = json.loads(run_obj["metricas_json"])
                    st.session_state.run_id_selecionado = id_run_carregar
                    st.session_state.universo_selecionado = "EXPERIMENTAL"
                    st.success(f"Lote '{id_run_carregar}' carregado com sucesso!")
                    st.rerun()

        with col_del_run:
            st.markdown("##### Excluir Lote")
            chk_del = st.checkbox(f"Confirmar exclusão de `{id_run_carregar}`", key=f"chk_del_run_{id_run_carregar}")
            if st.button("🗑️ Excluir Execução Selecionada", disabled=not chk_del, key="btn_del_sim_run", type="secondary"):
                ok = repo.delete_simulation_run(id_run_carregar)
                if ok:
                    st.session_state.ultimas_metricas_simulacao = None
                    st.success(f"Lote experimental '{id_run_carregar}' excluído com sucesso do banco de dados!")
                    st.rerun()
                else:
                    st.error("Falha ao excluir o lote experimental.")

st.markdown("---")

# -------------------------------------------------------------
# ETAPA 2 — EXECUTAR A SIMULAÇÃO
# -------------------------------------------------------------
st.markdown("### Etapa 2 • Execução do Lote TO-BE")
st.caption("Submete as 1.000 intenções às regras automatizadas do novo processo:")

col_btn_exec, col_btn_down = st.columns([2, 1])

with col_btn_exec:
    run_id_custom = st.text_input("Identificador desta Execução (Run ID):", value=f"EXP-{seed_input}", help="Identificador único para isolamento no banco de dados.")

    runs_ids = [r["id"] for r in repo.list_simulation_runs()]
    if run_id_custom in runs_ids:
        st.caption(f"ℹ️ *Nota de Idempotência: Já existe um lote com ID `{run_id_custom}`. Ao reexecutar, os registros anteriores deste ID serão substituídos deterministicamente sem duplicações.*")

    if st.button("🚀 Executar Simulação TO-BE (1.000 Casos)", type="primary", use_container_width=True):
        with st.spinner("Processando 1.000 intenções sintéticas e auditando tempos..."):
            run_id = run_id_custom.strip()
            metricas = engine.executar_lote(
                seed=seed_input,
                run_id=run_id,
                tempo_medio_excecao_minutos=tempo_excecao,
                tempo_medio_complemento_minutos=tempo_comp,
                tempo_supervisao_cadastro_minutos=tempo_cad
            )
            st.session_state.ultimas_metricas_simulacao = metricas
            st.session_state.run_id_selecionado = run_id
            st.session_state.universo_selecionado = "EXPERIMENTAL"

            # Gera relatório na pasta de outputs
            rel_path = OUTPUTS_DIR / "relatorio_experimento.md"
            gerar_relatorio_markdown(metricas, rel_path)
            tab_path = OUTPUTS_DIR / "tabela_slide10.md"
            tab_path.write_text(gerar_tabela_slide10(metricas), encoding="utf-8")
            st.success(f"✓ Simulação concluída com sucesso em {metricas['duracao_computacional_segundos']} segundos!")
            st.rerun()

with col_btn_down:
    csv_path = DATA_DIR / "raw_intents_1000.csv"
    if csv_path.exists():
        with open(csv_path, "rb") as f:
            st.download_button(
                "📥 Baixar Base Sintética (CSV)",
                data=f,
                file_name="raw_intents_1000.csv",
                mime="text/csv",
                use_container_width=True
            )

# -------------------------------------------------------------
# ETAPA 3 — VISUALIZAR RESULTADOS
# -------------------------------------------------------------
metricas = st.session_state.ultimas_metricas_simulacao

if not metricas:
    # Se ainda não rodou nesta sessão, carrega a última execução do banco
    conn = repo._get_conn()
    cursor = conn.cursor()
    cursor.execute("SELECT metricas_json FROM simulation_runs WHERE metricas_json IS NOT NULL ORDER BY iniciado_em DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        metricas = json.loads(row["metricas_json"])
        st.session_state.ultimas_metricas_simulacao = metricas

if metricas:
    st.markdown("---")
    st.markdown("### Etapa 3 • Visualização dos Resultados Auditados")

    comp = metricas.get("comparativo", {})
    as_is = comp.get("as_is", {})
    to_be = comp.get("to_be_estimado", {})
    cont = metricas.get("contadores", {})
    coorte = metricas.get("situacao_coorte", {})

    # GRUPO A: DESEMPENHO COMPUTACIONAL MEDIDO
    st.markdown("#### Grupo A • Desempenho Computacional Medido (Hardware Local)")
    st.caption("Velocidade pura de processamento de regras lógicas pelo software:")

    g_a1, g_a2, g_a3 = st.columns(3)
    with g_a1:
        st.metric("Tempo de CPU/Banco", f"{metricas['duracao_computacional_segundos']} s")
    with g_a2:
        st.metric("Vazão de Validação", f"{metricas['taxa_processamento_casos_por_segundo']} casos / seg")
    with g_a3:
        st.metric("Volume de Intenções Avaliadas", f"{metricas['total_intencoes']} registros")

    st.warning("⚠️ **Aviso Metodológico:** A duração de frações de segundo mede a vazão algorítmica do software. Ela NÃO significa conclusão instantânea de apólices bancárias nem eliminação total de tarefas operacionais.")

    st.markdown("<br/>", unsafe_allow_html=True)

    # GRUPO B: SITUAÇÃO DA COORTE DE 1.000 CASOS
    st.markdown("#### Grupo B • Situação da Coorte de 1.000 Casos na Simulação")
    st.caption("Destino operacional de cada intenção de solicitação submetida ao TO-BE:")

    g_b1, g_b2, g_b3, g_b4 = st.columns(4)
    with g_b1:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #15803D;">
            <div class="kpi-title">Aptas p/ Cadastro Direto (STP)</div>
            <div class="kpi-value">{coorte.get('prontas_para_cadastro', 0)}</div>
            <div class="kpi-caption">75,0% sem qualquer inconsistência</div>
        </div>
        """, unsafe_allow_html=True)

    with g_b2:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #B45309;">
            <div class="kpi-title">Aguardando Complemento</div>
            <div class="kpi-value">{coorte.get('aguardando_complemento_cliente', 0)}</div>
            <div class="kpi-caption">19,0% pendência com SLA pausado</div>
        </div>
        """, unsafe_allow_html=True)

    with g_b3:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #D97706;">
            <div class="kpi-title">Exceções para Analista</div>
            <div class="kpi-value">{coorte.get('em_excecao_humana', 0)}</div>
            <div class="kpi-caption">6,0% baixa legibilidade / dúvida</div>
        </div>
        """, unsafe_allow_html=True)

    with g_b4:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color: #2F73D8;">
            <div class="kpi-title">Erros Sintéticos Prevenidos</div>
            <div class="kpi-value">{cont.get('erros_preventivos_evitados', 0)}</div>
            <div class="kpi-caption">7,7% da amostra (hipótese de 8% do case)</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # GRUPO C: ESTIMATIVAS OPERACIONAIS AUDITADAS (DECOMPOSIÇÃO POR ATIVIDADE)
    st.markdown("#### Grupo C • Estimativa de Esforço Operacional Humano Residual (Por Atividade)")
    st.caption("Decomposição do trabalho humano por atividade no AS-IS vs TO-BE com tarefas residuais expressamente modeladas:")

    decomposicao = to_be.get("decomposicao_atividades", [])
    if decomposicao:
        df_dec = pd.DataFrame(decomposicao)
        st.dataframe(
            df_dec[["atividade", "as_is_horas", "to_be_horas", "variacao_horas", "mecanismo"]].rename(columns={
                "atividade": "Atividade Operacional",
                "as_is_horas": "AS-IS Histórico (Horas)",
                "to_be_horas": "TO-BE Estimado (Horas)",
                "variacao_horas": "Variação Projetada (Horas)",
                "mecanismo": "Mecanismo da Automação / Atividade Residual Modelada"
            }),
            use_container_width=True,
            hide_index=True
        )

    st.markdown(f"""
    **Resumo do Esforço Humano Ativo:**
    - **Esforço Histórico Manual (AS-IS):** `{as_is.get('horas_totais_esforco_ativo')} horas / mês` (Fato documentado no case — 3 analistas).
    - **Esforço Humano Residual Estimado no TO-BE:** `{to_be.get('horas_esforco_humano_estimadas')} horas / mês` (Hipótese de modelo com tarefas residuais).
    - **Redução Projetada no Cenário Simulado:** **-{to_be.get('reducao_esforco_humano_horas')} horas (-{to_be.get('reducao_esforco_humano_pct')}%)**
    """)

    with st.expander("🔍 Auditoria Metodológica Detalhada das Fórmulas do TO-BE", expanded=False):
        st.markdown("""
        **Memória de Cálculo do Esforço Humano Residual (Total = 40,25 horas / mês = 2.415 minutos):**
        1. **Triagem de Entrada (0,0 h = 0 min):**
           - *Volume:* 1.000 intenções.
           - *Tempo unitário:* 0,0 min.
           - *Origem:* Hipótese de canal digital estruturado com validação preventiva e protocolo imediato.
        2. **Conferência Inicial de Documentos (6,0 h = 360 min):**
           - *Volume:* 60 casos com legibilidade inconclusiva simulada.
           - *Tempo unitário:* 6,0 min/caso.
           - *Origem:* Hipótese configurável de discernimento humano para documentos ilegíveis.
        3. **Gestão de Complementos (17,67 h = 1.060 min):**
           - *Volume A:* 190 complementos recebidos × 4,0 min (reanálise de anexo) = 760 min.
           - *Volume B:* 100 clientes com atraso > 5 dias × 3,0 min (acompanhamento ativo) = 300 min.
           - *Origem:* Hipóteses de tempo aplicadas aos 250 casos de inadequação documental informados no case.
        4. **Cadastro e Efetivação no Legado (14,58 h = 875 min):**
           - *Volume A:* 750 casos regulares (STP) × 0,5 min (supervisão de lote de 30s) = 375 min.
           - *Volume B:* 250 casos com histórico de pendência/exceção × 2,0 min (conferência individual) = 500 min.
           - *Origem:* Hipótese conservadora (como não há integração descrita via API no legado, a efetivação cadastral não é considerada instantânea).
        5. **Respostas e Comunicações (2,0 h = 120 min):**
           - *Volume:* 60 casos com recusa ou dúvidas × 2,0 min = 120 min.
           - *Origem:* Hipótese de atendimento consultivo humano para exceções.

        **Atividades Humanas Não Contempladas no Modelo (Limitações Metodológicas):**
        - Reuniões de alinhamento da equipe e gestão de pessoas.
        - Tratamento de contestações em ouvidoria ou demandas jurídicas.
        - Manutenção de parametrizações e regras de negócio.
        """)

    st.markdown("---")

    # SÍNTESE PRONTA PARA O SLIDE 10
    st.markdown("### 🏆 Síntese de Resultados — Tabela Metodologicamente Defensável para o Slide 10")
    st.caption("Esta tabela compara os fatos do case com as medições e projeções tecnicamente defensáveis:")

    tabela_md = gerar_tabela_slide10(metricas)
    st.markdown(tabela_md)

    st.markdown("---")

    # -------------------------------------------------------------
    # ETAPA 4 — EXPORTAR
    # -------------------------------------------------------------
    st.markdown("### Etapa 4 • Exportação dos Relatórios da Simulação")
    exp_c1, exp_c2 = st.columns(2)

    with exp_c1:
        rel_path = OUTPUTS_DIR / "relatorio_experimento.md"
        if rel_path.exists():
            st.download_button(
                "📄 Baixar Relatório Técnico Completo (.md)",
                data=rel_path.read_text(encoding="utf-8"),
                file_name="relatorio_tecnico_experimento_beneficiarios.md",
                mime="text/markdown",
                use_container_width=True
            )

    with exp_c2:
        st.download_button(
            "📋 Baixar Tabela do Slide 10 em Markdown (.md)",
            data=tabela_md,
            file_name="tabela_slide_10_beneficiarios.md",
            mime="text/markdown",
            use_container_width=True
        )

else:
    st.info("ℹ️ Clique no botão 'Executar Simulação TO-BE' na Etapa 2 para gerar os resultados e a tabela do Slide 10.")
