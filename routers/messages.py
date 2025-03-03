from fastapi import APIRouter, Depends
from schemas.models import MessageRequest
from services.conversation import ConversationService

router = APIRouter()

@router.post("/message")
async def handle_message(request: MessageRequest):
    service = ConversationService()
    
    # Guardar mensaje en Supabase
    message_data = {
        'conversacion_id': request.conversation_id,
        'emisor_tipo': request.emisor_tipo,
        'emisor_id': request.emisor_id if request.emisor_tipo == 'agente' else request.lead_id,
        'contenido': request.content
    }
    service.supabase.save_message(message_data)
    
    # Si es mensaje del lead y chatbot activo
    if request.emisor_tipo == 'lead':
        response = await service.handle_message(request.dict())
        # Guardar respuesta del chatbot
        service.supabase.save_message({
            'conversacion_id': request.conversation_id,
            'emisor_tipo': 'chatbot',
            'emisor_id': request.chatbot_id,
            'contenido': response
        })
        return {"response": response}
    
    return {"status": "message received"}