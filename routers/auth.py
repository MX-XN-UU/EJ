from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from database import get_db
import models
from utils import hash_password, verify_password, create_access_token
from settings import SECRET_KEY, ALGORITHM  # ✅ 수정된 부분

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

class UserCreate(BaseModel):
    id: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# ✅ 현재 사용자 인증 함수
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # ✅ settings에서 불러온 키로 디코딩
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="토큰 오류")
    except JWTError:
        raise HTTPException(status_code=401, detail="토큰 디코딩 실패")
    
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="사용자 없음")
    return user

# ✅ 관리자 권한 확인 함수
def get_current_admin_user(current_user: models.User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user

@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다.")

    hashed_pw = hash_password(user.password)

    # ✅ 특정 이메일은 관리자 자동 등록
    admin_emails = ["prid6409@gmail.com"]
    is_admin = user.email in admin_emails

    new_user = models.User(
        id_name=user.id,
        email=user.email,
        password=hashed_pw,
        is_admin=is_admin
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {
        "message": "회원가입 성공!",
        "user_id": new_user.id,
        "is_admin": new_user.is_admin
    }

@router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 잘못되었습니다.")
    
    token = create_access_token(data={"sub": db_user.email})
    
    return {
        "message": "로그인 성공!",
        "access_token": token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "is_admin": db_user.is_admin  # ✅ 관리자 여부 포함
    }
