import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from dotenv import load_dotenv
from routers import messages, agents

# Configurar logging
logging.basicConfig(
    level=logging.DEBUG,  # Cambiado a DEBUG para más detalle
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Cargar variables del .env
load_dotenv()

app = FastAPI(
    title="Chatbot API",
    description="API para el servicio de chatbot con Supabase",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes durante pruebas
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos
    allow_headers=["*"],
    max_age=3600,
)

# Middleware para hosts confiables
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Ajustar según necesidades de producción
)

# Manejador global de errores
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor", "type": str(type(exc).__name__)}
    )

# Incluir routers
app.include_router(messages.router)
app.include_router(agents.router)

@app.on_event("startup")
async def startup_event():
    """Log cuando la aplicación inicia"""
    logger.info("Aplicación iniciando...")
    logger.info("CORS origins configurados: *")

@app.get("/health")
def health_check():
    """Endpoint para verificar el estado de la aplicación"""
    logger.info("Health check solicitado")
    return {
        "status": "ok",
        "version": "1.0.0",
        "environment": "production"
    }