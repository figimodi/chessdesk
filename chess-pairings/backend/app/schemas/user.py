from app.models.user import UserRole
from app.schemas.common import ORMModel
from pydantic import EmailStr, Field


class UserRead(ORMModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    must_change_password: bool


class UserCreate(ORMModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(ORMModel):
    username: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None


class LoginRequest(ORMModel):
    username: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)


class AuthToken(ORMModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class PasswordChangeRequest(ORMModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
