import google.generativeai as genai
import openai
import logging
from config import LLM_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY

logger = logging.getLogger(__name__)

# Configuração inicial
if LLM_PROVIDER == "gemini":
    genai.configure(api_key=GEMINI_API_KEY)
elif LLM_PROVIDER == "openai":
    openai.api_key = OPENAI_API_KEY

def generate_persona_response(text, persona_type):
    """
    Gera uma resposta da LLM baseada na persona e no texto de entrada.
    persona_type: 'mordomo', 'assistente', 'readonly'
    """
    if persona_type == "readonly":
        return "🚫 Apenas visualização permitida para o card Gravações."

    prompt = _build_prompt(text, persona_type)
    
    try:
        if LLM_PROVIDER == "gemini":
            return _generate_with_gemini(prompt)
        elif LLM_PROVIDER == "openai":
            return _generate_with_openai(prompt)
        else:
            return text # Fallback: retorna texto bruto
    except Exception as e:
        logger.error(f"LLM Error: {e}")
        return f"⚠️ Erro ao processar IA. Texto bruto:\n{text}"

def _build_prompt(text, persona_type):
    base_instruction = """
    Regra de Ouro da Formatação (Time-First):
    A saída DEVE seguir estritamente o padrão: ⏰ HH:mm - Descrição.
    Se o texto original disser 'duas da tarde', converta para ⏰ 14:00.
    Se não houver horário, force a saída: ❓ Sem Horário - Descrição.
    """

    if persona_type == "mordomo":
        return f"""
        {base_instruction}
        Você é um Mordomo Pessoal eficiente.
        Analise o texto do card de gravações abaixo.
        Extraia e liste cronologicamente APENAS os compromissos de HOJE.
        Se não houver nada, diga que o dia está livre.
        
        Texto do Card:
        {text}
        """
    elif persona_type == "assistente":
        return f"""
        {base_instruction}
        Você é a assistente pessoal.
        Avise o Fabrício que a Patroa (A Japa) mexeu na agenda.
        Resuma o que mudou ou como ficou o dia com base no texto abaixo.
        Use tom de alerta amigável.
        
        Texto do Evento/Card:
        {text}
        """
    return text

def _generate_with_gemini(prompt):
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text.strip()

def _generate_with_openai(prompt):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content.strip()
