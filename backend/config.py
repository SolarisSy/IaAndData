import os
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Caminho para o arquivo .env dentro da pasta backend
dotenv_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=dotenv_path)

# Carregar variáveis de ambiente e criar o cliente Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
openai_api_key = os.getenv("OPENAI_API_KEY")

if not supabase_url or not supabase_key:
    raise RuntimeError("Credenciais do Supabase (URL e Key) não encontradas no ambiente.")

if not openai_api_key:
    # O agente precisa desta chave para funcionar
    raise RuntimeError("Chave da API da OpenAI (OPENAI_API_KEY) não encontrada no ambiente.")

supabase: Client = create_client(supabase_url, supabase_key)
