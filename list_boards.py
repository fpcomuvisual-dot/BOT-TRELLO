import requests
import os
from dotenv import load_dotenv

load_dotenv()

KEY = os.getenv("TRELLO_API_KEY")
TOKEN = os.getenv("TRELLO_TOKEN")

url = f"https://api.trello.com/1/members/me/boards?key={KEY}&token={TOKEN}"

response = requests.get(url)
if response.status_code == 200:
    boards = response.json()
    print("Boards encontrados:")
    for b in boards:
        print(f"ID: {b['id']} | Nome: {b['name']}")
else:
    print(f"Erro ao listar boards: {response.text}")
