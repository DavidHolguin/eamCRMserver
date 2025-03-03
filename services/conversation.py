from services.supabase import SupabaseService
from services.ai import AIService
from typing import Optional, List, Dict, Any
import logging
import asyncio
from fastapi import HTTPException

logging.basicConfig(level=logging.DEBUG)  # Cambiado a DEBUG para más detalle
logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.ai = AIService()
    
    async def handle_message(self, message_data: dict) -> str:
        """Maneja un mensaje entrante y genera una respuesta"""
        try:
            # Validar datos de entrada
            self._validate_message_data(message_data)
            
            # Obtener configuración del chatbot
            chatbot_config = await self._get_chatbot_config(message_data['chatbot_id'])
            
            # Obtener historial y contexto
            history = await self._get_conversation_history(message_data['conversation_id'])
            programa_id = await self._get_program_context(history, message_data)
            
            # Manejar solicitud de plan de estudios si es necesario
            if self.ai.detect_study_plan_request(message_data['content']):
                return await self._handle_study_plan_request(programa_id)
            
            # Generar respuesta normal
            context = await self._build_context(chatbot_config, programa_id)
            response = await self.ai.generate_response(context, history, message_data['content'])
            
            if not response:
                raise HTTPException(
                    status_code=500,
                    detail="No se pudo generar una respuesta válida"
                )
            
            return response

        except HTTPException as he:
            logger.error(f"Error HTTP en handle_message: {he.detail}")
            raise he
        except Exception as e:
            logger.error(f"Error inesperado en handle_message: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Error interno del servidor: {str(e)}"
            )

    def _validate_message_data(self, message_data: dict) -> None:
        """Valida los datos del mensaje"""
        required_fields = ['chatbot_id', 'conversation_id', 'content']
        missing_fields = [field for field in required_fields if field not in message_data]
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail=f"Faltan campos requeridos: {', '.join(missing_fields)}"
            )

    async def _get_chatbot_config(self, chatbot_id: str) -> Dict[str, Any]:
        """Obtiene la configuración del chatbot"""
        try:
            config = await asyncio.wait_for(
                self.supabase.get_chatbot_config(chatbot_id),
                timeout=10.0
            )
            if not config:
                raise HTTPException(
                    status_code=404,
                    detail=f"No se encontró configuración para el chatbot {chatbot_id}"
                )
            return config
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail="Tiempo de espera agotado al obtener configuración del chatbot"
            )

    async def _get_conversation_history(self, conversation_id: str) -> List[str]:
        """Obtiene el historial de la conversación"""
        try:
            return await asyncio.wait_for(
                self.supabase.get_conversation_history(conversation_id),
                timeout=10.0
            )
        except Exception as e:
            logger.warning(f"Error al obtener historial: {e}")
            return []

    async def _get_program_context(self, history: List[str], message_data: dict) -> Optional[str]:
        """Obtiene el contexto del programa"""
        try:
            programa_id = message_data.get('programa_id')
            if programa_id and programa_id != 'string':
                return programa_id
            
            program_mentions = await asyncio.wait_for(
                self.supabase.get_program_mentions(history),
                timeout=10.0
            )
            return program_mentions[-1] if program_mentions else None
        except Exception as e:
            logger.warning(f"Error al obtener contexto del programa: {e}")
            return None

    async def _handle_study_plan_request(self, programa_id: Optional[str]) -> str:
        """Maneja una solicitud de plan de estudios"""
        try:
            if not programa_id:
                programs = await asyncio.wait_for(
                    self.supabase.get_available_programs(),
                    timeout=10.0
                )
                if not programs:
                    return "¿Sobre qué programa académico te gustaría conocer el plan de estudios?"
                
                program_list = "\n".join([f"- {p['nombre']}" for p in programs[:5]])
                return f"¿Sobre qué programa académico te gustaría conocer el plan de estudios? Algunos de nuestros programas son:\n{program_list}"
            
            study_plan = await asyncio.wait_for(
                self.supabase.get_study_plan(programa_id),
                timeout=10.0
            )
            
            if not study_plan:
                programa_info = await asyncio.wait_for(
                    self.supabase.get_program_info(programa_id),
                    timeout=10.0
                )
                if programa_info:
                    return f"Lo siento, no encontré el plan de estudios de {programa_info['nombre']}. ¿Te gustaría conocer más información sobre el programa?"
                return "Lo siento, no pude encontrar el plan de estudios para ese programa académico."
            
            return f"Aquí puedes ver el plan de estudios de {study_plan.get('titulo', 'el programa')}: {study_plan['url_pdf']}"
        except Exception as e:
            logger.error(f"Error al manejar solicitud de plan de estudios: {e}")
            return "Lo siento, hubo un error al buscar el plan de estudios. ¿Podrías intentarlo de nuevo?"

    async def _build_context(self, chatbot_config: dict, programa_id: Optional[str]) -> str:
        """Construye el contexto para la generación de respuestas"""
        try:
            context = chatbot_config.get('contexto', '')
            if programa_id and programa_id != 'string':
                programa_info = await asyncio.wait_for(
                    self.supabase.get_program_info(programa_id),
                    timeout=10.0
                )
                if programa_info:
                    info = f"\nContexto del programa académico {programa_info['nombre']}:"
                    info += f"\n- Nivel: {programa_info['nivel']}"
                    info += f"\n- Modalidad: {programa_info['modalidad']}"
                    info += f"\n- Duración: {programa_info['duracion']}"
                    info += f"\n- Créditos: {programa_info['creditos']}"
                    info += f"\n- Descripción: {programa_info['descripcion']}"
                    context += info
            return context
        except Exception as e:
            logger.warning(f"Error al construir contexto: {e}")
            return chatbot_config.get('contexto', '')