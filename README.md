# Club Backend

동아리 홈페이지를 위한 FastAPI 기반 백엔드 서버입니다.  
회원가입, 로그인(JWT), 권한(Role) 기반 접근 제어를 제공합니다.

---

## Tech Stack
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- JWT (python-jose)
- bcrypt (passlib)

---

## Project Structure
```
BACKEND
├─ app
│ ├─ core # 보안, 설정, 의존성
│ ├─ db # DB 세션, Base
│ ├─ models # ORM 모델
│ ├─ routers # API 라우터
│ └─ schemas # Pydantic 스키마
├─ alembic # DB 마이그레이션
├─ main.py
└─ requirements.txt
```
---

## Environment Variables

`.env.example`을 참고하여 `.env` 파일을 생성하세요.

```
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/dbname
SECRET_KEY=change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```
Install & Run
1. 가상환경 생성
bash
코드 복사
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
2. 의존성 설치
bash
코드 복사
pip install -r requirements.txt
3. DB 마이그레이션
bash
코드 복사
alembic upgrade head
4. 서버 실행
bash
코드 복사
uvicorn main:app --reload
API Docs
Swagger UI: http://127.0.0.1:8000/docs

Health Check
/health

/db-ping

Notes
.env 파일은 Git에 커밋하지 마세요.

운영 환경에서는 환경변수로 설정하세요.

yaml
코드 복사

---
