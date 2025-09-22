# 📖 IaAndData – IA + Dados Financeiros

## 🔹 O Problema

No mercado financeiro brasileiro, informações históricas de ações estão espalhadas em múltiplas fontes: relatórios da B3, balanços de empresas, APIs públicas e privadas.
Executivos, investidores e analistas gastam **horas consolidando dados** antes de tomar decisões, correndo o risco de usar informações incompletas ou desatualizadas.

---

## 🔹 A Solução

Criamos uma **Inteligência Artificial conectada a um banco de dados financeiro unificado**.
Nosso sistema permite que qualquer pessoa consulte, em linguagem natural, dados históricos de ações de empresas brasileiras — de forma precisa, rápida e confiável.

**Exemplo:**
👉 **Pergunta:** *“Qual foi o preço médio da PETR4 em 2020?”*
👉 **Resposta:** *“O preço médio foi R$ 19,47, com variação de X% ao longo do período.”* + gráfico interativo.

---

## 🔹 Como Vai Funcionar (MVP)

1.  **Coleta de Dados (Extract)**
    *   Utilizamos bibliotecas financeiras (ex.: `yfinance`) para extrair dados históricos de ações da B3 e APIs públicas.
    *   Dados são capturados automaticamente e atualizados em lote.

2.  **Transformação e Organização (Transform)**
    *   Usamos **Python + Pandas** para limpar e padronizar os dados.
    *   Normalizamos datas, ajustamos splits, dividendos e consolidamos métricas financeiras.

3.  **Armazenamento (Load)**
    *   Os dados transformados são armazenados em um **banco de dados Supabase (PostgreSQL)**, que oferece uma base relacional robusta com APIs auto-geradas.
    *   Estruturados por empresa, código da ação e período de tempo.

4.  **Camada de Inteligência Artificial**
    *   Implementamos **LangChain** conectado à **API da OpenAI (GPT-4/3.5)**.
    *   A IA entende a pergunta do usuário, traduz em consultas ao banco e devolve respostas completas.

5.  **Backend**
    *   Criado em **Python com FastAPI**, responsável por:
        *   Receber perguntas do usuário.
        *   Processar consultas no banco.
        *   Passar os dados para a IA.
        *   Retornar respostas estruturadas (texto + gráficos).

6.  **Frontend**
    *   Interface desenvolvida em **React + Next.js + TailwindCSS**, oferecendo:
        *   Campo de busca em linguagem natural.
        *   Visualização de respostas textuais e gráficas.
        *   Dashboard intuitivo para consultas frequentes.

---

## 🔹 Stacks do Projeto

*   **Linguagem principal:** Python 🐍
*   **Frontend:** React + Next.js + TailwindCSS
*   **Backend (API):** FastAPI (Python)
*   **Banco de dados:** Supabase (PostgreSQL)
*   **ETL / Data Processing:** Python + Pandas
*   **IA / RAG:** LangChain + OpenAI GPT API
*   **Hospedagem:**
    *   Frontend → Vercel (Next.js)
    *   Backend → Railway/Render/Heroku (FastAPI)
    *   Banco → Supabase (Cloud)

---

## 🔹 Roadmap de Evolução

*   **MVP:** consultas históricas básicas de ações.
*   **Versão 2:** relatórios automáticos, análises comparativas e alertas.
*   **Versão 3 (Enterprise):** dados em tempo real, previsões de mercado e dashboards personalizados.
