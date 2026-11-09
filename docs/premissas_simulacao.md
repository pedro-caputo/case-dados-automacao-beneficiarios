# Premissas, Hipóteses e Metodologia de Simulação — Versão Auditada

Este documento detalha o embasamento matemático e a auditoria metodológica empregada na comparação entre o cenário histórico (**AS-IS**) e o modelo futuro proposto (**TO-BE**).

---

## 1. Dados Factuais do Case (Imutáveis)

Estes números são fatos documentados e não sofreram qualquer alteração para favorecer o projeto:

- **Volume:** 1.000 solicitações por mês, com previsão de crescimento de 10% a.a.
- **Equipe:** 3 analistas dedicados.
- **Canais Históricos:** E-mail (550 = 55%), Agência (300 = 30%), Aplicativo (150 = 15%).
- **Inadequação Documental Inicial:** 25% (250 casos) chegam com documentos incompletos ou ilegíveis.
- **Comportamento do Cliente na Pendência:** 40% dos clientes que necessitam de complemento (100 clientes) demoram mais de 5 dias para responder.
- **Esforço Humano Ativo Mensal (18.800 minutos = 313,33 horas):**
  - Triagem manual: 1.000 × 4 min = 4.000 min (66,67 h)
  - Conferência manual: 1.000 × 6 min = 6.000 min (100,00 h)
  - Complemento manual: 250 × 10 min = 2.500 min (41,67 h)
  - Cadastro manual: 900 × 5 min = 4.500 min (75,00 h)
  - Resposta manual: 900 × 2 min = 1.800 min (30,00 h)
- **Indicadores Históricos de Qualidade:** 62% dentro do SLA de 5 dias / 38% fora do prazo; 60 reclamações mensais; 8% de erros manuais de digitação na operação.

---

## 2. Auditoria Metodológica do Esforço Humano no TO-BE

A versão preliminar do protótipo estimava uma redução de esforço de ~98% ao considerar apenas os casos de exceção documental (60 casos × 6 min = 6,0 horas).  
**Essa estimativa foi auditada e corrigida**, pois desconsiderava atividades humanas residuais indispensáveis para o funcionamento do processo em ambiente corporativo.

### Modelo Auditado e Decomposto por Atividade:

1. **Triagem (AS-IS: 4.000 min ➔ TO-BE: 0 min | Redução de 100%):**
   - No TO-BE, a entrada estruturada (portal, app e formulários de agência) valida os campos na origem e gera o protocolo unívoco automaticamente, extinguindo a triagem manual em caixa compartilhada de e-mails.
2. **Conferência Inicial (AS-IS: 6.000 min ➔ TO-BE: 360 min | Redução de 94%):**
   - O software confere regras determinísticas (presença de arquivos, extensões, integridade sintática e soma de 100%).
   - Casos com documentos ilegíveis ou divergentes (60 casos da amostra) são retidos para conferência humana pelo analista (60 casos × 6,0 min = **360 min = 6,0 h**).
3. **Gestão de Complementos (AS-IS: 2.500 min ➔ TO-BE: 1.060 min | Redução de 58%):**
   - O envio da solicitação de complemento é automatizado com pausa do relógio de SLA.
   - Porém, **quando os complementos retornam do cliente, é necessária re-análise humana** (190 casos × 4,0 min = 760 min), somada ao acompanhamento dos 100 clientes que demoram mais de 5 dias (100 × 3,0 min = 300 min). Total: **1.060 min = 17,67 h**.
4. **Cadastro e Efetivação (AS-IS: 4.500 min ➔ TO-BE: 875 min | Redução de 81%):**
   - A validação preventiva na entrada elimina os 8% de erros manuais de digitação de CPF e percentuais.
   - Os 750 casos regulares têm supervisão e confirmação em lote (750 × 0,5 min = 375 min).
   - Os 250 casos que passaram por complemento ou exceção recebem conferência cadastral individualizada (250 × 2,0 min = 500 min). Total: **875 min = 14,58 h**.
5. **Respostas e Comunicações (AS-IS: 1.800 min ➔ TO-BE: 120 min | Redução de 93%):**
   - Disparos automáticos de confirmação de recebimento, avisos de pendência e conclusão.
   - Atendimento humano personalizado reservado a 60 casos de exceção ou recusas (60 × 2,0 min = **120 min = 2,0 h**).

### Resultado Consolidado da Auditoria:
$$\text{Esforço Humano TO-BE} = 0 + 360 + 1.060 + 875 + 120 = 2.415\text{ minutos} \approx \mathbf{40,25\text{ horas/mês}}$$
$$\text{Redução Realista e Defensável} = 313,33\text{ h} - 40,25\text{ h} = 273,08\text{ horas} \rightarrow \mathbf{87,2\%}$$

---

## 3. Distinção entre Tempo Computacional e Esforço Operacional

- **Tempo Computacional Medido (~0,05 segundos):** refere-se exclusivamente ao tempo de CPU e SQLite para avaliar algoritmicamente 1.000 registros sintéticos em lote.
- **Esforço Operacional Humano Estimado (~40,25 horas):** reflete o tempo real de trabalho que os 3 analistas despenderão nas atividades que exigem julgamento humano, verificação de complementos e supervisão de cadastros.
