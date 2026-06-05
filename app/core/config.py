import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # API Configuration
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")
    LOG_LEVEL: str = Field(default="INFO")

    # OpenAI Configuration
    OPENAI_API_KEY: str = Field(default="your-openai-api-key-here")
    EMBEDDING_MODEL: str = Field(default="text-embedding-3-small")
    LLM_MODEL: str = Field(default="gpt-4o-mini")

    # Qdrant Vector DB Configuration
    QDRANT_URL: str = Field(default="http://localhost:6333")
    QDRANT_API_KEY: str = Field(default="")
    QDRANT_COLLECTION_NAME: str = Field(default="askdocs_collection")

# Instantiate settings
settings = Settings()
