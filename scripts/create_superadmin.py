"""

SUPERADMIN 초기 계정 생성 스크립트.

- 서버 최초 세팅 시 단 한 번 실행하는 용도
- .env에 정의된 SUPERADMIN_* 환경 변수를 읽어
  SUPERADMIN 계정을 생성한다.
- 이미 SUPERADMIN 계정이 존재하면 생성하지 않고 종료한다.

사용 목적:
- 관리자 승인/권한 관리 API에 접근할 수 있는
  최상위 관리자 계정을 안전하게 초기화하기 위함

사용 방법
- 가상환경 접속
- (.venv) ~\backend~$ python -m scripts.create_superadmin

"""

import os
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.user import User, Role
from app.core.security import get_password_hash



def main():
    db = SessionLocal()
    try:
        exists = db.scalar(
            select(User).where(User.role == Role.SUPERADMIN)
        )
        if exists:
            print("✅ SUPERADMIN already exists. Skip creation.")
            return

        email = os.environ["SUPERADMIN_EMAIL"]
        password = os.environ["SUPERADMIN_PASSWORD"]
        name = os.environ.get("SUPERADMIN_NAME", "Super Admin")
        student_id = os.environ.get("SUPERADMIN_STUDENT_ID", "00000000")
        phone = os.environ.get("SUPERADMIN_PHONE", "010-0000-0000")
        grade = int(os.environ.get("SUPERADMIN_GRADE", "1"))

        email_exists = db.scalar(
            select(User).where(User.email == email)
        )
        if email_exists:
            raise RuntimeError("Email already exists but is not SUPERADMIN")

        user = User(
            email=email,
            password_hash=get_password_hash(password),
            name=name,
            student_id=student_id,
            phone=phone,
            grade=grade,
            role=Role.SUPERADMIN,
        )

        db.add(user)
        db.commit()

        print(f"🚀 SUPERADMIN created: {email}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
