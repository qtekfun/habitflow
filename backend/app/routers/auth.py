"""
Auth router — /api/v1/auth
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.dependencies import get_current_user, get_refresh_token
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TOTPChallengeResponse,
    TOTPLoginRequest,
    TOTPSetupResponse,
    TOTPVerifyRequest,
    TokenResponse,
)
from app.schemas.user import UserRead
from app.services import auth_service
from app.services.auth_service import (
    DuplicateEmailError,
    DuplicateUsernameError,
    InvalidCredentialsError,
    InvalidTOTPError,
    InvalidTokenError,
)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_COOKIE_OPTS: dict = {
    "key": _REFRESH_COOKIE,
    "httponly": True,
    "samesite": "strict",
    "secure": not settings.DEBUG,
}


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        **_COOKIE_OPTS,
        value=token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.set_cookie(**_COOKIE_OPTS, value="", max_age=0)


# ---------------------------------------------------------------------------
# Register
# ---------------------------------------------------------------------------


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Registration disabled"
        )
    try:
        user = await auth_service.register(
            db=db, email=body.email, username=body.username, password=body.password
        )
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except DuplicateUsernameError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    return user


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


@router.post("/login")
async def login(
    body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    try:
        result = await auth_service.login(
            db=db, email=body.email, password=body.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    if result.get("totp_required"):
        return TOTPChallengeResponse(
            totp_required=True, temp_token=result["temp_token"]
        )

    _set_refresh_cookie(response, result["refresh_token"])
    return TokenResponse(access_token=result["access_token"])


@router.post("/login/totp")
async def login_totp(
    body: TOTPLoginRequest, response: Response, db: AsyncSession = Depends(get_db)
):
    try:
        result = await auth_service.complete_totp_login(
            db=db, temp_token=body.temp_token, code=body.code
        )
    except (InvalidTokenError, InvalidCredentialsError, InvalidTOTPError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    _set_refresh_cookie(response, result["refresh_token"])
    return TokenResponse(access_token=result["access_token"])


# ---------------------------------------------------------------------------
# Token refresh / logout
# ---------------------------------------------------------------------------


@router.post("/refresh")
async def refresh(
    response: Response,
    refresh_token: str = Depends(get_refresh_token),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await auth_service.refresh_tokens(db=db, refresh_token=refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    _set_refresh_cookie(response, result["refresh_token"])
    return TokenResponse(access_token=result["access_token"])


@router.post("/logout")
async def logout(
    response: Response,
    _current_user: User = Depends(get_current_user),
):
    _clear_refresh_cookie(response)
    return {"message": "Logged out"}


# ---------------------------------------------------------------------------
# TOTP management
# ---------------------------------------------------------------------------


@router.post("/totp/setup", response_model=TOTPSetupResponse)
async def totp_setup(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await auth_service.setup_totp(db=db, user=current_user)
    return TOTPSetupResponse(secret=result["secret"], qr_uri=result["qr_uri"])


@router.post("/totp/verify")
async def totp_verify(
    body: TOTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await auth_service.verify_totp_setup(db=db, user=current_user, code=body.code)
    except InvalidTOTPError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return {"message": "2FA enabled"}


@router.delete("/totp")
async def totp_disable(
    body: TOTPVerifyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await auth_service.disable_totp(db=db, user=current_user, code=body.code)
    except InvalidTOTPError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    return {"message": "2FA disabled"}
