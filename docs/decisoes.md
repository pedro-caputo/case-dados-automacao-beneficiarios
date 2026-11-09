# Registro de Decisões Técnicas e Defesas para a Banca Avaliadora

Este documento consolida as principais escolhas arquiteturais, justificativas de engenharia de software e respostas preparadas para a banca técnica.

---

## 1. Decisões Arquiteturais e de UX/UI

### D-01: Isolamento entre Regras de Negócio e Streamlit
- **Decisão:** Validações de CPF, cálculo de SLA com pausas, máquina de estados e repositórios relacionais não dependem do Streamlit.
- **Justificativa:** Garante 100% de testabilidade via `pytest` sem necessidade de abrir browser ou renderizar interfaces.

### D-02: Acessibilidade Visual e Alto Contraste (WCAG AA)
- **Decisão:** Eliminação de estilos que pudessem causar texto claro sobre fundo claro nos cartões de conformidade documental da bancada do analista. Utilização de texto escuro `#0F172A` de alto contraste e bordas sólidas.
- **Justificativa:** Atende aos padrões de acessibilidade corporativa e evita que informações cruciais fiquem ilegíveis na apresentação.

### D-03: Separação de Dados Interativos e Lote Experimental
- **Decisão:** A simulação em lote de 1.000 casos sintéticos grava solicitações com `run_id` específico, permitindo isolar a operação manual interativa dos dados experimentais.
- **Justificativa:** Permite que o avaliador teste a criação de casos individuais sem que estes se percam no meio do lote de 1.000 registros sintéticos.

### D-04: Auditoria do Modelo de Esforço Operacional Humano
- **Decisão:** Decomposição da estimativa de esforço por atividade (Triagem, Conferência, Complemento, Cadastro, Resposta), reconhecendo o trabalho humano residual em complementos e supervisão cadastral.
- **Justificativa:** Evita apresentar percentuais inflados (~98%) que confundiam tempo de CPU em memória com conclusão de processos bancários, substituindo por uma redução realista e defensável de ~87% (40,25h de trabalho humano ativo).

---

## 2. Respostas Estratégicas para Perguntas da Banca

**1. "Como o sistema garante que 8% de erros de digitação não ocorram no TO-BE?"**
> *Resposta:* "Através de validação preventiva no ponto de entrada. O formulário não permite o envio se o CPF não cumprir a fórmula oficial de dígitos verificadores ou se os percentuais não somarem exatamente 100%. O erro é bloqueado na origem, poupando retrabalho na esteira."

**2. "Por que o tempo computacional é medido em frações de segundo, mas o ganho do TO-BE é de 40 horas?"**
> *Resposta:* "Porque distinguimos rigorosamente o tempo de software do esforço de trabalho humano. O computador avalia regras em 0,05 segundos, mas a esteira de seguros requer tempo de analistas para inspecionar imagens de baixa legibilidade, reavaliar complementos retornados e supervisionar averbações cadastrais. Por isso, a redução é estimada em 87%, preservando 40,25 horas de trabalho humano focado em tarefas de alto valor."

**3. "O que acontece com o SLA quando o cliente demora para responder a uma pendência?"**
> *Resposta:* "O relógio de 5 dias do SLA é automaticamente pausado quando a pendência é aberta e a notificação é gerada. Ao receber o documento pelo canal digital, a pendência é encerrada e a contagem é retomada. Isso impede que os 40% de clientes que demoram mais de 5 dias distorçam os indicadores de pontualidade da equipe interna."

**4. "Como este protótipo em Python se traduz para o ambiente corporativo da instituição?"**
> *Resposta:* "A arquitetura foi mapeada conceitualmente para a Microsoft Power Platform: o formulário de entrada mapeia para um Power Apps Canvas; a bancada de análise para um Power Apps Model-Driven; as regras de transição e notificações para o Power Automate; as tabelas para o Microsoft Dataverse; e os dashboards para o Power BI. O código Python funciona como o gêmeo digital do processo TO-BE."
