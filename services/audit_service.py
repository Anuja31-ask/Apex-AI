from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.security_event import SecurityEvent


def log_audit_event(
    db: Session,
    action: str,
    user_id: Optional[UUID] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict] = None,
):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        details=details,
    )
    db.add(entry)
    db.commit()


def log_security_event(
    db: Session,
    event_type: str,
    severity: str = "LOW",
    user_id: Optional[UUID] = None,
    description: Optional[str] = None,
    ip_address: Optional[str] = None,
    event_metadata: Optional[dict] = None,
):
    entry = SecurityEvent(
        user_id=user_id,
        event_type=event_type,
        severity=severity,
        description=description,
        ip_address=ip_address,
        event_metadata=event_metadata,
    )
    db.add(entry)
    db.commit()
