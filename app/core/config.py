import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices, ValidationError
from typing import List, Literal

class Settings(BaseSettings):
    SECRET_KEY: str = Field(..., description="JWT secret key")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    ALGORITHM: str = "HS256"
    DATABASE_URL: str = "sqlite:///./app.db"
    CORS_ORIGINS: str = "http://localhost:3000"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_DIR: str = "./.chroma"
    LLM_BACKEND: Literal["ollama", "transformers"] = Field(
        "ollama",
        validation_alias=AliasChoices("LLM_BACKEND", "llm_backend"),
        description="Which LLM backend to use",
    )

    OLLAMA_MODEL: str = Field(
        "llama3",
        validation_alias=AliasChoices("OLLAMA_MODEL", "ollama_model"),
        description="Ollama model name/tag",
    )
    OLLAMA_HOST: str = Field(
        "http://127.0.0.1:11434",
        validation_alias=AliasChoices("OLLAMA_HOST", "ollama_host"),
        description="Ollama server base URL",
    )

    HF_MODEL: str = Field(
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        validation_alias=AliasChoices("HF_MODEL", "hf_model"),
    )
    MAX_NEW_TOKENS: int = Field(
        256,
        validation_alias=AliasChoices("MAX_NEW_TOKENS", "max_new_tokens"),
    )
    TEMPERATURE: float = Field(
        0.2,
        validation_alias=AliasChoices("TEMPERATURE", "temperature"),
    )

    VECTOR_TIMEOUT_SECONDS: int = 5
    LLM_TIMEOUT_SECONDS: int = 90

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

if not os.path.exists(".env"):
    raise RuntimeError(
        ".env not found. Create a .env file at project root with at least:\n"
        "SECRET_KEY=your-secret\n"
        "(Optional) OLLAMA_MODEL=llama3.2:3b, OLLAMA_HOST=http://127.0.0.1:11434"
    )

try:
    settings = Settings()
except ValidationError as e:
    raise RuntimeError(
        "Invalid configuration. Check your .env values.\n"
        "Required: SECRET_KEY. Optional: LLM settings.\n"
        f"Details: {e}"
    ) from e

def get_allowed_origins() -> List[str]:
    raw = (settings.CORS_ORIGINS or "").strip()
    return [o.strip() for o in raw.split(",") if o.strip()]
