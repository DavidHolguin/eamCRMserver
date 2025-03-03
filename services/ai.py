import os
from typing import List
import logging
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.model = ChatOpenAI(
            model_name="deepseek-chat",
            openai_api_key=os.getenv('DEEPSEEK_API_KEY'),
            openai_api_base="https://api.deepseek.com/v1",
            temperature=0.7,
            request_timeout=20,
            max_retries=1
        )

    def detect_study_plan_request(self, message: str) -> bool:
        """Detecta si el mensaje es una solicitud de plan de estudios"""
        message = message.lower()
        keywords = ['plan', 'estudio', 'pensum', 'materias', 'asignaturas', 'semestres']
        return any(keyword in message for keyword in keywords)

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
    async def generate_response(self, context: str, history: List[str], message: str) -> str:
        """Genera una respuesta usando el modelo de IA con reintentos"""
        try:
            # Preparar el contexto y el mensaje
            prompt = self._prepare_prompt(context, history[-3:], message)
            
            # Generar respuesta con timeout
            response = await asyncio.wait_for(
                asyncio.to_thread(self._generate_response_sync, prompt),
                timeout=20.0
            )
            
            # Validar y limpiar la respuesta
            cleaned_response = self._clean_response(response)
            return cleaned_response

        except asyncio.TimeoutError:
            logger.error("Timeout al generar respuesta de IA")
            return "Lo siento, estoy tardando demasiado en responder. ¿Podrías reformular tu pregunta de forma más específica?"
        except Exception as e:
            logger.error(f"Error al generar respuesta de IA: {e}")
            return "Lo siento, tuve un problema al procesar tu mensaje. ¿Podrías intentarlo de nuevo?"

    def _prepare_prompt(self, context: str, history: List[str], message: str) -> List:
        """Prepara el prompt para el modelo"""
        messages = [SystemMessage(content=context)]
        
        # Agregar historial limitado
        for msg in history:
            messages.append(HumanMessage(content=msg))
        
        # Agregar mensaje actual
        messages.append(HumanMessage(content=message))
        
        return messages

    def _generate_response_sync(self, messages) -> str:
        """Método sincrónico para generar respuesta"""
        try:
            response = self.model.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error en _generate_response_sync: {e}")
            raise

    def _clean_response(self, response: str) -> str:
        """Limpia y valida la respuesta del modelo"""
        if not response or len(response.strip()) == 0:
            return "Lo siento, no pude generar una respuesta válida. ¿Podrías reformular tu pregunta?"
        
        # Limitar longitud de respuesta
        if len(response) > 2000:
            response = response[:1997] + "..."
        
        return response