# dependencies.py (versión corregida)
from fastapi import Depends
from supabase import create_client, Client
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

def get_supabase() -> Client:
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    return create_client(url, key)

def get_ai_client(use_deepseek=True):  # Por defecto usamos Deepseek
    api_key = os.getenv('DEEPSEEK_API_KEY')
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY no está configurada en el archivo .env")
    
    return ChatOpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1",  # URL de la API de Deepseek
        model_name="deepseek-chat",  # Modelo de Deepseek
        temperature=0.7
    )