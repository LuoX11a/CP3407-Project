"""POST /api/v1/auth/register, /api/v1/auth/login, /api/v1/auth/logout"""

import os
import psycopg2.extras
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import RegisterRequest, LoginRequest
from app.services.auth import hash_password, verify_password, create_token, COOKIE_NAME
from app.database import get_sync_conn

router = APIRouter()

# Prod detection for Secure cookie flag
IS_PRODUCTION = os.getenv("RENDER", "") == "true" or os.getenv("ENVIRONMENT", "") == "production"


def _set_token_cookie(response: JSONResponse, token: str):
    """Set JWT as httpOnly Secure SameSite cookie."""
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict" if IS_PRODUCTION else "lax",
        max_age=86400 * 7,  # 7 days
        path="/",
    )


@router.post("/auth/register")
def register(body: RegisterRequest):
    with get_sync_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT id FROM users WHERE username = %s OR email = %s",
                        (body.username, body.email))
            if cur.fetchone():
                raise HTTPException(status_code=409, detail="Username or email already exists")

            hashed = hash_password(body.password)
            cur.execute(
                "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                (body.username, body.email, hashed),
            )
            user_id = cur.fetchone()["id"]

    token = create_token(user_id, body.username)
    response = JSONResponse(
        content={"user_id": user_id, "username": body.username, "status": "ok"}
    )
    _set_token_cookie(response, token)
    return response


@router.post("/auth/login")
def login(body: LoginRequest):
    with get_sync_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (body.username,),
            )
            user = cur.fetchone()
            if not user or not verify_password(body.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_token(user["id"], user["username"])
    response = JSONResponse(
        content={"user_id": user["id"], "username": user["username"], "status": "ok"}
    )
    _set_token_cookie(response, token)
    return response


@router.post("/auth/logout")
def logout():
    """Clear the auth cookie."""
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie(
        key=COOKIE_NAME,
        path="/",
        httponly=True,
        secure=IS_PRODUCTION,
        samesite="strict" if IS_PRODUCTION else "lax",
    )
    return response
