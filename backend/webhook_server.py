"""
API server entry point.

    python webhook_server.py              # dev server on API_PORT (default 8001)
    uvicorn webhook_server:app --port 8001

The application itself lives in `api/app.py`; routes in `api/routers/`.
Before the first run: `alembic upgrade head` and (for demo data) `python -m sim.build`.
"""

from api.app import create_app
from core.settings import get_settings

app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level=settings.log_level.lower())
