from fastapi import APIRouter
from schemas.models import AgentControl

router = APIRouter()

@router.post("/agent/control")
async def agent_control(control: AgentControl):
    supabase = SupabaseService()
    
    # Actualizar estado de la conversación
    status = 'agente_activo' if not control.activate_chatbot else 'chatbot_activo'
    supabase.update_conversation_status(control.conversation_id, status)
    
    # Si hay mensaje del agente
    if control.message:
        supabase.save_message({
            'conversacion_id': control.conversation_id,
            'emisor_tipo': 'agente',
            'emisor_id': control.agent_id,
            'contenido': control.message
        })
    
    return {"status": "control updated"}