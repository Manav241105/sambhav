"""
Authentication.

Staff (web dashboard): email + password -> access JWT + refresh token.
Owners (mobile app):   phone + one-time code -> access JWT + refresh token.
Refresh tokens rotate on every use; reusing a revoked one revokes them all.
"""

from __future__ import annotations

import logging
import re
import secrets
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update

from api.deps import DB, Auth
from core.ratelimit import client_key, login_limiter, otp_send_limiter, otp_verify_limiter
from core.security import (
    create_access_token,
    generate_otp,
    hash_secret,
    hash_token,
    new_refresh_token,
    utcnow,
    verify_secret,
)
from core.settings import get_settings
from db import models as m

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])

_PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")
_DUMMY_HASH = hash_secret(secrets.token_urlsafe(16))


# ── Schemas ───────────────────────────────────────────────────────────────────


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)  # lookup only; internal domains like .local allowed
    password: str = Field(min_length=1, max_length=256)
    role: str | None = None  # ignored; the account's role is authoritative


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105  (OAuth token type, not a secret)
    expires_at: str
    role: str
    user_id: int
    email: str | None = None
    full_name: str = ""
    customer_id: str | None = None
    token: str  # legacy alias of access_token for older clients


class RefreshRequest(BaseModel):
    refresh_token: str


class OtpRequest(BaseModel):
    phone: str


class OtpVerify(BaseModel):
    phone: str
    otp: str = Field(pattern=r"^[0-9]{6}$")


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr | None = None
    city: str | None = Field(default=None, max_length=60)
    language: str | None = Field(default=None, max_length=10)
    preferred_channel: str | None = Field(default=None, pattern=r"^(APP|WHATSAPP|SMS|EMAIL)$")


# ── Helpers ───────────────────────────────────────────────────────────────────


def normalize_phone(raw: str) -> str:
    phone = re.sub(r"[\s\-()]", "", raw or "")
    if phone and not phone.startswith("+") and len(phone) == 10:
        phone = "+91" + phone  # Indian mobile numbers without country code
    if not _PHONE_RE.match(phone):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Enter a valid mobile number")
    return phone if phone.startswith("+") else "+" + phone


async def _issue_tokens(db: DB, user: m.User, owner: m.Owner | None = None) -> TokenResponse:
    access, expires_at = create_access_token(user.id, user.role)
    plain, token_hash, refresh_exp = new_refresh_token()
    db.add(m.RefreshToken(user_id=user.id, token_hash=token_hash, expires_at=refresh_exp))
    user.last_login_at = utcnow()
    await db.commit()
    return TokenResponse(
        access_token=access,
        token=access,
        refresh_token=plain,
        expires_at=expires_at.isoformat(),
        role=user.role,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        customer_id=owner.code if owner else None,
    )


# ── Staff login ───────────────────────────────────────────────────────────────


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request, db: DB) -> TokenResponse:
    login_limiter.check(client_key(request, body.email.lower()))
    user = await db.scalar(select(m.User).where(m.User.email == body.email.lower()))
    # Same error and similar timing for unknown email and wrong password.
    ok = verify_secret(body.password, user.password_hash if user and user.password_hash else _DUMMY_HASH)
    if not user or not ok or not user.is_active or user.role == "owner":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    return await _issue_tokens(db, user)


# ── Owner OTP login ───────────────────────────────────────────────────────────


@router.post("/otp/send")
async def send_otp(body: OtpRequest, request: Request, db: DB) -> dict:
    settings = get_settings()
    phone = normalize_phone(body.phone)
    otp_send_limiter.check(client_key(request, phone))

    if settings.env == "prod" and not settings.sms_configured:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "SMS delivery is not configured")

    code = generate_otp()
    await db.execute(update(m.OtpCode).where(m.OtpCode.phone == phone, m.OtpCode.consumed_at.is_(None)).values(consumed_at=utcnow()))
    db.add(m.OtpCode(phone=phone, code_hash=hash_secret(code), expires_at=utcnow() + timedelta(seconds=settings.otp_ttl_seconds)))
    await db.commit()

    response = {"status": "sent", "phone": phone, "expires_in": settings.otp_ttl_seconds}
    if settings.sms_configured:
        from communication_service import SMSProvider

        result = await SMSProvider().send_message(to=phone, message=f"Your AutoPredict code is {code}. It expires in 5 minutes.")
        if not getattr(result, "success", False):
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Could not send the SMS, try again")
    else:
        # Dev/test only (prod without SMS was refused above): return the code and log it.
        log.info("DEV OTP for %s: %s", phone, code)
        response["debug_otp"] = code
    return response


@router.post("/otp/verify", response_model=TokenResponse)
async def verify_otp(body: OtpVerify, request: Request, db: DB) -> TokenResponse:
    settings = get_settings()
    phone = normalize_phone(body.phone)
    otp_verify_limiter.check(client_key(request, phone))

    otp = await db.scalar(
        select(m.OtpCode).where(m.OtpCode.phone == phone, m.OtpCode.consumed_at.is_(None)).order_by(m.OtpCode.created_at.desc()).limit(1)
    )
    if otp is None or otp.expires_at < utcnow() or otp.attempts >= settings.otp_max_attempts:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Code expired, request a new one")
    otp.attempts += 1
    if not verify_secret(body.otp, otp.code_hash):
        await db.commit()
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect code")
    otp.consumed_at = utcnow()

    user = await db.scalar(select(m.User).where(m.User.phone == phone))
    if user is None:
        user = m.User(phone=phone, role="owner")
        db.add(user)
        await db.flush()
    elif user.role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Staff accounts sign in with email")

    owner = await db.scalar(select(m.Owner).where(m.Owner.user_id == user.id))
    if owner is None:
        # Link an existing owner record with this phone (e.g. imported or demo data), else create one.
        owner = await db.scalar(select(m.Owner).where(m.Owner.phone == phone, m.Owner.user_id.is_(None)).limit(1))
        if owner is None:
            owner = m.Owner(code=f"OWN-{secrets.token_hex(4).upper()}", name="", phone=phone)
            db.add(owner)
        owner.user_id = user.id
        await db.flush()
    if not user.full_name and owner.name:
        user.full_name = owner.name
    return await _issue_tokens(db, user, owner)


# ── Token lifecycle ───────────────────────────────────────────────────────────


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, db: DB) -> TokenResponse:
    record = await db.scalar(select(m.RefreshToken).where(m.RefreshToken.token_hash == hash_token(body.refresh_token)))
    if record is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")
    if record.revoked_at is not None:
        # A rotated token was used again: assume theft, sign the user out everywhere.
        await db.execute(
            update(m.RefreshToken)
            .where(m.RefreshToken.user_id == record.user_id, m.RefreshToken.revoked_at.is_(None))
            .values(revoked_at=utcnow())
        )
        await db.commit()
        log.warning("Refresh token reuse detected for user %s", record.user_id)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, sign in again")
    if record.expires_at < utcnow():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session expired, sign in again")
    user = await db.get(m.User, record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Account disabled")
    record.revoked_at = utcnow()
    owner = await db.scalar(select(m.Owner).where(m.Owner.user_id == user.id))
    return await _issue_tokens(db, user, owner)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: DB) -> None:
    await db.execute(
        update(m.RefreshToken)
        .where(m.RefreshToken.token_hash == hash_token(body.refresh_token), m.RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    await db.commit()


@router.get("/me")
async def me(current: Auth, db: DB) -> dict:
    vehicles = []
    if current.owner:
        vehicles = (await db.scalars(select(m.Vehicle.code).where(m.Vehicle.owner_id == current.owner.id).order_by(m.Vehicle.code))).all()
    return {
        "user_id": current.user.id,
        "role": current.role,
        "email": current.user.email,
        "phone": current.user.phone,
        "full_name": current.user.full_name or (current.owner.name if current.owner else ""),
        "customer_id": current.owner.code if current.owner else None,
        "vehicle_ids": list(vehicles),
        "needs_profile": bool(current.owner and not current.owner.name),
    }


@router.post("/register")
async def complete_profile(body: ProfileUpdate, current: Auth, db: DB) -> dict:
    """Owners complete their profile after the first OTP sign-in."""
    if current.owner is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only owner accounts have a profile here")
    owner = current.owner
    owner.name = body.name.strip()
    current.user.full_name = owner.name
    for field in ("email", "city", "language", "preferred_channel"):
        value = getattr(body, field)
        if value is not None:
            setattr(owner, field, value)
    await db.commit()
    return {"customer_id": owner.code, "name": owner.name, "status": "updated"}
