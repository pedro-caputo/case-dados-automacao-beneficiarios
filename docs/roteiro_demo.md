# Roteiro de Demonstração Executiva (Aprox. 2 Minutos) — Versão Final Auditada

Este roteiro conduz o avaliador pela jornada operacional completa do modelo TO-BE de forma dinâmica, profissional, visualmente fluida e metodologicamente defensável.

---

## Cronograma Minuto a Minuto

### [0:00 – 0:25] Central de Operações & Apresentação da Jornada TO-BE
- **Tela:** `app.py` (Central de Operações).
- **Ação:** Aponte o stepper da jornada no topo (Registro ➔ Validação ➔ Fila ➔ Análise/Cadastro ➔ Conclusão ➔ Gestão) e os 3 cards de navegação rápida.
- **Fala Sugerida:**
  > *"Olá! Apresento a solução TO-BE de gestão de alteração de beneficiários em seguros de pessoas físicas. Transformamos uma operação manual e fragmentada — que consumia mais de 313 horas mensais da equipe em caixas de e-mail desordenadas — em uma esteira operacional estruturada em 6 etapas: do registro com validação preventiva na origem até a governança de SLA e auditoria executiva, com dados 100% sintéticos e rastreáveis."*

---

### [0:25 – 0:50] Validação Preventiva na Origem, Máscaras e Perfil Realista
- **Tela:** `pages/01_Nova_Solicitacao.py`.
- **Ação:** 
  1. Clique em **"🎲 Gerar Perfil Fictício Completo"** (destaque a geração de dados brasileiros realistas com `Faker pt_BR` e soma de 100%).
  2. Altere o CPF digitando apenas números e mostre a **máscara progressiva imediata** (`000.000.000-00`) e a validação do e-mail em tempo real.
  3. Provoque um erro rápido (ex: CPF incorreto ou soma de 120%) para demonstrar o **bloqueio na entrada**, impedindo os históricos 8% de erros manuais.
  4. Corrija e clique em **"Gravar Solicitação e Iniciar Validação"**.
  5. Mostre a **confirmação persistente estruturada** com o protocolo gerado (`BEN-AAAAMMDD-XXXX`).
- **Fala Sugerida:**
  > *"No AS-IS, 8% dos cadastros tinham erros de digitação. Aqui demonstramos a validação na origem: máscaras inteligentes de CPF e telefone, validação matemática de dígitos verificadores e exigência estrita de 100% na partilha. Ao submeter, o sistema gera protocolo unívoco e notificação imediata, mantendo a confirmação visível na esteira."*

---

### [0:50 – 1:15] Fila Operacional Inteligente & Gestão de SLA com Pausas
- **Tela:** `pages/02_Fila_Operacional.py`.
- **Ação:** 
  1. Destaque o filtro padrão **"Apenas Casos Ativos"** e a busca multi-campo.
  2. Localize um caso aguardando complemento: mostre o badge de **SLA pausado** (relógio congelado).
  3. Mostre um caso concluído com o badge **"✓ SLA encerrado (No prazo)"**, eliminando horas ativas fantasmas em casos finalizados.
  4. Clique em **"Receber Complemento do Cliente"** em um caso pausado: o sistema executa o checklist operacional de revalidação em 5 etapas e retoma o relógio de SLA.
- **Fala Sugerida:**
  > *"Na fila operacional, os analistas trabalham com priorização clara por criticidade de prazo. Destaco o controle de SLA: quando há pendência de documentos, o prazo de 5 dias é pausado para não penalizar a equipe pela demora do cliente — algo crítico quando 40% dos segurados levam mais de 5 dias para responder. Ao receber o documento, o sistema revalida em 5 etapas e retoma a contagem com precisão."*

---

### [1:15 – 1:40] Bancada do Analista (Human-in-the-Loop) & Decisões Justificadas
- **Tela:** `pages/03_Analise_Humana.py`.
- **Ação:** 
  1. Selecione um caso em exceção documental.
  2. Mostre o diagnóstico de alto contraste (`#0F172A`) explicando exatamente **o que a automação verificou e por que reteve**.
  3. Inicie o cronômetro de esforço humano ativo.
  4. Escolha a ação com **mensagem contextual específica** (ex.: documento ilegível vs ausente) ou aprove a exceção com justificativa.
  5. Grave a decisão e evidencie a confirmação persistente com trilha de auditoria no SQLite.
- **Fala Sugerida:**
  > *"A automação não substitui o analista nas decisões críticas; ela o empodera. A bancada organiza o atendimento em etapas lógicas, com contraste visual rigoroso. O sistema explica claramente o diagnóstico preventivo e permite que o analista registre seu parecer com cronômetro integrado, alimentando o histórico de auditoria imutável."*

---

### [1:40 – 2:05] Dashboard Gerencial & Laboratório com Auditoria do Slide 10
- **Tela:** `pages/04_Dashboard.py` e `pages/05_Laboratorio.py`.
- **Ação:** 
  1. No Dashboard, mostre as abas separadas de **Pendências em Aberto** (âmbar) versus **Histórico Resolvido** (verde).
  2. No Laboratório, mostre o processamento do lote de 1.000 intenções com semente reproduzível `20261108`.
  3. Abra o painel de **Auditoria Metodológica do Esforço** e aponte a síntese do **Slide 10**.
- **Fala Sugerida:**
  > *"Por fim, nos indicadores gerenciais, separamos pendências ativas de ocorrências resolvidas. No laboratório experimental, processamos 1.000 casos sintéticos em frações de segundo de CPU. Mas o dado fundamental para o Slide 10 é nossa projeção de esforço humano decomposto: eliminamos 100% da triagem e conferência mecânica, mantendo o tempo humano indispensável para exceções, complementos e supervisão cadastral. O resultado é uma redução sólida de 87,2% no esforço ativo, caindo de 313,3 horas para 40,25 horas mensais."*

---

## Plano de Contingência Técnica (Se houver limitação de exibição ao vivo)

1. **Apresentar a suíte de testes:** `python -m pytest tests/ -v` (25 testes cobrindo 100% das regras e casos de uso funcionais em ~3 segundos).
2. **Apresentar os relatórios gerados:** abrir `outputs/tabela_slide10.md` e `outputs/relatorio_experimento.md`.
3. **Mapeamento Low-Code:** detalhar `docs/arquitetura_low_code.md` (Power Apps Canvas, Model-Driven, Power Automate e Dataverse).