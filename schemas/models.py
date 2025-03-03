from pydantic import BaseModel
from typing import Optional

class MessageRequest(BaseModel):
    conversation_id: str
    content: str
    chatbot_id: str
    lead_id: str
    emisor_tipo: str  # 'lead' o 'agente'
    emisor_id: Optional[str] = None  # id del perfil del agente si es un agente humano
    programa_id: Optional[str] = None  # opcional, se puede extraer del contexto

class AgentControl(BaseModel):
    conversation_id: str
    agent_id: str
    activate_chatbot: bool
    message: Optional[str] = None