# Comparativo de Processo: Cenário AS-IS vs Cenário TO-BE

Este documento estabelece o confronto detalhado entre o fluxo operacional histórico legado (**AS-IS**) e o modelo transformado com automação e padronização (**TO-BE**) para alteração de beneficiários em seguros de pessoas físicas.

---

## 1. O Cenário AS-IS (Processo Histórico)

### 1.1 Características Operacionais
- **Entrada Não Padronizada:** Solicitações recebidas por e-mails com texto livre, formulários em papel escaneados nas agências e anexos avulsos.
- **Ausência de Crítica na Origem:** O cliente ou corretor enviava dados sem verificação prévia de CPF, sem conferência da soma dos percentuais (100%) e com documentos ilegíveis ou incompletos.
- **Triagem Manual:** Analistas precisavam abrir anexo por anexo para identificar apólice, titular e validade das certidões.
- **Gargalo de Pendências:** 25% das solicitações (250 de 1.000 mensais) chegavam com inadequação documental, gerando trocas repetidas de e-mails manuais para solicitar correções.
- **SLA e Reclamações:** Prazos frequentemente extrapolados, sem pausa oficial durante o tempo de espera pelo cliente, gerando 18 reclamações mensais registradas na Ouvidoria.
- **Esforço Humano Excessivo:** O volume de 1.000 solicitações consumia **313,33 horas de analista por mês**, exigindo uma equipe dedicada de 3 analistas seniores em atividades operacionais repetitivas.

### 1.2 Composição do Esforço no AS-IS
| Atividade | Volume Mensal | Tempo Unitário | Total Mensal (Minutos) | Total Mensal (Horas) |
|---|---|---|---|---|
| Triagem manual de e-mails/anexos | 1.000 casos | 5,0 min | 5.000 min | 83,33 h |
| Conferência manual de documentos | 1.000 casos | 8,0 min | 8.000 min | 133,33 h |
| Solicitação manual de complementos | 250 casos | 10,0 min | 2.500 min | 41,67 h |
| Cadastro manual nos sistemas legados | 750 casos | 4,0 min | 3.000 min | 50,00 h |
| Resposta formal ao segurado/agência | 150 casos | 2,0 min | 300 min | 5,00 h |
| **TOTAL GERAL AS-IS** | **1.000 casos** | — | **18.800 min** | **313,33 horas** |

---

## 2. O Cenário TO-BE (Processo Padronizado e Automatizado)

### 2.1 Princípios de Transformação
1. **Validação Preventiva na Origem (*Shift-Left*):** O formulário digital valida o CPF via algoritmo oficial dos dois dígitos verificadores, bloqueia somas divergentes de 100,00% e exige anexos obrigatórios legíveis antes de permitir a transmissão.
2. **Triagem Automática e Roteamento (*Straight-Through Processing - STP*):** Casos com documentação completa e legível avançam diretamente para a fila de cadastro, eliminando o esforço de triagem humana.
3. **Tratamento Automático de Inadequações:** Documentos ausentes geram pendência imediata, envio automatizado de mensagem com instruções claras e **pausa regulamentar no relógio de SLA**.
4. **Bancada de Exceções para Decisão Humana (*Human-in-the-Loop*):** O analista atua exclusivamente onde seu discernimento é insubstituível: certidões com legibilidade inconclusiva, pedidos de anulação ou discrepâncias complexas de vínculo familiar.
5. **Cadastro Assistido e Seguro:** A efetivação nos sistemas requer confirmação com rastreabilidade, impedindo a conclusão inadvertida de casos sem alteração real.

### 2.2 Composição do Esforço Projetado no TO-BE
| Atividade | Volume Simulado | Tempo Unitário | Total Mensal (Minutos) | Total Mensal (Horas) |
|---|---|---|---|---|
| Triagem e conferência automatizadas | 1.000 casos | 0,0 min (sistema) | 0 min | 0,00 h |
| Notificação automática de complementos | 190 casos | 0,0 min (sistema) | 0 min | 0,00 h |
| Análise humana de exceções complexas | 60 casos | 15,0 min | 900 min | 15,00 h |
| Efetivação de cadastro assistido | 750 casos | 2,0 min | 1.500 min | 25,00 h |
| Resposta automática final ao cliente | 1.000 casos | 0,0 min (sistema) | 0 min | 0,00 h |
| Auditoria e tratamento residual | 5 casos | 3,0 min | 15 min | 0,25 h |
| **TOTAL GERAL TO-BE** | **1.000 casos** | — | **2.415 min** | **40,25 horas** |

---

## 3. Síntese dos Ganhos de Negócio

| Indicador | Cenário AS-IS | Cenário TO-BE | Variação Observada |
|---|---|---|---|
| **Esforço Operacional Humano** | 313,33 horas/mês | 40,25 horas/mês | **-87,2%** de redução no esforço repetitivo |
| **Erros de Digitação na Entrada** | 77 erros/mês (estimado) | 0 erros gravados | **100%** interceptados preventivamente |
| **Tempo de Triagem de Lote (1.000)** | 83,3 horas humanas | ~0,22 segundo computacional | **Automação imediata** via motor de regras |
| **Pausa Oficial de SLA em Pendência** | Inexistente (tempo corria) | Automatizada com desconto | **Segurança jurídica e conformidade** |
| **Taxa de Processamento Direto (STP)** | 0% | 75% dos casos aptos | **750 solicitações** sem necessidade de retrabalho |
