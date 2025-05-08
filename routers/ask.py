from fastapi import APIRouter, Header, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from database import get_db
from utils import (
    decode_access_token,
    is_malicious_input,
    is_dangerous_response,
    jaccard_similarity  # ✅ 유사 질문 감지 함수
)
import models
import os
from openai import OpenAI
import logging

logger = logging.getLogger("risk_monitor")

router = APIRouter()

class AskRequest(BaseModel):
    question: str
    is_paid_user: bool = False
    save_history: bool = True

@router.post("/ask")
async def ask(
    req: AskRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    token = authorization.replace("Bearer ", "")
    decoded = decode_access_token(token)

    if not decoded:
        raise HTTPException(status_code=401, detail="인증 실패")

    email = decoded.get("sub")
    result = await db.execute(select(models.User).where(models.User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="사용자 없음")

    # ✅ 질문 필터링: 악의적 질문 차단
    if is_malicious_input(req.question):
        logger.warning(f"[악성 질문 차단] user={email} question='{req.question}'")
        raise HTTPException(status_code=400, detail="위험하거나 부적절한 질문입니다.")

    # 최근 질문 3개 불러오기
    result = await db.execute(
        select(models.Question)
        .where(models.Question.user_id == user.id)
        .order_by(models.Question.timestamp.desc())
        .limit(3)
    )
    recent_questions = result.scalars().all()

    # ✅ 유사 질문 반복 여부 감지
    similar_count = 0
    threshold = 0.7
    for q in recent_questions:
        sim = jaccard_similarity(req.question, q.question)
        if sim >= threshold:
            similar_count += 1
    if similar_count >= 2:
        logger.warning(f"[유사 질문 반복 감지] user={email} question='{req.question}'")

    history = []
    for q in reversed(recent_questions):
        history.append({"role": "user", "content": q.question})
        history.append({"role": "assistant", "content": q.answer})

    # 시스템 메시지 삽입
    if req.is_paid_user:
        history.insert(0, {"role": "system", "content": """
이 GPT는 한국어로 대화합니다.
이 GPT는 경계선 지능인, 노약자, 혹은 일반인을 위한 가치 판단 시스템입니다.
질문에 대한 가치 판단을 통해 소비자의 의사결정을 돕습니다.
이 GPT는 어떤 경우에도 위법하거나, 사용자 또는 타인에게 직·간접적으로 피해를 주는 답변을 할 수 없습니다.

이 GPT의 가치 판단 기준은 다음과 같습니다:
1. 법적 기준 – 가장 중요. 위법 여부를 먼저 판단.
2. 현실적 기준 – 실제로 실행 가능한 해결책을 우선 제시.
3. 도덕적·사회적 기준 – 사회적으로 용인되는 행동인지 고려.
4. 개인적 가치 존중 – 사용자의 신념을 존중하지만, 위 기준을 우선함.

이 GPT는 경계선 지능인과 노약자를 기준으로 설계되었기에, 답변을 네/아니요 형식으로 간단하게 제공합니다.
답변 후 짧고 쉬운 이유를 설명하며, 어려운 법률 용어 대신 쉬운 표현을 사용합니다.
필요한 경우 관련 기관 안내 및 신고 방법을 제공합니다.

이 GPT는 위험한 선택지가 감지될 경우 경고 메시지를 표시하며,
법적 문제가 있는 경우 공식적인 해결 기관을 안내합니다.

유료 사용자에게는 반드시 답변과 함께 짧고 쉬운 이유를 설명합니다.
"""})
    else:
        history.insert(0, {"role": "system", "content": """
이 GPT는 한국어로 대화합니다.
이 GPT는 경계선 지능인, 노약자, 혹은 일반인을 위한 가치 판단 시스템입니다.
질문에 대한 가치 판단을 통해 소비자의 의사결정을 돕습니다.
이 GPT는 어떤 경우에도 위법하거나, 사용자 또는 타인에게 직·간접적으로 피해를 주는 답변을 할 수 없습니다.

이 GPT의 가치 판단 기준은 다음과 같습니다:
1. 법적 기준 – 가장 중요. 위법 여부를 먼저 판단.
2. 현실적 기준 – 실제로 실행 가능한 해결책을 우선 제시.
3. 도덕적·사회적 기준 – 사회적으로 용인되는 행동인지 고려.
4. 개인적 가치 존중 – 사용자의 신념을 존중하지만, 위 기준을 우선함.

이 GPT는 경계선 지능인과 노약자를 기준으로 설계되었기에, 답변을 네/아니요 형식으로 간단하게 제공합니다.
어려운 법률 용어 대신 쉬운 표현을 사용합니다.
필요한 경우 관련 기관 안내 및 신고 방법을 제공합니다.

답변 형식은 다음과 같습니다:
1. 질문이 네/아니요로 대답 가능한 경우 → 반드시 "네" 또는 "아니요"로 대답합니다.
2. 질문이 네/아니요로 대답하기 어려운 경우 → 한 문장 또는 단어로 간단하게 대답합니다.
"""})

    history.append({"role": "user", "content": req.question})

    # OpenAI 호출
    openai_key = os.getenv("OPENAI_API_KEY", "").strip().replace('"', "")
    if not openai_key:
        raise HTTPException(status_code=500, detail="OpenAI API 키가 없습니다.")

    client = OpenAI(api_key=openai_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=history
        )
        answer = response.choices[0].message.content.strip()
    except Exception as e:
        print("❌ GPT 호출 실패:", e)
        raise HTTPException(status_code=500, detail="GPT 응답 실패")

    # ✅ 응답 필터링
    if is_dangerous_response(answer):
        logger.warning(f"[위험 응답 차단] user={email} question='{req.question}' answer='{answer}'")
        raise HTTPException(status_code=500, detail="응답에 부적절한 내용이 포함되어 차단되었습니다.")

    # ✅ DB 저장
    if req.save_history:
        new_q = models.Question(
            user_id=user.id,
            question=req.question,
            answer=answer,
            is_risky=is_malicious_input(req.question)  # ✅ 위험 여부 저장
        )
        db.add(new_q)
        await db.commit()

    return {"answer": answer}
