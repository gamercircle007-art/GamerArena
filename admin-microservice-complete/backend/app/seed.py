"""Seed admin roles and default super-admin account."""

import asyncio

from sqlalchemy import select

from app.models.admin_user import AdminRole, AdminRolePermission, AdminUser
from app.models.base import Base, SessionLocal, engine
from app.security import hash_password

ROLE_PERMISSIONS = {
    "super_admin": ["*"],
    "admin": ["view_users", "ban_users", "delete_users", "view_parlors", "view_platform_analytics"],
}

DEFAULT_ADMIN = {
    "username": "admin",
    "email": "admin@gameconnect.in",
    "name": "GameConnect Admin",
    "phone": "+919999999999",
    "password": "Admin@123",
}


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        result = await db.execute(select(AdminUser).where(AdminUser.username == DEFAULT_ADMIN["username"]))
        if result.scalar_one_or_none():
            print("Admin user already exists — skipping seed.")
            return

        role_map: dict[str, AdminRole] = {}
        for role_name, perms in ROLE_PERMISSIONS.items():
            role = AdminRole(
                name=role_name,
                display_name=role_name.replace("_", " ").title(),
                is_system_role=True,
            )
            db.add(role)
            await db.flush()
            for perm in perms:
                db.add(AdminRolePermission(role_id=role.id, permission=perm))
            role_map[role_name] = role

        admin = AdminUser(
            username=DEFAULT_ADMIN["username"],
            email=DEFAULT_ADMIN["email"],
            name=DEFAULT_ADMIN["name"],
            phone=DEFAULT_ADMIN["phone"],
            password_hash=hash_password(DEFAULT_ADMIN["password"]),
            role_id=role_map["super_admin"].id,
            is_active=True,
        )
        db.add(admin)
        await db.commit()

        print("Admin microservice seeded.")
        print(f"  Username: {DEFAULT_ADMIN['username']}")
        print(f"  Password: {DEFAULT_ADMIN['password']}")
        print(f"  Phone:    {DEFAULT_ADMIN['phone']}  OTP: 123456")


if __name__ == "__main__":
    asyncio.run(seed())