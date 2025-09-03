from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Adicionar o diretório raiz ao path para importar módulos do app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.infra.db import engine
from app.data.models import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use engine from app configuration
    connectable = engine
    
    # Configurações para schema efêmero em TEST
    configure_kwargs = {
        "connection": None,
        "target_metadata": target_metadata
    }
    
    # Verificar se está em modo TEST com schema efêmero
    test_schema_mode = os.getenv('TEST_SCHEMA_MODE') == 'true'
    test_schema_name = os.getenv('TEST_SCHEMA_NAME')
    
    if test_schema_mode and test_schema_name:
        # Configurar para schema de teste
        configure_kwargs.update({
            "include_schemas": True,
            "version_table_schema": test_schema_name
        })
        print(f"🧪 Alembic: usando schema de teste '{test_schema_name}'")

    with connectable.connect() as connection:
        # Configurar search_path para schema de teste
        if test_schema_mode and test_schema_name:
            connection.execute(f'SET search_path TO "{test_schema_name}", public')
        
        configure_kwargs["connection"] = connection
        context.configure(**configure_kwargs)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

