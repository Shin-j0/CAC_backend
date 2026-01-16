# Club Backend (FastAPI)

동아리 홈페이지용 백엔드 서버입니다.
인증/권한 관리, 회원 관리, 회비 관리 기능을 FastAPI + SQLAlchemy 기반으로 제공합니다.

---

## 🧩 기술 스택

* **Python 3.10+**
* **FastAPI** – REST API 서버
* **SQLAlchemy 2.x** – ORM
* **PostgreSQL** – 데이터베이스
* **Alembic** – DB 마이그레이션
* **JWT (Access / Refresh Token)** – 인증
* **pytest** – 테스트

---

## 📂 프로젝트 구조

```text
backend/
├─ app/
│  ├─ main.py              # 애플리케이션 진입점
│  ├─ core/                # 설정 / 보안 / 의존성
│  │  ├─ config.py
│  │  ├─ security.py
│  │  └─ deps.py
│  ├─ db/                  # DB 세션 / Base
│  │  ├─ base.py
│  │  └─ session.py
│  ├─ models/              # ORM 모델
│  │  ├─ user.py
│  │  ├─ dues.py
│  │  └─ admin_log.py
│  ├─ services/            # 비즈니스 로직
│  │  ├─ admin.py
│  │  ├─ admin_log.py
│  │  └─ dues.py
│  └─ routers/             # API 라우터
│     ├─ auth.py
│     ├─ users.py
│     ├─ admin.py
│     ├─ dues.py
│     └─ admin_dues.py
├─ scripts/
│  └─ create_superadmin.py # 초기 SUPERADMIN 생성 스크립트
├─ tests/                  # pytest 테스트 코드
├─ alembic/                # DB 마이그레이션
├─ .env.example
├─ requirements.txt
└─ README.md
```

---

## 🔐 인증 / 권한 구조

### Role 종류

* `GUEST` : 가입 후 승인 대기
* `MEMBER` : 일반 회원
* `ADMIN` : 관리자
* `SUPERADMIN` : 최고 관리자
* `DELETED` : 탈퇴(Soft Delete)

### 인증 방식

* **Access Token**

  * Authorization 헤더 (`Bearer <token>`)
  * 짧은 만료 시간

* **Refresh Token**

  * HttpOnly Cookie
  * refresh_token_version 기반 무효화 지원

---

## 👤 회원 흐름

1. 회원가입 → `GUEST`
2. 관리자 승인 → `MEMBER`
3. 로그인 가능
4. 관리자 권한 부여 → `ADMIN`
5. 탈퇴 시 → `DELETED` (Soft Delete)

---

## 💰 회비 관리 구조

* **DuesCharge** : 월별 회비 청구 (YYYY-MM)
* **DuesPayment** : 회비 납부 기록 (부분/추가 납부 허용)

### 납부 상태

* `PAID`
* `PARTIAL`
* `UNPAID`
* `NO_CHARGE`

---

## 🧪 테스트

```bash
pytest
```

테스트 범위:

* 인증/로그인/토큰 재발급 플로우
* 관리자 승인/거절/삭제
* 회비 청구/납부/상태 계산
* CSV / XLSX export

---

## ⚙️ 환경 변수 설정

```bash
cp .env.example .env
```

`.env` 예시:

```env
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/clubdb
SECRET_KEY=change-this-secret
REFRESH_SECRET_KEY=change-this-refresh-secret
```

---

## 🚀 서버 실행

```bash
uvicorn app.main:app --reload
```

Swagger 문서:

* [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🛠 초기 SUPERADMIN 생성

서버 최초 세팅 시 1회 실행:

```bash
python -m scripts.create_superadmin
```

> 이미 SUPERADMIN이 존재하면 자동으로 스킵됩니다.

---

## 📌 설계 원칙 요약

* **Router** : HTTP / 권한
* **Service** : 비즈니스 로직
* **Model** : 데이터 구조
* **Soft Delete 기본 사용**
* **권한(Role) 기반 접근 제어**

---

