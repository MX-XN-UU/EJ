import os
from dotenv import load_dotenv
from pathlib import Path

# ✅ 현재 실행 환경 (dev / staging / prod)
ENV_MODE = os.getenv("ENV_MODE", "dev")
BASE_DIR = Path(__file__).resolve().parent
DOTENV_PATH = BASE_DIR / f".env.{ENV_MODE}"

# ✅ .env 파일 로드
load_dotenv(dotenv_path=DOTENV_PATH)

# ✅ 환경 변수 불러오기
SECRET_KEY = os.getenv("SECRET_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip().replace('"', "")  # 쌍따옴표 제거 포함
DATABASE_URL = os.getenv("DATABASE_URL")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# ✅ 고정 상수
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ✅ 디버깅 출력
print("📦 Loaded ENV_MODE:", ENV_MODE)
print("📦 Raw DEBUG value:", os.getenv("DEBUG"))
print("📦 Interpreted DEBUG flag:", DEBUG)
print("🔑 원본 OPENAI_API_KEY:", repr(OPENAI_API_KEY))
print("📏 API KEY 길이:", len(OPENAI_API_KEY))
