from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# ✅ PostgreSQL 비동기 드라이버 강제 적용
DATABASE_URL = os.getenv("DATABASE_URL", "").replace("postgresql://", "postgresql+asyncpg://")

# ✅ PostgreSQL 비동기 엔진 생성
engine = create_async_engine(DATABASE_URL, echo=True)

# ✅ 세션 팩토리
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ✅ Base 클래스 (Alembic에서 인식 가능)
Base = declarative_base()

# ✅ DB 세션 의존성 (FastAPI에서 Depends로 사용 가능)
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
