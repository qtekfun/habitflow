from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TOTPLoginRequest(BaseModel):
    temp_token: str
    code: str


class TOTPVerifyRequest(BaseModel):
    code: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TOTPChallengeResponse(BaseModel):
    totp_required: bool
    temp_token: str


class TOTPSetupResponse(BaseModel):
    secret: str
    qr_uri: str
