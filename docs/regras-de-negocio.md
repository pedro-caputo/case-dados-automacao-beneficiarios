# Regras de Negócio e Critérios de Aceite (AC)

Este documento formaliza as regras de negócio implementadas nos validadores (`src/validators.py`) e no fluxo de trabalho (`src/workflow.py`).

---

## 1. Critérios de Aceite da Especificação Funcional

| Código | Critério de Aceite | Implementação no Sistema | Comportamento Observado |
|---|---|---|---|
| **AC01** | Validação Preventiva de CPF | Algoritmo oficial dos dois dígitos verificadores (módulo 11) | Rejeita CPFs inválidos na digitação ou na ingestão, bloqueando sequência repetida (ex: 111.111.111-11). |
| **AC02** | Soma dos Percentuais de Beneficiários | Soma de pontos flutuantes com tolerância de precisão (`round(soma, 2) == 100.00`) | Impede avanço se a soma for menor ou maior que 100,00%, e bloqueia CPFs repetidos na mesma apólice. |
| **AC03** | Anexos Obrigatórios e Formato | Verificação determinística de presença de documento de identificação e certidão de vínculo | Bloqueia submissão sem os documentos exigidos e valida extensões (.pdf, .png, .jpg). |
| **AC04** | Geração de Protocolo Único | Máscara padronizada `BEN-AAAAMMDD-XXXXXX` | Protocolo único gerado atomicamente e gravado com evento inicial na linha do tempo. |
| **AC05** | Inadequação Gera Pendência | Classificação automática de inadequação documental em `pendencias` | Gera pendência com tipo estruturado e descrição amigável para o cliente. |
| **AC06** | Pausa Automática do Relógio de SLA | Registro de `sla_pausado_em = now()` e transição de estado para `PAUSADO` | Desconta rigorosamente as horas decorridas entre a notificação e o envio do documento. |
| **AC07** | Roteamento Automático de Casos Regulares | Identificação de integridade documental total | Encaminha solicitação automaticamente para o status `PRONTA_PARA_CADASTRO` (STP). |
| **AC08** | Fila Operacional Priorizada | Ordenação dinâmica por Criticidade de SLA e Prioridade da Apólice | Casos em risco de expiração e apólices de alta prioridade encabeçam a lista. |
| **AC09** | Bancada de Análise de Exceções | Interface dedicada para atuação de analista humano em casos complexos | Exibe parecer prévio da automação, dados do titular, beneficiários e botões de decisão. |
| **AC10** | Decisão Humana Justificada | Obrigatoriedade de preenchimento de justificativa textual para aprovação/rejeição | Bloqueia submissão sem justificativa e armazena parecer no histórico auditável. |
| **AC11** | Cadastro Assistido Seguro | Bloqueio de conclusão direta sem confirmação de efetivação cadastral | O botão "Concluir Solicitação" só é habilitado após a gravação da confirmação cadastral. |
| **AC12** | Histórico e Rastreabilidade Completa | Tabela `eventos` com carimbo ISO 8601, ator e descrição | Linha do tempo exibe todos os passos cronológicos da solicitação. |
| **AC13** | Mensageria e Notificações ao Cliente | Templates parametrizados de e-mail/SMS/App para cada transição | Registra comunicações simuladas na tabela `comunicacoes`. |
| **AC14** | Regra de SLA Líquido (120 Horas / 5 Dias) | Cálculo que deduz `sla_pausa_acumulada_segundos` do tempo total transcorrido | Horas pausadas em espera pelo segurado não consomem o prazo regulamentar da seguradora. |
| **AC15** | Separação Estrita de Universos | Chave `universo` (`INTERATIVO` vs `EXPERIMENTAL`) e `run_id` | Impede vazamento de dados entre testes manuais e simulações em lote. |

---

## 2. Regras de Transição e Validação Atômica

Antes de persistir qualquer alteração de estado no banco de dados, a camada de serviço executa:
1. Verificação se a solicitação ainda existe e coincide com o protocolo informado.
2. Conferência de que o estado atual permite a transição solicitada.
3. Gravação simultânea da solicitação, do evento de auditoria e do fechamento/abertura de pendências dentro da mesma transação SQLite.
