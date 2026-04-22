import pytest

from app.models.user import UserRole
from app.services import auth as auth_service
from app.services import user as user_service


async def _create_admin_and_headers(client, session_factory):
    async with session_factory() as session:
        admin = await user_service.create_user(
            session,
            email="admin-teams@example.com",
            username="adminteams",
            password="password123",
            role=UserRole.admin,
            email_confirmed=True,
        )
    token = auth_service.create_access_token(admin.id)
    return {"Authorization": f"Bearer {token}"}


async def _create_team_tournament(client, headers):
    response = await client.post(
        "/api/v1/admin/tournaments/",
        headers=headers,
        json={
            "name": "Gestione Squadre",
            "type": "team",
            "format": "swiss",
            "time_control": "90+30",
            "start_date": "2026-06-01",
            "end_date": "2026-06-03",
            "rounds_count": 3,
            "pairings_system": "dutch",
            "tie_breaks": ["individual_points", "head_to_head", "weighted_sonneborn"],
            "is_elo_rated": False,
            "max_players_per_team": 4,
            "boards_per_match": 2,
            "enforce_board_order": False,
            "match_points_win": 2,
            "match_points_draw": 1,
            "match_points_loss": 0,
            "venue": "Milano",
            "description": "Test gestione squadre",
            "is_published": True,
            "is_private": False,
            "round_schedule": [],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


async def _create_player(client, headers, full_name: str, fide_id: str):
    response = await client.post(
        "/api/v1/admin/players/",
        headers=headers,
        json={"full_name": full_name, "fide_id": fide_id, "federation": "ITA", "rating": 1800},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_admin_team_crud_and_member_management(client, session_factory):
    headers = await _create_admin_and_headers(client, session_factory)
    tournament_id = await _create_team_tournament(client, headers)

    player_1_id = await _create_player(client, headers, "Rossi, Mario", "10000001")
    player_2_id = await _create_player(client, headers, "Bianchi, Luigi", "10000002")

    assign_player_1 = await client.post(
        f"/api/v1/admin/tournaments/{tournament_id}/players",
        headers=headers,
        json={"player_id": player_1_id},
    )
    assign_player_2 = await client.post(
        f"/api/v1/admin/tournaments/{tournament_id}/players",
        headers=headers,
        json={"player_id": player_2_id},
    )
    assert assign_player_1.status_code == 200
    assert assign_player_2.status_code == 200

    create_team = await client.post(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/",
        headers=headers,
        json={"name": "Orizzonte"},
    )
    assert create_team.status_code == 201
    team_id = create_team.json()["id"]

    update_team = await client.put(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}",
        headers=headers,
        json={"name": "Orizzonte A"},
    )
    assert update_team.status_code == 200
    assert update_team.json()["name"] == "Orizzonte A"

    add_member_1 = await client.post(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/members",
        headers=headers,
        json={"player_id": player_1_id},
    )
    add_member_2 = await client.post(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/members",
        headers=headers,
        json={"player_id": player_2_id},
    )
    assert add_member_1.status_code == 200
    assert add_member_2.status_code == 200

    reorder_members = await client.patch(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/members/order",
        headers=headers,
        json={"player_ids": [player_2_id, player_1_id]},
    )
    assert reorder_members.status_code == 200
    assert [member["player_id"] for member in reorder_members.json()["members"]] == [player_2_id, player_1_id]

    update_availability = await client.patch(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/availability",
        headers=headers,
        json={"round_number": 1, "is_available": False},
    )
    assert update_availability.status_code == 200

    update_status = await client.patch(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/status",
        headers=headers,
        json={"is_active": False},
    )
    assert update_status.status_code == 200
    assert update_status.json()["is_active"] is False

    update_lineup = await client.patch(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/lineup",
        headers=headers,
        json={"player_id": player_1_id, "round_number": 1, "is_selected": True},
    )
    assert update_lineup.status_code == 200

    remove_member = await client.delete(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/members/{player_2_id}",
        headers=headers,
    )
    assert remove_member.status_code == 200
    assert len(remove_member.json()["members"]) == 1

    list_teams = await client.get(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/",
        headers=headers,
    )
    assert list_teams.status_code == 200
    assert any(team["id"] == team_id for team in list_teams.json())

    delete_team = await client.delete(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}",
        headers=headers,
    )
    assert delete_team.status_code == 200
    assert delete_team.json()["ok"] is True
