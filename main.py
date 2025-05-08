import sys
import io
import subprocess
from sqlalchemy import text  # ✅ 추가

sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import traceback
import os

from settings import SECRET_KEY, OPENAI_API_KEY, ALGORITHM, DEBUG
print(f"\U0001F525 DEBUG 모드: {DEBUG}")
print(f"\U0001F512 Loaded OPENAI_API_KEY: {OPENAI_API_KEY[:10]}...")
print(f"🔐 현재 사용 중인 SECRET_KEY: {SECRET_KEY}")

from openai import OpenAI
from database import get_db
from routers import auth, user, question, ask
from routers.admin import router as admin_router
from models import User
from database import Base, engine
import asyncio

app = FastAPI(debug=DEBUG, default_response_class=JSONResponse)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 라우터 등록
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(question.router)
app.include_router(ask.router)
app.include_router(admin_router)

client = OpenAI(api_key=OPENAI_API_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ✅ 현재 사용자 불러오기
async def get_current_user(db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.email == user_email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str


@app.put("/change-password")
async def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not pwd_context.verify(data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="비밀번호가 틀렸습니다.")

    current_user.password = pwd_context.hash(data.new_password)
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return {"message": "비밀번호가 변경되었습니다."}


# ✅ DB 테이블 자동 생성 + 마이그레이션 보정
async def init_models():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # ✅ is_risky 컬럼 수동 추가 (존재하지 않을 경우만)
        try:
            await conn.execute(text(
                "ALTER TABLE questions ADD COLUMN IF NOT EXISTS is_risky BOOLEAN DEFAULT FALSE"
            ))
            print("✅ is_risky 컬럼 보정 완료")
        except Exception as e:
            print(f"❌ is_risky 컬럼 보정 실패: {e}")


@app.on_event("startup")
async def on_startup():
    await init_models()
