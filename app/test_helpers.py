"""
Test Helpers - Schema Efêmero para E2E
Cria/destrói schemas temporários quando não pode criar database
"""
import os
import time
import json
import logging
import psycopg2
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

def log_structured(event: str, **kwargs):
    """Log estruturado"""
    log_data = {"evt": event, **kwargs}
    print(json.dumps(log_data))

class TestSchemaManager:
    """Gerenciador de schema efêmero para testes"""
    
    def __init__(self):
        self.schema_name: Optional[str] = None
        self.original_search_path: Optional[str] = None
        
    def generate_schema_name(self) -> str:
        """Gerar nome único do schema de teste"""
        from app.settings import settings
        
        prefix = getattr(settings, 'TEST_SCHEMA_PREFIX', 'test_mb')
        pid = os.getpid()
        timestamp = int(time.time())
        
        return f"{prefix}_{pid}_{timestamp}"
    
    def create_schema(self) -> str:
        """Criar schema de teste"""
        from app.settings import settings
        
        if self.schema_name:
            raise RuntimeError("Schema já existe")
        
        self.schema_name = self.generate_schema_name()
        
        # Conectar ao PostgreSQL
        dsn = f'host={settings.DB_HOST} port={settings.DB_PORT} dbname={settings.DB_NAME} user={settings.DB_USER} password={settings.DB_PASSWORD}'
        
        with psycopg2.connect(dsn) as conn:
            conn.autocommit = True
            with conn.cursor() as cur:
                # Salvar search_path original
                cur.execute("SHOW search_path;")
                self.original_search_path = cur.fetchone()[0]
                
                # Criar schema
                cur.execute(f'CREATE SCHEMA "{self.schema_name}";')
                
                # Definir search_path para priorizar o schema de teste
                cur.execute(f'SET search_path TO "{self.schema_name}", public;')
        
        log_structured("test_schema", schema=self.schema_name, created=True)
        logger.info(f"✅ Schema de teste criado: {self.schema_name}")
        
        return self.schema_name
    
    def migrate_schema(self):
        """Executar migrações no schema de teste"""
        if not self.schema_name:
            raise RuntimeError("Schema não foi criado")
        
        import subprocess
        
        # Configurar variáveis de ambiente para Alembic
        env = os.environ.copy()
        env['TEST_SCHEMA_MODE'] = 'true'
        env['TEST_SCHEMA_NAME'] = self.schema_name
        
        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                env=env,
                capture_output=True,
                text=True,
                check=True
            )
            
            log_structured("test_schema", schema=self.schema_name, migrated=True)
            logger.info(f"✅ Migrações aplicadas no schema: {self.schema_name}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Erro nas migrações do schema {self.schema_name}: {e.stderr}")
            raise
    
    def drop_schema(self):
        """Remover schema de teste"""
        if not self.schema_name:
            return
        
        try:
            from app.settings import settings
            
            dsn = f'host={settings.DB_HOST} port={settings.DB_PORT} dbname={settings.DB_NAME} user={settings.DB_USER} password={settings.DB_PASSWORD}'
            
            with psycopg2.connect(dsn) as conn:
                conn.autocommit = True
                with conn.cursor() as cur:
                    # Restaurar search_path original
                    if self.original_search_path:
                        cur.execute(f'SET search_path TO {self.original_search_path};')
                    
                    # Remover schema
                    cur.execute(f'DROP SCHEMA IF EXISTS "{self.schema_name}" CASCADE;')
            
            log_structured("test_schema", schema=self.schema_name, dropped=True)
            logger.info(f"✅ Schema de teste removido: {self.schema_name}")
            
        except Exception as e:
            logger.error(f"❌ Erro ao remover schema {self.schema_name}: {e}")
        finally:
            self.schema_name = None
            self.original_search_path = None
    
    def get_schema_connection_args(self) -> Dict[str, Any]:
        """Obter argumentos de conexão para o schema de teste"""
        if not self.schema_name:
            raise RuntimeError("Schema não foi criado")
        
        return {
            "options": f'-csearch_path="{self.schema_name}",public'
        }

# Instância global para testes
_test_schema_manager: Optional[TestSchemaManager] = None

def get_test_schema_manager() -> TestSchemaManager:
    """Obter instância global do gerenciador de schema"""
    global _test_schema_manager
    if _test_schema_manager is None:
        _test_schema_manager = TestSchemaManager()
    return _test_schema_manager

@asynccontextmanager
async def test_schema_context():
    """Context manager para schema de teste"""
    from app.settings import settings
    
    # Verificar se está em modo de teste por schema
    if not getattr(settings, 'TEST_SCHEMA_MODE', False):
        yield None
        return
    
    manager = get_test_schema_manager()
    
    try:
        # Criar e migrar schema
        schema_name = manager.create_schema()
        manager.migrate_schema()
        
        yield schema_name
        
    finally:
        # Limpar schema
        manager.drop_schema()

def setup_test_environment():
    """Setup do ambiente de teste com detecção automática"""
    from app.settings import settings
    
    # Carregar audit result para decidir estratégia
    audit_file = ".audit_result.json"
    db_mode = "unit_only"  # Default
    
    if os.path.exists(audit_file):
        try:
            with open(audit_file, 'r') as f:
                audit = json.load(f)
                db_mode = audit.get('db_mode', 'unit_only')
        except Exception as e:
            logger.warning(f"Erro ao ler audit: {e}")
    
    print(f"🔍 Modo de teste detectado: {db_mode}")
    
    if db_mode == "schema":
        # Ativar modo schema
        os.environ['TEST_SCHEMA_MODE'] = 'true'
        os.environ['APP_ENV'] = 'test'
        print("✅ Modo schema efêmero ativado")
        return True
    elif db_mode == "database":
        # Tentar usar database de teste (se existir)
        os.environ['APP_ENV'] = 'test'
        print("✅ Modo database de teste ativado")
        return True
    else:
        print("⚠️ Apenas testes unitários (sem E2E)")
        return False

def can_run_e2e_tests() -> bool:
    """Verificar se pode executar testes E2E"""
    return setup_test_environment()
