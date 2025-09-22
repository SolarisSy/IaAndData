import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

def load_data(df: pd.DataFrame):
    """
    Carrega os dados de um DataFrame para a tabela 'acoes_historico' no Supabase.

    Args:
        df (pd.DataFrame): DataFrame transformado e pronto para ser carregado.
    """
    if df.empty:
        print("DataFrame vazio. Nenhum dado para carregar.")
        return

    # 1. Carregar variáveis de ambiente do arquivo .env
    load_dotenv()
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        print("Erro: As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY não foram definidas.")
        return

    try:
        # 2. Inicializar o cliente Supabase
        supabase: Client = create_client(supabase_url, supabase_key)

        # 3. Converter DataFrame para lista de dicionários
        data_to_insert = df.to_dict(orient='records')

        # 4. Inserir os dados na tabela
        # A biblioteca do Supabase lida com a inserção em lotes
        response = supabase.table('acoes_historico').insert(data_to_insert).execute()
        
        # Verifica se houve algum erro na resposta da API
        if hasattr(response, 'error') and response.error:
            print(f"Erro ao inserir dados: {response.error}")
        else:
            print(f"{len(data_to_insert)} registros inseridos com sucesso na tabela 'acoes_historico'.")

    except Exception as e:
        print(f"Ocorreu uma exceção: {e}")

if __name__ == '__main__':
    # Exemplo de uso para teste
    from extract import extract_data
    from transform import transform_data

    # Certifique-se de que você criou o arquivo etl/.env com suas credenciais
    
    print("Iniciando teste do script de carga...")
    
    # Extrai e transforma os dados
    raw_data = extract_data("VALE3.SA")
    transformed_data = transform_data(raw_data)
    
    # Pega apenas os últimos 5 dias para um teste rápido
    sample_data = transformed_data.tail(5)
    
    # Carrega os dados de exemplo
    load_data(sample_data)
    print("\nDados de exemplo da VALE3 (últimos 5 dias) enviados para o Supabase.")
