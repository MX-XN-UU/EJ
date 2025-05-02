from logging.config import fileConfig
import asyncio
import os
import sys
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# ✅ sys.path에 프로젝트 루트 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# ✅ 환경 및 베이스 설정
from settings import DATABASE_URL
from database import Base

# ✅ 모델 전체 import (핵심!)
import models  # ⬅️ 이것이 있어야 테이블들이 인식됨!

# ✅ Alembic config 객체 설정
config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# ✅ 로그 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ✅ 마이그레이션 메타데이터
target_metadata = Base.metadata

# ✅ 실제 마이그레이션 수행
def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()

# ✅ 비동기 마이그레이션 실행
def run_migrations_online():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async def run_migrations():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    asyncio.run(run_migrations())

# ✅ 진입점
if context.is_offline_mode():
    raise RuntimeError("🔴 Offline mode not supported for async migrations")
else:
    run_migrations_online()
