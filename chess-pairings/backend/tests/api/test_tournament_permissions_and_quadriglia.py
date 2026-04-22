import pytest

from app.models.user import UserRole
from app.services import auth as auth_service
from app.services import user as user_service


@pytest.mark.asyncio
async def test_admin_can_view_private_tournament_of_other_owner(client, session_factory):
    async with session_factory() as session:
        owner = await user_service.create_user(
            session,
            email="owner@example.com",
            username="owneruser",
            password="password123",
            email_confirmed=True,
        )
        admin = await user_service.create_user(
            session,
            email="admin@example.com",
            username="adminuser",
            password="password123",
            role=UserRole.admin,
            email_confirmed=True,
        )

    owner_token = auth_service.create_access_token(owner.id)
    admin_token = auth_service.create_access_token(admin.id)

    create_response = await client.post(
        "/api/v1/admin/tournaments/",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "name": "Privato Owner",
            "type": "individual",
            "format": "swiss",
            "time_control": "90+30",
            "start_date": "2026-05-01",
            "end_date": "2026-05-02",
            "rounds_count": 3,
            "pairings_system": "dutch",
            "tie_breaks": ["buchholz_cut1", "buchholz", "sonneborn_berger"],
            "is_elo_rated": False,
            "venue": "Torino",
            "description": "Privato",
            "is_published": False,
            "is_private": True,
            "round_schedule": [],
        },
    )
    tournament_id = create_response.json()["id"]

    list_response = await client.get("/api/v1/tournaments/", headers={"Authorization": f"Bearer {admin_token}"})
    detail_response = await client.get(f"/api/v1/tournaments/{tournament_id}", headers={"Authorization": f"Bearer {admin_token}"})

    assert list_response.status_code == 200
    assert any(item["id"] == tournament_id for item in list_response.json())
    assert detail_response.status_code == 200


@pytest.mark.asyncio
async def test_create_quadriglia_tournament(client, session_factory):
    async with session_factory() as session:
        owner = await user_service.create_user(
            session,
            email="quadriglia-owner@example.com",
            username="quadrigliaowner",
            password="password123",
            email_confirmed=True,
        )

    owner_token = auth_service.create_access_token(owner.id)
    create_response = await client.post(
        "/api/v1/admin/tournaments/",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={
            "name": "Quadriglia Test",
            "type": "quadriglia",
            "format": "swiss",
            "time_control": "90+30",
            "start_date": "2026-05-01",
            "end_date": "2026-05-03",
            "rounds_count": 3,
            "pairings_system": "dutch",
            "tie_breaks": ["head_to_head"],
            "is_elo_rated": False,
            "max_players_per_team": 2,
            "boards_per_match": 2,
            "enforce_board_order": False,
            "match_points_win": 2,
            "match_points_draw": 1,
            "match_points_loss": 0,
            "venue": "Test",
            "description": "Quadriglia",
            "is_published": True,
            "is_private": False,
            "round_schedule": [],
        },
    )

    assert create_response.status_code == 201
    payload = create_response.json()
    assert payload["type"] == "quadriglia"
    assert payload["max_players_per_team"] == 2
    assert payload["boards_per_match"] == 2
    assert payload["tie_breaks"] == ["head_to_head"]
