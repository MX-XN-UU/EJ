from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from database import get_db
from models import User, Subscription
from routers.auth import get_current_admin_user  # auth.py에 있는 관리자 확인 함수 사용

router = APIRouter()

# ✅ 전체 사용자 조회
@router.get("/admin/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    users = db.query(User).all()
    return [
        {
            "id": user.id,
            "id_name": user.id_name,
            "email": user.email,
            "is_admin": user.is_admin,
            "created_at": user.created_at,
            "plan": user.plan  # ✅ models.py의 plan 필드 사용
        }
        for user in users
    ]

# ✅ 사용자 플랜 변경
@router.put("/admin/plan")
def update_plan(
    data: dict = Body(...),
    db: Session = Depends(get_db),
    admin: User = Depends(get_current_admin_user)
):
    email = data.get("email")
    new_plan = data.get("plan")

    if not email or not new_plan:
        raise HTTPException(status_code=400, detail="이메일 또는 플랜이 누락되었습니다.")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="해당 사용자를 찾을 수 없습니다.")

    # ✅ User 모델의 plan 필드 직접 업데이트
    user.plan = new_plan
    db.commit()

    return {"message": f"{email}님의 플랜이 {new_plan}으로 변경되었습니다."}
