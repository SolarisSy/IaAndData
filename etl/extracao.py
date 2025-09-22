import os
import yfinance as yf
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

# --- 1. Carregar Variáveis de Ambiente ---
# Garante que o script encontre o .env na raiz do projeto
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("As variáveis de ambiente SUPABASE_URL e SUPABASE_KEY são necessárias.")

# --- 2. Conexão com o Supabase ---
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Conexão com o Supabase estabelecida com sucesso.")
except Exception as e:
    print(f"🔥 Erro ao conectar com o Supabase: {e}")
    exit()

# --- 3. Lista de Tickers do IBOVESPA (Exemplo, pode ser expandida) ---
# Fonte: B3, StatusInvest, etc. (Verificar periodicamente)
# Adicionar ".SA" para compatibilidade com o yfinance
ibovespa_tickers = [
    "RRRP3.SA", "ALOS3.SA", "ALPA4.SA", "ABEV3.SA", "ARZZ3.SA", "ASAI3.SA", 
    "AZUL4.SA", "B3SA3.SA", "BBSE3.SA", "BBDC3.SA", "BBDC4.SA", "BRAP4.SA", 
    "BBAS3.SA", "BRKM5.SA", "BRFS3.SA", "BPAC11.SA", "CRFB3.SA", "BHIA3.SA", 
    "CMIG4.SA", "CIEL3.SA", "COGN3.SA", "CPLE6.SA", "CSAN3.SA", "CPFE3.SA", 
    "CMIN3.SA", "CVCB3.SA", "CYRE3.SA", "DXCO3.SA", "ELET3.SA", "ELET6.SA", 
    "EMBR3.SA", "ENEV3.SA", "ENGI11.SA", "EQTL3.SA", "EZTC3.SA", "FLRY3.SA", 
    "GGBR4.SA", "GOAU4.SA", "NTCO3.SA", "SOMA3.SA", "HAPV3.SA", "HYPE3.SA", 
    "IGTI11.SA", "IRBR3.SA", "ITSA4.SA", "ITUB4.SA", "JBSS3.SA", "KLBN11.SA", 
    "RENT3.SA", "LWSA3.SA", "LREN3.SA", "MGLU3.SA", "MRFG3.SA", "BEEF3.SA", 
    "MRVE3.SA", "MULT3.SA", "PCAR3.SA", "PETR3.SA", "PETR4.SA", "RECV3.SA", 
    "PRIO3.SA", "PETZ3.SA", "RADL3.SA", "RAIZ4.SA", "RDOR3.SA", "RAIL3.SA", 
    "SBSP3.SA", "SANB11.SA", "SMTO3.SA", "CSNA3.SA", "SLCE3.SA", "SUZB3.SA", 
    "TAEE11.SA", "VIVT3.SA", "TIMS3.SA", "TOTS3.SA", "UGPA3.SA", "USIM5.SA", 
    "VALE3.SA", "VAMO3.SA", "VBBR3.SA", "VIVA3.SA", "WEGE3.SA", "YDUQ3.SA"
]


def extrair_e_carregar_dados():
    """
    Função principal que busca dados históricos de uma lista de tickers
    e os insere no banco de dados Supabase.
    """
    print(f"🚀 Iniciando extração para {len(ibovespa_tickers)} tickers...")
    
    sucessos = 0
    falhas = []

    for ticker in ibovespa_tickers:
        print(f"\n🔄 Processando ticker: {ticker}...")
        try:
            # --- Extração (E) ---
            # Baixa o histórico de dados dos últimos 5 anos
            dados = yf.download(ticker, period="5y", progress=False)

            if dados.empty:
                print(f"⚠️  Nenhum dado encontrado para {ticker}. Pulando.")
                falhas.append(ticker)
                continue

            # --- Transformação (T) ---
            df = pd.DataFrame(dados)
            df.reset_index(inplace=True)
            df.rename(columns={
                "Date": "date",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume"
            }, inplace=True)
            
            # Adiciona a coluna 'ticker'
            df["ticker"] = ticker
            
            # Converte a coluna de data para string no formato ISO 8601
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            
            # Converte o dataframe para uma lista de dicionários (formato esperado pelo Supabase)
            dados_para_inserir = df.to_dict(orient='records')

            # --- Carga (L) ---
            # Deleta dados existentes para o ticker para evitar duplicatas
            print(f"🗑️  Limpando dados antigos para {ticker}...")
            supabase.table("acoes_historico").delete().eq("ticker", ticker).execute()
            
            # Insere os novos dados
            print(f"💾 Inserindo {len(dados_para_inserir)} registros para {ticker}...")
            _, count = supabase.table("acoes_historico").insert(dados_para_inserir).execute()

            if count:
                 print(f"✅ Sucesso! {len(dados_para_inserir)} registros inseridos para {ticker}.")
                 sucessos += 1
            else:
                 print(f"❌ Falha ao inserir dados para {ticker}.")
                 falhas.append(ticker)

        except Exception as e:
            print(f"🔥 ERRO GERAL ao processar {ticker}: {e}")
            falhas.append(ticker)
    
    print("\n--- Relatório Final ---")
    print(f"Total de tickers processados: {len(ibovespa_tickers)}")
    print(f"✅ Sucessos: {sucessos}")
    print(f"❌ Falhas: {len(falhas)}")
    if falhas:
        print(f"Tickers com falha: {', '.join(falhas)}")
    print("--- Fim da Execução ---")


if __name__ == "__main__":
    extrair_e_carregar_dados()
