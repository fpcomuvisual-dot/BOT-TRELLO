import requests
import logging
from config import WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID

logger = logging.getLogger(__name__)

BASE_URL = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"

def send_message(to_number, text):
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": to_number,
        "type": "text",
        "text": {
            "body": text
        }
    }
    
    try:
        response = requests.post(BASE_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Error sending WhatsApp message: {e.response.text}")
        # Não levantar exceção para não quebrar o fluxo principal se o envio falhar
        return None

def extract_message_data(payload):
    """
    Extrai dados relevantes do payload do webhook do WhatsApp.
    Retorna (sender_id, message_text) ou (None, None).
    """
    try:
        entry = payload.get("entry", [])[0]
        changes = entry.get("changes", [])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])
        
        if not messages:
            return None, None
            
        message = messages[0]
        sender_id = message.get("from")
        text = message.get("text", {}).get("body")
        
        return sender_id, text
    except (IndexError, AttributeError) as e:
        logger.error(f"Error extracting message data: {e}")
        return None, None
