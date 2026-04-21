from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tournament import Tournament
from app.models.user import User, UserRole
from app.services.auth import hash_password, verify_password


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower().strip()))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username.strip()))
    return result.scalar_one_or_none()


async def list_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.role.desc(), User.username.asc(), User.email.asc()))
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    password: str,
    role: UserRole = UserRole.user,
    is_active: bool = True,
    must_change_password: bool = False,
) -> User:
    user = User(
        email=email.lower().strip(),
        username=username.strip(),
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
        must_change_password=must_change_password,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def ensure_admin_user(db: AsyncSession, *, email: str, username: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    if user is None:
        return await create_user(
            db,
            email=email,
            username=username,
            password=password,
            role=UserRole.admin,
            is_active=True,
            must_change_password=False,
        )

    user.username = username.strip()
    user.password_hash = hash_password(password)
    user.role = UserRole.admin
    user.is_active = True
    user.must_change_password = False
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def update_user(
    db: AsyncSession,
    user: User,
    *,
    username: str | None = None,
    password: str | None = None,
    is_active: bool | None = None,
    must_change_password: bool | None = None,
) -> User:
    if username is not None:
        user.username = username.strip()
    if password is not None:
        user.password_hash = hash_password(password)
    if is_active is not None:
        user.is_active = is_active
    if must_change_password is not None:
        user.must_change_password = must_change_password
    await db.commit()
    await db.refresh(user)
    return user


async def change_password(
    db: AsyncSession,
    user: User,
    *,
    current_password: str,
    new_password: str,
) -> User:
    if not verify_password(current_password, user.password_hash):
        return None

    user.password_hash = hash_password(new_password)
    user.must_change_password = False
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User, *, reassigned_owner_id: int) -> None:
    await db.execute(
        update(Tournament)
        .where(Tournament.owner_id == user.id)
        .values(owner_id=reassigned_owner_id)
    )
    await db.execute(delete(User).where(User.id == user.id))
    await db.commit()
