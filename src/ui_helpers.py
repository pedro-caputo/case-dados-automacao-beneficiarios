"""
Utilitários de interface, design system corporativo e componentes de UX acessíveis (WCAG AA).
"""
import streamlit as st
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import json
from src.config import STATUS_ROTULOS, ETAPA_ROTULOS, THEME_COLORS


def apply_corporate_style():
    """Aplica identidade visual executiva baseada em azul-marinho, azul, laranja e alto contraste."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #0F172A;
        }
        
        /* Banner superior corporativo */
        .corporate-header {
            background: linear-gradient(135deg, #0C2340 0%, #1E3A8A 100%);
            padding: 1.4rem 1.8rem;
            border-radius: 8px;
            color: #FFFFFF;
            margin-bottom: 1.2rem;
            box-shadow: 0 2px 8px rgba(12, 35, 64, 0.12);
        }
        .corporate-header h1 {
            color: #FFFFFF !important;
            font-size: 1.7rem;
            font-weight: 700;
            margin: 0;
            letter-spacing: -0.02em;
        }
        .corporate-header p {
            color: #CBD5E1 !important;
            font-size: 0.95rem;
            margin: 0.35rem 0 0 0;
            font-weight: 400;
        }
        
        /* Stepper da Jornada Operacional */
        .journey-stepper {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(90deg, #0F172A 0%, #1E293B 100%);
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 0.85rem 1.4rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
            overflow-x: auto;
        }
        .journey-step {
            display: inline-flex;
            align-items: center;
            font-size: 0.84rem;
            font-weight: 500;
            color: #94A3B8;
            white-space: nowrap;
        }
        .journey-step.active {
            color: #38BDF8;
            font-weight: 700;
        }
        .journey-step.completed {
            color: #4ADE80;
            font-weight: 600;
        }
        .step-circle {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background-color: #334155;
            color: #CBD5E1;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            font-weight: 700;
            margin-right: 0.45rem;
            flex-shrink: 0;
            border: 1px solid #475569;
        }
        .journey-step.active .step-circle {
            background-color: #0284C7;
            color: #FFFFFF;
            border-color: #38BDF8;
            box-shadow: 0 0 8px rgba(56, 189, 248, 0.4);
        }
        .journey-step.completed .step-circle {
            background-color: #16A34A;
            color: #FFFFFF;
            border-color: #4ADE80;
        }
        .step-arrow {
            color: #64748B;
            font-size: 0.85rem;
            margin: 0 0.45rem;
            user-select: none;
        }
        
        /* Cartões de Métricas (KPIs) com alto contraste */
        .kpi-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            padding: 1rem 1.2rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            border-top: 4px solid #2F73D8;
        }
        .kpi-title {
            font-size: 0.8rem;
            text-transform: uppercase;
            font-weight: 600;
            color: #475569;
            letter-spacing: 0.4px;
        }
        .kpi-value {
            font-size: 1.75rem;
            font-weight: 700;
            color: #0C2340;
            margin: 0.25rem 0;
            line-height: 1.2;
        }
        .kpi-caption {
            font-size: 0.8rem;
            color: #64748B;
        }
        
        /* Badges de Status em Linguagem Acessível */
        .badge {
            display: inline-block;
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            text-align: center;
            line-height: 1.2;
        }
        .badge-recebida { background-color: #EFF6FF; color: #1E40AF; border: 1px solid #BFDBFE; }
        .badge-em_validacao { background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; }
        .badge-aguardando_cliente { background-color: #FFF7ED; color: #9A3412; border: 1px solid #FFEDD5; }
        .badge-pronta_para_cadastro { background-color: #ECFDF5; color: #065F46; border: 1px solid #A7F3D0; }
        .badge-em_cadastro { background-color: #F0FDF4; color: #166534; border: 1px solid #BBF7D0; }
        .badge-concluida { background-color: #DCFCE7; color: #14532D; border: 1px solid #86EFAC; }
        .badge-excecao { background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; font-weight: 600; }
        .badge-rejeitada { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; }
        
        /* Badges de SLA de Alto Contraste */
        .badge-sla-ok { background-color: #DCFCE7; color: #14532D; border: 1px solid #86EFAC; font-weight: 600; }
        .badge-sla-warning { background-color: #FEF3C7; color: #92400E; border: 1px solid #FDE68A; font-weight: 600; }
        .badge-sla-danger { background-color: #FEE2E2; color: #991B1B; border: 1px solid #FECACA; font-weight: 600; }
        .badge-sla-paused { background-color: #E0E7FF; color: #3730A3; border: 1px solid #C7D2FE; font-weight: 600; }
        .badge-sla-closed { background-color: #F1F5F9; color: #334155; border: 1px solid #CBD5E1; font-weight: 600; }

        /* Banner de Confirmação Persistente */
        .confirm-banner {
            background: linear-gradient(90deg, #0F2E1E 0%, #163E27 100%);
            border: 1px solid #22C55E;
            border-left: 6px solid #22C55E;
            border-radius: 8px;
            padding: 1.1rem 1.4rem;
            margin-bottom: 1.5rem;
            color: #F0FDF4;
            box-shadow: 0 4px 12px rgba(34, 197, 94, 0.15);
        }
        .confirm-banner-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #4ADE80;
            margin-bottom: 0.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .confirm-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 0.6rem;
            font-size: 0.86rem;
            color: #DCFCE7;
            margin-top: 0.6rem;
        }
        .confirm-grid div strong {
            color: #FFFFFF;
        }

        /* Cartões de Diagnóstico Documental (Correção Crítica de Contraste WCAG AA) */
        .doc-card {
            background-color: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-radius: 6px !important;
            padding: 0.9rem 1rem !important;
            margin-bottom: 0.6rem !important;
            color: #0F172A !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
        }
        .doc-card-valid {
            border-left: 5px solid #15803D !important;
        }
        .doc-card-issue {
            border-left: 5px solid #B91C1C !important;
            background-color: #FFFBFB !important;
        }
        .doc-title {
            font-size: 0.92rem;
            font-weight: 700;
            color: #0C2340 !important;
            margin-bottom: 0.3rem;
        }
        .doc-meta {
            font-size: 0.82rem;
            color: #334155 !important;
            line-height: 1.5;
        }
        .doc-meta strong {
            color: #0F172A !important;
        }

        /* Timeline de Auditoria Limpa */
        .timeline-item {
            padding: 0.75rem 1rem;
            border-left: 3px solid #2F73D8;
            margin-left: 0.5rem;
            margin-bottom: 0.6rem;
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-left: 3px solid #2F73D8;
            border-radius: 0 6px 6px 0;
        }
        .timeline-header {
            font-weight: 600;
            font-size: 0.86rem;
            color: #0C2340;
        }
        .timeline-meta {
            font-size: 0.76rem;
            color: #64748B;
        }
        .timeline-detail {
            font-size: 0.82rem;
            color: #1E293B;
            margin-top: 0.25rem;
        }

        /* Banner de Diagnóstico de Automação */
        .automation-banner {
            background-color: #F8FAFC;
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .automation-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #0C2340;
            margin-bottom: 0.5rem;
        }
        .automation-item {
            font-size: 0.84rem;
            color: #1E293B;
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
        }
        .automation-icon {
            font-size: 0.95rem;
            margin-right: 0.4rem;
        }
    </style>
    """, unsafe_allow_html=True)


def render_corporate_header(titulo: str, subtitulo: str):
    """Renderiza cabeçalho institucional padrão."""
    html = f'<div class="corporate-header"><h1>{titulo}</h1><p>{subtitulo}</p></div>'
    st.markdown(html, unsafe_allow_html=True)


def render_journey_stepper(etapa_ativa: int = 1):
    """
    Exibe a jornada operacional de 6 etapas de forma clara e profissional:
    1. Registro ➔ 2. Validação ➔ 3. Fila ➔ 4. Análise / Cadastro ➔ 5. Conclusão ➔ 6. Gestão
    """
    etapas = [
        (1, "Registro"),
        (2, "Validação"),
        (3, "Fila"),
        (4, "Análise / Cadastro"),
        (5, "Conclusão"),
        (6, "Gestão")
    ]
    step_elements = []
    for num, nome in etapas:
        if num < etapa_ativa:
            classe = "journey-step completed"
            icon = "✓"
        elif num == etapa_ativa:
            classe = "journey-step active"
            icon = str(num)
        else:
            classe = "journey-step"
            icon = str(num)
        step_elements.append(
            f'<div class="{classe}"><div class="step-circle">{icon}</div><span>{nome}</span></div>'
        )
    
    arrow_html = '<span class="step-arrow">➔</span>'
    inner_html = arrow_html.join(step_elements)
    full_html = f'<div class="journey-stepper">{inner_html}</div>'
    st.markdown(full_html, unsafe_allow_html=True)


def get_status_badge_html(status: str) -> str:
    """Retorna badge HTML acessível com nome em português amigável."""
    status_upper = status.upper()
    status_lower = status.lower()
    classes = {
        "recebida": "badge-recebida",
        "em_validacao": "badge-em_validacao",
        "aguardando_cliente": "badge-aguardando_cliente",
        "pronta_para_cadastro": "badge-pronta_para_cadastro",
        "em_cadastro": "badge-em_cadastro",
        "concluida": "badge-concluida",
        "excecao": "badge-excecao",
        "rejeitada": "badge-rejeitada"
    }
    css_class = classes.get(status_lower, "badge-rejeitada")
    nome_amigavel = STATUS_ROTULOS.get(status_upper, status.replace("_", " ").title())
    return f'<span class="badge {css_class}">{nome_amigavel}</span>'


def get_sla_badge_html(metricas_sla: Dict[str, Any], status: Optional[str] = None) -> str:
    """
    Retorna badge de SLA com cores de alto contraste, indicação de pausa e encerramento para casos concluídos.
    Para casos concluídos: exibe 'SLA encerrado' e indica se foi dentro ou fora do prazo interno, sem saldo restante ativo.
    """
    status_upper = (status or "").upper()
    concluido = status_upper in ["CONCLUIDA", "REJEITADA"] or metricas_sla.get("concluido", False)
    
    if concluido:
        lead_liquido = metricas_sla.get("lead_time_liquido_horas")
        if lead_liquido is None:
            lead_liquido = max(0.0, metricas_sla.get("lead_time_bruto_horas", 0.0) - metricas_sla.get("pausa_acumulada_horas", 0.0))
        
        if metricas_sla.get("expirado"):
            return f'<span class="badge badge-sla-danger">SLA encerrado (Fora do prazo: {lead_liquido:.1f}h)</span>'
        else:
            return f'<span class="badge badge-sla-closed">✓ SLA encerrado (No prazo: {lead_liquido:.1f}h)</span>'

    estado = metricas_sla.get("estado")
    if estado == "PAUSADO":
        horas = metricas_sla.get("horas_restantes", 0)
        return f'<span class="badge badge-sla-paused">⏸️ SLA Pausado ({horas:.1f}h rest.)</span>'
    if metricas_sla.get("expirado"):
        return f'<span class="badge badge-sla-danger">Expirado ({abs(metricas_sla.get("horas_restantes", 0)):.1f}h atr.)</span>'
    horas = metricas_sla.get("horas_restantes", 0)
    if horas < 48:
        return f'<span class="badge badge-sla-warning">Atenção: {horas:.1f}h rest.</span>'
    return f'<span class="badge badge-sla-ok">{horas:.1f}h restantes</span>'


def set_persistent_confirmation(
    protocolo: str,
    acao: str,
    status_anterior: str,
    status_novo: str,
    sla_impacto: str,
    proxima_etapa: str,
    proxima_acao: str
):
    """Grava confirmação estruturada em st.session_state para sobreviver a reruns e redirecionamentos."""
    st.session_state.confirmacao_persistente = {
        "protocolo": protocolo,
        "acao": acao,
        "status_anterior": STATUS_ROTULOS.get(status_anterior, status_anterior),
        "status_novo": STATUS_ROTULOS.get(status_novo, status_novo),
        "sla_impacto": sla_impacto,
        "proxima_etapa": ETAPA_ROTULOS.get(proxima_etapa, proxima_etapa),
        "proxima_acao": proxima_acao,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    }


def render_persistent_confirmation():
    """Renderiza a notificação persistente de confirmação se houver uma ativa."""
    conf = st.session_state.get("confirmacao_persistente")
    if not conf:
        return

    col_banner, col_btn = st.columns([5, 1])
    with col_banner:
        html = (
            f'<div class="confirm-banner">'
            f'<div class="confirm-banner-title">✓ Operação Persistida com Sucesso — Protocolo <code>{conf["protocolo"]}</code></div>'
            f'<div class="confirm-grid">'
            f'<div><strong>Ação Executada:</strong> {conf["acao"]}</div>'
            f'<div><strong>Transição de Status:</strong> <code>{conf["status_anterior"]}</code> ➔ <code>{conf["status_novo"]}</code></div>'
            f'<div><strong>Impacto no SLA:</strong> {conf["sla_impacto"]}</div>'
            f'<div><strong>Próxima Etapa:</strong> {conf["proxima_etapa"]}</div>'
            f'<div><strong>Próxima Ação:</strong> {conf["proxima_acao"]}</div>'
            f'<div><strong>Horário do Registro:</strong> {conf["timestamp"]}</div>'
            f'</div></div>'
        )
        st.markdown(html, unsafe_allow_html=True)
    with col_btn:
        st.write("")
        if st.button("✕ Dispensar", key="btn_disp_conf", use_container_width=True):
            st.session_state.confirmacao_persistente = None
            st.rerun()


def render_document_card(doc: Dict[str, Any]):
    """
    Renderiza cartão de diagnóstico de documento com CONTRASTE RIGOROSO (WCAG AA).
    Garante texto 100% legível com contraste superior a 4.5:1.
    """
    tipo = doc.get("tipo", "DOCUMENTO").replace("_", " ").title()
    nome = doc.get("nome_arquivo") or "Arquivo não enviado"
    formato = (doc.get("formato") or "").lower()
    presente = doc.get("presente", True)
    valido = doc.get("valido_sintatico", True)
    legivel = doc.get("legibilidade_simulada", True)

    tudo_valido = presente and valido and legivel
    card_class = "doc-card doc-card-valid" if tudo_valido else "doc-card doc-card-issue"

    diag_itens = []
    if not presente:
        diag_itens.append("<span style='color: #B91C1C; font-weight: 600;'>✕ Ausente: anexo obrigatório não localizado</span>")
    elif not valido:
        diag_itens.append(f"<span style='color: #B91C1C; font-weight: 600;'>✕ Formato inválido ou corrompido (<code>{formato}</code>)</span>")
    elif not legivel:
        diag_itens.append("<span style='color: #B45309; font-weight: 600;'>⚠ Baixa legibilidade simulada: ilegível para leitura automática (exige análise humana)</span>")
    else:
        diag_itens.append("<span style='color: #15803D; font-weight: 600;'>✓ Conforme: arquivo íntegro e legível</span>")

    diag_str = " • ".join(diag_itens)
    html = (
        f'<div class="{card_class}">'
        f'<div class="doc-title">{tipo}</div>'
        f'<div class="doc-meta">'
        f'<strong>Arquivo:</strong> <code>{nome}</code><br/>'
        f'<strong>Diagnóstico da Automação:</strong> {diag_str}'
        f'</div></div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def render_timeline(eventos: List[Dict[str, Any]]):
    """Renderiza linha do tempo de auditoria sem JSONs brutos."""
    if not eventos:
        st.info("Nenhum evento registrado ainda para esta solicitação.")
        return

    for ev in eventos:
        tipo = ev.get("tipo_evento", "EVENTO").replace("_", " ").title()
        timestamp = ev.get("timestamp", "")
        ator = ev.get("origem_ator", "SISTEMA")
        est_ant = ev.get("estado_anterior")
        est_novo = ev.get("estado_novo")
        detalhes_str = ev.get("detalhes_json", "{}")

        try:
            detalhes = json.loads(detalhes_str) if isinstance(detalhes_str, str) else detalhes_str
        except Exception:
            detalhes = {}

        data_formatada = timestamp[:19].replace("T", " ") if timestamp else "N/A"
        meta = f"{data_formatada} • Ator: <strong>{ator}</strong>"
        if est_ant and est_novo:
            ant_lbl = STATUS_ROTULOS.get(est_ant, est_ant)
            novo_lbl = STATUS_ROTULOS.get(est_novo, est_novo)
            meta += f" • Transição: <code>{ant_lbl}</code> ➔ <code>{novo_lbl}</code>"

        detalhe_desc = ""
        if "justificativa" in detalhes:
            detalhe_desc += f"<strong>Justificativa:</strong> {detalhes['justificativa']}<br/>"
        if "protocolo" in detalhes:
            detalhe_desc += f"Protocolo: <code>{detalhes['protocolo']}</code> "
        if "descricao" in detalhes:
            detalhe_desc += f"{detalhes['descricao']} "
        if "observacao" in detalhes:
            detalhe_desc += f"{detalhes['observacao']} "

        desc = detalhe_desc or "Registro de auditoria gravado no sistema."
        html = (
            f'<div class="timeline-item">'
            f'<div class="timeline-header">{tipo}</div>'
            f'<div class="timeline-meta">{meta}</div>'
            f'<div class="timeline-detail">{desc}</div>'
            f'</div>'
        )
        st.markdown(html, unsafe_allow_html=True)


def render_universe_selector(repo, key_prefix: str = "global") -> Tuple[str, Optional[str], str]:
    """
    Renderiza seletor de universo de dados (Operação Interativa vs Simulação Experimental).
    Garante sincronização entre páginas e isolamento rigoroso dos dados.
    Retorna (universo: str, run_id: Optional[str], nome_exibicao: str).
    """
    if "universo_selecionado" not in st.session_state:
        st.session_state.universo_selecionado = "INTERATIVO"
    if "run_id_selecionado" not in st.session_state:
        st.session_state.run_id_selecionado = None

    runs = repo.list_simulation_runs() if hasattr(repo, "list_simulation_runs") else []

    opcoes = ["Operação Interativa (Casos Criados na Demonstração)"]
    mapa_runs = {}
    for r in runs:
        dt_str = (r.get("iniciado_em") or "")[:19].replace("T", " ")
        rotulo = f"Simulação Experimental: {r['id']} ({r.get('total_solicitacoes', 0)} casos — {dt_str})"
        opcoes.append(rotulo)
        mapa_runs[rotulo] = r["id"]

    # Determina índice inicial baseado na sessão
    idx_padrao = 0
    if st.session_state.universo_selecionado == "EXPERIMENTAL":
        if st.session_state.run_id_selecionado:
            for i, opt in enumerate(opcoes):
                if f": {st.session_state.run_id_selecionado} " in opt:
                    idx_padrao = i
                    break
        elif len(opcoes) > 1:
            idx_padrao = 1

    col_u1, col_u2 = st.columns([3, 2])
    with col_u1:
        escolha = st.selectbox(
            "Selecione o Universo de Dados:",
            opcoes,
            index=idx_padrao,
            key=f"{key_prefix}_universe_selector"
        )

    if "Simulação Experimental" in escolha:
        universo = "EXPERIMENTAL"
        run_id = mapa_runs.get(escolha)
        nome = f"Lote Experimental ({run_id})"
    else:
        universo = "INTERATIVO"
        run_id = None
        nome = "Operação Interativa Manual"

    # Se houve troca de universo, limpa seleções ativas de casos
    if st.session_state.universo_selecionado != universo or st.session_state.run_id_selecionado != run_id:
        st.session_state.universo_selecionado = universo
        st.session_state.run_id_selecionado = run_id
        if "fila_caso_selecionado_id" in st.session_state:
            st.session_state.fila_caso_selecionado_id = None
        if "caso_analise_id" in st.session_state:
            st.session_state.caso_analise_id = None

    with col_u2:
        badge_cor = "#2563EB" if universo == "INTERATIVO" else "#D97706"
        badge_txt = "Operação Interativa (Manual)" if universo == "INTERATIVO" else f"Lote Simulado ({run_id})"
        st.markdown(
            f'<div style="background-color: #1E293B; border-left: 4px solid {badge_cor}; padding: 0.65rem 1rem; border-radius: 6px; font-size: 0.85rem; color: #F8FAFC; margin-top: 1.45rem;">'
            f'<strong>Contexto Ativo:</strong> <code>{badge_txt}</code> (dados isolados)'
            f'</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br/>", unsafe_allow_html=True)
    return universo, run_id, nome
