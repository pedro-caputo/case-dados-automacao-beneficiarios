"""
Geração de métricas consolidadas, relatórios analíticos e tabela metodologicamente defensável para o Slide 10.
"""
from pathlib import Path
from typing import Dict, Any
import json
from src.config import OUTPUTS_DIR


def gerar_relatorio_markdown(metricas: Dict[str, Any], output_path: Path) -> str:
    """
    Gera relatório técnico com separação rigorosa entre fatos do case, premissas de modelagem,
    medições computacionais de software e estimativas de esforço humano residual por atividade.
    """
    comp = metricas.get("comparativo", {})
    as_is = comp.get("as_is", {})
    to_be = comp.get("to_be_estimado", {})
    cont = metricas.get("contadores", {})
    coorte = metricas.get("situacao_coorte", {})
    decomposicao = to_be.get("decomposicao_atividades", [])

    linhas_atividades = ""
    for at in decomposicao:
        linhas_atividades += f"| **{at['atividade']}** | {at['as_is_horas']} h | {at['to_be_horas']} h | {at['variacao_horas']:+} h | {at['mecanismo']} |\n"

    conteudo = f"""# Relatório Técnico Experimental — Processo de Beneficiários Seguros PF (Modelo TO-BE)

**Identificador da Execução:** `{metricas.get('run_id')}`  
**Data e Hora:** {metricas.get('iniciado_em', 'N/A')}  
**Semente Determinística:** `{metricas.get('seed')}`  
**Amostra Testada:** {metricas.get('total_intencoes')} intenções sintéticas  

---

## 1. Fatos Documentados do Case (Cenário Histórico AS-IS)
*Dados e premissas imutáveis informados no enunciado do case:*

- **Volume Mensal:** 1.000 solicitações/mês (crescimento previsto de 10% a.a. a ser validado).
- **Equipe Operacional:** 3 analistas dedicados.
- **Canais Históricos:** E-mail (55% = 550), Agência (30% = 300), App (15% = 150) com convergência manual para caixa de e-mail.
- **Inadequação Documental Inicial:** 25% (250 casos incompletos ou ilegíveis).
- **Tempo de Espera de Complemento:** 40% dos clientes com pendência (100 clientes) levam mais de 5 dias para responder.
- **Esforço Humano Ativo Mensal (Fato do Case):** **313,33 horas** (18.800 minutos):
  - Triagem manual: 1.000 × 4 min = 4.000 min (66,67 h)
  - Conferência manual: 1.000 × 6 min = 6.000 min (100,00 h)
  - Complemento manual: 250 × 10 min = 2.500 min (41,67 h)
  - Cadastro manual no sistema legado: 900 × 5 min = 4.500 min (75,00 h)
  - Resposta manual aos segurados: 900 × 2 min = 1.800 min (30,00 h)
- **Indicadores Históricos:** 62% no prazo de 5 dias / 38% fora do prazo; 60 reclamações/mês; 8% de taxa histórica de erros manuais de digitação.

---

## 2. Desempenho Computacional Medido (Software em Hardware Local)
*Mede unicamente a velocidade de execução das regras de validação em lote na CPU local:*

- **Tempo Computacional do Lote (1.000 casos):** `{metricas.get('duracao_computacional_segundos')} segundos`.
- **Vazão Sistêmica de Processamento:** `{metricas.get('taxa_processamento_casos_por_segundo')} casos/segundo`.

> **Distinção Metodológica Fundamental:** A duração de frações de segundo reflete unicamente o tempo computacional dos algoritmos de validação preventiva e inserção no SQLite local. Esse tempo **NÃO** deve ser confundido com a conclusão de processos bancários nem com a extinção total do trabalho humano. A efetivação na apólice depende da esteira e de intervenções humanas nos casos de exceção e pendência.

---

## 3. Situação da Coorte de 1.000 Casos na Simulação
*Classificação operacional de cada intenção de solicitação após aplicação das regras TO-BE:*

- **Aptas para Cadastro Direto (STP):** `{coorte.get('prontas_para_cadastro', 0)} casos ({coorte.get('prontas_para_cadastro', 0)/10:.1f}%)` — dados íntegros e documentos sinteticamente conformes.
- **Aguardando Complemento do Cliente:** `{coorte.get('aguardando_complemento_cliente', 0)} casos ({coorte.get('aguardando_complemento_cliente', 0)/10:.1f}%)` — pendência aberta e relógio de SLA pausado.
- **Em Exceção para Revisão Humana:** `{coorte.get('em_excecao_humana', 0)} casos ({coorte.get('em_excecao_humana', 0)/10:.1f}%)` — documentos com legibilidade simulada inconclusiva ou divergência.
- **Erros Sintéticos de Digitação Potencialmente Prevenidos:** `{cont.get('erros_preventivos_evitados', 0)} casos` — bloqueados preventivamente na validação de entrada (baseado na probabilidade histórica de 8% informada no case).

---

## 4. Projeção de Esforço Humano Residual Decomposto por Atividade
*Comparação entre o esforço histórico (AS-IS) e o esforço humano residual estimado no TO-BE:*

| Atividade Operacional | Esforço AS-IS | Esforço TO-BE Estimado | Variação (Horas) | Mecanismo de Transformação e Hipótese Adotada |
|---|---:|---:|---:|---|
{linhas_atividades}
| **TOTAL GERAL DE ESFORÇO** | **{as_is.get('horas_totais_esforco_ativo')} h** | **{to_be.get('horas_esforco_humano_estimadas')} h** | **-{to_be.get('reducao_esforco_humano_horas')} h (-{to_be.get('reducao_esforco_humano_pct')}%)** | **Redução projetada no cenário simulado focada em triagem mecânica e validação preventiva** |

---

## 5. Justificativa das Hipóteses e Fórmulas da Projeção

1. **Triagem (0 h no TO-BE):** A entrada estruturada por canal digital (App/Web/Agência) substitui a triagem manual de caixa de e-mails, gerando protocolo único e metadados preventivos automaticamente.
2. **Conferência Inicial ({to_be.get('decomposicao_atividades', [{}])[1].get('to_be_horas', 6.0)} h no TO-BE):** Casos 100% regulares têm consistência garantida por código. O analista atua unicamente sobre as 60 exceções humanas (hipótese de 6,0 min/caso = 360 min).
3. **Gestão de Complementos ({to_be.get('decomposicao_atividades', [{}])[2].get('to_be_horas', 17.7)} h no TO-BE):** O disparo de pendência é automático com pausa de SLA. O esforço humano residual modela a reanálise dos 190 complementos recebidos (hipótese de 4,0 min/caso = 760 min) e o acompanhamento ativo dos 100 clientes com atraso superior a 5 dias (hipótese de 3,0 min/caso = 300 min). Total: 1.060 min.
4. **Cadastro no Legado ({to_be.get('decomposicao_atividades', [{}])[3].get('to_be_horas', 14.6)} h no TO-BE):** Como o case não documenta integração direta por API com o core legado, a efetivação cadastral não é assumida como instantânea. Modela-se supervisão humana em lote para 750 casos regulares (0,5 min/caso = 375 min) e conferência cadastral individual para os 250 casos que passaram por complemento/exceção (2,0 min/caso = 500 min). Total: 875 min.
5. **Respostas e Comunicações ({to_be.get('decomposicao_atividades', [{}])[4].get('to_be_horas', 2.0)} h no TO-BE):** Mensagens transacionais são disparadas de forma automática pelo sistema. O analista trata apenas exceções e recusas (60 casos × 2,0 min = 120 min).

---

## 6. Limitações Metodológicas do Protótipo
1. **Ambiente Simulado:** Os dados e eventos são 100% sintéticos e executados localmente; não houve integração com servidores externos ou bancos legados de produção.
2. **Capacidade Operacional Futura Não Validada:** O atendimento ao crescimento anual de 10% demandará testes de estresse com o core legado e análise de volumetria em ambiente real.
3. **Validação de Documentos:** A verificação de arquivos no protótipo avalia formato, presença e legibilidade simulada; não substitui perícia documental ou assinatura digital ICP-Brasil.
4. **Comunicações:** As notificações com clientes são simuladas em tabela relacional de auditoria; não houve disparo de e-mails para provedores públicos.
"""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(conteudo, encoding="utf-8")
    return conteudo


def gerar_tabela_slide10(metricas: Dict[str, Any]) -> str:
    """Gera tabela comparativa metodologicamente defensável pronta para o Slide 10 da apresentação."""
    comp = metricas.get("comparativo", {})
    as_is = comp.get("as_is", {})
    to_be = comp.get("to_be_estimado", {})
    cont = metricas.get("contadores", {})
    coorte = metricas.get("situacao_coorte", {})

    tabela = f"""
| Dimensão | AS-IS (Fato Histórico do Case) | TO-BE (Projetado / Simulado) | Validação Funcional Demonstrada no Protótipo |
|---|---|---|---|
| **Volume Mensal de Entrada** | 1.000 solicitações manuais (3 analistas sobrecarregados) | 1.000 intenções avaliadas em {metricas.get('duracao_computacional_segundos')}s de CPU local | Regras preventivas executadas; capacidade futura a ser validada com legado |
| **Esforço Operacional Ativo** | 313,33 h/mês (18.800 min manuais) | Estimativa modelada: {to_be.get('horas_esforco_humano_estimadas')} h/mês (-{to_be.get('reducao_esforco_humano_pct')}%) | Redução projetada no cenário simulado preservando esforço humano em exceções |
| **Validação de Dados na Entrada** | Manual (8% de taxa histórica de erros de digitação) | Preventiva (bloqueio matemático de CPF e soma de 100%) | Validação preventiva em tempo real impede entrada de registros inconsistentes |
| **Tratamento de Pendências e SLA** | 250 casos manuais; espera eleva lead time | {coorte.get('aguardando_complemento_cliente')} casos com disparo automático de pendência | Pausa estruturada do prazo interno de SLA durante a espera do cliente |
| **Intervenção Humana** | 100% dos casos dependem de análise manual | {coorte.get('em_excecao_humana')} casos encaminhados para Bancada do Analista | Atuação humana focada em documentos ilegíveis e exceções de negócio |
| **Rastreabilidade e Gestão** | Caixa de e-mail compartilhada; sem painel estruturado | Protocolo único, log de auditoria relacional e dashboards | Rastreabilidade dos eventos implementados por etapa e controle de SLA |
"""
    return tabela.strip()
