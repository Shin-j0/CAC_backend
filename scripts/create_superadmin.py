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
