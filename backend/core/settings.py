"""
Application settings.

Single source of truth for everything that varies between environments
(database URL, secrets, external service credentials). Values come from
environment variables or a `.env` file next to the backend; nothing secret
is hardcoded here.

Static domain constants (priority thresholds, event names) stay in
`config.py` because they are product rules, not deployment settings.
"""

from __future__ import annotations

import json
import logging
import secrets
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

log = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent

# Values copied from old templates that must never count as "configured".
_PLACEHOLDER_MARKERS = ("your_", "your-", "changeme", "change-me", "xxxx", "<", "example")


def is_configured(value: str | None) -> bool:
    """True when a credential holds a real-looking value, not a placeholder."""
    if not value or not value.strip():
        return False
    lowered = value.strip().lower()
    return not any(marker in lowered for marker in _PLACEHOLDER_MARKERS)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR.parent / ".env", BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        env_ignore_empty=True,  # `DATABASE_URL=` in a copied template keeps the default
    )

    # ── Runtime ───────────────────────────────────────────────────────────
    env: Literal["dev", "test", "prod"] = "dev"
    log_level: str = "INFO"
    app_timezone: str = "Asia/Kolkata"  # timestamps are stored in UTC, shown in this zone
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    # NoDecode: accept the comma-separated form from .env, not only JSON.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
        ]
    )

    # ── Database / cache ──────────────────────────────────────────────────
    database_url: str = f"sqlite+aiosqlite:///{(BACKEND_DIR / 'autopredict.db').as_posix()}"
    database_echo: bool = False
    redis_url: str | None = None

    # ── Auth ──────────────────────────────────────────────────────────────
    jwt_secret: str | None = None
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 30
    refresh_token_ttl_days: int = 30
    otp_ttl_seconds: int = 300
    otp_max_attempts: int = 5

    # ── Demo data ─────────────────────────────────────────────────────────
    demo_staff_password: str | None = None  # used only by `python -m sim.build`

    # ── AI runtime ────────────────────────────────────────────────────────
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    enable_background_diagnosis: bool = True
    diagnosis_interval_minutes: int = 30

    # ── Business configuration ────────────────────────────────────────────
    # Monthly cost of running the platform, used by the ROI view. Set it to
    # your real figure; it is configuration, not generated data.
    platform_monthly_cost_inr: int = 50_000

    # ── Channels (all optional; unset = channel disabled) ─────────────────
    twilio_account_sid: str | None = None
    twilio_auth_token: str | None = None
    twilio_phone_number: str | None = None
    twilio_whatsapp_number: str | None = None
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    groq_api_key: str | None = None
    elevenlabs_api_key: str | None = None
    huggingface_api_key: str | None = None
    webhook_base_url: str | None = None
    email_webhook_secret: str | None = None  # shared secret header for the inbound-email webhook

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value):
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                return json.loads(text)
            return [v.strip() for v in text.split(",") if v.strip()]
        return value

    @model_validator(mode="after")
    def _require_secrets_in_prod(self) -> Settings:
        if self.env == "prod":
            if not is_configured(self.jwt_secret) or len(self.jwt_secret or "") < 32:
                raise ValueError("JWT_SECRET must be set to 32+ random characters in prod")
            if self.database_url.startswith("sqlite"):
                raise ValueError("Use PostgreSQL (DATABASE_URL) in prod, not SQLite")
        elif not is_configured(self.jwt_secret):
            # Dev/test convenience: an ephemeral secret. Tokens stop working on restart.
            self.jwt_secret = secrets.token_urlsafe(48)
            if self.env == "dev":
                log.warning("JWT_SECRET not set; using a temporary secret for this process")
        return self

    # ── Derived flags ─────────────────────────────────────────────────────
    @property
    def is_dev(self) -> bool:
        return self.env == "dev"

    @property
    def ollama_openai_url(self) -> str:
        """OpenAI-compatible endpoint used by AutoGen clients."""
        return self.ollama_base_url.rstrip("/") + "/v1"

    @property
    def sms_configured(self) -> bool:
        return all(map(is_configured, (self.twilio_account_sid, self.twilio_auth_token, self.twilio_phone_number)))

    @property
    def whatsapp_configured(self) -> bool:
        return all(map(is_configured, (self.twilio_account_sid, self.twilio_auth_token, self.twilio_whatsapp_number)))

    @property
    def email_configured(self) -> bool:
        return all(map(is_configured, (self.smtp_host, self.smtp_user, self.smtp_password, self.smtp_from)))


@lru_cache
def get_settings() -> Settings:
    return Settings()
