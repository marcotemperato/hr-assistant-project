# config.py
import os


class Config:
    DOCUMENTS_DIR = "resumes"
    COLLECTION_NAME = "CVs"
    PERSISTENT_DIR = "data/chromadb"
    # Embedding
    MODEL_NAME = "text-embedding-3-small"
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    # Completamento
    ### ollama
    # LLM_MODEL = "llama3.2"  # "deepseek-r1:1.5b"  # "llama3.2" #  "deepseek-r1:1.5b"
    # AI_API_URL = "http://localhost:11434/v1"
    # AI_API_KEY = "ollama"
    ### openai
    LLM_MODEL = "gpt-4o-mini"
    AI_API_URL = "https://api.openai.com/v1/"
    AI_API_KEY = os.getenv("OPENAI_API_KEY")
