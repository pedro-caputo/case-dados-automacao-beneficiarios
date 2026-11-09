# Relatório Técnico Experimental — Processo de Beneficiários Seguros PF (Modelo TO-BE)

**Identificador da Execução:** `EXP-20261108`  
**Data e Hora:** N/A  
**Semente Determinística:** `20261108`  
**Amostra Testada:** 1000 intenções sintéticas  

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

- **Tempo Computacional do Lote (1.000 casos):** `0.221 segundos`.
- **Vazão Sistêmica de Processamento:** `4534.1 casos/segundo`.

> **Distinção Metodológica Fundamental:** A duração de frações de segundo reflete unicamente o tempo computacional dos algoritmos de validação preventiva e inserção no SQLite local. Esse tempo **NÃO** deve ser confundido com a conclusão de processos bancários nem com a extinção total do trabalho humano. A efetivação na apólice depende da esteira e de intervenções humanas nos casos de exceção e pendência.

---

## 3. Situação da Coorte de 1.000 Casos na Simulação
*Classificação operacional de cada intenção de solicitação após aplicação das regras TO-BE:*

- **Aptas para Cadastro Direto (STP):** `750 casos (75.0%)` — dados íntegros e documentos sinteticamente conformes.
- **Aguardando Complemento do Cliente:** `190 casos (19.0%)` — pendência aberta e relógio de SLA pausado.
- **Em Exceção para Revisão Humana:** `60 casos (6.0%)` — documentos com legibilidade simulada inconclusiva ou divergência.
- **Erros Sintéticos de Digitação Potencialmente Prevenidos:** `77 casos` — bloqueados preventivamente na validação de entrada (baseado na probabilidade histórica de 8% informada no case).

---

## 4. Projeção de Esforço Humano Residual Decomposto por Atividade
*Comparação entre o esforço histórico (AS-IS) e o esforço humano residual estimado no TO-BE:*

| Atividade Operacional | Esforço AS-IS | Esforço TO-BE Estimado | Variação (Horas) | Mecanismo de Transformação e Hipótese Adotada |
|---|---:|---:|---:|---|
| **Triagem de Solicitações** | 66.7 h | 0.0 h | -66.7 h | 100% automatizada por formulário digital e validação prévia de entrada |
| **Conferência Inicial de Documentos** | 100.0 h | 6.0 h | -94.0 h | Automação filtra casos regulares; analista atua em 60 exceções (6.0 min/caso) |
| **Gestão de Complementos e Pendências** | 41.7 h | 17.7 h | -24.0 h | Disparo automático de pendências; analista revalida 190 complementos recebidos e casos em atraso |
| **Cadastro e Efetivação no Sistema** | 75.0 h | 14.6 h | -60.4 h | Eliminação de erros de digitação; supervisão em lote de casos padrão e conferência individual de exceções |
| **Respostas e Retorno aos Clientes** | 30.0 h | 2.0 h | -28.0 h | Disparos transacionais simulados com protocolo; retorno humano restrito a exceções e recusas |

| **TOTAL GERAL DE ESFORÇO** | **313.33 h** | **40.25 h** | **-273.08 h (-87.2%)** | **Redução projetada no cenário simulado focada em triagem mecânica e validação preventiva** |

---

## 5. Justificativa das Hipóteses e Fórmulas da Projeção

1. **Triagem (0 h no TO-BE):** A entrada estruturada por canal digital (App/Web/Agência) substitui a triagem manual de caixa de e-mails, gerando protocolo único e metadados preventivos automaticamente.
2. **Conferência Inicial (6.0 h no TO-BE):** Casos 100% regulares têm consistência garantida por código. O analista atua unicamente sobre as 60 exceções humanas (hipótese de 6,0 min/caso = 360 min).
3. **Gestão de Complementos (17.7 h no TO-BE):** O disparo de pendência é automático com pausa de SLA. O esforço humano residual modela a reanálise dos 190 complementos recebidos (hipótese de 4,0 min/caso = 760 min) e o acompanhamento ativo dos 100 clientes com atraso superior a 5 dias (hipótese de 3,0 min/caso = 300 min). Total: 1.060 min.
4. **Cadastro no Legado (14.6 h no TO-BE):** Como o case não documenta integração direta por API com o core legado, a efetivação cadastral não é assumida como instantânea. Modela-se supervisão humana em lote para 750 casos regulares (0,5 min/caso = 375 min) e conferência cadastral individual para os 250 casos que passaram por complemento/exceção (2,0 min/caso = 500 min). Total: 875 min.
5. **Respostas e Comunicações (2.0 h no TO-BE):** Mensagens transacionais são disparadas de forma automática pelo sistema. O analista trata apenas exceções e recusas (60 casos × 2,0 min = 120 min).

---

## 6. Limitações Metodológicas do Protótipo
1. **Ambiente Simulado:** Os dados e eventos são 100% sintéticos e executados localmente; não houve integração com servidores externos ou bancos legados de produção.
2. **Capacidade Operacional Futura Não Validada:** O atendimento ao crescimento anual de 10% demandará testes de estresse com o core legado e análise de volumetria em ambiente real.
3. **Validação de Documentos:** A verificação de arquivos no protótipo avalia formato, presença e legibilidade simulada; não substitui perícia documental ou assinatura digital ICP-Brasil.
4. **Comunicações:** As notificações com clientes são simuladas em tabela relacional de auditoria; não houve disparo de e-mails para provedores públicos.
