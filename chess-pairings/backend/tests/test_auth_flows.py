import pytest
from sqlalchemy.exc import IntegrityError

from app.services import user as user_service


@pytest.mark.asyncio
async def test_register_normalizes_username_and_sends_confirmation(client, outbox, session_factory):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "new@example.com",
            "username": "  NewUser  ",
            "password": "password123",
        },
    )

    assert response.status_code == 201
    assert len(outbox) == 1
    assert outbox[0]["username"] == "newuser"

    async with session_factory() as session:
        user = await user_service.get_user_by_email(session, "new@example.com")
        assert user is not None
        assert user.username == "newuser"
        assert user.email_confirmed is False
        assert user.email_confirmation_sent_at is not None


@pytest.mark.asyncio
async def test_register_rejects_duplicate_email_and_username(client, outbox):
    first_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "username": "dupuser", "password": "password123"},
    )
    duplicate_email = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "username": "anotheruser", "password": "password123"},
    )
    duplicate_username = await client.post(
        "/api/v1/auth/register",
        json={"email": "other@example.com", "username": "DupUser", "password": "password123"},
    )

    assert first_response.status_code == 201
    assert duplicate_email.status_code == 409
    assert duplicate_email.json()["detail"] == "Esiste gia un account con questa email"
    assert duplicate_username.status_code == 409
    assert duplicate_username.json()["detail"] == "Esiste gia un account con questo username"


@pytest.mark.asyncio
async def test_db_enforces_unique_normalized_username(session_factory):
    async with session_factory() as session:
        await user_service.create_user(session, email="one@example.com", username="CaseUser", password="password123")
        with pytest.raises(IntegrityError):
            await user_service.create_user(session, email="two@example.com", username="caseuser", password="password123")


@pytest.mark.asyncio
async def test_login_is_blocked_until_email_is_confirmed(client, outbox):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wait@example.com", "username": "waituser", "password": "password123"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "waituser", "password": "password123"},
    )

    assert response.status_code == 403
    assert "confermare" in response.json()["detail"]


@pytest.mark.asyncio
async def test_resend_invalidates_previous_confirmation_token(client, outbox):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "confirm@example.com", "username": "confirmuser", "password": "password123"},
    )
    first_token = outbox[-1]["token"]

    resend_response = await client.post(
        "/api/v1/auth/resend-confirmation",
        json={"email": "confirm@example.com"},
    )
    second_token = outbox[-1]["token"]

    first_confirm = await client.post("/api/v1/auth/confirm-email", json={"token": first_token})
    second_confirm = await client.post("/api/v1/auth/confirm-email", json={"token": second_token})
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "confirmuser", "password": "password123"},
    )

    assert resend_response.status_code == 200
    assert first_confirm.status_code == 400
    assert "non e piu valido" in first_confirm.json()["detail"]
    assert second_confirm.status_code == 200
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_inactive_account_is_blocked_even_with_valid_password(client, session_factory):
    async with session_factory() as session:
        await user_service.create_user(
            session,
            email="inactive@example.com",
            username="inactiveuser",
            password="password123",
            is_active=False,
            email_confirmed=True,
        )

    response = await client.post(
        "/api/v1/auth/login",
        json={"username": "inactiveuser", "password": "password123"},
    )

    assert response.status_code == 403
    assert "disattivato" in response.json()["detail"]


@pytest.mark.asyncio
async def test_change_password_and_me_flow(client, session_factory):
    async with session_factory() as session:
        await user_service.create_user(
            session,
            email="profile@example.com",
            username="profileuser",
            password="password123",
            email_confirmed=True,
        )

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "profileuser", "password": "password123"},
    )
    token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {token}"}

    me_response = await client.get("/api/v1/auth/me", headers=auth_headers)
    wrong_change = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrongpass1", "new_password": "newpassword123"},
        headers=auth_headers,
    )
    correct_change = await client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "password123", "new_password": "newpassword123"},
        headers=auth_headers,
    )
    old_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "profileuser", "password": "password123"},
    )
    new_login = await client.post(
        "/api/v1/auth/login",
        json={"username": "profileuser", "password": "newpassword123"},
    )

    assert me_response.status_code == 200
    assert me_response.json()["username"] == "profileuser"
    assert wrong_change.status_code == 400
    assert correct_change.status_code == 200
    assert old_login.status_code == 401
    assert new_login.status_code == 200


@pytest.mark.asyncio
async def test_login_rate_limit_triggers_after_repeated_failures(client):
    for _ in range(5):
        response = await client.post(
            "/api/v1/auth/login",
            json={"username": "missinguser", "password": "password123"},
        )
        assert response.status_code == 401

    blocked_response = await client.post(
        "/api/v1/auth/login",
        json={"username": "missinguser", "password": "password123"},
    )

    assert blocked_response.status_code == 429
