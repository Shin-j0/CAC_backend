# 동아리 홈페이지 백엔드 코드 설명서 (최종)
> 생성일: 2026-01-13

본 문서는 **현재까지 업로드된 모든 파일**을 기준으로 FastAPI 기반 동아리 홈페이지 백엔드의 구조, 데이터베이스, 인증/권한, API, 마이그레이션을 설명합니다.

## 1. 프로젝트 구성 파일

### 핵심 애플리케이션
- `main.py` : FastAPI 엔트리포인트, 라우터 등록, 헬스체크
- `auth.py` : 인증 API (회원가입, 로그인, 토큰 재발급, 로그아웃, 회원탈퇴)
- `users.py` : 사용자 API (내 프로필, 회원 목록)
- `admin.py` : 관리자 API (대기자 승인/거절, 유저 관리, 로그 조회)

### 보안/권한/설정
- `security.py` : 비밀번호 해싱, JWT 생성/검증
- `deps.py` : DB 세션, 현재 사용자, Role 기반 권한 의존성
- `config.py` : 환경변수 설정 (`BaseSettings`)

### DB 레이어
- `base.py` : SQLAlchemy Base
- `session.py` : Engine / SessionLocal
- `user.py` : User ORM 모델
- `admin_log.py` : AdminActionLog ORM 모델

### 스키마(Pydantic)
- 인증/회원 스키마 (`RegisterRequest`, `LoginRequest`, `UserResponse` 등)

### 마이그레이션(Alembic)
- `env.py`
- `0dcb864f20be_init.py`
- `4162e7692e74_add_admin_action_logs.py`
- `f711ec857a1e_create_admin_action_logs_table.py`

### 기타
- `requirements.txt`
- `.env.example`
## 2. 전체 동작 흐름

1. 사용자가 `/auth/register`로 회원가입
   - 비밀번호는 bcrypt 해싱
   - 기본 Role = `GUEST`
2. `/auth/login` 성공 시 Access / Refresh 토큰 발급
3. Access Token은 `Authorization: Bearer` 헤더로 사용
4. Refresh Token은 HttpOnly 쿠키로 저장
5. 관리자는 `/admin/guest/pending`에서 대기자를 승인/거절
6. 모든 관리자 행위는 `admin_action_logs`에 기록
## 3. 데이터베이스 설계

### 3.1 users 테이블
- id (UUID, PK)
- email (unique)
- password_hash
- name
- student_id (unique)
- phone
- grade
- role (GUEST / MEMBER / ADMIN)

초기 생성: `0dcb864f20be_init.py`

### 3.2 admin_action_logs 테이블
- id (UUID, PK)
- actor_id (관리자)
- target_user_id (대상 사용자)
- action (APPROVE_USER, REJECT_USER, DELETE_USER, SET_ROLE)
- before_role / after_role
- ip / user_agent
- created_at

최종 생성 마이그레이션:
- `f711ec857a1e_create_admin_action_logs_table.py`
## 4. Alembic 마이그레이션 흐름

- `env.py`에서 `settings.DATABASE_URL`을 Alembic에 연결
- `Base.metadata`를 target_metadata로 사용
- 모델 변경 → `alembic revision --autogenerate`
- `alembic upgrade head`로 반영

⚠️ `4162e7692e74_add_admin_action_logs.py`는 중간 스텁 리비전이며,
실제 테이블 생성은 다음 리비전에서 이루어집니다.
## 5. 인증 / 보안 구조

### 비밀번호
- passlib(bcrypt) 기반 해싱
- 평문 비밀번호는 저장/로그에 남지 않음

### JWT
- Access Token: API 인증용
- Refresh Token: HttpOnly 쿠키

### 권한(Role)
- `deps.require_min_role(Role.X)` 패턴
- MEMBER / ADMIN / SUPERADMIN 단계적 권한
## 6. 주요 API 요약

### Auth
- POST /auth/register
- POST /auth/login
- POST /auth/refresh
- POST /auth/logout
- DELETE /auth/me

### Users
- GET /users/profile
- GET /users/users

### Admin
- GET /admin/guest/pending
- POST /admin/guest/{user_id}/approve
- POST /admin/guest/{user_id}/reject
- GET /admin/users
- DELETE /admin/users/{user_id}
- GET /admin/logs
## 7. 환경변수 (.env.example)

- DATABASE_URL
- SECRET_KEY / REFRESH_SECRET_KEY
- ACCESS_TOKEN_EXPIRE_MINUTES
- REFRESH_TOKEN_EXPIRE_DAYS
- CORS_ORIGINS
- COOKIE_SECURE / COOKIE_SAMESITE / COOKIE_DOMAIN
## 8. requirements.txt 참고

⚠️ 현재 requirements.txt에는 FastAPI/SQLAlchemy 관련 패키지가 없고,
자동화/매크로 관련 패키지가 포함되어 있습니다.

👉 실제 배포용 백엔드라면 다음이 필요합니다:
- fastapi
- uvicorn
- sqlalchemy
- alembic
- python-jose
- passlib[bcrypt]
- pydantic
## 9. 현재 기준 추가로 필요한 파일 ❌ 없음

이번에 업로드된 파일 기준으로 **설계/구현/마이그레이션/환경설정 설명에 필요한 파일은 모두 확보되었습니다.**
이 상태에서 문서는 완결성을 가집니다.

이제 남은 건:
- 회비 관리(dues) 기능 추가
- 테스트 코드
- 배포 설정(Docker, CI/CD)
