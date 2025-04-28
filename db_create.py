from database import Base, engine
from models import User, Question, Subscription, Setting

print("📦 Creating database tables...")
Base.metadata.create_all(bind=engine)
print("✅ DB 생성 완료: app.db 파일이 생성됐을 거야.")