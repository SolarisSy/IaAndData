import pandas as pd
import pandas_ta as ta
from langchain.agents import tool
from typing import List

# Importa a ferramenta de busca de dados para ser reutilizada aqui
from .data_retrieval_tools import get_stock_data

# --- Ferramentas de Análise Técnica e Comparativa ---

@tool
def get_asset_analytics(ticker: str, rsi_period: int = 14, sma_period: int = 21) -> str:
    """
    Calcula indicadores de análise técnica para uma única ação, como o Índice de Força Relativa (RSI) e a Média Móvel Simples (SMA).
    Use esta ferramenta para responder perguntas sobre o estado técnico de um ativo, como "PETR4 está sobrecomprada?" ou "Qual a média móvel de 21 dias da VALE3?".
    Um RSI acima de 70 geralmente indica que um ativo está 'sobrecomprado'. Um RSI abaixo de 30 indica 'sobrevendido'.
    """
    print(f"🤖 Ferramenta 'get_asset_analytics' chamada para {ticker} com RSI({rsi_period}) e SMA({sma_period}).")

    # 1. Obter os dados usando a função da ferramenta existente diretamente
    historical_data = get_stock_data.func(ticker=ticker)
    
    if isinstance(historical_data, str) and "Nenhum dado encontrado" in historical_data:
        return f"Não foi possível calcular os indicadores para {ticker} porque não foram encontrados dados históricos."

    if not isinstance(historical_data, list) or len(historical_data) < sma_period:
         return f"Dados históricos insuficientes para {ticker} para calcular a SMA de {sma_period} dias."

    # 2. Converter para DataFrame do Pandas e preparar os dados
    df = pd.DataFrame(historical_data)
    df = df.sort_values(by='date', ascending=True) # Garante a ordem cronológica
    df.set_index('date', inplace=True)
    
    # 3. Calcular os indicadores usando pandas_ta
    df.ta.rsi(length=rsi_period, append=True)
    df.ta.sma(length=sma_period, append=True)
    
    # 4. Obter os valores mais recentes
    latest_rsi = df[f'RSI_{rsi_period}'].iloc[-1]
    latest_sma = df[f'SMA_{sma_period}'].iloc[-1]
    latest_close = df['close'].iloc[-1]
    
    # 5. Gerar uma análise textual
    rsi_interpretation = "neutro"
    if latest_rsi > 70:
        rsi_interpretation = f"sobrecomprado ({latest_rsi:.2f}), indicando uma possível reversão de tendência para baixa."
    elif latest_rsi < 30:
        rsi_interpretation = f"sobrevendido ({latest_rsi:.2f}), indicando uma possível reversão de tendência para alta."
    else:
        rsi_interpretation = f"neutro ({latest_rsi:.2f})."
        
    sma_interpretation = "acima" if latest_close > latest_sma else "abaixo"

    # Constrói a resposta em Markdown de forma mais limpa
    analysis_parts = [
        f"Análise técnica para **{ticker}**:",
        f"- **Preço de Fechamento Mais Recente:** R$ {latest_close:,.2f}",
        f"- **Média Móvel Simples ({sma_period} dias):** R$ {latest_sma:,.2f}. O preço atual está {sma_interpretation} da média.",
        f"- **Índice de Força Relativa (RSI, {rsi_period} dias):** O ativo está em território {rsi_interpretation}"
    ]
    analysis = "\n".join(analysis_parts)
    
    return analysis

@tool
def compare_assets(tickers: List[str], start_date: str, end_date: str) -> str:
    """
    Compara a performance, volatilidade e correlação de duas ou mais ações em um determinado período.
    Use esta ferramenta para perguntas comparativas, como "Quem performou melhor entre PETR4 e VALE3 no último ano?" ou "Qual a correlação entre MGLU3 e ABEV3?".
    """
    print(f"🤖 Ferramenta 'compare_assets' chamada para {tickers} entre {start_date} e {end_date}.")
    
    all_data = {}
    for ticker in tickers:
        # Chama a função interna da ferramenta diretamente
        data = get_stock_data.func(ticker=ticker, start_date=start_date, end_date=end_date)
        if isinstance(data, list) and data:
            df = pd.DataFrame(data)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            all_data[ticker] = df['close']
    
    if len(all_data) < 2:
        return "Não foi possível realizar a comparação pois dados suficientes foram encontrados para menos de dois dos tickers solicitados."

    # Cria um único DataFrame com o preço de fechamento de todos os ativos
    comparison_df = pd.DataFrame(all_data).sort_index()
    comparison_df.dropna(inplace=True) # Garante que só temos datas onde todos os ativos negociaram

    # 1. Cálculo de Performance
    performance = (comparison_df.iloc[-1] / comparison_df.iloc[0]) - 1
    
    # 2. Cálculo de Volatilidade (desvio padrão dos retornos diários)
    returns = comparison_df.pct_change()
    volatility = returns.std() * (252**0.5) # Volatilidade anualizada

    # 3. Cálculo de Correlação
    correlation_matrix = returns.corr()

    # 4. Montar a análise final
    analysis = f"Análise Comparativa entre {', '.join(tickers)} de {start_date} a {end_date}:\n\n"
    
    analysis += "**Performance no Período:**\n"
    for ticker, perf in performance.items():
        analysis += f"- {ticker}: {perf:+.2%}\n"
    
    analysis += "\n**Volatilidade Anualizada:**\n"
    for ticker, vol in volatility.items():
        analysis += f"- {ticker}: {vol:.2%}\n"
        
    analysis += "\n**Matriz de Correlação:**\n"
    analysis += f"```{correlation_matrix.to_string(float_format='{:.2f}'.format)}```\n\n"
    
    winner = performance.idxmax()
    analysis += f"**Conclusão:** No período analisado, **{winner}** teve a melhor performance com um retorno de **{performance[winner]:+.2%}**."
    
    return analysis
