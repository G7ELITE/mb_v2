#!/usr/bin/env python3
"""
🔍 ManyBlack V2 - Dev Audit (Autodetecção de Infraestrutura)
Detecta DB, Redis, configs e decide estratégia TEST (database vs schema)
"""
import os
import sys
import json
import time
import psycopg2
from pathlib import Path

# Adicionar app ao path
sys.path.insert(0, str(Path(__file__).parent))

def log_structured(event: str, **kwargs):
    """Log estruturado"""
    log_data = {"evt": event, **kwargs}
    print(json.dumps(log_data))

def audit_config():
    """Auditar configurações"""
    print("🔍 AUDIT — Configurações")
    print("=" * 40)
    
    # Detectar arquivos de config
    has_env = os.path.exists(".env")
    has_env_test = os.path.exists(".env.test") 
    has_env_local = os.path.exists(".env.local")
    
    print(f"📄 .env: {'✅' if has_env else '❌'}")
    print(f"📄 .env.test: {'✅' if has_env_test else '❌'}")  
    print(f"📄 .env.local: {'✅' if has_env_local else '❌'}")
    
    # Testar precedência
    try:
        from app.settings import settings
        print(f"⚙️ APP_ENV: {settings.APP_ENV}")
        print(f"⚙️ DB_NAME: {settings.DB_NAME}")
        print(f"⚙️ REDIS_URL: {'SET' if settings.REDIS_URL else 'NOT_SET'}")
        print(f"⚙️ TELEGRAM_BOT_TOKEN: {'***' + settings.TELEGRAM_BOT_TOKEN[-6:] if settings.TELEGRAM_BOT_TOKEN and len(settings.TELEGRAM_BOT_TOKEN) > 6 else 'NOT_SET'}")
    except Exception as e:
        print(f"❌ Erro ao carregar settings: {e}")
        return False, False, False, "error"
    
    return has_env, has_env_test, has_env_local, "ok"

def audit_postgres():
    """Auditar PostgreSQL e permissões"""
    print("\n🔍 AUDIT — PostgreSQL")
    print("=" * 40)
    
    try:
        from app.settings import settings
        
        # Conectar
        dsn = f'host={settings.DB_HOST} port={settings.DB_PORT} dbname={settings.DB_NAME} user={settings.DB_USER} password={settings.DB_PASSWORD}'
        
        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        try:
            with conn.cursor() as cur:
                # Info básica
                cur.execute('SELECT current_database(), current_user, version();')
                db, user, version = cur.fetchone()
                print(f"✅ Database: {db}")
                print(f"✅ User: {user}")
                print(f"✅ Version: {version.split()[0]} {version.split()[1]}")
                
                # Testar CREATE DATABASE
                test_db_name = f'test_mb_permissions_{int(time.time())}'
                can_create_db = False
                try:
                    cur.execute(f'CREATE DATABASE {test_db_name};')
                    cur.execute(f'DROP DATABASE {test_db_name};')
                    can_create_db = True
                    print("✅ CREATE DATABASE: SIM")
                except Exception as e:
                    print(f"❌ CREATE DATABASE: NÃO ({str(e).split('.')[0]})")
                
                # Testar CREATE SCHEMA
                can_create_schema = False
                try:
                    cur.execute('CREATE SCHEMA test_schema_temp;')
                    cur.execute('DROP SCHEMA test_schema_temp;')
                    can_create_schema = True
                    print("✅ CREATE SCHEMA: SIM")
                except Exception as e:
                    print(f"❌ CREATE SCHEMA: NÃO ({str(e).split('.')[0]})")
                
                # Decidir db_mode
                if can_create_db:
                    db_mode = "database"
                    strategy = "Criar DB de teste separado"
                elif can_create_schema:
                    db_mode = "schema"
                    strategy = "Usar schema temporário"
                else:
                    db_mode = "unit_only"
                    strategy = "Apenas testes unitários"
                
                print(f"🎯 Estratégia: {strategy}")
        
        finally:
            conn.close()
        
        return True, can_create_db, can_create_schema, db_mode
        
    except Exception as e:
        print(f"❌ Falha ao conectar: {e}")
        return False, False, False, "error"

def audit_redis():
    """Auditar Redis"""
    print("\n🔍 AUDIT — Redis")
    print("=" * 40)
    
    try:
        from app.settings import settings
        
        if not settings.REDIS_URL:
            print("⚠️ REDIS_URL não configurado")
            return False, "not_configured"
        
        import redis
        r = redis.from_url(settings.REDIS_URL)
        result = r.ping()
        
        if result:
            info = r.info('server')
            print(f"✅ Redis conectado: {result}")
            print(f"✅ Version: {info['redis_version']}")
            return True, "ok"
        else:
            print("❌ Redis PING falhou")
            return False, "ping_failed"
            
    except Exception as e:
        print(f"❌ Redis não disponível: {e}")
        return False, "unavailable"

def audit_scripts():
    """Auditar scripts existentes"""
    print("\n🔍 AUDIT — Scripts")
    print("=" * 40)
    
    scripts = {
        "start.sh": "Iniciar backend+frontend",
        "setup_ngrok.sh": "Setup ngrok túnel único",
        "activate_webhook.sh": "Ativar webhook Telegram",
        "quick_start.sh": "Quick start completo"
    }
    
    script_status = {}
    for script, desc in scripts.items():
        exists = os.path.exists(script)
        print(f"📜 {script}: {'✅' if exists else '❌'} ({desc})")
        script_status[script] = exists
    
    # Verificar se usa 1 túnel
    tunnel_unified = True
    if os.path.exists("setup_ngrok.sh"):
        with open("setup_ngrok.sh", "r") as f:
            content = f.read()
            if "5173" in content and "frontend" in content.lower():
                print("✅ Túnel unificado: Frontend+Backend via proxy")
            else:
                print("⚠️ Verificar configuração de túnel")
                tunnel_unified = False
    
    return script_status, tunnel_unified

def main():
    """Executar audit completa"""
    print("🔍 ManyBlack V2 — DEV AUDIT (Autodetecção)")
    print("=" * 50)
    
    # Config audit
    has_env, has_env_test, has_env_local, config_status = audit_config()
    
    # PostgreSQL audit
    db_connected, can_create_db, can_create_schema, db_mode = audit_postgres()
    
    # Redis audit  
    redis_available, redis_status = audit_redis()
    
    # Scripts audit
    script_status, tunnel_unified = audit_scripts()
    
    # Log estruturado final
    log_structured(
        "infra_audit",
        can_create_db=can_create_db,
        can_create_schema=can_create_schema, 
        db_mode=db_mode,
        redis_available=redis_available,
        has_env_test=has_env_test,
        config_status=config_status,
        redis_status=redis_status,
        tunnel_unified=tunnel_unified
    )
    
    # Resumo e recomendações
    print("\n📋 RESUMO & RECOMENDAÇÕES")
    print("=" * 50)
    
    if db_mode == "database":
        print("🎯 TESTE: Criar database separado (manyblack_v2_test)")
    elif db_mode == "schema": 
        print("🎯 TESTE: Schema temporário efêmero")
    else:
        print("🎯 TESTE: Apenas unitários (sem E2E)")
    
    if not redis_available:
        print("🎯 REDIS: Fallback in-memory em DEV/TEST")
    
    if tunnel_unified:
        print("🎯 NGROK: Túnel único OK")
    else:
        print("🎯 NGROK: Ajustar para túnel único")
    
    # Salvar resultado
    audit_result = {
        "timestamp": int(time.time()),
        "db_mode": db_mode,
        "can_create_db": can_create_db,
        "can_create_schema": can_create_schema,
        "redis_available": redis_available,
        "redis_status": redis_status,
        "has_env_test": has_env_test,
        "script_status": script_status,
        "tunnel_unified": tunnel_unified
    }
    
    with open(".audit_result.json", "w") as f:
        json.dump(audit_result, f, indent=2)
    
    print("\n✅ Audit salvo em: .audit_result.json")
    
    return audit_result

if __name__ == "__main__":
    main()
