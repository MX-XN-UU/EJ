from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from utils import decode_access_token
from database import get_db
import models

router = APIRouter()

# ✅ 내 정보 조회
@router.get("/me")
def get_me(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return {
        "username": user.id_name,
        "user_id": user.email,
        "password": user.password,
        "created_at": str(user.created_at),
        "is_admin": user.is_admin,
        "plan": user.plan,  # ✅ 플랜 정보 추가
    }

# ✅ 회원 탈퇴
@router.delete("/users/delete")
def delete_user(authorization: str = Header(...), db: Session = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = payload.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    db.delete(user)
    db.commit()

    return {"message": "회원 탈퇴가 완료되었습니다."}
