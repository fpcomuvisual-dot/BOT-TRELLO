import sys
import os

# Adicionar diretório pai ao path para importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services import trello_service
from config import SERVER_PUBLIC_URL

def setup_webhook():
    if not SERVER_PUBLIC_URL:
        print("Erro: SERVER_PUBLIC_URL não está definido no .env ou config.py")
        return

    webhook_url = f"{SERVER_PUBLIC_URL}/trello-webhook"
    print(f"Tentando registrar webhook para: {webhook_url}")
    
    try:
        response = trello_service.create_webhook(webhook_url)
        print("Webhook criado com sucesso!")
        print(response)
    except Exception as e:
        print(f"Falha ao criar webhook: {e}")

if __name__ == "__main__":
    setup_webhook()
