from pydantic_settings import BaseSettings
from dotenv import load_dotenv, find_dotenv
import os

# Load .env from project root
load_dotenv(find_dotenv())


class Settings(BaseSettings):
    # App runtime
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("1", "true", "yes")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))

    # OpenSearch
    OPENSEARCH_HOST: str = os.getenv("OPENSEARCH_HOST")
    OPENSEARCH_INDEX: str = os.getenv("OPENSEARCH_INDEX")

    # Ingest
    BATCH_SIZE: int = int(os.getenv("BATCH", 64))
    CHUNK_MAX_WORDS: int = int(os.getenv("CHUNK_MAX_WORDS", 140))
    CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", 30))


settings = Settings()
