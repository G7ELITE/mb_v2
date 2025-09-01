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
    
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
