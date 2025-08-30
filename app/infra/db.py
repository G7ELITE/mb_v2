from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.settings import settings


# Construir URL de conexão com PostgreSQL
url = f"postgresql+psycopg2://{settings.DB_USER}:{settings.DB_PASSWORD}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"

# Engine do SQLAlchemy
engine = create_engine(url, pool_pre_ping=True, echo=False, future=True)

# Session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db():
    """Dependency para obter sessão do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
