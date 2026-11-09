| Dimensão | AS-IS (Fato Histórico do Case) | TO-BE (Projetado / Simulado) | Validação Funcional Demonstrada no Protótipo |
|---|---|---|---|
| **Volume Mensal de Entrada** | 1.000 solicitações manuais (3 analistas sobrecarregados) | 1.000 intenções avaliadas em 0.221s de CPU local | Regras preventivas executadas; capacidade futura a ser validada com legado |
| **Esforço Operacional Ativo** | 313,33 h/mês (18.800 min manuais) | Estimativa modelada: 40.25 h/mês (-87.2%) | Redução projetada no cenário simulado preservando esforço humano em exceções |
| **Validação de Dados na Entrada** | Manual (8% de taxa histórica de erros de digitação) | Preventiva (bloqueio matemático de CPF e soma de 100%) | Validação preventiva em tempo real impede entrada de registros inconsistentes |
| **Tratamento de Pendências e SLA** | 250 casos manuais; espera eleva lead time | 190 casos com disparo automático de pendência | Pausa estruturada do prazo interno de SLA durante a espera do cliente |
| **Intervenção Humana** | 100% dos casos dependem de análise manual | 60 casos encaminhados para Bancada do Analista | Atuação humana focada em documentos ilegíveis e exceções de negócio |
| **Rastreabilidade e Gestão** | Caixa de e-mail compartilhada; sem painel estruturado | Protocolo único, log de auditoria relacional e dashboards | Rastreabilidade dos eventos implementados por etapa e controle de SLA |