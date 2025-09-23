import os
import re
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from langchain_openai import ChatOpenAI
from langchain.agents import tool, AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from datetime import datetime, timedelta
import pytz

# --- 1. Importar a configuração centralizada ---
from .config import supabase

# --- 2. Definição das Ferramentas (Tools) ---
@tool
def get_stock_data(ticker: str, start_date: str | None = None, end_date: str | None = None):
    """
    Busca dados históricos de uma ação (OHLCV) no banco de dados.
    Pode filtrar por um período específico usando start_date e end_date (formato: 'AAAA-MM-DD').
    Retorna também o 'volume_financeiro' (Preço de Fechamento * Volume).
    Use esta ferramenta para perguntas sobre preços, volumes ou performance de ações em datas específicas ou intervalos.
    O ticker deve ser o código da ação na bolsa brasileira, como 'PETR.SA'.
    """
    print(f"🤖 Ferramenta 'get_stock_data' chamada com ticker: {ticker}, start_date: {start_date}, end_date: {end_date}")

    # Adiciona robustez para limpar a entrada do ticker
    match = re.search(r"([A-Z0-9]+\.SA)", str(ticker).upper())
    if match:
        cleaned_ticker = match.group(1)
    else:
        cleaned_ticker = str(ticker)
    
    print(f"✨ Ticker limpo para a consulta: {cleaned_ticker}")
    
    try:
        query = supabase.table('acoes_historico').select("date, open, high, low, close, volume").eq('ticker', cleaned_ticker)

        # Aplica os filtros de data se forem fornecidos
        if start_date:
            query = query.gte('date', start_date)
        if end_date:
            query = query.lte('date', end_date)

        # Ordena por data e executa a consulta
        response = query.order('date', desc=True).limit(252).execute() # Limita a 1 ano de dados por consulta

        if response.data:
            # Usa pandas para calcular o volume financeiro
            df = pd.DataFrame(response.data)
            df['volume_financeiro'] = df['close'] * df['volume']
            # Retorna como uma lista de dicionários
            return df.to_dict(orient='records')
        else:
            return f"Nenhum dado encontrado para o ticker {cleaned_ticker} no período especificado."
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


@tool
def get_market_summary(date: str):
    """
    Calcula o volume financeiro total negociado em um dia específico, somando o volume de todas as ações disponíveis no banco de dados.
    Use esta ferramenta quando a pergunta for sobre o mercado em geral, como 'volume total da bolsa' ou 'volume negociado na B3' em uma data específica.
    A data deve estar no formato 'AAAA-MM-DD'.
    """
    print(f"🤖 Ferramenta 'get_market_summary' chamada para a data: {date}")

    try:
        # Busca todas as ações para a data especificada
        response = supabase.table('acoes_historico').select("close, volume") \
            .eq('date', date) \
            .execute()

        if not response.data:
            return f"Nenhum dado de mercado encontrado para a data {date}."

        # Usa pandas para os cálculos
        df = pd.DataFrame(response.data)
        
        # Garante que não há valores nulos que possam quebrar o cálculo
        df.dropna(subset=['close', 'volume'], inplace=True)

        if df.empty:
            return f"Os dados para {date} estão incompletos e não foi possível calcular o volume."

        # Calcula o volume financeiro total
        total_volume_financeiro = (df['close'] * df['volume']).sum()
        
        # Formata o resultado para melhor legibilidade
        formatted_volume = f"R$ {total_volume_financeiro:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        return {
            "date": date,
            "total_volume_financeiro": formatted_volume,
            "tickers_considerados": len(df),
            "analysis": f"O volume financeiro total negociado em {date}, com base em {len(df)} tickers, foi de {formatted_volume}."
        }
        
    except Exception as e:
        return f"Ocorreu um erro ao calcular o resumo do mercado: {e}"


@tool
def get_top_stocks_by_criteria(start_date: str, end_date: str, criteria: str = 'volume_financeiro', top_n: int = 5):
    """
    Analisa todas as ações em um período e retorna um ranking das 'top_n' melhores com base em um critério.
    Use esta ferramenta para perguntas comparativas ou de ranking, como 'qual ação teve o maior volume' ou 'quais as 5 ações com maior volume financeiro'.
    O critério pode ser 'volume_financeiro' ou 'volume'.
    As datas devem estar no formato 'AAAA-MM-DD'.
    """
    print(f"🤖 Ferramenta 'get_top_stocks_by_criteria' chamada com: start_date={start_date}, end_date={end_date}, criteria={criteria}, top_n={top_n}")

    if criteria not in ['volume_financeiro', 'volume']:
        return f"Critério '{criteria}' inválido. Use 'volume_financeiro' ou 'volume'."

    try:
        # Busca dados de todas as ações no período
        response = supabase.table('acoes_historico') \
            .select("ticker, close, volume") \
            .gte('date', start_date) \
            .lte('date', end_date) \
            .execute()

        if not response.data:
            return f"Nenhum dado encontrado no período de {start_date} a {end_date}."

        df = pd.DataFrame(response.data)
        df.dropna(subset=['close', 'volume'], inplace=True)

        if df.empty:
            return "Os dados para o período estão incompletos."

        # Calcula o critério para cada registro
        if criteria == 'volume_financeiro':
            df['criteria_value'] = df['close'] * df['volume']
        else: # 'volume'
            df['criteria_value'] = df['volume']

        # Agrupa por ticker, soma o critério e ordena
        ranking = df.groupby('ticker')['criteria_value'].sum().sort_values(ascending=False).head(top_n)

        # Formata o resultado para a IA
        ranking_list = []
        for ticker, value in ranking.items():
            formatted_value = f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") if criteria == 'volume_financeiro' else f"{int(value):,}".replace(",",".")
            ranking_list.append(f"{ticker}: {formatted_value}")

        return {
            "period": f"{start_date} a {end_date}",
            "criteria": criteria,
            "ranking": ranking_list,
            "analysis": f"O ranking das {top_n} ações com maior '{criteria}' entre {start_date} e {end_date} é: {'; '.join(ranking_list)}."
        }

    except Exception as e:
        return f"Ocorreu um erro ao gerar o ranking: {e}"


@tool
def get_current_datetime() -> str:
    """Retorna a data e hora atuais no fuso horário de São Paulo (America/Sao_Paulo), incluindo o dia da semana. Formato: 'YYYY-MM-DD HH:MM:SS (Dia da Semana)'."""
    sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
    now_sp = datetime.now(sao_paulo_tz)
    # Mapeia os dias da semana em inglês para português
    dias_semana = {
        'Monday': 'Segunda-feira',
        'Tuesday': 'Terça-feira',
        'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira',
        'Friday': 'Sexta-feira',
        'Saturday': 'Sábado',
        'Sunday': 'Domingo'
    }
    dia_semana_en = now_sp.strftime('%A')
    dia_semana_pt = dias_semana[dia_semana_en]
    
    return f"{now_sp.strftime('%Y-%m-%d %H:%M:%S')} ({dia_semana_pt})"


# --- 3. Montagem do Agente ---
def create_agent_executor():
    """
    Cria e configura o agente LangChain com as ferramentas e o LLM.
    """
    print("🧠 Inicializando o agente...")
    
    tools = [get_stock_data, get_volatility_cone, get_market_summary, get_top_stocks_by_criteria, get_current_datetime]
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    
    # 1. Escolha do LLM (gpt-4o-mini é uma excelente escolha para performance/custo)
    # 2. Lista de ferramentas que o agente pode usar
    # 3. Definição do Prompt (instruções para o agente)
    # Injetando a data e hora atuais diretamente no prompt do sistema
    sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
    now_sp = datetime.now(sao_paulo_tz)
    dias_semana = {
        'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    dia_semana_en = now_sp.strftime('%A')
    dia_semana_pt = dias_semana[dia_semana_en]
    current_time_str = f"{now_sp.strftime('%Y-%m-%d %H:%M:%S')} ({dia_semana_pt})"
    
    system_prompt = f"""Você é um assistente especialista em dados financeiros do mercado brasileiro.
A data e hora atuais são: {current_time_str}. Use essa informação como referência para qualquer pergunta sobre datas relativas (como 'hoje' ou 'ontem').

Seu objetivo é ser preciso и prestativo.
- Sempre que uma ferramenta retornar "Nenhum dado encontrado" para uma data específica, sua primeira hipótese deve ser que a data caiu em um fim de semana ou feriado.
- Nesse caso, informe ao usuário sobre essa possibilidade e, se possível, ofereça buscar pelo dia útil anterior ou seguinte.
- Se a pergunta do usuário for um cumprimento ou uma conversa fiada, responda educadamente sem usar ferramentas."""

    # Prompt otimizado para agentes de conversação com ferramentas
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
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
