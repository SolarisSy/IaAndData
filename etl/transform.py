import pandas as pd

def transform_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e padroniza o DataFrame de dados históricos de ações.

    Args:
        df (pd.DataFrame): DataFrame bruto extraído do yfinance.

    Returns:
        pd.DataFrame: DataFrame transformado e pronto para ser carregado.
    """
    if df.empty:
        return pd.DataFrame()

    # 1. A coluna de data já vem como índice, vamos transformá-la em uma coluna
    df_transformed = df.reset_index()

    # 2. Renomear colunas para o padrão do banco (minúsculas)
    df_transformed.rename(columns={
        'Date': 'date',
        'Open': 'open',
        'High': 'high',
        'Low': 'low',
        'Close': 'close',
        'Volume': 'volume'
    }, inplace=True)

    # 3. Selecionar apenas as colunas que vamos inserir no banco
    # Removemos 'Dividends' e 'Stock Splits' que não estão na nossa tabela
    columns_to_keep = ['date', 'open', 'high', 'low', 'close', 'volume', 'ticker']
    df_transformed = df_transformed[columns_to_keep]

    # 4. Formatar a data para o formato YYYY-MM-DD
    df_transformed['date'] = df_transformed['date'].dt.strftime('%Y-%m-%d')
    
    # 5. Remover linhas com dados nulos, se houver
    df_transformed.dropna(inplace=True)

    return df_transformed

if __name__ == '__main__':
    # Exemplo de uso para teste
    from extract import extract_data

    # Extrai dados brutos
    petr4_raw_data = extract_data("PETR4.SA")
    
    if not petr4_raw_data.empty:
        # Transforma os dados
        petr4_transformed_data = transform_data(petr4_raw_data)
        print("Dados da PETR4 transformados com sucesso:")
        print(petr4_transformed_data.head())
        print("\nTipos de dados das colunas:")
        print(petr4_transformed_data.dtypes)
