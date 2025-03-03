from dependencies import get_supabase
from typing import Optional, List
import logging
import uuid

logging.basicConfig(level=logging.DEBUG)

class SupabaseService:
    def __init__(self):
        self.client = get_supabase()

    def get_chatbot_config(self, chatbot_id: str) -> Optional[dict]:
        try:
            result = self.client.table('chatbots')\
                .select('*')\
                .eq('id', chatbot_id)\
                .execute()
            logging.debug(f"Obteniendo configuración del chatbot: {result.data}")
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error al obtener configuración del chatbot: {e}")
            return None
    
    def get_study_plan(self, program_id: str) -> Optional[dict]:
        try:
            # Validar que program_id sea un UUID válido y no sea el literal 'string'
            if program_id == 'string':
                return None
                
            try:
                uuid.UUID(program_id)
            except ValueError:
                logging.error(f"ID de programa inválido: {program_id}")
                return None

            # Buscar el plan de estudio activo más reciente
            result = self.client.table('planes_estudio')\
                .select('url_imagen,url_pdf,titulo')\
                .eq('programa_id', program_id)\
                .eq('activo', True)\
                .order('fecha_actualizacion', desc=True)\
                .limit(1)\
                .execute()
            
            logging.debug(f"Obteniendo plan de estudios: {result.data}")
            if not result.data:
                return None
                
            plan = result.data[0]
            return {
                'titulo': plan.get('titulo', ''),
                'url_pdf': plan.get('url_imagen') or plan.get('url_pdf')
            }
        except Exception as e:
            logging.error(f"Error al obtener plan de estudios: {e}")
            return None
    
    def get_available_programs(self) -> List[dict]:
        """Obtiene una lista de programas académicos disponibles"""
        try:
            result = self.client.table('programas_academicos')\
                .select('id,nombre,nivel')\
                .order('nombre')\
                .execute()
            return result.data if result.data else []
        except Exception as e:
            logging.error(f"Error al obtener programas disponibles: {e}")
            return []
    
    def save_message(self, message_data: dict):
        try:
            valid_fields = {
                'conversacion_id': message_data.get('conversacion_id'),
                'emisor_tipo': message_data.get('emisor_tipo'),
                'emisor_id': message_data.get('emisor_id'),
                'contenido': message_data.get('contenido')
            }
            logging.debug(f"Guardando mensaje con campos: {valid_fields}")
            return self.client.table('mensajes').insert(valid_fields).execute()
        except Exception as e:
            logging.error(f"Error al guardar mensaje: {e}")
            raise
    
    def get_program_mentions(self, history: List[str]) -> List[str]:
        try:
            # Obtener todos los programas para buscar menciones
            programs = self.client.table('programas_academicos').select('id', 'nombre').execute()
            logging.debug(f"Obteniendo programas para buscar menciones: {programs.data}")
            mentioned_programs = []
            
            for message in history:
                for program in programs.data:
                    if program['nombre'].lower() in message.lower():
                        mentioned_programs.append(program['id'])
            
            logging.debug(f"Menciones de programas encontradas: {mentioned_programs}")
            return mentioned_programs
        except Exception as e:
            logging.error(f"Error al buscar menciones de programas: {e}")
            return []
    
    def get_program_info(self, program_id: str) -> Optional[dict]:
        try:
            # Validar que program_id sea un UUID válido y no sea el literal 'string'
            if program_id == 'string':
                return None
                
            try:
                uuid.UUID(program_id)
            except ValueError:
                logging.error(f"ID de programa inválido: {program_id}")
                return None

            result = self.client.table('programas_academicos')\
                .select('nombre,descripcion,nivel,modalidad,duracion,creditos')\
                .eq('id', program_id)\
                .execute()
            logging.debug(f"Obteniendo información del programa: {result.data}")
            return result.data[0] if result.data else None
        except Exception as e:
            logging.error(f"Error al obtener información del programa: {e}")
            return None
    
    def update_conversation_status(self, conversation_id: str, status: str):
        try:
            return self.client.table('conversaciones')\
                .update({'estado': status})\
                .eq('id', conversation_id)\
                .execute()
        except Exception as e:
            logging.error(f"Error al actualizar estado de conversación: {e}")
            raise