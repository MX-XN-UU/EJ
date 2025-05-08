from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext

# 🔐 비밀번호 해싱 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 🔐 JWT 관련 설정
from settings import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# 🔐 비밀번호 해싱 함수
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# 🔐 비밀번호 검증 함수
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# 🔐 토큰 생성 함수
def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# 🔐 토큰 해석 함수
def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# 🚨 질문 필터링 유틸 - 악의적 질문 차단용
def is_malicious_input(text: str) -> bool:
    blacklist = [
        "죽이고", "죽여", "죽일까", "자살", "살인", "폭탄", "칼로", "휘두르",
        "폭력", "성폭행", "테러", "총기", "불태워", "납치", "강간", "공격"
    ]
    return any(keyword in text.lower() for keyword in blacklist)

# 🚨 응답 필터링 유틸 - 위험한 GPT 응답 차단용
def is_dangerous_response(text: str) -> bool:
    flagged_terms = [
        "휘두르세요", "공격하세요", "죽이세요", "칼로", "망치를 들고", "물리적으로 대응",
        "직접 해결", "상대를 해치세요", "복수하세요", "혼내주세요"
    ]
    return any(term in text.lower() for term in flagged_terms)

# 🚨 유사 질문 감지 유틸 - 반복 유도 질문 방지용
def jaccard_similarity(a: str, b: str) -> float:
    a_set = set(a.lower().split())
    b_set = set(b.lower().split())
    intersection = a_set.intersection(b_set)
    union = a_set.union(b_set)
    return len(intersection) / len(union) if union else 0

