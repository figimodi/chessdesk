from app.models.user import UserRole
from app.schemas.common import ORMModel
from pydantic import EmailStr, Field, field_validator


class UserRead(ORMModel):
    id: int
    email: EmailStr
    username: str
    role: UserRole
    is_active: bool
    email_confirmed: bool
    must_change_password: bool


class UserCreate(ORMModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class UserUpdate(ORMModel):
    username: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    is_active: bool | None = None

    @field_validator("username")
    @classmethod
    def normalize_optional_username(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip().lower()


class PublicRegistrationRequest(ORMModel):
    email: EmailStr
    username: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        return value.strip().lower()


class EmailConfirmationRequest(ORMModel):
    token: str = Field(min_length=10, max_length=2000)


class EmailConfirmationResendRequest(ORMModel):
    email: EmailStr


class MessageResponse(ORMModel):
    message: str


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
