import requests
import os
from dotenv import load_dotenv
import sys

load_dotenv()

KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")

def check_board(board_id):
    url = f"https://api.trello.com/1/boards/{board_id}/lists?key={KEY}&token={TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        lists = response.json()
        print(f"Listas do Board {board_id}:")
        for l in lists:
            print(f"- {l['name']}")
            if "TAREFAS FABRÍCIO" in l['name'].upper() or "TAREFAS FABRICIO" in l['name'].upper():
                print("!!! ENCONTRADO !!!")
    else:
        print(f"Erro ao ler listas do board {board_id}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_board(sys.argv[1])
