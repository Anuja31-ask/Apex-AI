import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    action = Column(String, nullable=False)          # e.g. LOGIN_SUCCESS, DOCUMENT_UPLOADED
    resource_type = Column(String, nullable=True)    # e.g. "document", "user"
    resource_id = Column(String, nullable=True)       # id of the affected resource

    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    details = Column(JSON, nullable=True)             # extra context, never secrets

    user = relationship("User")