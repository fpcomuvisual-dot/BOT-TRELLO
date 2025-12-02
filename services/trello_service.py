import requests
import json
import logging
from config import TRELLO_API_KEY, TRELLO_TOKEN, TRELLO_BOARD_ID

logger = logging.getLogger(__name__)

BASE_URL = "https://api.trello.com/1"

def _get_auth_params():
    return {
        "key": TRELLO_API_KEY,
        "token": TRELLO_TOKEN
    }

def get_board_lists():
    url = f"{BASE_URL}/boards/{TRELLO_BOARD_ID}/lists"
    response = requests.get(url, params=_get_auth_params())
    response.raise_for_status()
    return response.json()

def get_cards_in_list(list_id):
    url = f"{BASE_URL}/lists/{list_id}/cards"
    response = requests.get(url, params=_get_auth_params())
    response.raise_for_status()
    return response.json()

def get_target_card():
    """
    Busca ESPECIFICAMENTE o card 'GRAVAÇÕES' na lista 'TAREFAS FABRÍCIO'.
    Retorna o objeto card ou None.
    """
    lists = get_board_lists()
    target_list = next((l for l in lists if "tarefas fabrício" in l["name"].lower() or "tarefas fabricio" in l["name"].lower()), None)
    
    if not target_list:
        logger.warning("Lista 'TAREFAS FABRÍCIO' não encontrada.")
        return None

    cards = get_cards_in_list(target_list["id"])
    target_card = next((c for c in cards if "gravações" in c["name"].lower() or "gravacoes" in c["name"].lower()), None)
    
    return target_card

def create_webhook(callback_url):
    url = f"{BASE_URL}/webhooks"
    params = _get_auth_params()
    params.update({
        "callbackURL": callback_url,
        "idModel": TRELLO_BOARD_ID,
        "description": "Personal Assistant Bot Webhook"
    })
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error creating webhook: {e.response.text}")
        raise

def validate_webhook_event(payload):
    """
    Valida se o evento do webhook é relevante segundo as regras estritas:
    1. Card deve ser 'GRAVAÇÕES' (case-insensitive).
    2. Lista NÃO pode conter 'Sandra'.
    Retorna (is_valid, card_data, action_type)
    """
    action = payload.get("action", {})
    action_type = action.get("type")
    data = action.get("data", {})
    
    card_name = data.get("card", {}).get("name", "")
    list_name = data.get("list", {}).get("name", "")
    list_after_name = data.get("listAfter", {}).get("name", "")
    list_before_name = data.get("listBefore", {}).get("name", "")
    
    # Regra 1: Escopo Estrito - Apenas card "GRAVAÇÕES"
    if "gravações" not in card_name.lower() and "gravacoes" not in card_name.lower():
        return False, None, None

    # Regra 2: Bloqueio Anti-Sandra
    # Verificar lista atual, lista de destino ou lista de origem
    if "sandra" in list_name.lower() or "sandra" in list_after_name.lower() or "sandra" in list_before_name.lower():
        logger.info(f"Evento ignorado pela regra Anti-Sandra. Card: {card_name}")
        return False, None, None

    return True, data, action_type
