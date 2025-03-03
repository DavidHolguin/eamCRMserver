from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from schemas.models import MessageRequest
from services.conversation import ConversationService
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/message")
async def handle_message(request: MessageRequest, req: Request) -> Dict[str, Any]:
    """
    Maneja los mensajes entrantes del chatbot
    """
    try:
        # Log de la solicitud entrante
        logger.debug(f"Headers de la solicitud: {dict(req.headers)}")
        logger.info(f"Mensaje recibido de tipo: {request.emisor_tipo}")
        
        service = ConversationService()
        
        # Guardar mensaje en Supabase
        message_data = {
            'conversacion_id': request.conversation_id,
            'emisor_tipo': request.emisor_tipo,
            'emisor_id': request.emisor_id if request.emisor_tipo == 'agente' else request.lead_id,
            'contenido': request.content
        }
        
        try:
            await service.supabase.save_message(message_data)
            logger.info(f"Mensaje guardado exitosamente: {request.conversation_id}")
        except Exception as e:
            logger.error(f"Error al guardar mensaje en Supabase: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error al guardar mensaje en la base de datos"
            )
        
        # Si es mensaje del lead y chatbot activo
        if request.emisor_tipo == 'lead':
            try:
                # Generar respuesta de forma asíncrona
                response = await service.handle_message(request.dict())
                
                if not response:
                    logger.warning("Respuesta vacía del servicio de conversación")
                    raise HTTPException(
                        status_code=500,
                        detail="No se pudo generar una respuesta"
                    )
                
                # Guardar respuesta del chatbot
                bot_message = {
                    'conversacion_id': request.conversation_id,
                    'emisor_tipo': 'chatbot',
                    'emisor_id': request.chatbot_id,
                    'contenido': response
                }
                
                await service.supabase.save_message(bot_message)
                logger.info(f"Respuesta del chatbot guardada: {request.conversation_id}")
                
                return {"response": response, "status": "success"}
            
            except Exception as e:
                logger.error(f"Error al procesar respuesta del chatbot: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Error al procesar la respuesta del chatbot"
                )
        
        return {"status": "message received"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error no manejado en handle_message: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Error interno del servidor"
        )