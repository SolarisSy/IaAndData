import yfinance as yf
import pandas as pd
import re
import numpy as np # Import numpy para lidar com 'nan'

def get_intraday_data_with_vwap(ticker: str):
    """
    Busca dados intraday (intervalo de 1 minuto) para um ticker e calcula o VWAP.
    
    Args:
        ticker (str): O código do ativo (ex: "PETR4.SA").
        
    Returns:
        dict: Um dicionário contendo os dados do gráfico ou uma mensagem de erro.
    """
    print(f"Buscando dados intraday para o ticker: {ticker}")

    match = re.search(r"([A-Z0-9]+\.SA)", str(ticker).upper())
    if not match:
        return {"error": f"Ticker inválido: {ticker}. O formato deve ser como 'PETR4.SA'."}
    cleaned_ticker = match.group(1)

    try:
        stock = yf.Ticker(cleaned_ticker)
        # Busca dados do dia atual ('1d') com intervalo de 1 minuto ('1m')
        hist = stock.history(period="1d", interval="1m")

        if hist.empty:
            return {"error": f"Não foram encontrados dados intraday para {cleaned_ticker}. O mercado pode estar fechado."}

        # Cálculo do VWAP (Volume Weighted Average Price)
        hist['Typical Price'] = (hist['High'] + hist['Low'] + hist['Close']) / 3
        hist['TP x Volume'] = hist['Typical Price'] * hist['Volume']
        hist['Cumulative TP x Volume'] = hist['TP x Volume'].cumsum()
        hist['Cumulative Volume'] = hist['Volume'].cumsum()
        hist['VWAP'] = hist['Cumulative TP x Volume'] / hist['Cumulative Volume']

        # --- CORREÇÃO: Limpar valores inválidos antes de enviar ---
        # Substitui qualquer 'nan' ou infinito por None, que é compatível com JSON (vira 'null')
        hist.replace([np.inf, -np.inf, np.nan], None, inplace=True)
        # Se algum 'None' permanecer após a limpeza, preenchemos com o valor anterior para não quebrar o gráfico
        hist.ffill(inplace=True)
        # E se o primeiro valor for None, preenchemos com o próximo
        hist.bfill(inplace=True)

        # Preparar dados para o frontend
        hist.reset_index(inplace=True)
        
        # Formatar 'Datetime' para string para evitar problemas de serialização JSON
        hist['Datetime'] = hist['Datetime'].dt.strftime('%H:%M')

        chart_data = {
            'labels': hist['Datetime'].tolist(),
            'price': hist['Close'].tolist(),
            'vwap': hist['VWAP'].tolist()
        }
        
        return chart_data

    except Exception as e:
        print(f"Erro ao buscar dados intraday: {e}")
        return {"error": f"Ocorreu um erro ao buscar os dados intraday: {e}"}

if __name__ == '__main__':
    # Teste rápido
    petr4_data = get_intraday_data_with_vwap("PETR4.SA")
    if 'error' not in petr4_data:
        print("Dados da PETR4 obtidos com sucesso:")
        print(f"Labels: {petr4_data['labels'][-5:]}")
        print(f"Preços: {petr4_data['price'][-5:]}")
        print(f"VWAP: {petr4_data['vwap'][-5:]}")
    else:
        print(petr4_data)

    vale3_data = get_intraday_data_with_vwap("VALE3.SA")
    if 'error' not in vale3_data:
        print("\nDados da VALE3 obtidos com sucesso:")
        print(f"Labels: {vale3_data['labels'][-5:]}")
        print(f"Preços: {vale3_data['price'][-5:]}")
        print(f"VWAP: {vale3_data['vwap'][-5:]}")
    else:
        print(vale3_data)
