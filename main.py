import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session
import traceback
import os

from settings import SECRET_KEY, OPENAI_API_KEY, ALGORITHM, DEBUG
print(f"\U0001F525 DEBUG 모드: {DEBUG}")
print(f"\U0001F512 Loaded OPENAI_API_KEY: {OPENAI_API_KEY[:10]}...")
print(f"🔐 현재 사용 중인 SECRET_KEY: {SECRET_KEY}")


from openai import OpenAI
from database import SessionLocal, engine, get_db
from routers import auth, user, question, ask
from routers.admin import router as admin_router  # ✅ 관리자 라우터 import
import models
from models import User, Question

models.Base.metadata.create_all(bind=engine)

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
app.include_router(admin_router)  # ✅ 관리자 라우터 등록

client = OpenAI(api_key=OPENAI_API_KEY)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_email = payload.get("sub")
        if user_email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.email == user_email).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str

@app.put("/change-password")
def change_password(
    data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not pwd_context.verify(data.current_password, current_user.password):
        raise HTTPException(status_code=400, detail="비밀번호가 틀렸습니다.")

    current_user.password = pwd_context.hash(data.new_password)
    db.commit()
    return {"message": "비밀번호가 변경되었습니다."}
