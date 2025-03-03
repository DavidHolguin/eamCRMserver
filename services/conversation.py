from services.supabase import SupabaseService
from services.ai import AIService
from typing import Optional, List
import logging
import asyncio
from fastapi import HTTPException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConversationService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.ai = AIService()
    
    async def handle_message(self, message_data: dict):
        try:
            # Obtener configuración del chatbot con timeout
            chatbot_config = await asyncio.wait_for(
                asyncio.to_thread(self.supabase.get_chatbot_config, message_data['chatbot_id']),
                timeout=10.0
            )
            if not chatbot_config:
                raise HTTPException(status_code=404, detail="Configuración del chatbot no encontrada")
            
            # Obtener el historial y extraer el contexto del programa
            history = await asyncio.wait_for(
                asyncio.to_thread(self.get_conversation_history, message_data['conversation_id']),
                timeout=10.0
            )
            programa_id = await asyncio.wait_for(
                asyncio.to_thread(self.extract_program_context, history, message_data),
                timeout=10.0
            )
            
            # Verificar si es solicitud de plan de estudios
            if self.ai.detect_study_plan_request(message_data['content']):
                if not programa_id:
                    programs = await asyncio.wait_for(
                        asyncio.to_thread(self.supabase.get_available_programs),
                        timeout=10.0
                    )
                    if not programs:
                        return "¿Sobre qué programa académico te gustaría conocer el plan de estudios?"
                    
                    program_list = "\n".join([f"- {p['nombre']}" for p in programs[:5]])
                    return f"¿Sobre qué programa académico te gustaría conocer el plan de estudios? Algunos de nuestros programas son:\n{program_list}"
                
                study_plan = await asyncio.wait_for(
                    asyncio.to_thread(self.supabase.get_study_plan, programa_id),
                    timeout=10.0
                )
                if not study_plan:
                    programa_info = await asyncio.wait_for(
                        asyncio.to_thread(self.supabase.get_program_info, programa_id),
                        timeout=10.0
                    )
                    if programa_info:
                        return f"Lo siento, no encontré el plan de estudios de {programa_info['nombre']}. ¿Te gustaría conocer más información sobre el programa?"
                    return "Lo siento, no pude encontrar el plan de estudios para ese programa académico."
                
                return f"Aquí puedes ver el plan de estudios de {study_plan.get('titulo', 'el programa')}: {study_plan['url_pdf']}"
            
            # Generar respuesta con IA con timeout
            context = await asyncio.wait_for(
                asyncio.to_thread(self.build_context, chatbot_config, programa_id),
                timeout=10.0
            )
            
            # Timeout más largo para la generación de IA
            response = await asyncio.wait_for(
                asyncio.to_thread(self.ai.generate_response, context, history, message_data['content']),
                timeout=30.0
            )
            return response

        except asyncio.TimeoutError:
            logger.error("Timeout al procesar el mensaje")
            raise HTTPException(status_code=504, detail="Tiempo de espera agotado")
        except Exception as e:
            logger.error(f"Error en handle_message: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def get_conversation_history(self, conversation_id: str) -> List[str]:
        try:
            result = self.supabase.client.table('mensajes')\
                .select('contenido')\
                .eq('conversacion_id', conversation_id)\
                .order('timestamp')\
                .execute()
            return [msg['contenido'] for msg in result.data] if result.data else []
        except Exception as e:
            logger.error(f"Error al obtener historial de conversación: {e}")
            return []
    
    def extract_program_context(self, history: List[str], message_data: dict) -> Optional[str]:
        try:
            programa_id = message_data.get('programa_id')
            if programa_id and programa_id != 'string':
                return programa_id
            
            program_mentions = self.supabase.get_program_mentions(history)
            if program_mentions:
                return program_mentions[-1]
            
            return None
        except Exception as e:
            logger.error(f"Error al extraer contexto del programa: {e}")
            return None
    
    def build_context(self, chatbot_config: dict, programa_id: Optional[str]) -> str:
        try:
            context = chatbot_config.get('contexto', '')
            if programa_id and programa_id != 'string':
                programa_info = self.supabase.get_program_info(programa_id)
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
            logger.error(f"Error al construir contexto: {e}")
            return chatbot_config.get('contexto', '')