from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import logging
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz
import config
from config import WHATSAPP_VERIFY_TOKEN, ADMIN_PHONE, TIMEZONE
from services import trello_service, whatsapp_service, llm_service

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Personal Assistant Bot V3")

# --- APScheduler (Rotina Matinal) ---

def morning_routine_job():
    """
    Job executado diariamente às 07:00.
    Persona: Mordomo.
    """
    logger.info("Executando Rotina Matinal...")
    if not ADMIN_PHONE:
        logger.warning("ADMIN_PHONE não configurado. Rotina abortada.")
        return

    target_card = trello_service.get_target_card()
    if not target_card:
        logger.warning("Card 'GRAVAÇÕES' não encontrado para a rotina matinal.")
        whatsapp_service.send_message(ADMIN_PHONE, "⚠️ Bom dia! Não encontrei o card de Gravações para gerar sua agenda.")
        return

    # Extrair descrição e checklists (se houver, aqui simplificado para desc)
    card_content = f"Nome: {target_card['name']}\nDescrição: {target_card.get('desc', '')}"
    
    # Gerar resposta com Persona Mordomo
    response = llm_service.generate_persona_response(card_content, "mordomo")
    
    whatsapp_service.send_message(ADMIN_PHONE, f"☕ *Bom dia, Fabrício!*\n\n{response}")

scheduler = BackgroundScheduler()
trigger = CronTrigger(hour=7, minute=0, timezone=pytz.timezone(TIMEZONE))
scheduler.add_job(morning_routine_job, trigger)
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

@app.get("/")
def read_root():
    return {"status": "online", "version": "V3", "message": "Personal Assistant Bot is running"}

# --- WhatsApp Webhook ---

@app.get("/whatsapp-webhook")
def verify_whatsapp_webhook(request: Request):
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Token inválido")
    return {"status": "error", "message": "Parâmetros ausentes"}

@app.post("/whatsapp-webhook")
async def receive_whatsapp_message(request: Request, background_tasks: BackgroundTasks):
    payload = await request.json()
    sender_id, message_text = whatsapp_service.extract_message_data(payload)

    if sender_id and message_text:
        # V3: Read-Only Strict
        # Qualquer mensagem recebida é tratada como tentativa de interação.
        # Se for pergunta (ex: "status"), respondemos com Mordomo.
        # Se for comando (ex: "mude"), respondemos com ReadOnly.
        # Como a LLM decide a intenção, vamos simplificar:
        # Sempre gerar resposta de Mordomo para leitura, mas se a LLM detectar intenção de escrita (no prompt V2 tinhamos isso),
        # aqui na V3 a regra é: "O usuário NÃO tem permissão de escrita".
        # Vamos assumir que qualquer interação é um pedido de leitura da agenda atual.
        # Se o usuário tentar escrever, a LLM (se configurada para detectar) poderia avisar,
        # mas a regra diz: "Qualquer tentativa de comando de edição deve receber uma resposta negando".
        
        # Para simplificar e seguir a regra "Somente Leitura", vamos processar como leitura
        # mas usando uma validação simples de keywords ou deixando a LLM responder.
        # O prompt "mordomo" é para agenda. Vamos usar um prompt genérico de leitura ou o próprio mordomo.
        
        # Melhor abordagem: Usar LLM para classificar se é escrita ou leitura?
        # A regra diz: "Crie uma função generate_persona_response...".
        # Vamos usar a persona "readonly" se detectarmos verbos de ação imperativos?
        # Ou simplesmente assumir que se o usuário falou, ele quer saber da agenda, a menos que seja explícito.
        
        # Decisão: Vamos buscar o card. Se não achar, erro.
        # Se achar, passamos o texto do usuário + texto do card para a LLM (novo prompt ad-hoc ou adaptar).
        # Mas a especificação pede "generate_persona_response(text, persona_type)".
        # Vamos usar uma lógica simples:
        # Se o texto contém palavras de comando (criar, mover, agendar), responder com ReadOnly.
        # Caso contrário, responder com o resumo do dia (Mordomo).
        
        background_tasks.add_task(process_whatsapp_interaction, sender_id, message_text)
    
    return {"status": "received"}

async def process_whatsapp_interaction(sender_id, user_text):
    # Verificação simples de intenção de escrita (pode ser melhorada com LLM)
    forbidden_keywords = ["criar", "mover", "agendar", "adicionar", "mude", "altere", "apague"]
    if any(k in user_text.lower() for k in forbidden_keywords):
        response = llm_service.generate_persona_response("", "readonly")
        whatsapp_service.send_message(sender_id, response)
        return

    # Se for leitura/pergunta, trazemos a agenda atual
    target_card = trello_service.get_target_card()
    if target_card:
        card_content = f"Nome: {target_card['name']}\nDescrição: {target_card.get('desc', '')}"
        # Usamos persona Mordomo para responder sobre a agenda
        response = llm_service.generate_persona_response(card_content, "mordomo")
        whatsapp_service.send_message(sender_id, response)
    else:
        whatsapp_service.send_message(sender_id, "⚠️ Não encontrei o card 'GRAVAÇÕES' na lista correta.")

# --- Trello Webhook ---

@app.head("/trello-webhook")
def verify_trello_webhook():
    return {"status": "ok"}

@app.post("/trello-webhook")
async def receive_trello_event(request: Request):
    payload = await request.json()
    
    is_valid, card_data, action_type = trello_service.validate_webhook_event(payload)
    
    if is_valid and config.ADMIN_PHONE:
        # Cenário B: Notificação de Mudança (Assistente)
        # Precisamos do texto atualizado do card. O webhook traz dados parciais.
        # O ideal é buscar o card completo para ter a descrição atualizada.
        card_id = card_data.get("card", {}).get("id")
        # Como não temos get_card_by_id no service (temos get_cards_in_list), 
        # e o payload pode ter a descrição nova se for updateCard...
        # Vamos confiar nos dados do payload para o resumo da mudança ou buscar o card alvo novamente.
        
        # Estratégia: Buscar o card alvo (GRAVAÇÕES) para ter o estado atual completo.
        target_card = trello_service.get_target_card()
        
        if target_card:
            card_content = f"Evento: {action_type}\nEstado Atual do Card:\nNome: {target_card['name']}\nDescrição: {target_card.get('desc', '')}"
            response = llm_service.generate_persona_response(card_content, "assistente")
            whatsapp_service.send_message(config.ADMIN_PHONE, response)
            
    return {"status": "received"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)
