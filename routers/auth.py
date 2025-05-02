from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from database import get_db
import models
from utils import hash_password, verify_password, create_access_token
from settings import SECRET_KEY, ALGORITHM

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


# ✅ Pydantic 모델
class UserCreate(BaseModel):
    id: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str


# ✅ 현재 사용자 인증
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="토큰 오류")
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰 디코딩 실패")

    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자 없음")
    return user


# ✅ 관리자 권한 확인
def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user


# ✅ 회원가입
@router.post("/register")
async def register_user(user: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    hashed_pw = hash_password(user.password)
    is_admin = user.email in ["prid6409@gmail.com"]

    new_user = models.User(
        id_name=user.id,
        email=user.email,
        password=hashed_pw,
        is_admin=is_admin
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return {
        "message": "회원가입 성공!",
        "user_id": new_user.id,
        "is_admin": new_user.is_admin
    }


# ✅ 로그인
@router.post("/login")
async def login_user(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.User).where(models.User.email == user.email))
    db_user = result.scalar_one_or_none()

    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")

    token = create_access_token(data={"sub": db_user.email})

    return {
        "message": "로그인 성공!",
        "access_token": token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "is_admin": db_user.is_admin
    }
