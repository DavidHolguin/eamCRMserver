from fastapi import APIRouter, Depends, HTTPException
from schemas.models import MessageRequest
from services.conversation import ConversationService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/message")
async def handle_message(request: MessageRequest):
    try:
        service = ConversationService()
        
        # Guardar mensaje en Supabase
        message_data = {
            'conversacion_id': request.conversation_id,
            'emisor_tipo': request.emisor_tipo,
            'emisor_id': request.emisor_id if request.emisor_tipo == 'agente' else request.lead_id,
            'contenido': request.content
        }
        await service.supabase.save_message(message_data)
        
        # Si es mensaje del lead y chatbot activo
        if request.emisor_tipo == 'lead':
            # Generar respuesta de forma asíncrona
            response = await service.handle_message(request.dict())
            
            if response:
                # Guardar respuesta del chatbot
                bot_message = {
                    'conversacion_id': request.conversation_id,
                    'emisor_tipo': 'chatbot',
                    'emisor_id': request.chatbot_id,
                    'contenido': response
                }
                await service.supabase.save_message(bot_message)
                return {"response": response}
            else:
                raise HTTPException(status_code=500, detail="No se pudo generar una respuesta")
        
        return {"status": "message received"}
        
    except Exception as e:
        logger.error(f"Error en handle_message: {e}")
        raise HTTPException(status_code=500, detail=str(e))