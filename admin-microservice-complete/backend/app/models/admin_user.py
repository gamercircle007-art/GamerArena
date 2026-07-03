import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class AdminRole(Base):
    __tablename__ = "admin_roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100))
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=True)

    permissions: Mapped[list["AdminRolePermission"]] = relationship(back_populates="role", cascade="all, delete-orphan")
    users: Mapped[list["AdminUser"]] = relationship(back_populates="role")


class AdminRolePermission(Base):
    __tablename__ = "admin_role_permissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("admin_roles.id", ondelete="CASCADE"))
    permission: Mapped[str] = mapped_column(String(100), nullable=False)

    role: Mapped[AdminRole] = relationship(back_populates="permissions")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("admin_roles.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    role: Mapped[AdminRole | None] = relationship(back_populates="users")