from services.supabase import SupabaseService
from services.ai import AIService
from typing import Optional, List
import logging

logging.basicConfig(level=logging.DEBUG)

class ConversationService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.ai = AIService()
    
    async def handle_message(self, message_data: dict):
        try:
            # Obtener configuración del chatbot
            chatbot_config = self.supabase.get_chatbot_config(message_data['chatbot_id'])
            if not chatbot_config:
                return "Lo siento, no pude encontrar la configuración del chatbot."
            
            # Obtener el historial y extraer el contexto del programa
            history = self.get_conversation_history(message_data['conversation_id'])
            programa_id = self.extract_program_context(history, message_data)
            
            # Verificar si es solicitud de plan de estudios
            if self.ai.detect_study_plan_request(message_data['content']):
                if not programa_id:
                    programs = self.supabase.get_available_programs()
                    if not programs:
                        return "¿Sobre qué programa académico te gustaría conocer el plan de estudios?"
                    
                    program_list = "\n".join([f"- {p['nombre']}" for p in programs[:5]])
                    return f"¿Sobre qué programa académico te gustaría conocer el plan de estudios? Algunos de nuestros programas son:\n{program_list}"
                
                study_plan = self.supabase.get_study_plan(programa_id)
                if not study_plan:
                    programa_info = self.supabase.get_program_info(programa_id)
                    if programa_info:
                        return f"Lo siento, no encontré el plan de estudios de {programa_info['nombre']}. ¿Te gustaría conocer más información sobre el programa?"
                    return "Lo siento, no pude encontrar el plan de estudios para ese programa académico. ¿Te gustaría conocer más información sobre el programa?"
                
                return f"Aquí puedes ver el plan de estudios de {study_plan.get('titulo', 'el programa')}: {study_plan['url_pdf']}"
            
            # Generar respuesta con IA
            context = self.build_context(chatbot_config, programa_id)
            return self.ai.generate_response(context, history, message_data['content'])
        except Exception as e:
            logging.error(f"Error en handle_message: {e}")
            return "Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta nuevamente."
    
    def get_conversation_history(self, conversation_id: str) -> List[str]:
        try:
            result = self.supabase.client.table('mensajes')\
                .select('contenido')\
                .eq('conversacion_id', conversation_id)\
                .order('timestamp')\
                .execute()
            
            return [msg['contenido'] for msg in result.data] if result.data else []
        except Exception as e:
            logging.error(f"Error al obtener historial de conversación: {e}")
            return []
    
    def extract_program_context(self, history: List[str], message_data: dict) -> Optional[str]:
        try:
            # Si viene en el mensaje actual, usamos ese
            programa_id = message_data.get('programa_id')
            if programa_id and programa_id != 'string':  # Validar que no sea el literal 'string'
                return programa_id
            
            # Buscar en el historial menciones a programas
            program_mentions = self.supabase.get_program_mentions(history)
            if program_mentions:
                return program_mentions[-1]  # Retornar el programa mencionado más recientemente
            
            return None
        except Exception as e:
            logging.error(f"Error al extraer contexto del programa: {e}")
            return None
    
    def build_context(self, chatbot_config: dict, programa_id: Optional[str]) -> str:
        try:
            context = chatbot_config.get('contexto', '')
            if programa_id and programa_id != 'string':  # Validar que no sea el literal 'string'
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
            logging.error(f"Error al construir contexto: {e}")
            return chatbot_config.get('contexto', '')