import uuid
from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from shared.database.base import BaseModel


class SubUser(BaseModel):
    """
    Represents an end-user of an Enterprise customer.
    Created automatically via JIT provisioning when an Enterprise
    makes a request on behalf of this sub-user.
    """
    __tablename__ = "sub_users"

    # Auto-generated primary key
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # The enterprise user this sub-user belongs to
    enterprise_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # The identifier provided by the enterprise
    external_user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # Optional status for ban/suspend
    status: Mapped[str] = mapped_column(String(50), nullable=False, default='active')

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to the enterprise user
    enterprise_user = relationship("User")

    def __repr__(self):
        return f"<SubUser(id={self.id}, external_user_id='{self.external_user_id}')>"
