from pathlib import Path
import sys

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.api.deps import get_db
from app.core.rate_limit import reset_rate_limits
from app.main import app
from app.models.base import Base


@pytest_asyncio.fixture
async def session_factory():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def client(session_factory):
    async def override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
        yield async_client
    app.dependency_overrides.clear()
    reset_rate_limits()


@pytest.fixture
def outbox(monkeypatch):
    sent_messages: list[dict[str, str]] = []

    def fake_send_registration_confirmation(self, *, recipient_email: str, username: str, token: str) -> None:
        sent_messages.append(
            {
                "recipient_email": recipient_email,
                "username": username,
                "token": token,
            }
        )

    monkeypatch.setattr(
        "app.services.mail.MailService.send_registration_confirmation",
        fake_send_registration_confirmation,
    )
    return sent_messages
