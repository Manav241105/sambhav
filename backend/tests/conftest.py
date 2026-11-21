"""
Test fixtures: a fresh SQLite database, migrated with Alembic and filled by
the simulator (small world), and an in-process HTTP client for the app.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

# Configure the app BEFORE anything imports core.settings (it is cached).
_TMP = Path(tempfile.mkdtemp(prefix="autopredict-test-"))
os.environ.update(
    {
        "ENV": "test",
        # CI also runs the suite on PostgreSQL by setting TEST_DATABASE_URL (must point at an empty database).
        "DATABASE_URL": os.environ.get("TEST_DATABASE_URL") or f"sqlite+aiosqlite:///{(_TMP / 'test.db').as_posix()}",
        "JWT_SECRET": "test-secret-" + "x" * 40,
        "DEMO_STAFF_PASSWORD": "test-staff-password",
        "ENABLE_BACKGROUND_DIAGNOSIS": "false",
        "REDIS_URL": "",
        "LOG_LEVEL": "WARNING",
    }
)

import httpx  # noqa: E402
import pytest  # noqa: E402
from sqlalchemy import select  # noqa: E402

from core import ratelimit  # noqa: E402
from db import models as m  # noqa: E402
from db.session import get_sessionmaker  # noqa: E402
from sim.build import build, migrate  # noqa: E402
from sim.world import SimConfig  # noqa: E402

STAFF_PASSWORD = os.environ["DEMO_STAFF_PASSWORD"]


def pytest_sessionstart(session):
    # Alembic runs its own event loop, so migrate before pytest-asyncio starts one.
    migrate(reset=False)


@pytest.fixture(scope="session", autouse=True)
async def seeded_db():
    await build(SimConfig(seed=7, owners=30, vehicles=40, platform_months=4), STAFF_PASSWORD)
    yield


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    for limiter in (ratelimit.login_limiter, ratelimit.otp_send_limiter, ratelimit.otp_verify_limiter):
        limiter.reset()


@pytest.fixture(scope="session")
async def client(seeded_db):
    from api.app import create_app

    app = create_app()
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def login(client: httpx.AsyncClient, email: str = "ops@autopredict.local") -> dict:
    r = await client.post("/api/auth/login", json={"email": email, "password": STAFF_PASSWORD})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
async def staff_headers(client) -> dict:
    return {"Authorization": f"Bearer {(await login(client))['access_token']}"}


async def owner_login(client: httpx.AsyncClient, phone: str) -> dict:
    sent = await client.post("/api/auth/otp/send", json={"phone": phone})
    assert sent.status_code == 200, sent.text
    r = await client.post("/api/auth/otp/verify", json={"phone": phone, "otp": sent.json()["debug_otp"]})
    assert r.status_code == 200, r.text
    return r.json()


async def owner_with_vehicles(n: int = 0) -> tuple[m.Owner, list[str]]:
    """The n-th demo owner and their vehicle codes."""
    async with get_sessionmaker()() as s:
        owner = (await s.scalars(select(m.Owner).order_by(m.Owner.id).offset(n).limit(1))).one()
        codes = (await s.scalars(select(m.Vehicle.code).where(m.Vehicle.owner_id == owner.id))).all()
        return owner, list(codes)


@pytest.fixture
async def owner_headers(client) -> tuple[dict, list[str]]:
    owner, codes = await owner_with_vehicles(0)
    tokens = await owner_login(client, owner.phone)
    return {"Authorization": f"Bearer {tokens['access_token']}"}, codes
