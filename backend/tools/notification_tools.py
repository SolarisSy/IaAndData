import os
import requests
from langchain.agents import tool
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env na raiz do projeto
load_dotenv()

@tool
def notify_developer_of_missing_tool(required_analysis: str) -> str:
    """
    Use esta ferramenta como último recurso, somente quando você tiver certeza de que nenhuma das ferramentas existentes pode responder à pergunta do usuário.
    Esta função notifica o desenvolvedor de que uma nova ferramenta é necessária para atender a uma solicitação específica.
    O argumento 'required_analysis' deve ser uma descrição clara e concisa da análise que o usuário solicitou e que você não conseguiu realizar.
    """
    print(f"🤖 Ferramenta 'notify_developer_of_missing_tool' chamada com a análise: {required_analysis}")
    
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url:
        print("🔥 A variável de ambiente DISCORD_WEBHOOK_URL não foi configurada.")
        return "A funcionalidade de notificação ao desenvolvedor não está configurada."

    try:
        message = {
            "embeds": [
                {
                    "title": "🚨 Nova Ferramenta Necessária!",
                    "description": "O agente de IA identificou a necessidade de uma nova capacidade para responder a uma consulta de usuário.",
                    "color": 15158332, # Cor vermelha
                    "fields": [
                        {
                            "name": "Análise Solicitada",
                            "value": f"```{required_analysis}```"
                        }
                    ],
                    "footer": {
                        "text": "Por favor, considere desenvolver uma nova ferramenta para atender a esta demanda."
                    }
                }
            ]
        }
        
        response = requests.post(webhook_url, json=message)
        response.raise_for_status() # Lança um erro se a requisição falhar (status code não for 2xx)
        
        print("✅ Notificação enviada ao Discord com sucesso.")
        return "O desenvolvedor foi notificado com sucesso sobre a necessidade da nova ferramenta. Por favor, informe ao usuário que esta capacidade estará disponível em breve."

    except requests.exceptions.RequestException as e:
        print(f"🔥 Erro ao enviar notificação para o Discord: {e}")
        return "Ocorreu um erro ao tentar notificar o desenvolvedor."
    except Exception as e:
        print(f"🔥 Erro inesperado na ferramenta de notificação: {e}")
        return "Ocorreu um erro inesperado."
