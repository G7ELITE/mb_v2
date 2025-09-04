import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    OPENAI_API_KEY: str | None = None
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_NAME: str = "manyblack_v2"
    DB_USER: str = "mbuser"
    DB_PASSWORD: str = "change-me"
    REDIS_URL: str | None = None
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    JWT_SECRET: str = ""
    
    # URLs para diferentes ambientes
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"
    DOMAIN: str = "localhost"
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://127.0.0.1:5173,http://127.0.0.1:5174"
    
    # Configurações do sistema de confirmação LLM-first
    CONFIRM_AGENT_MODE: str = "llm_first"  # llm_first | hybrid | det_only
    CONFIRM_AGENT_TIMEOUT_MS: int = 1000
    CONFIRM_AGENT_THRESHOLD: float = 0.80
    CONFIRM_AGENT_MAX_HISTORY: int = 10
    
    # Flag para Gate determinístico (testes)
    GATE_YESNO_DETERMINISTICO: bool = False
    
    # Configurações do Gate retroativo
    GATE_RETROACTIVE_WINDOW_MIN: int = 10  # janela retroativa em minutos
    
    # Configurações do Orquestrador com sinais LLM
    ORCH_ACCEPT_LLM_PROPOSAL: bool = True
    
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
