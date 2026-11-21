"""Request dependencies: database session, current user, role checks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.security import TokenError, decode_access_token
from db.models import STAFF_ROLES, Owner, User, Vehicle
from db.session import get_session

DB = Annotated[AsyncSession, Depends(get_session)]
_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    user: User
    owner: Owner | None

    @property
    def id(self) -> int:
        return self.user.id

    @property
    def role(self) -> str:
        return self.user.role

    @property
    def is_staff(self) -> bool:
        return self.user.role in STAFF_ROLES


async def user_from_token(session: AsyncSession, token: str) -> CurrentUser:
    try:
        payload = decode_access_token(token)
    except TokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, str(exc), headers={"WWW-Authenticate": "Bearer"}) from exc
    user = await session.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User not found or disabled")
    owner = await session.scalar(select(Owner).where(Owner.user_id == user.id)) if user.role == "owner" else None
    return CurrentUser(user=user, owner=owner)


async def get_current_user(
    session: DB,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> CurrentUser:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})
    return await user_from_token(session, creds.credentials)


Auth = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: str) -> Callable:
    async def checker(current: Auth) -> CurrentUser:
        if current.role not in roles and current.role != "admin":
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed for your role")
        return current

    return checker


Staff = Annotated[CurrentUser, Depends(require_roles(*STAFF_ROLES))]
OwnerOrStaff = Auth


async def get_vehicle_for(session: AsyncSession, current: CurrentUser, code: str) -> Vehicle:
    """Load a vehicle by code; owners may only reach their own cars (404 otherwise)."""
    vehicle = await session.scalar(select(Vehicle).where(Vehicle.code == code))
    if vehicle is None or (not current.is_staff and (current.owner is None or vehicle.owner_id != current.owner.id)):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Vehicle {code} not found")
    return vehicle
