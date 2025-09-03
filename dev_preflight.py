#!/usr/bin/env python3
"""
🚀 ManyBlack V2 - DEV Preflight (Pré-voo)
Prepara ambiente DEV: migrations, Redis, webhook
"""
import os
import sys
import json
import subprocess
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, str(Path(__file__).parent))

def log_structured(event: str, **kwargs):
    """Log estruturado"""
    log_data = {"evt": event, **kwargs}
    print(json.dumps(log_data))

def run_migrations():
    """Executar migrações Alembic"""
    print("🗃️ Executando migrações...")
    
    try:
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        print("✅ Migrações aplicadas com sucesso")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro nas migrações: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ Alembic não encontrado")
        return False

def test_redis():
    """Testar Redis e configurar fallback se necessário"""
    print("🔄 Testando Redis...")
    
    try:
        from app.redis_adapter import get_redis
        
        redis = get_redis()
        if redis.ping():
            print("✅ Redis conectado")
            return "ok"
        else:
            print("⚠️ Redis fallback in-memory ativo")
            return "inmemory"
    except Exception as e:
        print(f"⚠️ Redis fallback in-memory ativo: {e}")
        return "inmemory"

def validate_webhook_config():
    """Validar configurações do webhook"""
    print("🤖 Validando configurações webhook...")
    
    try:
        from app.settings import settings
        
        token_ok = bool(settings.TELEGRAM_BOT_TOKEN and len(settings.TELEGRAM_BOT_TOKEN) > 20)
        secret_ok = bool(settings.TELEGRAM_WEBHOOK_SECRET)
        
        if token_ok:
            print("✅ TELEGRAM_BOT_TOKEN configurado")
        else:
            print("❌ TELEGRAM_BOT_TOKEN não configurado ou inválido")
        
        if secret_ok:
            print("✅ TELEGRAM_WEBHOOK_SECRET configurado")
        else:
            print("⚠️ TELEGRAM_WEBHOOK_SECRET não configurado")
        
        webhook_ready = token_ok and secret_ok
        
        return webhook_ready
    except Exception as e:
        print(f"❌ Erro ao validar webhook: {e}")
        return False

def check_single_worker():
    """Verificar se está configurado para processo único"""
    print("👷 Verificando configuração de workers...")
    
    try:
        from app.settings import settings
        
        workers = getattr(settings, 'UVICORN_WORKERS', 1)
        if workers == 1:
            print("✅ Processo único configurado (locks in-memory funcionam)")
        else:
            print(f"⚠️ {workers} workers configurados (pode afetar locks in-memory)")
        
        return workers == 1
    except Exception as e:
        print(f"⚠️ Erro ao verificar workers: {e}")
        return True  # Assumir OK se não conseguir verificar

def main():
    """Executar pré-voo completo"""
    print("🚀 ManyBlack V2 — DEV PREFLIGHT")
    print("=" * 40)
    
    # Verificar se está na raiz do projeto
    if not os.path.exists("requirements.txt"):
        print("❌ Execute da raiz do projeto")
        sys.exit(1)
    
    # Executar verificações
    print("📋 Executando verificações pré-voo...")
    print()
    
    # 1. Migrações
    db_migrated = run_migrations()
    
    # 2. Redis
    redis_status = test_redis()
    
    # 3. Webhook
    webhook_ready = validate_webhook_config()
    
    # 4. Workers
    single_worker = check_single_worker()
    
    # Log estruturado
    log_structured(
        "dev_preflight",
        db_migrated=db_migrated,
        redis=redis_status,
        webhook_ready=webhook_ready,
        single_worker=single_worker
    )
    
    # Resumo
    print()
    print("📋 RESUMO PRÉ-VOO")
    print("=" * 40)
    
    if db_migrated:
        print("✅ Database: Migrações aplicadas")
    else:
        print("❌ Database: Falha nas migrações")
    
    print(f"✅ Redis: {redis_status}")
    
    if webhook_ready:
        print("✅ Webhook: Configurações OK")
    else:
        print("❌ Webhook: Configurações pendentes")
    
    if single_worker:
        print("✅ Workers: Processo único")
    else:
        print("⚠️ Workers: Múltiplos processos")
    
    # Status geral
    all_ok = db_migrated and webhook_ready
    
    if all_ok:
        print()
        print("🎯 PRÉ-VOO CONCLUÍDO COM SUCESSO!")
        print("🚀 Sistema pronto para DEV")
    else:
        print()
        print("⚠️ PRÉ-VOO COM AVISOS")
        print("🔧 Verifique configurações pendentes")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
