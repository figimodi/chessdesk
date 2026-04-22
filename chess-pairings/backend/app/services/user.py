from datetime import datetime, timezone

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
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


def normalize_username(username: str) -> str:
    return username.strip().lower()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == normalize_username(username)))
    return result.scalar_one_or_none()


async def get_users_by_username(db: AsyncSession, username: str) -> list[User]:
    result = await db.execute(select(User).where(User.username == normalize_username(username)).order_by(User.id.asc()))
    return list(result.scalars().all())


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
    email_confirmed: bool = True,
    email_confirmation_sent_at: datetime | None = None,
    must_change_password: bool = False,
) -> User:
    user = User(
        email=email.lower().strip(),
        username=normalize_username(username),
        password_hash=hash_password(password),
        role=role,
        is_active=is_active,
        email_confirmed=email_confirmed,
        email_confirmation_sent_at=email_confirmation_sent_at,
        must_change_password=must_change_password,
    )
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        return user
    except IntegrityError:
        await db.rollback()
        raise


async def ensure_admin_user(db: AsyncSession, *, email: str, username: str, password: str) -> User:
    user = await get_user_by_email(db, email)
    users_with_same_username = await get_users_by_username(db, username)

    for conflicting_user in users_with_same_username:
        if conflicting_user.email == email:
            continue
        conflicting_user.username = f"{username}-legacy-{conflicting_user.id}"

    if users_with_same_username:
        await db.commit()

    if user is None:
        user = next((item for item in users_with_same_username if item.email == email), None)
    if user is None:
        user = await create_user(
            db,
            email=email,
            username=username,
            password=password,
            role=UserRole.admin,
            is_active=True,
            email_confirmed=True,
            email_confirmation_sent_at=datetime.now(timezone.utc),
            must_change_password=False,
        )

    user.username = normalize_username(username)
    user.password_hash = hash_password(password)
    user.role = UserRole.admin
    user.is_active = True
    user.email_confirmed = True
    user.must_change_password = False
    result = await db.execute(select(User).where(User.role == UserRole.admin, User.id != user.id))
    other_admins = list(result.scalars().all())
    await db.execute(
        update(Tournament)
        .where(Tournament.owner_id.in_([admin.id for admin in other_admins]))
        .values(owner_id=user.id)
    )
    for other_admin in other_admins:
        other_admin.role = UserRole.user

    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    user = await get_user_by_username(db, username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def confirm_user_email(db: AsyncSession, user: User) -> User:
    user.email_confirmed = True
    await db.commit()
    await db.refresh(user)
    return user


async def mark_confirmation_sent(db: AsyncSession, user: User, *, sent_at: datetime) -> User:
    user.email_confirmation_sent_at = sent_at
    await db.commit()
    await db.refresh(user)
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
        user.username = normalize_username(username)
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


async def delete_user_without_reassignment(db: AsyncSession, user: User) -> None:
    await db.execute(delete(User).where(User.id == user.id))
    await db.commit()
