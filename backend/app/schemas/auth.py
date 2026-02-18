"""Auth request/response schemas."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request body."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)
    totp_code: str | None = Field(default=None, min_length=6, max_length=6)


class TokenData(BaseModel):
    """Access token response payload."""

    access_token: str
    token_type: str = "bearer"


class TotpSetupRequest(BaseModel):
    """TOTP setup request body."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class TotpVerifyRequest(BaseModel):
    """TOTP verify request body."""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)
    secret: str = Field(..., min_length=16, max_length=64)
    code: str = Field(..., min_length=6, max_length=6)

