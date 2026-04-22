import pytest

from app.services import auth as auth_service
from app.services import user as user_service


async def _create_admin_and_tournament(client, session_factory, *, max_players_per_team: int = 4):
    async with session_factory() as session:
        admin = await user_service.create_user(
            session,
            email="admin-team@example.com",
            username="adminteam",
            password="password123",
            role="admin",
            email_confirmed=True,
        )

    token = auth_service.create_access_token(admin.id)
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.post(
        "/api/v1/admin/tournaments/",
        headers=headers,
        json={
            "name": "Team Test Tournament",
            "type": "team",
            "format": "swiss",
            "time_control": "90+30",
            "start_date": "2026-05-01",
            "end_date": "2026-05-03",
            "rounds_count": 3,
            "pairings_system": "dutch",
            "tie_breaks": ["individual_points", "head_to_head", "weighted_sonneborn"],
            "is_elo_rated": False,
            "max_players_per_team": max_players_per_team,
            "boards_per_match": 4 if max_players_per_team >= 4 else max_players_per_team,
            "enforce_board_order": False,
            "match_points_win": 2,
            "match_points_draw": 1,
            "match_points_loss": 0,
            "venue": "Test Venue",
            "description": "Team flow test",
            "is_published": True,
            "is_private": False,
            "round_schedule": [],
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_public_team_with_manual_teammates(client, session_factory):
    tournament_id = await _create_admin_and_tournament(client, session_factory)

    response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/create",
        json={
            "team_name": "Leoni",
            "teammate_player_ids": [],
            "teammate_fide_ids": [],
            "teammate_manual_entries": [
                {"first_name": "Mario", "last_name": "Rossi"},
                {"first_name": "Luigi", "last_name": "Bianchi"},
            ],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["team_name"] == "Leoni"
    assert len(payload["pin"]) == 4
    assert payload["members_count"] == 2

    detail_response = await client.get(f"/api/v1/tournaments/{tournament_id}")
    detail_payload = detail_response.json()
    assert detail_response.status_code == 200
    assert detail_payload["teams"][0]["members_count"] == 2
    assert [member["full_name"] for member in detail_payload["teams"][0]["members"]] == ["Rossi, Mario", "Bianchi, Luigi"]


@pytest.mark.asyncio
async def test_join_public_team_with_valid_pin(client, session_factory):
    tournament_id = await _create_admin_and_tournament(client, session_factory)
    create_response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/create",
        json={
            "team_name": "Falchi",
            "teammate_player_ids": [],
            "teammate_fide_ids": [],
            "teammate_manual_entries": [{"first_name": "Anna", "last_name": "Verdi"}],
        },
    )
    team_payload = create_response.json()

    join_response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/join",
        json={
            "team_id": team_payload["team_id"],
            "pin": team_payload["pin"],
            "registrant": {"first_name": "Carla", "last_name": "Neri"},
        },
    )

    assert join_response.status_code == 200
    assert join_response.json()["team_name"] == "Falchi"


@pytest.mark.asyncio
async def test_join_public_team_rejects_invalid_pin(client, session_factory):
    tournament_id = await _create_admin_and_tournament(client, session_factory)
    create_response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/create",
        json={
            "team_name": "Lupi",
            "teammate_player_ids": [],
            "teammate_fide_ids": [],
            "teammate_manual_entries": [{"first_name": "Piero", "last_name": "Blu"}],
        },
    )
    team_payload = create_response.json()

    join_response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/join",
        json={
            "team_id": team_payload["team_id"],
            "pin": "9999",
            "registrant": {"first_name": "Sara", "last_name": "Rosa"},
        },
    )

    assert join_response.status_code == 409
    assert join_response.json()["message"] == "PIN squadra non valido"


@pytest.mark.asyncio
async def test_create_public_team_rejects_duplicate_team_name(client, session_factory):
    tournament_id = await _create_admin_and_tournament(client, session_factory)
    payload = {
        "team_name": "Aquilotti",
        "teammate_player_ids": [],
        "teammate_fide_ids": [],
        "teammate_manual_entries": [{"first_name": "Marco", "last_name": "Rossi"}],
    }

    first_response = await client.post(f"/api/v1/tournaments/{tournament_id}/team-registration/create", json=payload)
    duplicate_response = await client.post(f"/api/v1/tournaments/{tournament_id}/team-registration/create", json=payload)

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["message"] == "Esiste gia una squadra con questo nome"


@pytest.mark.asyncio
async def test_join_public_team_rejects_player_already_in_team(client, session_factory):
    tournament_id = await _create_admin_and_tournament(client, session_factory)
    create_response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/create",
        json={
            "team_name": "Draghi",
            "teammate_player_ids": [],
            "teammate_fide_ids": [],
            "teammate_manual_entries": [{"first_name": "Giulia", "last_name": "Viola"}],
        },
    )
    team_payload = create_response.json()

    join_response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/join",
        json={
            "team_id": team_payload["team_id"],
            "pin": team_payload["pin"],
            "registrant": {"first_name": "Giulia", "last_name": "Viola"},
        },
    )

    assert join_response.status_code == 409
    assert join_response.json()["message"] == "Il giocatore risulta gia assegnato a una squadra"


@pytest.mark.asyncio
async def test_create_public_team_enforces_max_players_per_team(client, session_factory):
    tournament_id = await _create_admin_and_tournament(client, session_factory, max_players_per_team=1)

    response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/create",
        json={
            "team_name": "Stelle",
            "teammate_player_ids": [],
            "teammate_fide_ids": [],
            "teammate_manual_entries": [
                {"first_name": "Luca", "last_name": "Gialli"},
                {"first_name": "Marta", "last_name": "Bianchi"},
            ],
        },
    )

    assert response.status_code == 409
    assert response.json()["message"] == "La squadra ha raggiunto il numero massimo di giocatori."


@pytest.mark.asyncio
async def test_create_public_team_ignores_legacy_captain_payload(client, session_factory):
    tournament_id = await _create_admin_and_tournament(client, session_factory)

    first_team_response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/create",
        json={
            "team_name": "Alfieri",
            "teammate_player_ids": [],
            "teammate_fide_ids": [],
            "teammate_manual_entries": [{"first_name": "Giulia", "last_name": "Viola"}],
        },
    )
    assert first_team_response.status_code == 200

    second_team_response = await client.post(
        f"/api/v1/tournaments/{tournament_id}/team-registration/create",
        json={
            "team_name": "Cavalli",
            "captain": {"first_name": "Giulia", "last_name": "Viola"},
            "teammate_player_ids": [],
            "teammate_fide_ids": [],
            "teammate_manual_entries": [{"first_name": "Marta", "last_name": "Bianchi"}],
        },
    )

    assert second_team_response.status_code == 200
    payload = second_team_response.json()
    assert payload["team_name"] == "Cavalli"
    assert payload["members_count"] == 1
