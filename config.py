import os
from dotenv import load_dotenv

load_dotenv()

# Trello
TRELLO_API_KEY = os.getenv("TRELLO_API_KEY")
TRELLO_TOKEN = os.getenv("TRELLO_TOKEN")
TRELLO_BOARD_ID = os.getenv("TRELLO_BOARD_ID")

# WhatsApp
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")

# LLM
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Server
SERVER_PUBLIC_URL = os.getenv("SERVER_PUBLIC_URL")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")
TIMEZONE = "America/Sao_Paulo"

def validate_config():
    missing = []
    if not TRELLO_API_KEY: missing.append("TRELLO_API_KEY")
    if not TRELLO_TOKEN: missing.append("TRELLO_TOKEN")
    if not WHATSAPP_TOKEN: missing.append("WHATSAPP_TOKEN")
    if not WHATSAPP_PHONE_NUMBER_ID: missing.append("WHATSAPP_PHONE_NUMBER_ID")
    if not ADMIN_PHONE: missing.append("ADMIN_PHONE")
    
    if LLM_PROVIDER == "gemini" and not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")
    elif LLM_PROVIDER == "openai" and not OPENAI_API_KEY:
        missing.append("OPENAI_API_KEY")
        
    if missing:
        raise ValueError(f"Missing environment variables: {', '.join(missing)}")
