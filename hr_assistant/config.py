# config.py
import os
from dotenv import load_dotenv

load_dotenv()

PLACEHOLDER_KEY_MARKERS = ("sk-your", "your-openai", "changeme")


class Config:
    DOCUMENTS_DIR = "resumes"
    COLLECTION_NAME = "CVs"
    PERSISTENT_DIR = "data/chromadb" #news
    # Embedding
    MODEL_NAME = "text-embedding-3-small"
    OPENAI_KEY = os.getenv("OPENAI_API_KEY")
    # Completamento
    ### ollama
    # LLM_MODEL = "llama3.2"  # "deepseek-r1:1.5b"  # "llama3.2" #  "deepseek-r1:1.5b"
    # LLM_MODEL_LOW = "llama3.2"  # "deepseek-r1:1.5b"  # "llama3.2" #  "deepseek-r1:1.5b"
    # AI_API_URL = "http://localhost:11434/v1"
    # AI_API_KEY = "ollama"
    ### openai
    LLM_MODEL = "gpt-4o"
    LLM_MODEL_LOW = "gpt-4o-mini"
    AI_API_URL = "https://api.openai.com/v1/"
    AI_API_KEY = os.getenv("AI_API_KEY") or os.getenv("OPENAI_API_KEY")

    @classmethod
    def validate_api_keys(cls):
        missing = []
        invalid = []

        for name, value in (("OPENAI_API_KEY", cls.OPENAI_KEY),):
            if not value or not value.strip():
                missing.append(name)
                continue
            lowered = value.lower()
            if any(marker in lowered for marker in PLACEHOLDER_KEY_MARKERS):
                invalid.append(name)

        if missing or invalid:
            details = []
            if missing:
                details.append(f"mancanti: {', '.join(missing)}")
            if invalid:
                details.append(f"placeholder in .env: {', '.join(invalid)}")
            raise ValueError(
                "Configura OPENAI_API_KEY in .env (" + "; ".join(details) + "). "
                "Ottieni una chiave valida da "
                "https://platform.openai.com/account/api-keys"
            )
