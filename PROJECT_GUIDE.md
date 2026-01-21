# 🚀 Club Backend API 가이드

> 동아리 관리 및 회비 시스템 백엔드 프로젝트
>
> **대상**: 프론트엔드 개발자 및 신규 팀원
>
> **마지막 업데이트**: 2026년 1월 21일

---

## 📖 목차

1. [프로젝트 소개](#-프로젝트-소개)
2. [빠른 시작](#-빠른-시작)
3. [인증 시스템](#-인증-시스템)
4. [API 응답 표준](#-api-응답-표준)
5. [에러 코드 가이드](#-에러-코드-가이드)
6. [주요 API 엔드포인트](#-주요-api-엔드포인트)
7. [API 호출 예시](#-api-호출-예시)
8. [FAQ](#-자주-묻는-질문)

---

## 🎯 프로젝트 소개

**주요 기능**:
- 👤 **회원 관리**: 회원가입, 로그인, 프로필 관리
- 📧 **이메일 인증**: 가입 시 이메일 인증 코드 발송
- 📝 **가입 신청**: 신규 회원 가입 신청 및 관리자 승인
- 💰 **회비 시스템**: 회비 부과, 조회, 납부 기록
- 🔐 **권한 관리**: GUEST, MEMBER, ADMIN, SUPERADMIN 계층

### 기술 스택

| 분류 | 기술 |
|------|------|
| **언어** | Python 3.13+ |
| **프레임워크** | FastAPI |
| **데이터베이스** | PostgreSQL |
| **ORM** | SQLAlchemy 2.0 |
| **인증** | JWT (Access Token + Refresh Token) |
| **이메일** | FastAPI-Mail (SMTP) |
| **테스트** | pytest |

---

## ⚡ 빠른 시작

### 1. 환경 설정

```bash
# 저장소 클론
git clone <repository-url>
cd cac-backend

# 가상환경 생성 및 활성화
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Mac/Linux

# 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 입력하세요:

```env
# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost:5432/club_db

# JWT 설정
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=14

# CORS 설정
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# 이메일 설정 (Gmail 예시)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
MAIL_FROM=your-email@gmail.com
MAIL_FROM_NAME=Club Admin
```

### 3. 데이터베이스 마이그레이션

```bash
# 최신 스키마로 업그레이드
alembic upgrade head
```

### 4. 서버 실행

```bash
# 개발 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면:
- 🌐 **API**: http://localhost:8000
- 📚 **Swagger 문서**: http://localhost:8000/docs
- 📖 **ReDoc 문서**: http://localhost:8000/redoc

---

## 🔐 인증 시스템

### JWT 토큰 기반 인증

본 프로젝트는 **Access Token**과 **Refresh Token** 두 가지 토큰을 사용합니다.

| 토큰 종류 | 유효 기간 | 용도 | 저장 위치 |
|----------|----------|------|----------|
| **Access Token** | 30분 | API 요청 인증 | 로컬스토리지 or 메모리 |
| **Refresh Token** | 14일 | Access Token 갱신 | HttpOnly 쿠키 (권장) |

### 인증 플로우

```
1️⃣ 로그인
   POST /auth/login
   → Access Token + Refresh Token 발급

2️⃣ API 요청
   GET /users/profile
   Header: Authorization: Bearer {access_token}

3️⃣ 토큰 만료 시
   POST /auth/refresh
   Cookie: refresh_token={refresh_token}
   → 새로운 Access Token 발급

4️⃣ 로그아웃
   POST /auth/logout
   → Refresh Token 무효화
```

### API 요청 시 인증 헤더

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**JavaScript 예시**:
```javascript
fetch('http://localhost:8000/users/profile', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
})
```

---

## 📋 API 응답 표준

### ✅ 성공 응답 (2xx)

모든 성공 응답은 다음 구조를 따릅니다:

```json
{
  "data": { /* 실제 데이터 */ },
  "meta": {
    "count": null,      // 목록의 총 개수 (목록 응답일 경우)
    "has_more": null    // 추가 데이터 존재 여부
  }
}
```

#### 단일 객체 응답 (200 OK)

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "홍길동",
    "role": "MEMBER",
    "created_at": "2026-01-21T10:30:00Z"
  },
  "meta": {
    "count": null,
    "has_more": null
  }
}
```

#### 목록 응답 (200 OK)

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "홍길동",
      "role": "MEMBER"
    },
    {
      "id": "6fa459ea-ee8a-3ca4-894e-db77e160355e",
      "name": "김철수",
      "role": "ADMIN"
    }
  ],
  "meta": {
    "count": 2,
    "has_more": false
  }
}
```

#### 생성 성공 (201 Created)

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "created_at": "2026-01-21T10:30:00Z"
  },
  "meta": {
    "count": null,
    "has_more": null
  }
}
```

### ❌ 에러 응답 (4xx, 5xx)

모든 에러 응답은 다음 구조를 따릅니다:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "에러 메시지",
    "details": { /* 선택적: 상세 정보 */ }
  }
}
```

#### 400 Bad Request - 잘못된 요청

```json
{
  "error": {
    "code": "BAD_REQUEST",
    "message": "Invalid period format. Use YYYY-MM"
  }
}
```

#### 401 Unauthorized - 인증 실패

```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid password"
  }
}
```

#### 403 Forbidden - 권한 없음

```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Account pending approval"
  }
}
```

#### 404 Not Found - 리소스 없음

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "User not found"
  }
}
```

#### 409 Conflict - 충돌 (중복)

```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Email already registered"
  }
}
```

#### 422 Validation Error - 입력 검증 실패

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "요청 값이 올바르지 않습니다",
    "details": {
      "email": "value is not a valid email address",
      "password": "String should have at least 8 characters"
    }
  }
}
```

#### 429 Too Many Requests - 요청 제한 초과

```json
{
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many verification requests. Please try again later."
  }
}
```

#### 500 Internal Server Error - 서버 오류

```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "An unexpected error occurred"
  }
}
```

---

## 🚨 에러 코드 가이드

### HTTP 상태 코드 & ErrorCode 매핑

| HTTP Status | ErrorCode | 설명 | 발생 상황 예시 |
|-------------|-----------|------|---------------|
| **400** | `BAD_REQUEST` | 잘못된 요청 형식 | 날짜 형식 오류, 비밀번호 불일치, 필수 필드 누락 |
| **401** | `UNAUTHORIZED` | 인증 실패 | 비밀번호 틀림, 토큰 만료/없음/유효하지 않음 |
| **403** | `FORBIDDEN` | 접근 권한 없음 | GUEST 상태로 MEMBER 기능 접근, 일반 회원이 관리자 기능 접근 |
| **404** | `NOT_FOUND` | 리소스 없음 | 사용자 없음, 신청서 없음, 회비 기록 없음 |
| **409** | `CONFLICT` | 충돌 (중복/이미 처리됨) | 이메일 중복, 학번 중복, 이미 승인된 신청서 |
| **422** | `VALIDATION_ERROR` | 입력 검증 실패 | 이메일 형식 오류, 문자열 길이 부족, 타입 불일치 |
| **429** | `RATE_LIMITED` | 요청 횟수 제한 | 이메일 인증 재발송 제한 (1분 내 재발송 불가) |
| **500** | `INTERNAL_ERROR` | 서버 내부 오류 | 예기치 못한 오류, DB 연결 실패 |

### 도메인별 ErrorCode

#### 인증 관련 (`EMAIL_ALREADY_REGISTERED`, `STUDENT_ID_ALREADY_IN_USE`)

```json
// 이메일 중복 (409 CONFLICT)
{
  "error": {
    "code": "CONFLICT",
    "message": "Email already registered"
  }
}

// 학번 중복 (409 CONFLICT)
{
  "error": {
    "code": "CONFLICT",
    "message": "Student ID already in use"
  }
}
```

### 프론트엔드에서 에러 처리 예시

```javascript
async function loginUser(email, password) {
  try {
    const response = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      // 에러 응답 처리
      const { code, message } = data.error;

      switch (code) {
        case 'UNAUTHORIZED':
          alert('이메일 또는 비밀번호가 올바르지 않습니다.');
          break;
        case 'FORBIDDEN':
          alert('관리자 승인 대기 중입니다.');
          break;
        case 'VALIDATION_ERROR':
          alert(`입력 오류: ${message}`);
          break;
        default:
          alert(`오류 발생: ${message}`);
      }
      return null;
    }

    // 성공 응답 처리
    const { access_token, refresh_token, user } = data.data;
    localStorage.setItem('access_token', access_token);
    // refresh_token은 HttpOnly 쿠키로 자동 저장됨

    return user;
  } catch (error) {
    console.error('Network error:', error);
    alert('서버와 통신할 수 없습니다.');
    return null;
  }
}
```

---

## 📡 주요 API 엔드포인트

### 🔑 인증 (Authentication)

#### POST `/auth/register` - 회원가입

**요청**:
```json
{
  "email": "user@example.com",
  "password": "Password123!",
  "name": "홍길동",
  "student_id": "20240001",
  "major": "컴퓨터공학과",
  "join_year": 2024,
  "grade": 2,
  "phone": "010-1234-5678"
}
```

**응답 (201 Created)**:
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "홍길동",
    "role": "GUEST",
    "created_at": "2026-01-21T10:30:00Z"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 409 CONFLICT: `Email already registered`
- 409 CONFLICT: `Student ID already in use`
- 422 VALIDATION_ERROR: 입력 형식 오류

---

#### POST `/auth/login` - 로그인

**요청**:
```json
{
  "email": "user@example.com",
  "password": "Password123!"
}
```

**응답 (200 OK)**:
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "홍길동",
      "role": "MEMBER"
    }
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 401 UNAUTHORIZED: `Invalid credentials`
- 403 FORBIDDEN: `Account pending approval` (GUEST 상태)

---

#### POST `/auth/refresh` - 토큰 갱신

**요청**:
```
Cookie: refresh_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**응답 (200 OK)**:
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 401 UNAUTHORIZED: `Refresh token missing`
- 401 UNAUTHORIZED: `Invalid or expired refresh token`
- 404 NOT_FOUND: `User not found`

---

#### POST `/auth/send-verification` - 이메일 인증 코드 발송

**요청**:
```json
{
  "email": "user@example.com"
}
```

**응답 (200 OK)**:
```json
{
  "data": {
    "message": "Verification email sent",
    "expires_in_minutes": 10
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 429 RATE_LIMITED: `Too many verification requests` (1분 내 재발송 제한)

---

#### POST `/auth/verify-email` - 이메일 인증 확인

**요청**:
```json
{
  "email": "user@example.com",
  "code": "123456"
}
```

**응답 (200 OK)**:
```json
{
  "data": {
    "message": "Email verified successfully"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 404 NOT_FOUND: `Verification not found`
- 400 BAD_REQUEST: `Verification code expired or invalid`

---

### 👤 사용자 (Users)

#### GET `/users/profile` - 내 프로필 조회

**인증 필요**: ✅ (모든 권한)

**응답 (200 OK)**:
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "홍길동",
    "student_id": "20240001",
    "major": "컴퓨터공학과",
    "role": "MEMBER",
    "join_year": 2024,
    "grade": 2,
    "phone": "010-1234-5678",
    "created_at": "2026-01-21T10:30:00Z"
  },
  "meta": { "count": null, "has_more": null }
}
```

---

#### PATCH `/users/profile` - 프로필 수정

**인증 필요**: ✅

**요청**:
```json
{
  "name": "홍길동",
  "major": "소프트웨어학과",
  "grade": 3,
  "phone": "010-9999-8888",
  "password": "CurrentPassword123!"  // 현재 비밀번호 (필수)
}
```

**응답 (200 OK)**:
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "name": "홍길동",
    "major": "소프트웨어학과",
    "grade": 3,
    "phone": "010-9999-8888"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 400 BAD_REQUEST: `No changes to update`
- 401 UNAUTHORIZED: `Invalid password`

---

#### DELETE `/users/me` - 회원 탈퇴

**인증 필요**: ✅

**요청**:
```json
{
  "password": "Password123!"  // 본인 확인
}
```

**응답 (200 OK)**:
```json
{
  "data": {
    "message": "User deleted successfully"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 401 UNAUTHORIZED: `Invalid password`
- 403 FORBIDDEN: `Admin users cannot be deleted via this endpoint`

---

### 📝 가입 신청 (Applications)

#### POST `/applications` - 신청서 제출

**인증 필요**: ❌ (비회원도 가능)

**요청**:
```json
{
  "email": "newuser@example.com",
  "password": "Password123!",
  "name": "김신규",
  "student_id": "20260001",
  "major": "컴퓨터공학과",
  "grade": 1,
  "phone": "010-1111-2222",
  "privacy_consent": true
}
```

**응답 (201 Created)**:
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "newuser@example.com",
    "name": "김신규",
    "status": "PENDING",
    "created_at": "2026-01-21T10:30:00Z"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 400 BAD_REQUEST: `Privacy consent is required`
- 409 CONFLICT: `Email already registered`
- 409 CONFLICT: `Student ID already in use`

---

#### GET `/applications/{id}` - 신청서 상세 조회

**인증 필요**: ✅ (관리자)

**응답 (200 OK)**:
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "user_id": "6fa459ea-ee8a-3ca4-894e-db77e160355e",
    "email": "newuser@example.com",
    "name": "김신규",
    "student_id": "20260001",
    "major": "컴퓨터공학과",
    "status": "PENDING",
    "created_at": "2026-01-21T10:30:00Z"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 404 NOT_FOUND: `Application not found`

---

#### PATCH `/admin/applications/{id}/approve` - 신청 승인

**인증 필요**: ✅ (관리자)

**응답 (200 OK)**:
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "APPROVED",
    "approved_at": "2026-01-21T11:00:00Z"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 404 NOT_FOUND: `Application not found`
- 409 CONFLICT: `Application already approved`

---

#### PATCH `/admin/applications/{id}/reject` - 신청 반려

**인증 필요**: ✅ (관리자)

**요청**:
```json
{
  "reason": "신청 조건 미충족"
}
```

**응답 (200 OK)**:
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "REJECTED",
    "rejected_at": "2026-01-21T11:00:00Z",
    "reason": "신청 조건 미충족"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 404 NOT_FOUND: `Application not found`
- 409 CONFLICT: `Application already rejected`

---

### 💰 회비 (Dues)

#### GET `/dues/me` - 내 회비 조회

**인증 필요**: ✅ (MEMBER 이상)

**쿼리 파라미터**:
- `year` (선택): 연도 필터 (예: 2026)

**응답 (200 OK)**:
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "year": 2026,
      "month": 1,
      "amount": 10000,
      "paid_at": "2026-01-15T14:30:00Z",
      "payment_method": "계좌이체"
    },
    {
      "id": "6fa459ea-ee8a-3ca4-894e-db77e160355e",
      "year": 2026,
      "month": 2,
      "amount": 10000,
      "paid_at": null,  // 미납
      "payment_method": null
    }
  ],
  "meta": {
    "count": 2,
    "has_more": false
  }
}
```

---

#### POST `/dues/me/pay` - 회비 납부

**인증 필요**: ✅ (MEMBER 이상)

**요청**:
```json
{
  "dues_id": "6fa459ea-ee8a-3ca4-894e-db77e160355e",
  "payment_method": "계좌이체"
}
```

**응답 (200 OK)**:
```json
{
  "data": {
    "id": "6fa459ea-ee8a-3ca4-894e-db77e160355e",
    "paid_at": "2026-01-21T11:00:00Z",
    "payment_method": "계좌이체"
  },
  "meta": { "count": null, "has_more": null }
}
```

**가능한 에러**:
- 404 NOT_FOUND: `Dues record not found`

---

### 🔧 관리자 API (Admin)

#### POST `/admin/dues/charge` - 회비 부과

**인증 필요**: ✅ (관리자)

**요청**:
```json
{
  "period": "2026-02",
  "user_ids": [
    "550e8400-e29b-41d4-a716-446655440000",
    "6fa459ea-ee8a-3ca4-894e-db77e160355e"
  ],
  "amount": 10000
}
```

**응답 (201 Created)**:
```json
{
  "data": {
    "period": "2026-02",
    "charged_count": 2,
    "amount": 10000
  },
  "meta": { "count": 2, "has_more": false }
}
```

**가능한 에러**:
- 400 BAD_REQUEST: `Invalid period format. Use YYYY-MM`
- 409 CONFLICT: `Dues already charged for 2026-02`

---

#### GET `/admin/dues/status` - 회비 납부 현황

**인증 필요**: ✅ (관리자)

**쿼리 파라미터**:
- `period` (필수): 기간 (예: 2026-01)

**응답 (200 OK)**:
```json
{
  "data": [
    {
      "user_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "홍길동",
      "student_id": "20240001",
      "amount": 10000,
      "paid_at": "2026-01-15T14:30:00Z",
      "payment_method": "계좌이체",
      "status": "paid"
    },
    {
      "user_id": "6fa459ea-ee8a-3ca4-894e-db77e160355e",
      "name": "김철수",
      "student_id": "20240002",
      "amount": 10000,
      "paid_at": null,
      "payment_method": null,
      "status": "unpaid"
    }
  ],
  "meta": {
    "count": 2,
    "has_more": false
  }
}
```

---

#### GET `/admin/dues/export.xlsx` - 회비 현황 엑셀 다운로드

**인증 필요**: ✅ (관리자)

**쿼리 파라미터**:
- `period` (필수): 기간 (예: 2026-01)

**응답**: XLSX 파일 다운로드

---

## 💡 API 호출 예시

### JavaScript (Fetch API)

#### 회원가입

```javascript
async function register(userData) {
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email: userData.email,
      password: userData.password,
      name: userData.name,
      student_id: userData.studentId,
      major: userData.major,
      join_year: userData.joinYear,
      grade: userData.grade,
      phone: userData.phone
    })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error.message);
  }

  return data.data;
}
```

#### 로그인 (토큰 저장 포함)

```javascript
async function login(email, password) {
  const response = await fetch('http://localhost:8000/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    credentials: 'include',  // 쿠키 포함
    body: JSON.stringify({ email, password })
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.error.message);
  }

  // Access Token 저장
  localStorage.setItem('access_token', data.data.access_token);

  return data.data.user;
}
```

#### 인증이 필요한 API 호출

```javascript
async function getMyProfile() {
  const token = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/users/profile', {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });

  const data = await response.json();

  if (!response.ok) {
    // 401 에러 시 토큰 갱신 시도
    if (response.status === 401) {
      await refreshToken();
      return getMyProfile();  // 재시도
    }
    throw new Error(data.error.message);
  }

  return data.data;
}
```

#### 토큰 갱신

```javascript
async function refreshToken() {
  const response = await fetch('http://localhost:8000/auth/refresh', {
    method: 'POST',
    credentials: 'include'  // refresh_token 쿠키 포함
  });

  const data = await response.json();

  if (!response.ok) {
    // Refresh Token도 만료됨 → 재로그인 필요
    localStorage.removeItem('access_token');
    window.location.href = '/login';
    throw new Error('Session expired');
  }

  // 새로운 Access Token 저장
  localStorage.setItem('access_token', data.data.access_token);
}
```

---

### cURL 예시

#### 회원가입

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "Password123!",
    "name": "홍길동",
    "student_id": "20240001",
    "major": "컴퓨터공학과",
    "join_year": 2024,
    "grade": 2,
    "phone": "010-1234-5678"
  }'
```

#### 로그인

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{
    "email": "user@example.com",
    "password": "Password123!"
  }'
```

#### 프로필 조회 (인증 필요)

```bash
curl http://localhost:8000/users/profile \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### 회비 납부 현황 (관리자)

```bash
curl "http://localhost:8000/admin/dues/status?period=2026-01" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## 🤔 자주 묻는 질문

### Q1. Access Token이 만료되면 어떻게 하나요?

**A**: `/auth/refresh` 엔드포인트로 Refresh Token을 사용하여 새로운 Access Token을 발급받으세요.

```javascript
// 401 에러 감지 시 자동 갱신
if (response.status === 401) {
  await refreshToken();
  // 원래 요청 재시도
}
```

---

### Q2. CORS 오류가 발생합니다.

**A**: `.env` 파일의 `CORS_ORIGINS`에 프론트엔드 URL을 추가했는지 확인하세요.

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

---

### Q3. 회원가입 후 바로 로그인할 수 있나요?

**A**: 회원가입 시 `role`이 `GUEST`로 설정됩니다. 로그인은 가능하지만, 일부 기능은 관리자가 `MEMBER`로 승인한 후에 사용할 수 있습니다.

---

### Q4. 에러 응답을 어떻게 처리해야 하나요?

**A**: 응답의 `error.code`를 확인하여 적절한 사용자 메시지를 표시하세요.

```javascript
if (!response.ok) {
  const { code, message } = data.error;

  switch (code) {
    case 'UNAUTHORIZED':
      showMessage('로그인이 필요합니다.');
      break;
    case 'FORBIDDEN':
      showMessage('권한이 없습니다.');
      break;
    case 'CONFLICT':
      showMessage('이미 존재하는 데이터입니다.');
      break;
    default:
      showMessage(message);
  }
}
```

---

### Q5. 목록 조회 시 페이지네이션은 어떻게 하나요?

**A**: `skip`과 `limit` 쿼리 파라미터를 사용하세요.

```javascript
// 10개씩, 2페이지 조회
fetch('http://localhost:8000/admin/users?skip=10&limit=10')
```

---

### Q6. Swagger 문서에서 인증이 필요한 API를 테스트하려면?

**A**:
1. `/auth/login`으로 로그인하여 `access_token` 복사
2. Swagger 페이지 우측 상단 "Authorize" 버튼 클릭
3. `Bearer {access_token}` 형식으로 입력
4. 이후 모든 요청에 자동으로 토큰이 포함됩니다

---

### Q7. 회비 내보내기 파일은 어떻게 다운로드하나요?

**A**: `/admin/dues/export.xlsx` 엔드포인트는 파일 스트림을 반환합니다.

```javascript
async function downloadDuesReport(period) {
  const token = localStorage.getItem('access_token');

  const response = await fetch(
    `http://localhost:8000/admin/dues/export.xlsx?period=${period}`,
    {
      headers: { 'Authorization': `Bearer ${token}` }
    }
  );

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `dues_${period}.xlsx`;
  a.click();
}
```

---

### Q8. 권한별 접근 가능한 엔드포인트는?

| 권한 | 접근 가능 엔드포인트 |
|------|---------------------|
| **GUEST** | 로그인, 프로필 조회, 프로필 수정, 로그아웃 (제한적) |
| **MEMBER** | GUEST 권한 + 회비 조회/납부, 전체 회원 목록 조회 |
| **ADMIN** | MEMBER 권한 + 관리자 전용 API (회원 관리, 회비 관리, 로그 조회) |
| **SUPERADMIN** | 모든 API + 관리자 권한 변경 |

---

**마지막 업데이트**: 2026년 1월 21일 | **버전**: 1.0
