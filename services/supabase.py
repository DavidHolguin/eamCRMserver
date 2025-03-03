import os
from supabase import create_client, Client
import logging
from typing import List, Dict, Any, Optional
import asyncio
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class SupabaseService:
    def __init__(self):
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL y SUPABASE_KEY son requeridos")
        
        self.client = create_client(supabase_url, supabase_key)

    async def save_message(self, message_data: Dict[str, Any]) -> None:
        """Guarda un mensaje en la base de datos"""
        try:
            required_fields = ['conversacion_id', 'emisor_tipo', 'emisor_id', 'contenido']
            for field in required_fields:
                if field not in message_data:
                    raise ValueError(f"Campo requerido faltante: {field}")
            
            await asyncio.to_thread(
                self.client.table('mensajes').insert(message_data).execute
            )
            logger.debug(f"Mensaje guardado: {message_data['conversacion_id']}")
        
        except Exception as e:
            logger.error(f"Error al guardar mensaje: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Error al guardar mensaje: {str(e)}"
            )

    async def get_chatbot_config(self, chatbot_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene la configuración de un chatbot"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table('chatbots')
                    .select('*')
                    .eq('id', chatbot_id)
                    .single()
                    .execute()
            )
            return result.data if result else None
        
        except Exception as e:
            logger.error(f"Error al obtener configuración del chatbot: {e}")
            return None

    async def get_conversation_history(self, conversation_id: str) -> List[str]:
        """Obtiene el historial de una conversación"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table('mensajes')
                    .select('contenido')
                    .eq('conversacion_id', conversation_id)
                    .order('timestamp')
                    .execute()
            )
            return [msg['contenido'] for msg in result.data] if result.data else []
        
        except Exception as e:
            logger.error(f"Error al obtener historial de conversación: {e}")
            return []

    async def get_program_mentions(self, history: List[str]) -> List[str]:
        """Obtiene menciones de programas en el historial"""
        try:
            # Obtener todos los programas
            result = await asyncio.to_thread(
                lambda: self.client.table('programas_academicos')
                    .select('id, nombre')
                    .execute()
            )
            
            if not result.data:
                return []
            
            # Buscar menciones en el historial
            mentions = []
            for programa in result.data:
                if any(programa['nombre'].lower() in msg.lower() for msg in history):
                    mentions.append(programa['id'])
            
            return mentions
        
        except Exception as e:
            logger.error(f"Error al buscar menciones de programas: {e}")
            return []

    async def get_available_programs(self) -> List[Dict[str, Any]]:
        """Obtiene la lista de programas disponibles"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table('programas_academicos')
                    .select('id, nombre')
                    .execute()
            )
            return result.data if result.data else []
        
        except Exception as e:
            logger.error(f"Error al obtener programas disponibles: {e}")
            return []

    async def get_study_plan(self, programa_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el plan de estudios de un programa"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table('planes_estudio')
                    .select('*')
                    .eq('programa_id', programa_id)
                    .single()
                    .execute()
            )
            return result.data if result else None
        
        except Exception as e:
            logger.error(f"Error al obtener plan de estudios: {e}")
            return None

    async def get_program_info(self, programa_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información detallada de un programa"""
        try:
            result = await asyncio.to_thread(
                lambda: self.client.table('programas_academicos')
                    .select('*')
                    .eq('id', programa_id)
                    .single()
                    .execute()
            )
            return result.data if result else None
        
        except Exception as e:
            logger.error(f"Error al obtener información del programa: {e}")
            return None