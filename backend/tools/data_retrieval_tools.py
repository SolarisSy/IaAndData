import re
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from langchain.agents import tool
from datetime import datetime
import pytz

# --- Importar a configuração centralizada ---
# Esta importação assume que a estrutura de pastas permite a referência relativa.
# Se executado como um script autônomo, pode precisar de ajuste no sys.path.
from ..config import supabase


# --- Ferramentas de Busca e Recuperação de Dados ---

@tool
def get_stock_data(ticker: str, start_date: str | None = None, end_date: str | None = None):
    """
    Busca dados históricos de uma ação (OHLCV) no banco de dados.
    Pode filtrar por um período específico usando start_date e end_date (formato: 'AAAA-MM-DD').
    Se nenhuma data for fornecida, busca os dados mais recentes disponíveis.
    Se as datas fornecidas não retornarem dados, a função tentará encontrar o pregão mais recente disponível.
    Retorna também o 'volume_financeiro' (Preço de Fechamento * Volume).
    Use esta ferramenta para perguntas sobre preços, volumes ou performance de ações.
    O ticker deve ser o código da ação na bolsa brasileira, como 'PETR4.SA'.
    """
    print(f"🤖 Ferramenta 'get_stock_data' chamada com ticker: {ticker}, start_date: {start_date}, end_date: {end_date}")

    match = re.search(r"([A-Z0-9]+\.SA)", str(ticker).upper())
    cleaned_ticker = match.group(1) if match else str(ticker)
    
    print(f"✨ Ticker limpo para a consulta: {cleaned_ticker}")
    
    try:
        query = supabase.table('acoes_historico').select("date, open, high, low, close, volume").eq('ticker', cleaned_ticker)

        # Lógica de busca aprimorada
        if start_date and end_date:
            query = query.gte('date', start_date).lte('date', end_date)
        
        response = query.order('date', desc=True).limit(252).execute()

        # Se nenhum dado for encontrado para o período específico, busque o mais recente
        if not response.data:
            print(f"⚠️ Nenhum dado para '{cleaned_ticker}' no período. Buscando o pregão mais recente...")
            fallback_response = supabase.table('acoes_historico') \
                .select("date, open, high, low, close, volume") \
                .eq('ticker', cleaned_ticker) \
                .order('date', desc=True) \
                .limit(1) \
                .execute()
            
            if not fallback_response.data:
                return f"Nenhum dado encontrado para o ticker {cleaned_ticker}."
            
            response = fallback_response
            print(f"✅ Encontrado dado mais recente em: {response.data[0]['date']}")


        df = pd.DataFrame(response.data)
        df['volume_financeiro'] = df['close'] * df['volume']
        return df.to_dict(orient='records')
        
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
    Calcula o volume financeiro total negociado em um dia específico.
    Se não encontrar dados para a data fornecida, busca automaticamente o último dia com dados disponíveis e informa o usuário.
    Use para perguntas sobre o mercado geral, como 'volume total da bolsa'. Formato da data: 'AAAA-MM-DD'.
    """
    print(f"🤖 Ferramenta 'get_market_summary' chamada para a data: {date}")

    try:
        response = supabase.table('acoes_historico').select("date, close, volume").eq('date', date).execute()

        # Lógica de fallback se a data específica não retornar dados
        if not response.data:
            print(f"⚠️ Nenhum dado de mercado encontrado para {date}. Buscando a data mais recente...")
            latest_date_response = supabase.table('acoes_historico').select("date").order('date', desc=True).limit(1).execute()
            
            if not latest_date_response.data:
                return "Não há nenhum dado histórico no banco de dados."
            
            latest_date = latest_date_response.data[0]['date']
            print(f"✅ Última data com dados encontrada: {latest_date}")
            
            response = supabase.table('acoes_historico').select("date, close, volume").eq('date', latest_date).execute()
            date = latest_date # Atualiza a data para a que foi realmente usada

        df = pd.DataFrame(response.data)
        df.dropna(subset=['close', 'volume'], inplace=True)

        if df.empty:
            return f"Os dados para {date} estão incompletos e não foi possível calcular o volume."

        total_volume_financeiro = (df['close'] * df['volume']).sum()
        formatted_volume = f"R$ {total_volume_financeiro:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        analysis_text = f"O volume financeiro total negociado em {date}, com base em {len(df)} tickers, foi de {formatted_volume}."
        
        # Adiciona um aviso se a data usada for diferente da solicitada
        if date != locals().get('original_date', date):
             analysis_text = f"Não foram encontrados dados para a data solicitada. O resumo do último pregão disponível ({date}) é o seguinte: " + analysis_text

        return {
            "date": date,
            "total_volume_financeiro": formatted_volume,
            "tickers_considerados": len(df),
            "analysis": analysis_text
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

        if criteria == 'volume_financeiro':
            df['criteria_value'] = df['close'] * df['volume']
        else:
            df['criteria_value'] = df['volume']

        ranking = df.groupby('ticker')['criteria_value'].sum().sort_values(ascending=False).head(top_n)

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
    """Retorna a data e hora atuais no fuso horário de São Paulo (America/Sao_Paulo), incluindo o dia da semana."""
    sao_paulo_tz = pytz.timezone("America/Sao_Paulo")
    now_sp = datetime.now(sao_paulo_tz)
    dias_semana = {
        'Monday': 'Segunda-feira', 'Tuesday': 'Terça-feira', 'Wednesday': 'Quarta-feira',
        'Thursday': 'Quinta-feira', 'Friday': 'Sexta-feira', 'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    dia_semana_en = now_sp.strftime('%A')
    dia_semana_pt = dias_semana[dia_semana_en]
    
    return f"{now_sp.strftime('%Y-%m-%d %H:%M:%S')} ({dia_semana_pt})"


@tool
def list_available_tickers() -> str:
    """
    Retorna uma lista completa de todos os tickers de ações para os quais há dados históricos disponíveis.
    Use esta ferramenta sempre que o usuário perguntar quais ações você conhece, sobre quais empresas tem dados, ou qual a abrangência dos dados.
    """
    print("🤖 Ferramenta 'list_available_tickers' chamada.")
    try:
        response = supabase.table('acoes_historico').select('ticker').execute()

        if not response.data:
            return "Não foram encontrados tickers de ações no banco de dados."
            
        tickers = sorted(list(set(item['ticker'] for item in response.data)))
        
        return f"Tenho acesso aos dados históricos dos seguintes {len(tickers)} tickers: {', '.join(tickers)}."

    except Exception as e:
        print(f"🔥 Erro ao listar tickers: {e}")
        return "Ocorreu um erro ao tentar buscar a lista de tickers disponíveis."
