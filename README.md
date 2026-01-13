# 🛠 Backend Core Logic & Technologies

이 백엔드는 **동아리 홈페이지 운영을 위한 실제 서비스 수준의 기능**을 목표로 설계·구현되었습니다.  
FastAPI를 기반으로 인증, 권한 관리, 회비 관리 등 핵심 도메인 로직을 중심으로 구성되어 있습니다.

---

## 1. Backend Architecture

- **FastAPI 기반 REST API**
- 책임 분리를 고려한 계층 구조
  - `routers` : HTTP 요청/응답 처리
  - `services` : 비즈니스 로직 및 도메인 규칙
  - `models` : SQLAlchemy ORM 기반 DB 스키마
  - `schemas` : Pydantic 기반 요청/응답 검증

> HTTP 로직과 비즈니스 로직을 분리하여 유지보수성과 확장성을 고려한 구조

---

## 2. Authentication & Authorization

- **JWT 기반 인증**
  - Access Token + Refresh Token 구조
- **Access Token**
  - 짧은 만료 시간 (stateless)
  - Authorization Header(`Bearer`)로 전달
- **Refresh Token**
  - HttpOnly Cookie 저장
  - Rotation + Versioning 방식 적용

### 🔐 Refresh Token Versioning
- `refresh_token_version` 컬럼을 User 모델에 추가
- 다음 상황에서 version 증가:
  - 로그아웃
  - 비밀번호 변경
  - 회원 탈퇴
- 기존 refresh token 자동 무효화 → 강제 로그아웃 효과

---

## 3. Role-Based Access Control (RBAC)

- 사용자 권한(Role) 기반 접근 제어
  - `GUEST`, `MEMBER`, `ADMIN`, `SUPERADMIN`, `DELETED`
- FastAPI Dependency를 활용한 권한 검증
  - 관리자 전용 API (`/admin/**`)
  - 일반 회원 전용 API (`/dues/**`)
- 승인되지 않은 사용자(GUEST)는 로그인 제한

---

## 4. Password & Security

- 비밀번호 해싱 저장
- 비밀번호 변경 시:
  - 기존 비밀번호 검증
  - 새 비밀번호 중복 방지
  - `refresh_token_version` 증가
  - 모든 기존 세션 무효화

---

## 5. Dues (회비) Domain Logic

### 📌 Charge (회비 청구)
- 월 단위 회비 정책 (`YYYY-MM`)
- 한 달에 하나의 charge만 허용 (Unique Constraint)
- 회비 금액 변경 시 명확한 기준 제공

### 📌 Payment (회비 납부)
- 사용자별 납부 기록
- 부분 납부 / 다회 납부 지원
- `charge_id` 기준으로 청구와 납부 연결

### 📊 상태 계산 로직
- `PAID / PARTIAL / UNPAID / NO_CHARGE`
- 사용자별 누적 미납액 계산
- 관리자 월별 납부 현황 조회

---

## 6. Transaction Management

- SQLAlchemy Session 기반 트랜잭션 관리
- **Commit / Rollback 책임을 Router 계층에서 명확히 관리**
  - Service: 로직 처리 (`add`, `flush`)
  - Router: 트랜잭션 확정 (`commit`, `rollback`)
- 예외 발생 시 세션 안정성 보장

---

## 7. Validation & Error Handling

- Pydantic 기반 입력 검증
- period(`YYYY-MM`) 정규식 검증
- 비즈니스 오류(ValueError)는 400 응답
- 시스템 오류는 FastAPI 전역 예외 처리로 전달 (500)

---

## 8. Development & Environment

- PostgreSQL + SQLAlchemy ORM
- Alembic 마이그레이션 관리
- 환경 변수(.env) 기반 설정 분리
- CORS 설정 및 Cookie 옵션 관리

---

## Summary

이 프로젝트는 단순 CRUD를 넘어,
- **실제 서비스에서 필요한 인증 구조**
- **권한 기반 API 보호**
- **도메인 중심 로직 설계**
- **트랜잭션 및 보안 고려**

를 모두 반영한 **실전형 백엔드 구현**을 목표로 개발되었습니다.
