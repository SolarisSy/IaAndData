# 🗺️ Plano de Desenvolvimento – IaAndData (MVP)

Este documento detalha o plano de ação para o desenvolvimento do MVP (Minimum Viable Product) do projeto IaAndData, com base nas especificações do `README.md`.

## Fase 0: Configuração e Estrutura do Projeto

O objetivo desta fase é preparar o ambiente de desenvolvimento, garantindo que todas as ferramentas e estruturas de pastas estejam prontas para iniciar a codificação.

*   **Tarefa 0.1: Controle de Versão**
    *   [x] Iniciar um repositório Git (`git init`).
    *   [x] Criar um arquivo `.gitignore` adequado para projetos Python e Node.js.
    *   [x] Realizar o primeiro commit com a documentação (`README.md` e `PLANO_DESENVOLVIMENTO.md`).

*   **Tarefa 0.2: Estrutura de Pastas**
    *   [x] Criar a estrutura principal do monorepo:
        ```
        /ia-and-data
        ├── backend/         # Projeto FastAPI
        ├── frontend/        # Projeto Next.js
        └── etl/             # Scripts de Extração, Transformação e Carga
        ```

*   **Tarefa 0.3: Ambiente de Desenvolvimento**
    *   [ ] **Backend:** Configurar um ambiente virtual Python (`python -m venv venv`) dentro da pasta `backend`.
    *   [ ] **Frontend:** Iniciar o projeto Next.js com TailwindCSS (`npx create-next-app@latest`) dentro da pasta `frontend`.

---

## Fase 1: Camada de Dados (ETL e Supabase)

O foco aqui é estabelecer a fundação de dados do projeto: coletar, limpar e armazenar as informações financeiras no Supabase.

*   **Tarefa 1.1: Configuração do Supabase**
    *   [x] Criar um novo projeto na plataforma Supabase.
    *   [x] Usando o editor de tabelas do Supabase, criar a tabela `acoes_historico` com as colunas necessárias (ex: `ticker`, `date`, `open`, `high`, `low`, `close`, `volume`).
    *   [x] Salvar as credenciais de acesso (URL e `anon_key`) de forma segura (ex: arquivo `.env`).

*   **Tarefa 1.2: Script de Extração (E)**
    *   [x] Dentro da pasta `etl`, criar o script `extract.py`.
    *   [x] Usar a biblioteca `yfinance` para baixar dados históricos de um ticker de teste (ex: `PETR4.SA`).
    *   [x] O script deve retornar um DataFrame do Pandas.

*   **Tarefa 1.3: Script de Transformação (T)**
    *   [x] Criar o script `transform.py`.
    *   [x] Implementar funções para limpar os dados recebidos do `extract.py`:
        *   Normalizar nomes de colunas (letras minúsculas).
        *   Verificar e tratar dados faltantes.
        *   Ajustar tipos de dados (ex: converter data para formato ISO).

*   **Tarefa 1.4: Script de Carga (L)**
    *   [x] Criar o script `load.py`.
    *   [x] Instalar a biblioteca `supabase-py`.
    *   [x] Implementar uma função que recebe o DataFrame transformado e o insere na tabela `acoes_historico` do Supabase.

*   **Tarefa 1.5: Orquestrador do ETL**
    *   [x] Criar um arquivo `main_etl.py` que importe e execute as funções de `extract`, `transform` e `load` em sequência.
    *   [x] O objetivo é rodar um único comando para popular o banco de dados com os dados de um ativo.

---

## Fase 2: Backend (API com FastAPI)

Com os dados no lugar, o próximo passo é criar uma API que possa servi-los para qualquer cliente (nosso frontend).

*   **Tarefa 2.1: Configuração do FastAPI**
    *   [ ] Dentro da pasta `backend`, criar o arquivo `main.py`.
    *   [ ] Instalar as dependências: `fastapi`, `uvicorn`, `python-dotenv`, `supabase-py`.
    *   [ ] Configurar um servidor básico do FastAPI.

*   **Tarefa 2.2: Endpoint de Consulta Direta**
    *   [ ] Criar um endpoint `GET /api/v1/acoes/{ticker}`.
    *   [ ] Este endpoint deve se conectar ao Supabase e retornar os dados históricos para o `ticker` especificado.
    *   [ ] Servirá como uma base antes da integração com a IA.

---

## Fase 3: Frontend (Interface com Next.js)

Agora, vamos construir a interface onde o usuário irá interagir com o sistema.

*   **Tarefa 3.1: Componentes da UI**
    *   [ ] Criar um componente de input para o usuário digitar a pergunta.
    *   [ ] Criar uma área de exibição para a resposta em texto.
    *   [ ] (Opcional no MVP) Criar um placeholder para o gráfico.

*   **Tarefa 3.2: Integração com a API**
    *   [ ] Implementar a lógica para chamar o endpoint `GET /api/v1/acoes/{ticker}` do backend.
    *   [ ] Exibir os dados recebidos na tela de forma formatada.

---

## Fase 4: Integração da Inteligência Artificial (LangChain)

Esta é a fase central, onde transformamos a consulta de dados em uma conversa em linguagem natural.

*   **Tarefa 4.1: Configuração do LangChain no Backend**
    *   [ ] Adicionar `langchain`, `langchain-openai` e `openai` às dependências do backend.
    *   [ ] Configurar a chave da API da OpenAI de forma segura (via `.env`).

*   **Tarefa 4.2: Novo Endpoint de IA**
    *   [ ] Criar um endpoint `POST /api/v1/query`.
    *   [ ] Este endpoint receberá uma pergunta em linguagem natural no corpo da requisição (ex: `{"question": "Qual foi o preço médio da PETR4 em 2020?"}`).

*   **Tarefa 4.3: Desenvolvimento do Agente (Agent)**
    *   [ ] Criar um "agente" LangChain que usa um LLM (GPT-3.5/4).
    *   [ ] Criar uma "ferramenta" (tool) para o agente: uma função Python que sabe como consultar os dados no Supabase.
    *   [ ] O agente irá interpretar a pergunta do usuário, decidir qual ferramenta usar (a de consulta ao banco), executar a consulta e obter os dados brutos.

*   **Tarefa 4.4: Geração da Resposta Final**
    *   [ ] O agente usará o LLM novamente para transformar os dados brutos em uma resposta textual, amigável e completa.
    *   [ ] O endpoint `/api/v1/query` retornará essa resposta final.

---

## Fase 5: Finalização e Deploy

A última etapa é conectar todas as partes e disponibilizar o MVP online.

*   **Tarefa 5.1: Conectar Frontend à IA**
    *   [ ] Modificar o frontend para chamar o endpoint `POST /api/v1/query` em vez do endpoint antigo.
    *   [ ] Exibir a resposta em linguagem natural na interface.

*   **Tarefa 5.2: Deploy**
    *   [ ] **Frontend:** Fazer deploy do projeto Next.js na Vercel.
    *   [ ] **Backend:** Fazer deploy do projeto FastAPI no Railway ou Render.
    *   [ ] **Banco de Dados:** O Supabase já está na nuvem.
    *   [ ] Configurar as variáveis de ambiente em todas as plataformas (URL do backend no frontend, chaves de API, etc.).
