import pytest

from app.models.user import UserRole
from app.services import auth as auth_service
from app.services import user as user_service


async def _create_admin_headers(session_factory):
    async with session_factory() as session:
        admin = await user_service.create_user(
            session,
            email="admin-pairings@example.com",
            username="adminpairings",
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
            "name": "Pairings Team Test",
            "type": "team",
            "format": "swiss",
            "time_control": "90+30",
            "start_date": "2026-07-01",
            "end_date": "2026-07-03",
            "rounds_count": 1,
            "pairings_system": "dutch",
            "tie_breaks": ["individual_points", "head_to_head", "weighted_sonneborn"],
            "is_elo_rated": False,
            "max_players_per_team": 4,
            "boards_per_match": 2,
            "enforce_board_order": False,
            "match_points_win": 2,
            "match_points_draw": 1,
            "match_points_loss": 0,
            "venue": "Roma",
            "description": "Pairings flow",
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
async def test_generate_reorder_update_and_delete_latest_round(client, session_factory):
    headers = await _create_admin_headers(session_factory)
    tournament_id = await _create_team_tournament(client, headers)

    player_ids = [
        await _create_player(client, headers, "Rossi, Mario", "20000001"),
        await _create_player(client, headers, "Bianchi, Luigi", "20000002"),
        await _create_player(client, headers, "Verdi, Anna", "20000003"),
        await _create_player(client, headers, "Neri, Carla", "20000004"),
    ]

    for player_id in player_ids:
        assign_response = await client.post(
            f"/api/v1/admin/tournaments/{tournament_id}/players",
            headers=headers,
            json={"player_id": player_id},
        )
        assert assign_response.status_code == 200

    team_1 = await client.post(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/",
        headers=headers,
        json={"name": "Nord"},
    )
    team_2 = await client.post(
        f"/api/v1/admin/tournaments/{tournament_id}/teams/",
        headers=headers,
        json={"name": "Sud"},
    )
    assert team_1.status_code == 201
    assert team_2.status_code == 201
    team_1_id = team_1.json()["id"]
    team_2_id = team_2.json()["id"]

    for team_id, member_ids in ((team_1_id, player_ids[:2]), (team_2_id, player_ids[2:])):
        for player_id in member_ids:
            member_response = await client.post(
                f"/api/v1/admin/tournaments/{tournament_id}/teams/{team_id}/members",
                headers=headers,
                json={"player_id": player_id},
            )
            assert member_response.status_code == 200

    close_response = await client.post(
        f"/api/v1/admin/tournaments/{tournament_id}/close-registration",
        headers=headers,
    )
    assert close_response.status_code == 200
    assert close_response.json()["is_registration_closed"] is True

    generate_response = await client.post(
        f"/api/v1/admin/tournaments/{tournament_id}/pairings/generate",
        headers=headers,
    )
    assert generate_response.status_code == 200
    round_payload = generate_response.json()["round"]
    assert round_payload["number"] == 1
    assert len(round_payload["pairings"]) == 2

    first_pairing = round_payload["pairings"][0]
    second_pairing = round_payload["pairings"][1]

    reorder_response = await client.patch(
        f"/api/v1/admin/tournaments/{tournament_id}/pairings/board-order/{first_pairing['id']}",
        headers=headers,
        json={"side": "white", "target_pairing_id": second_pairing["id"]},
    )
    assert reorder_response.status_code == 200
    assert reorder_response.json()["ok"] is True

    for pairing in (first_pairing, second_pairing):
        result_response = await client.patch(
            f"/api/v1/admin/tournaments/{tournament_id}/pairings/results/{pairing['id']}",
            headers=headers,
            json={"result": "1-0"},
        )
        assert result_response.status_code == 200
        assert result_response.json()["ok"] is True

    delete_round = await client.delete(
        f"/api/v1/admin/tournaments/{tournament_id}/pairings/latest-round",
        headers=headers,
    )
    assert delete_round.status_code == 200
    assert delete_round.json()["ok"] is True
