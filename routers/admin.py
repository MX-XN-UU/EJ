from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from database import get_db
from models import User, Question
from routers.auth import get_current_admin_user

router = APIRouter()

# ✅ 전체 사용자 조회
@router.get("/admin/users")
async def get_all_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(User))
    users = result.scalars().all()

    return [
        {
            "id": user.id,
            "id_name": user.id_name,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "plan": user.plan
        }
        for user in users
    ]

# ✅ 사용자 플랜 변경
@router.put("/admin/plan")
async def update_plan(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    email = data.get("email")
    new_plan = data.get("plan")

    if not email or not new_plan:
        raise HTTPException(status_code=400, detail="이메일 또는 플랜이 누락되었습니다.")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")

    user.plan = new_plan
    await db.commit()

    return {"message": f"{email}님의 플랜이 {new_plan}으로 변경되었습니다."}

# ✅ 위험 질문만 조회
@router.get("/admin/risky-questions")
async def get_risky_questions(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    result = await db.execute(
        select(Question).where(Question.is_risky == True).order_by(Question.timestamp.desc())
    )
    risky_questions = result.scalars().all()

    return [
        {
            "id": q.id,
            "user_id": q.user_id,
            "question": q.question,
            "timestamp": q.timestamp.isoformat()
        }
        for q in risky_questions
    ]

# ✅ 의심 사용자 조회 (위험 질문 ≥ 2개)
@router.get("/admin/suspicious-users")
async def get_suspicious_users(
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    result = await db.execute(
        select(User, func.count(Question.id))
        .join(Question, User.id == Question.user_id)
        .where(Question.is_risky == True)
        .group_by(User.id)
        .having(func.count(Question.id) >= 2)
        .order_by(func.count(Question.id).desc())
    )

    users = result.all()

    return [
        {
            "user_id": u.id,
            "id_name": u.id_name,
            "email": u.email,
            "plan": u.plan,
            "created_at": u.created_at,
            "risky_question_count": count
        }
        for u, count in users
    ]

# ✅ 사용자 삭제
@router.delete("/admin/user")
async def delete_user_by_email(
    email: str,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")

    await db.delete(user)
    await db.commit()

    return {"message": f"{email} 계정이 삭제되었습니다."}
