"""
ManyBlack V2 - Backend FastAPI orientado a contexto
Ponto de entrada principal da aplicação
"""
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.settings import settings
from app.infra.logging import configure_logging

# Importar routers
from app.channels.telegram import router as tg_router
from app.channels.whatsapp import router as wa_router
from app.core.orchestrator import router as engine_router  
from app.tools.apply_plan import router as apply_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia lifespan da aplicação."""
    # Startup
    configure_logging()
    yield
    # Shutdown (se necessário)


app = FastAPI(
    title="ManyBlack V2",
    description="Backend FastAPI orientado a contexto com orquestração de leads",
    version="2.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    """Endpoint de saúde básico."""
    return {"status": "ok", "service": "ManyBlack V2", "env": settings.APP_ENV}


@app.get("/health")
async def health():
    """Endpoint de health check."""
    return {"status": "healthy", "env": settings.APP_ENV}


@app.get("/info")
async def info():
    """Informações detalhadas do sistema."""
    return {
        "service": "ManyBlack V2",
        "version": "2.0.0",
        "env": settings.APP_ENV,
        "features": {
            "telegram": True,
            "whatsapp": False,  # Placeholder
            "orchestrator": True,
            "apply_plan": True
        }
    }


# Incluir routers
app.include_router(tg_router, prefix="/channels/telegram", tags=["channels:telegram"])
app.include_router(wa_router, prefix="/channels/whatsapp", tags=["channels:whatsapp"])
app.include_router(engine_router, prefix="/engine", tags=["engine"])
app.include_router(apply_router, prefix="/api/tools", tags=["apply"])


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=settings.APP_PORT, 
        reload=True
    )
