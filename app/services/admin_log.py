from sqlalchemy.orm import Session
from app.models.admin_log import AdminActionLog, AdminAction

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
