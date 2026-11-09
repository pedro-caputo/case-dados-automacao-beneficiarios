# Limitações Técnicas, Premissas e Fronteiras do Projeto

Em observância às boas práticas de engenharia de software e integridade acadêmica, este documento explicita de forma transparente todas as fronteiras, premissas conservadoras e limitações operacionais da prova de conceito.

---

## 1. Dados Exclusivamente Sintéticos
- Todos os segurados, beneficiários, números de apólice, telefones e e-mails foram gerados deterministicamente por bibliotecas sintéticas (Python `Faker` e PRNG padrão).
- Não há consulta à base da Receita Federal, bancos de dados corporativos ou cadastros reais de clientes.

## 2. OCR e Validação Documental Simulados
- O sistema simula a qualidade da imagem (documento legível vs ilegível) com base em distribuição probabilística controlada pela semente sintética, e não por meio de modelo computacional de visão/OCR treinado em nuvem.
- Em um ambiente de produção bancária, a solução deverá ser conectada a um serviço especializado de Computer Vision / Document AI (ex: Google Cloud Document AI, AWS Textract ou Azure AI Document Intelligence).

## 3. Calendário Operacional e Cálculo de SLA
- O relógio de SLA calcula o prazo regulatório líquido descontando as horas acumuladas na tabela `pendencias`.
- Por se tratar de um ambiente simulado de teste, o cálculo baseia-se em horas contínuas transcorridas (120 horas = 5 dias). Em uma implantação bancária de larga escala, o motor de SLA deverá integrar uma tabela de feriados nacionais, estaduais e municipais, além de turnos de expediente bancário.

## 4. Cadastro Assistido vs Integração com Core Bancário Legado
- No protótipo, a etapa de cadastro assistido valida as regras de negócio e exige a confirmação do analista antes de permitir o fechamento do protocolo, simulando o comportamento de um barramento SOA/API moderna.
- Em produção, essa etapa seria conectada a mensageria assíncrona (ex: Apache Kafka ou IBM MQ) ou APIs REST diretas para o core legado de seguros (Mainframe/AS400).

## 5. Projeção de Redução de Esforço (-87,2%)
- A projeção de 40,25 horas/mês contra 313,33 horas/mês baseia-se estritamente nas premissas factuais documentadas na especificação do case e nos tempos operacionais modelados.
- Trata-se de uma estimativa para o cenário modelado na semente `20261108`, devendo ser revalidada empiricamente em projeto piloto (*Rollout gradual*) em ambiente de produção.
