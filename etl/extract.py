import yfinance as yf
import pandas as pd

def extract_data(ticker: str) -> pd.DataFrame:
    """
    Extrai o histórico de dados de um ticker usando a biblioteca yfinance.

    Args:
        ticker (str): O código do ativo (ex: "PETR4.SA").

    Returns:
        pd.DataFrame: DataFrame do Pandas com os dados históricos.
                       Retorna um DataFrame vazio se o ticker for inválido.
    """
    stock = yf.Ticker(ticker)
    # Baixa o histórico de dados completo
    hist = stock.history(period="max")
    
    if hist.empty:
        print(f"Não foram encontrados dados para o ticker: {ticker}")
        return pd.DataFrame()
        
    # Adiciona o ticker como uma coluna para referência futura
    hist['ticker'] = ticker
    
    return hist

if __name__ == '__main__':
    # Exemplo de uso para teste
    petr4_data = extract_data("PETR4.SA")
    if not petr4_data.empty:
        print("Dados da PETR4 extraídos com sucesso:")
        print(petr4_data.head())

    vale3_data = extract_data("VALE3.SA")
    if not vale3_data.empty:
        print("\nDados da VALE3 extraídos com sucesso:")
        print(vale3_data.head())
        
    # Teste com ticker inválido
    invalid_data = extract_data("INEXISTENTE.SA")
