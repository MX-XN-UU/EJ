from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from utils import decode_access_token
from database import get_db
import models

router = APIRouter()

# ✅ 내 정보 조회
@router.get("/me")
async def get_me(authorization: str = Header(...), db: AsyncSession = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = payload.get("sub")
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    return {
        "username": user.id_name,
        "user_id": user.email,
        "password": user.password,
        "created_at": str(user.created_at),
        "is_admin": user.is_admin,
        "plan": user.plan,
    }


# ✅ 회원 탈퇴
@router.delete("/delete")
async def delete_user(authorization: str = Header(...), db: AsyncSession = Depends(get_db)):
    token = authorization.replace("Bearer ", "")
    payload = decode_access_token(token)

    if not payload:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = payload.get("sub")
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    await db.delete(user)
    await db.commit()

    return {"message": "회원 탈퇴가 완료되었습니다."}
