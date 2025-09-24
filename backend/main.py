import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import re

# --- Importações centralizadas ---
from .config import supabase
from .agent import query_agent
from .tools.data_retrieval_tools import get_volatility_cone
from .intraday import get_intraday_data_with_vwap

app = FastAPI(
    title="IaAndData API",
    description="API para servir dados financeiros e insights gerados por IA.",
    version="0.1.0"
)

# --- FUNÇÃO DE PRÉ-VALIDAÇÃO ---
def verificar_data_ambigua(texto: str) -> bool:
    """Verifica se há datas no formato DD/MM ou DD-MM sem um ano."""
    # Padrão para DD/MM ou DD-MM não seguido por /YYYY ou -YYYY
    padrao = r'\b(\d{1,2}[/-]\d{1,2})(?!([/-]\d{4}))\b'
    if re.search(padrao, texto):
        return True
    return False

# --- Configuração do CORS ---
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:3001",
    "https://app.iaanddata.perseuai.online", # Adicionado o domínio de produção do frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    """Endpoint raiz para verificar o status da API."""
    return {"status": "ok", "message": "Bem-vindo à API IaAndData!"}

class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None # Adiciona o ID da sessão opcional

@app.post("/api/v1/query")
def run_agent_query(request: QueryRequest):
    """
    Recebe uma pergunta em linguagem natural e a envia para o agente de IA,
    após passar por uma camada de pré-validação.
    """
    if not request.question:
        raise HTTPException(status_code=400, detail="A pergunta não pode estar vazia.")
    
    # --- CAMADA DE VALIDAÇÃO ANTES DE CHAMAR O AGENTE ---
    if verificar_data_ambigua(request.question):
        return {
            "answer": "Notei que a data na sua pergunta não especifica o ano. Para garantir a precisão, por favor, reformule a pergunta incluindo o ano completo (ex: '18/09/2024')."
        }

    try:
        # Passa a pergunta e o ID da sessão para a função do agente
        session_id = request.session_id or "default_user"
        response = query_agent(request.question, session_id=session_id)
        
        # Se a resposta for um dicionário (nosso cone), retorne-o diretamente
        if isinstance(response, dict):
            return {"chart_data": response}

        return {"answer": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar a pergunta: {e}")


@app.get("/api/v1/volatility-cone/{ticker}")
def get_volatility_cone_endpoint(ticker: str):
    """
    Retorna os dados para o gráfico de cone de volatilidade de uma ação específica.
    """
    try:
        # Reutiliza a lógica da ferramenta do agente diretamente
        result = get_volatility_cone(ticker)
        
        if isinstance(result, str) and "Erro" in result:
            raise HTTPException(status_code=500, detail=result)
        
        if isinstance(result, str) and "insuficientes" in result:
            raise HTTPException(status_code=404, detail=result)

        return {"chart_data": result}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/intraday/{ticker}")
def get_intraday_endpoint(ticker: str):
    """
    Retorna dados intraday (1 minuto) e o VWAP para uma ação específica.
    """
    try:
        data = get_intraday_data_with_vwap(ticker)
        if "error" in data:
            raise HTTPException(status_code=404, detail=data["error"])
        return data
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno no servidor: {e}")


@app.get("/api/v1/acoes/{ticker}")
def get_historico_acao(ticker: str):
    """
    Retorna o histórico de dados de uma ação específica.
    """
    try:
        response = supabase.table('acoes_historico').select("*").eq('ticker', ticker.upper()).order('date', desc=True).limit(100).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Dados não encontrados para o ticker {ticker}")
            
        return {"ticker": ticker, "data": response.data}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
