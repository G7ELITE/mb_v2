from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_ENV: str = "dev"
    APP_PORT: int = 8000
    OPENAI_API_KEY: str | None = None
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_NAME: str = "manyblack_v2"
    DB_USER: str = "mbuser"
    DB_PASSWORD: str = "change-me"
    REDIS_URL: str | None = None
    TELEGRAM_BOT_TOKEN: str = "8365690952:AAE6KhKQ0qqmxM3iUvX0n9WOCS-WCFzXSnI"
    TELEGRAM_WEBHOOK_SECRET: str = ""
    JWT_SECRET: str = ""
    
    # Configurações do sistema de confirmação LLM-first
    CONFIRM_AGENT_MODE: str = "llm_first"  # llm_first | hybrid | det_only
    CONFIRM_AGENT_TIMEOUT_MS: int = 1000
    CONFIRM_AGENT_THRESHOLD: float = 0.80
    CONFIRM_AGENT_MAX_HISTORY: int = 10
    
    # Flag para Gate determinístico (testes)
    GATE_YESNO_DETERMINISTICO: bool = False
    
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
