import pytest

from app.models.user import UserRole
from app.services import auth as auth_service
from app.services import user as user_service


async def _create_user_and_token(session_factory, *, email: str, username: str, role: UserRole = UserRole.user):
    async with session_factory() as session:
        user = await user_service.create_user(
            session,
            email=email,
            username=username,
            password="password123",
            role=role,
            email_confirmed=True,
        )
    return user, auth_service.create_access_token(user.id)


@pytest.mark.asyncio
async def test_admin_can_create_update_and_delete_user(client, session_factory):
    _, admin_token = await _create_user_and_token(
        session_factory,
        email="admin-users@example.com",
        username="adminusers",
        role=UserRole.admin,
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    create_response = await client.post(
        "/api/v1/admin/users/",
        headers=headers,
        json={
            "email": "managed@example.com",
            "username": "manageduser",
            "password": "password123",
        },
    )
    assert create_response.status_code == 201
    created_payload = create_response.json()

    list_response = await client.get("/api/v1/admin/users/", headers=headers)
    assert list_response.status_code == 200
    assert any(item["id"] == created_payload["id"] for item in list_response.json())

    update_response = await client.patch(
        f"/api/v1/admin/users/{created_payload['id']}",
        headers=headers,
        json={"username": "manageduser2", "is_active": False},
    )
    assert update_response.status_code == 200
    assert update_response.json()["username"] == "manageduser2"
    assert update_response.json()["is_active"] is False

    delete_response = await client.delete(f"/api/v1/admin/users/{created_payload['id']}", headers=headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["ok"] is True


@pytest.mark.asyncio
async def test_admin_cannot_delete_own_account(client, session_factory):
    admin, admin_token = await _create_user_and_token(
        session_factory,
        email="admin-self@example.com",
        username="adminself",
        role=UserRole.admin,
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    response = await client.delete(f"/api/v1/admin/users/{admin.id}", headers=headers)

    assert response.status_code == 409
    assert response.json()["message"] == "Non puoi eliminare l'account attualmente in uso"


@pytest.mark.asyncio
async def test_non_admin_cannot_access_admin_users_routes(client, session_factory):
    _, user_token = await _create_user_and_token(
        session_factory,
        email="plain-user@example.com",
        username="plainuser",
    )

    response = await client.get("/api/v1/admin/users/", headers={"Authorization": f"Bearer {user_token}"})

    assert response.status_code == 403
    assert response.json()["message"] == "Permessi amministratore richiesti"


@pytest.mark.asyncio
async def test_admin_user_routes_handle_conflicts_and_not_found(client, session_factory):
    admin, admin_token = await _create_user_and_token(
        session_factory,
        email="admin-conflicts@example.com",
        username="adminconflicts",
        role=UserRole.admin,
    )
    await _create_user_and_token(
        session_factory,
        email="existing@example.com",
        username="existinguser",
    )
    headers = {"Authorization": f"Bearer {admin_token}"}

    duplicate_email = await client.post(
        "/api/v1/admin/users/",
        headers=headers,
        json={
            "email": "existing@example.com",
            "username": "anotheruser",
            "password": "password123",
        },
    )
    assert duplicate_email.status_code == 409

    duplicate_username = await client.post(
        "/api/v1/admin/users/",
        headers=headers,
        json={
            "email": "fresh@example.com",
            "username": "existinguser",
            "password": "password123",
        },
    )
    assert duplicate_username.status_code == 409

    missing_update = await client.patch(
        "/api/v1/admin/users/99999",
        headers=headers,
        json={"username": "nobody"},
    )
    assert missing_update.status_code == 404

    deactivate_admin = await client.patch(
        f"/api/v1/admin/users/{admin.id}",
        headers=headers,
        json={"is_active": False},
    )
    assert deactivate_admin.status_code == 409

    missing_delete = await client.delete("/api/v1/admin/users/99999", headers=headers)
    assert missing_delete.status_code == 404

    update_with_taken_username = await client.patch(
        f"/api/v1/admin/users/{admin.id}",
        headers=headers,
        json={"username": "existinguser"},
    )
    assert update_with_taken_username.status_code == 409

    self_delete = await client.delete(f"/api/v1/admin/users/{admin.id}", headers=headers)
    assert self_delete.status_code == 409
