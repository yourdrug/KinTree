import asyncio
import importlib
from logging.config import fileConfig

from alembic import context
from domain.models.basemodel import BaseModel
from infrastructure.common.settings import settings
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config


config = context.config
section = config.config_ini_section
target_metadata = BaseModel.metadata


def load_model_modules() -> None:
    """
    load_models_modules: Function for loading models modules.
    Models located in different files so their modules need to be imported before making migrations.
    """

    model_modules: tuple = (
        "domain.models.basemodel",
        "domain.models.account",
        "domain.models.family",
        "domain.models.parent_child",
        "domain.models.person",
        "domain.models.spouse",
    )

    for model_module in model_modules:
        try:
            importlib.import_module(model_module)
        except ModuleNotFoundError:
            print(f"Module {model_module} not found")


def init_alembic_config() -> None:
    """
    init_alembic_config: Function for initializing alembic config.
    Also Initialize database connection settings.
    """

    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

    config.set_section_option(section, "DB_USER", settings.DB_USER)
    config.set_section_option(section, "DB_PASSWORD", settings.DB_PASSWORD)
    config.set_section_option(section, "DB_HOST", settings.DB_HOST)
    config.set_section_option(section, "DB_PORT", settings.DB_PORT)
    config.set_section_option(section, "DB_NAME", settings.DB_NAME)


def run_migrations_offline() -> None:
    """
    run_migrations_offline: Run migrations in 'offline' mode.
    This configures the context with just a URL and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the script output.
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


def do_run_migrations(connection: Connection) -> None:
    """
    do_run_migrations: Execute all pending migrations with alembic.
    """

    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    run_async_migrations: We need to create an Engine and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """
    run_migrations_online: Run migrations in 'online' mode.
    """

    asyncio.run(run_async_migrations())


load_model_modules()
init_alembic_config()
run_migrations_offline() if context.is_offline_mode() else run_migrations_online()
