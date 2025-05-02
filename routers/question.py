from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime
from database import get_db
from utils import decode_access_token
import models
from pydantic import BaseModel

router = APIRouter()

# ✅ 질문 생성 모델
class QuestionCreate(BaseModel):
    question: str
    answer: str
    save_history: bool = True

# ✅ 질문 저장 API
@router.post("/questions")
async def save_question(
    payload: QuestionCreate,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    print("📥 save_history 값:", payload.save_history)

    token = authorization.replace("Bearer ", "")
    decoded = decode_access_token(token)

    if not decoded:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = decoded.get("sub")
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    if not payload.save_history:
        print("❌ 질문 저장 생략됨 (save_history = False)")
        return {"message": "저장 생략됨"}

    new_q = models.Question(
        user_id=user.id,
        question=payload.question,
        answer=payload.answer,
        timestamp=datetime.utcnow()
    )
    db.add(new_q)
    await db.commit()
    print("✅ 질문이 정상 저장되었습니다.")
    return {"message": "질문 저장 완료!"}

# ✅ 질문 불러오기 API
@router.get("/questions")
async def get_questions(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    decoded = decode_access_token(token)

    if not decoded:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = decoded.get("sub")
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    result = await db.execute(
        select(models.Question)
        .where(models.Question.user_id == user.id)
        .order_by(models.Question.timestamp.desc())
    )
    questions = result.scalars().all()

    return [
        {
            "question": q.question,
            "answer": q.answer,
            "timestamp": q.timestamp.isoformat()
        } for q in questions
    ]

# ✅ 질문 전체 삭제 API
@router.delete("/questions")
async def delete_questions(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    decoded = decode_access_token(token)

    if not decoded:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = decoded.get("sub")
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    await db.execute(
        models.Question.__table__.delete().where(models.Question.user_id == user.id)
    )
    await db.commit()

    return {"message": "질문이 모두 삭제되었습니다."}

# ✅ 오늘 질문한 횟수 조회 API
@router.get("/questions/count")
async def get_today_question_count(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    decoded = decode_access_token(token)

    if not decoded:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = decoded.get("sub")
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    today = datetime.utcnow().date()

    result = await db.execute(
        select(models.Question)
        .where(
            models.Question.user_id == user.id,
            models.Question.timestamp >= today
        )
    )
    questions_today = result.scalars().all()

    return {"count": len(questions_today)}
