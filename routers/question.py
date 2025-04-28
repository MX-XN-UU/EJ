from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from database import get_db
from utils import decode_access_token
import models
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# ✅ 질문 생성 모델
class QuestionCreate(BaseModel):
    question: str
    answer: str
    save_history: bool = True  # ✅ 기본값 true, 프론트에서 비활성화할 수 있음

# ✅ 질문 저장 API
@router.post("/questions")
def save_question(
    payload: QuestionCreate,
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    print("📥 save_history 값:", payload.save_history)  # ✅ 로그 추가

    token = authorization.replace("Bearer ", "")
    decoded = decode_access_token(token)

    if not decoded:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = decoded.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    if not payload.save_history:
        print("❌ 질문 저장 생략됨 (save_history = False)")  # ✅ 저장 생략 로그
        return {"message": "저장 생략됨"}

    new_q = models.Question(
        user_id=user.id,
        question=payload.question,
        answer=payload.answer,
        timestamp=datetime.utcnow()
    )

    db.add(new_q)
    db.commit()

    print("✅ 질문이 정상 저장되었습니다.")
    return {"message": "질문 저장 완료!"}

# ✅ 질문 불러오기 API
@router.get("/questions")
def get_questions(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    decoded = decode_access_token(token)

    if not decoded:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = decoded.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    questions = (
        db.query(models.Question)
        .filter(models.Question.user_id == user.id)
        .order_by(models.Question.timestamp.desc())
        .all()
    )

    return [
        {
            "question": q.question,
            "answer": q.answer,
            "timestamp": q.timestamp.isoformat()
        } for q in questions
    ]

# ✅ 질문 전체 삭제 API
@router.delete("/questions")
def delete_questions(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    decoded = decode_access_token(token)

    if not decoded:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = decoded.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    deleted_count = db.query(models.Question).filter(models.Question.user_id == user.id).delete()
    db.commit()

    return {"message": f"{deleted_count}개 질문 삭제 완료!"}

# ✅ 오늘 질문한 횟수 조회 API
@router.get("/questions/count")
def get_today_question_count(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    decoded = decode_access_token(token)

    if not decoded:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다.")

    email = decoded.get("sub")
    user = db.query(models.User).filter(models.User.email == email).first()

    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    today = datetime.utcnow().date()

    count = db.query(models.Question).filter(
        models.Question.user_id == user.id,
        models.Question.timestamp >= today
    ).count()

    return {"count": count}
