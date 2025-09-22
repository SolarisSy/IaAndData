import os
import re
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from langchain_openai import ChatOpenAI
from langchain.agents import tool, AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage

# --- 1. Importar a configuração centralizada ---
from .config import supabase

# --- 2. Definição das Ferramentas (Tools) ---
@tool
def get_stock_data(ticker: str):
    """
    Busca os dados históricos de uma ação (OHLCV) no banco de dados.
    Use esta ferramenta quando precisar de informações sobre preços de ações, como preço de fechamento, abertura, máxima, mínima ou volume.
    O ticker deve ser o código da ação na bolsa brasileira, como 'PETR4.SA' ou 'VALE3.SA'.
    """
    print(f"🤖 Ferramenta 'get_stock_data' chamada com o ticker: {ticker}")
    
    # Adiciona robustez para limpar a entrada do ticker
    match = re.search(r"([A-Z0-9]+\.SA)", str(ticker).upper())
    if match:
        cleaned_ticker = match.group(1)
    else:
        cleaned_ticker = str(ticker)
    
    print(f"✨ Ticker limpo para a consulta: {cleaned_ticker}")
    
    try:
        response = supabase.table('acoes_historico').select("date, open, high, low, close, volume").eq('ticker', cleaned_ticker).order('date', desc=True).limit(100).execute() # Limita a 100 registros para não sobrecarregar
        if response.data:
            return response.data
        else:
            return f"Nenhum dado encontrado para o ticker {cleaned_ticker}."
    except Exception as e:
        return f"Ocorreu um erro ao buscar os dados: {e}"

@tool
def get_volatility_cone(ticker: str, days_to_predict: int = 30):
    """
    Calcula e projeta a volatilidade de uma ação para criar um "cone de incerteza" para o futuro.
    Use esta ferramenta quando o usuário pedir uma projeção, previsão, ou algo sobre a volatilidade futura de uma ação.
    O ticker deve ser o código da ação na bolsa brasileira, como 'PETR4.SA' ou 'VALE3.SA'.
    """
    print(f"🤖 Ferramenta 'get_volatility_cone' chamada para {ticker} com projeção de {days_to_predict} dias.")

    match = re.search(r"([A-Z0-9]+\.SA)", str(ticker).upper())
    if not match:
        return f"Ticker inválido: {ticker}. O formato deve ser como 'PETR4.SA'."
    cleaned_ticker = match.group(1)

    try:
        response = supabase.table('acoes_historico').select("date, close") \
            .eq('ticker', cleaned_ticker) \
            .order('date', desc=False) \
            .limit(252) \
            .execute()

        if not response.data or len(response.data) < 20:
            return f"Dados históricos insuficientes para calcular a volatilidade para {cleaned_ticker}. São necessários pelo menos 20 dias."

        df = pd.DataFrame(response.data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        df['log_return'] = np.log(df['close'] / df['close'].shift(1))
        
        annual_volatility = df['log_return'].std() * np.sqrt(252)
        
        X = np.arange(len(df)).reshape(-1, 1)
        y = df['close'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        last_date = df.index[-1]
        future_dates = pd.to_datetime([last_date + pd.DateOffset(days=i) for i in range(1, days_to_predict + 1)])
        future_X = np.arange(len(df), len(df) + days_to_predict).reshape(-1, 1)
        
        future_prices = model.predict(future_X)
        
        historical_data = df.reset_index()[['date', 'close']].to_dict(orient='records')

        cone_data = []
        for i in range(days_to_predict):
            days_ahead = i + 1
            std_dev = annual_volatility * np.sqrt(days_ahead / 252)
            price = future_prices[i]
            
            cone_data.append({
                'date': future_dates[i].strftime('%Y-%m-%d'),
                'predicted_price': price,
                'upper_bound_95': price * (1 + 1.96 * std_dev),
                'lower_bound_95': price * (1 - 1.96 * std_dev),
                'upper_bound_70': price * (1 + 1.04 * std_dev),
                'lower_bound_70': price * (1 - 1.04 * std_dev),
            })

        return {
            "historical": historical_data,
            "cone": cone_data,
            "analysis": f"A volatilidade anualizada calculada para {cleaned_ticker} é de {annual_volatility:.2%}. Com base na tendência linear, projetamos os preços para os próximos {days_to_predict} dias com bandas de confiança de 70% e 95%."
        }

    except Exception as e:
        return f"Ocorreu um erro ao calcular o cone de volatilidade: {e}"


# --- 3. Montagem do Agente ---
def create_agent_executor():
    """
    Cria e configura o agente LangChain com as ferramentas e o LLM.
    """
    print("🧠 Inicializando o agente...")
    
    tools = [get_stock_data, get_volatility_cone]
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    # Prompt otimizado para agentes de conversação com ferramentas
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Você é um assistente prestativo especialista em dados financeiros. Se a pergunta do usuário for um cumprimento ou uma conversa fiada, responda educadamente sem usar ferramentas."),
        MessagesPlaceholder(variable_name="chat_history"), # <-- Importante para a memória
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    agent_executor = AgentExecutor(
        agent=agent, 
        tools=tools, 
        verbose=True,
    )
    
    print("✅ Agente pronto para uso.")
    return agent_executor

# --- 4. Função Principal de Consulta com Gerenciamento de Histórico ---
agent_executor = create_agent_executor()
chat_history_per_session = {} # Usaremos um dicionário para simular sessões de usuário

def query_agent(question: str, session_id: str = "default_user"):
    """
    Executa uma consulta contra o agente, mantendo um histórico da conversa.
    """
    print(f"❓ Nova pergunta para o agente (Sessão: {session_id}): {question}")
    
    # Recupera o histórico da sessão atual ou cria um novo
    chat_history = chat_history_per_session.get(session_id, [])

    response = agent_executor.invoke({
        "input": question,
        "chat_history": chat_history
    })
    
    # Atualiza o histórico com a pergunta atual e a resposta da IA
    chat_history.extend([
        HumanMessage(content=question),
        AIMessage(content=response['output']),
    ])
    chat_history_per_session[session_id] = chat_history

    if isinstance(response.get('output'), dict) and ('historical' in response['output'] and 'cone' in response['output']):
        return response['output']
        
    return response['output']
