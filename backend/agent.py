import os
import re
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime
import pytz

# --- 1. Importar as ferramentas da nova estrutura modular ---
from .tools.data_retrieval_tools import (
    get_stock_data,
    get_volatility_cone,
    get_market_summary,
    get_top_stocks_by_criteria,
    get_current_datetime,
    list_available_tickers
)
from .tools.analysis_tools import (
    get_asset_analytics,
    compare_assets
)
from .tools.notification_tools import (
    notify_developer_of_missing_tool
)

# --- 2. Montagem do Agente ---
def create_agent_executor():
    """
    Cria e configura o agente LangChain com o novo cérebro analítico
    e todas as ferramentas disponíveis.
    """
    print("🧠 Inicializando o agente com capacidades analíticas avançadas...")
    
    # Agrega todas as ferramentas importadas em uma única lista
    all_tools = [
        get_stock_data,
        get_volatility_cone,
        get_market_summary,
        get_top_stocks_by_criteria,
        get_current_datetime,
        list_available_tickers,
        get_asset_analytics,
        compare_assets,
        notify_developer_of_missing_tool
    ]
    
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # Injeta a data/hora atual para consciência temporal
    sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
    now_sp = datetime.now(sao_paulo_tz)
    dias_semana = {
        'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    dia_semana_en = now_sp.strftime('%A')
    dia_semana_pt = dias_semana[dia_semana_en]
    current_time_str = f"{now_sp.strftime('%Y-%m-%d %H:%M:%S')} ({dia_semana_pt})"
    
    # --- O Novo Cérebro do Agente (System Prompt) ---
    system_prompt = f"""Você é um assistente Sênior de análise de dados da B3. Seu objetivo é decompor perguntas complexas, usar suas ferramentas em sequência e sintetizar os resultados para gerar insights.

# Persona e Escopo:
- Sua identidade: Analista de dados Sênior.
- Seu conhecimento é estritamente baseado nos dados retornados por suas ferramentas.
- A data e hora atuais são: {current_time_str}. Use essa informação como referência para datas relativas.

# Diretriz de Eficiência:
- **NÃO FAÇA CHAMADAS DUPLICADAS.** Antes de usar uma ferramenta, verifique seu histórico e o resultado da chamada anterior. Se você já tem a informação, use-a. Não chame a mesma ferramenta com os mesmos parâmetros duas vezes.

# Raciocínio e Plano de Ação (Chain of Thought):
1.  **Decomponha a Pergunta:** Ao receber uma consulta do usuário, primeiro entenda o objetivo final. Se a pergunta for complexa (ex: "Compare X e Y", "X está sobrecomprado?"), crie um plano mental de quais ferramentas usar em sequência.
2.  **Execute o Plano com Eficiência:** Chame as ferramentas necessárias, UMA ÚNICA VEZ, para coletar todos os dados.
3.  **Sintetize o Insight:** Não apenas retorne os dados brutos das ferramentas. Combine os resultados para formular uma conclusão coesa e bem fundamentada. Responda à pergunta original do usuário com um resumo analítico.

# Exemplo de Raciocínio Eficiente:
- **Pergunta do Usuário:** "A PETR4.SA parece sobrecomprada em comparação com sua média móvel?"
- **Seu Plano Mental:**
    1. "Preciso de indicadores técnicos (RSI e Média Móvel) da PETR4.SA. A ferramenta `get_asset_analytics` fornece AMBOS em uma única chamada."
    2. "Vou chamar `get_asset_analytics` UMA VEZ para obter todos os dados necessários."
    3. "Com o resultado, vou analisar o valor do RSI e comparar o preço com a média móvel para dar uma resposta completa e fundamentada."

# Diretriz de Escalada (Feedback Loop):
- Se, durante o planejamento, você concluir que NENHUMA combinação de suas ferramentas atuais pode responder à pergunta, use a ferramenta `notify_developer_of_missing_tool`.
- Informe ao usuário que a análise solicitada ainda não é possível, mas que o time de desenvolvimento foi notificado para criar essa nova capacidade.

# Limites:
- Você continua NÃO PODENDO prever o futuro ou dar conselhos de investimento. Sua análise é estritamente quantitativa e baseada em dados históricos.
- Se o usuário pedir uma opinião ou previsão, recuse educadamente e sugira uma pergunta baseada em dados que você PODE responder.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history"),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, all_tools, prompt)
    
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=all_tools, 
        verbose=True,
    )
    
    print("✅ Agente Sênior pronto para uso.")
    return agent_executor

# --- 3. Função Principal de Consulta com Gerenciamento de Histórico ---
agent_executor = create_agent_executor()
chat_history_per_session = {}

def query_agent(question: str, session_id: str = "default_user"):
    """
    Executa uma consulta contra o agente, mantendo um histórico da conversa.
    """
    print(f"❓ Nova pergunta para o agente (Sessão: {session_id}): {question}")
    
    chat_history = chat_history_per_session.get(session_id, [])

    response = agent_executor.invoke({
        "input": question,
        "chat_history": chat_history
    })
    
    chat_history.extend([
        HumanMessage(content=question),
        AIMessage(content=response['output']),
    ])
    chat_history_per_session[session_id] = chat_history

    # Retorna a resposta final, que pode ser um texto ou um JSON para gráficos
    return response['output']
