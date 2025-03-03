from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from routers import messages, agents

load_dotenv()  # Cargar variables del .env

app = FastAPI()

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

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "1.0.0"}