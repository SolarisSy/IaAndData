from extract import extract_data
from transform import transform_data
from load import load_data

def run_etl_pipeline(tickers: list):
    """
    Executa o pipeline de ETL (Extract, Transform, Load) para uma lista de tickers.

    Args:
        tickers (list): Uma lista de códigos de ativos (ex: ["PETR4.SA", "VALE3.SA"]).
    """
    print("🚀 Iniciando pipeline de ETL...")

    for ticker in tickers:
        print(f"\n--- Processando ticker: {ticker} ---")

        # 1. Extração
        print("Fase 1: Extraindo dados...")
        raw_data = extract_data(ticker)

        if raw_data.empty:
            print(f"Não foi possível extrair dados para {ticker}. Pulando para o próximo.")
            continue

        # 2. Transformação
        print("Fase 2: Transformando dados...")
        transformed_data = transform_data(raw_data)

        if transformed_data.empty:
            print(f"Transformação resultou em dados vazios para {ticker}. Pulando para o próximo.")
            continue

        # 3. Carga
        print("Fase 3: Carregando dados para o Supabase...")
        # Para evitar sobrecarregar o banco, vamos carregar os últimos 365 dias
        load_data(transformed_data.tail(365))
        
        print(f"--- Finalizado processamento para: {ticker} ---")

    print("\n✅ Pipeline de ETL concluído com sucesso!")

if __name__ == '__main__':
    # Lista de tickers para popular o banco de dados
    target_tickers = [
        "PETR4.SA",  # Petrobras
        "VALE3.SA",  # Vale
        "ITUB4.SA",  # Itaú Unibanco
        "BBDC4.SA",  # Bradesco
        "ABEV3.SA",  # Ambev
        "MGLU3.SA",  # Magazine Luiza
        "WEGE3.SA"   # WEG
    ]

    run_etl_pipeline(target_tickers)
