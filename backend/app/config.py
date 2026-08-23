"""
ResQNet — Application Configuration
All settings are read from environment variables (see .env.example).
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env", "../.env", ".env.example", "../.env.example"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────
    app_name: str = "ResQNet"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me-to-a-random-64-char-string"
    allowed_origins: str = "http://localhost:3000,http://localhost:3001"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = "postgresql+asyncpg://root@localhost:26257/resqnet"

    # ── AI Provider ──────────────────────────────────────────────────────
    ai_provider: str = "gemini"          # "bedrock" | "gemini"

    # Bedrock
    aws_region: str = "us-east-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    bedrock_chat_model: str = "anthropic.claude-3-haiku-20240307-v1:0"
    bedrock_embed_model: str = "amazon.titan-embed-text-v2:0"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.7-flash"
    gemini_chat_model: str = "gemini-3.7-flash"
    gemini_embed_model: str = "gemini-embedding-001"

    # Embedding dimension (768 for Gemini, 1536 for Titan v2)
    embedding_dim: int = 768

    # ── AWS S3 ───────────────────────────────────────────────────────────
    use_s3_mock: bool = True
    s3_bucket_name: str = "resqnet-evidence"
    s3_region: str = "us-east-1"
    local_upload_dir: str = "./uploads"

    # ── AWS Lambda ───────────────────────────────────────────────────────
    use_lambda_mock: bool = True
    lambda_function_name: str = "resqnet-report-analyzer"
    lambda_region: str = "us-east-1"

    # ── Auth ─────────────────────────────────────────────────────────────
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080     # 7 days

    # ── Backend ──────────────────────────────────────────────────────────
    backend_port: int = 8000


settings = Settings()
