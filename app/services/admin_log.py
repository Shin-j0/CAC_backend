"""
services/admin_log.py

관리자 행위 로그 기록 서비스.

이 파일은 관리자(Admin)가 수행한 주요 행위를
AdminActionLog 테이블에 기록하는 역할을 담당한다.

라우터 또는 서비스 계층에서 호출되며,
로그 기록 자체는 DB에만 영향을 주고
비즈니스 흐름에는 개입하지 않는다.

설계 원칙:
- 로그 기록 실패가 주 기능을 방해하지 않도록 단순화
- 로그 데이터는 수정/삭제하지 않는 것을 전제로 설계

"""

from sqlalchemy.orm import Session
from app.models.admin_log import AdminActionLog, AdminAction


"""
관리자 행위 로그 기록 함수

- actor_id       : 행위를 수행한 관리자 ID
- action         : 수행된 관리자 행위 유형
- target_user_id : 행위 대상 사용자 ID (선택)
- before_role    : 변경 전 권한 (선택)
- after_role     : 변경 후 권한 (선택)
- ip             : 요청 IP 주소 (선택)
- user_agent     : 요청 User-Agent (선택)

NOTE:
- db.commit()은 호출 측(라우터/서비스)에서 수행

"""
def write_admin_log(
    db: Session,
    *,
    actor_id,
    action: AdminAction,
    target_user_id=None,
    before_role=None,
    after_role=None,
    ip=None,
    user_agent=None,
):
    log = AdminActionLog(
        actor_id=actor_id,
        action=action,
        target_user_id=target_user_id,
        before_role=before_role,
        after_role=after_role,
        ip=ip,
        user_agent=user_agent,
    )
    db.add(log)
