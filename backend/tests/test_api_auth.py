"""Authentication and access control."""

from __future__ import annotations

from tests.conftest import STAFF_PASSWORD, login, owner_login, owner_with_vehicles


async def test_staff_login_and_me(client):
    tokens = await login(client, "manager@autopredict.local")
    assert tokens["role"] == "manager"
    me = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "manager@autopredict.local"


async def test_wrong_password_and_unknown_user_look_the_same(client):
    a = await client.post("/api/auth/login", json={"email": "ops@autopredict.local", "password": "nope"})
    b = await client.post("/api/auth/login", json={"email": "ghost@autopredict.local", "password": "nope"})
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


async def test_login_is_rate_limited(client):
    codes = [
        (await client.post("/api/auth/login", json={"email": "ops@autopredict.local", "password": "bad"})).status_code for _ in range(12)
    ]
    assert codes[-1] == 429


async def test_refresh_rotates_and_detects_reuse(client):
    tokens = await login(client)
    first = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert first.status_code == 200
    # Reusing the rotated token signs the user out everywhere.
    reuse = await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    assert reuse.status_code == 401
    after = await client.post("/api/auth/refresh", json={"refresh_token": first.json()["refresh_token"]})
    assert after.status_code == 401


async def test_logout_revokes_refresh_token(client):
    tokens = await login(client)
    assert (await client.post("/api/auth/logout", json={"refresh_token": tokens["refresh_token"]})).status_code == 204
    assert (await client.post("/api/auth/refresh", json={"refresh_token": tokens["refresh_token"]})).status_code == 401


async def test_owner_otp_links_existing_owner(client):
    owner, codes = await owner_with_vehicles(1)
    tokens = await owner_login(client, owner.phone)
    assert tokens["role"] == "owner"
    assert tokens["customer_id"] == owner.code
    mine = await client.get("/api/me/vehicles", headers={"Authorization": f"Bearer {tokens['access_token']}"})
    assert sorted(v["vehicle_id"] for v in mine.json()) == sorted(codes)


async def test_wrong_otp_rejected(client):
    owner, _ = await owner_with_vehicles(2)
    await client.post("/api/auth/otp/send", json={"phone": owner.phone})
    r = await client.post("/api/auth/otp/verify", json={"phone": owner.phone, "otp": "000000"})
    assert r.status_code in (400, 401)


async def test_new_phone_creates_owner_needing_profile(client):
    tokens = await owner_login(client, "+919999000111")
    h = {"Authorization": f"Bearer {tokens['access_token']}"}
    assert (await client.get("/api/auth/me", headers=h)).json()["needs_profile"] is True
    r = await client.post("/api/auth/register", headers=h, json={"name": "Test Owner", "city": "Pune"})
    assert r.status_code == 200
    assert (await client.get("/api/auth/me", headers=h)).json()["needs_profile"] is False


async def test_owner_cannot_use_password_login(client):
    r = await client.post("/api/auth/login", json={"email": "anyone@example.com", "password": STAFF_PASSWORD})
    assert r.status_code == 401


# ── Access control ────────────────────────────────────────────────────────────


async def test_requests_without_token_are_rejected(client):
    for path in ("/api/vehicles", "/api/bookings", "/api/dashboard/summary", "/api/analytics/revenue"):
        assert (await client.get(path)).status_code == 401, path


async def test_owner_sees_only_own_data(client, owner_headers):
    headers, codes = owner_headers
    vehicles = (await client.get("/api/vehicles", headers=headers)).json()
    assert {v["vehicle_id"] for v in vehicles} == set(codes)
    _, other_codes = await owner_with_vehicles(5)
    r = await client.get(f"/api/vehicles/{other_codes[0]}", headers=headers)
    assert r.status_code == 404  # not 403: don't reveal it exists


async def test_owner_blocked_from_staff_endpoints(client, owner_headers):
    headers, _ = owner_headers
    for path in ("/api/dashboard/summary", "/api/analytics/fleet", "/api/conversations", "/api/bookings/today"):
        assert (await client.get(path, headers=headers)).status_code == 403, path
