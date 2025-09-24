# 🎙️ Roteiro de Demonstração – IaAndData

Este documento contém uma lista de perguntas estratégicas para demonstrar o potencial completo da plataforma IaAndData. A sequência foi projetada para contar uma história, começando com consultas simples e progredindo para análises complexas e visuais.

---

### Parte 1: A IA é Precisa e Conectada (Demonstração de Conhecimento Básico)

**Objetivo:** Estabelecer confiança, mostrando que a IA está conectada aos dados e responde com precisão.

1.  **Pergunta:** `Qual foi o preço de fechamento da PETR4.SA no último pregão?`
    *   **O que demonstra:** Acesso direto ao banco de dados e precisão na recuperação de dados simples.

2.  **Pergunta de Acompanhamento (Continuidade):** `E qual foi o volume negociado nesse dia?`
    *   **O que demonstra:** A **memória da conversa**. A IA entende que "nesse dia" se refere ao contexto da pergunta anterior (PETR4.SA, último pregão).

3.  **Pergunta de Acompanhamento (Cálculo Simples):** `Esse fechamento foi maior ou menor que o do dia anterior?`
    *   **O que demonstra:** A capacidade da IA de não apenas buscar, mas também **comparar dados** para fornecer um insight simples.

---

### Parte 2: A IA é um Analista Visual (Demonstração dos Gráficos Preditivos)

**Objetivo:** Mostrar as funcionalidades visuais mais impressionantes que construímos.

4.  **Pergunta (Ativando o Cone de Incerteza):** `Gere uma projeção de volatilidade para a VALE3.SA para os próximos 30 dias.`
    *   **O que demonstra:** A principal funcionalidade de **análise preditiva**. O sistema identifica a intenção e, em vez de um texto, gera o gráfico do Cone de Incerteza, mostrando a capacidade da plataforma de realizar análises estatísticas complexas e apresentá-las visualmente.

5.  **Pergunta (Ativando o Gráfico em Tempo Real):** `Me dê um resumo sobre a performance recente da MGLU3.SA.`
    *   **O que demonstra:** A **reatividade do sistema**. A IA fornecerá uma resposta em texto, e a interface, de forma proativa e automática, identificará o ticker `MGLU3.SA` e renderizará o **gráfico em tempo real com o indicador preditivo VWAP**, mostrando que a plataforma está "viva" e conectada ao mercado.

---

### Parte 3: A IA Pensa e Conecta Ideias (Demonstração de Raciocínio Avançado)

**Objetivo:** Fazer perguntas que forçam a IA a usar suas ferramentas de forma criativa e combinar informações.

6.  **Pergunta (Comparação entre Ativos):** `Qual empresa teve o maior volume de negociação no último pregão, PETR4.SA ou VALE3.SA?`
    *   **O que demonstra:** A capacidade de executar a mesma ferramenta (`get_stock_data`) múltiplas vezes com parâmetros diferentes, comparar os resultados internamente e fornecer uma resposta final consolidada.

7.  **Pergunta de Múltiplos Passos (Pergunta Final "Uau"):** `Considerando a VALE3.SA, qual foi a data na última semana que teve o menor preço de fechamento e qual foi o volume negociado nesse dia específico?`
    *   **O que demonstra:** Raciocínio complexo. A IA precisa:
        1.  Entender o período ("última semana").
        2.  Buscar todos os dados desse período para a VALE3.SA.
        3.  Iterar sobre os resultados para encontrar o menor valor de fechamento.
        4.  Extrair a data e o volume correspondentes a esse dia específico.
        5.  Formular uma resposta final clara com todas as informações solicitadas.

---

### Parte 4: Explorando Todas as Capacidades Visuais (Perguntas Adicionais)

**Objetivo:** Demonstrar a flexibilidade do sistema em exibir os gráficos a partir de diferentes tipos de perguntas, garantindo que todas as visualizações sejam mostradas.

#### Acionando o Gráfico de Projeção (Cone de Incerteza)

Estas perguntas foram projetadas para acionar diretamente nossa lógica de roteamento inteligente, sempre exibindo o gráfico de análise preditiva de longo prazo.

*   `Qual a tendência futura para a ITUB4.SA?`
*   `Me mostre um cone de incerteza para a ABEV3.SA.`
*   `É possível prever o comportamento da WEGE3.SA para as próximas semanas?`
*   `Gere uma análise de previsão para a BBDC4.SA.`

#### Acionando o Gráfico em Tempo Real (Intraday com VWAP)

Estas perguntas são mais abertas. A IA responderá com texto, mas a interface irá detectar o ticker na resposta e, de forma proativa, exibirá o gráfico "vivo" de análise de curto prazo.

*   `Como a PETR4.SA está se saindo hoje no mercado?`
*   `Fale um pouco sobre a VALE3.SA.`
*   `Qual a cotação mais recente que você tem para a ITUB4.SA?` (A IA dará o último preço do banco de dados, mas o sistema mostrará o gráfico com a cotação do minuto).
*   `O que você sabe sobre a ABEV3.SA?`

---

### Parte 5: Análise Sênior (Insights e Comparações)

**Objetivo:** Testar as novas capacidades de raciocínio multi-etapas e as ferramentas de análise avançada do agente.

#### Análise Técnica de Ativo Único
*   `A PETR4.SA está atualmente sobrecomprada ou sobrevendida?`
    *   **O que demonstra:** Força o uso da ferramenta `get_asset_analytics` para buscar e interpretar o indicador RSI.
*   `O preço atual da VALE3.SA está acima ou abaixo da sua média móvel de 21 dias?`
    *   **O que demonstra:** Força o uso da `get_asset_analytics` para calcular a SMA e comparar o resultado com o preço de fechamento mais recente.

#### Análise Comparativa Complexa
*   `Compare a performance e a volatilidade da MGLU3.SA e da ABEV3.SA desde o início de 2023.`
    *   **O que demonstra:** Força o uso da ferramenta `compare_assets`, que por sua vez chama `get_stock_data` duas vezes, para consolidar e analisar múltiplos ativos.
*   `Quais foram as 3 ações com maior volume financeiro no último trimestre e qual delas teve a melhor performance no período?`
    *   **O que demonstra:** Raciocínio em duas etapas. A IA deve primeiro usar `get_top_stocks_by_criteria` para identificar os ativos e, em seguida, usar `compare_assets` para analisar a performance desses ativos.

#### Teste do Mecanismo de Feedback
*   `Qual a relação entre o volume de negociação da PETR4.SA e o preço do barril de petróleo?`
    *   **O que demonstra:** A capacidade da IA de reconhecer os limites de suas ferramentas. Ela deve concluir que não pode responder, usar a ferramenta `notify_developer_of_missing_tool` para enviar uma notificação ao Discord, e informar ao usuário sobre a ação tomada.

Seguir este roteiro garantirá uma demonstração fluida, lógica e que destaca cada camada de inteligência que construímos no projeto IaAndData.
