"""Esquemas de /api/v1/auth."""
from pydantic import BaseModel, ConfigDict


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str
    password: str
