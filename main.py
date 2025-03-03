import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import messages, agents

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables del .env
load_dotenv()

app = FastAPI(title="Chatbot API",
             description="API para el servicio de chatbot con Supabase",
             version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, reemplazar con los dominios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(messages.router)
app.include_router(agents.router)

@app.on_event("startup")
async def startup_event():
    """Log cuando la aplicación inicia"""
    logger.info("Aplicación iniciando...")

@app.get("/health")
def health_check():
    """Endpoint para verificar el estado de la aplicación"""
    logger.info("Health check solicitado")
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": "production"
    }