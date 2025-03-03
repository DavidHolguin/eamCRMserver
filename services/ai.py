from langchain_core.messages import HumanMessage, SystemMessage
from dependencies import get_ai_client

class AIService:
    def __init__(self, use_deepseek=False):
        self.client = get_ai_client(use_deepseek)
    
    def generate_response(self, context: str, history: list, prompt: str):
        messages = [
            SystemMessage(content=context),
            *[HumanMessage(content=msg) for msg in history[-5:]],  # Últimos 5 mensajes
            HumanMessage(content=prompt)
        ]
        return self.client(messages).content
    
    def detect_study_plan_request(self, message: str) -> bool:
        keywords = ["plan de estudio", "plan estudios", "programa académico", "malla curricular"]
        return any(keyword in message.lower() for keyword in keywords)
    
    def detect_room_query(self, message: str) -> bool:
        keywords = ["habitación", "habitaciones", "cuarto", "cuartos", "alojamiento", "hospedaje"]
        return any(keyword in message.lower() for keyword in keywords)
    
    def detect_image_query(self, message: str) -> bool:
        keywords = ["imagen", "imágenes", "foto", "fotos", "galería", "ver", "mostrar"]
        return any(keyword in message.lower() for keyword in keywords)