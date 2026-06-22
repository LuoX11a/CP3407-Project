"""POST /api/v1/auth/register, /api/v1/auth/login"""

import os
import psycopg2
import psycopg2.extras
from fastapi import APIRouter, HTTPException

from app.models.schemas import RegisterRequest, LoginRequest, AuthResponse
from app.services.auth import hash_password, verify_password, create_token

router = APIRouter()
_raw_db_url = os.getenv("DATABASE_URL", "")
if "channel_binding=" in _raw_db_url:
    import re
    _raw_db_url = re.sub(r"[&?]channel_binding=[^&]*", "", _raw_db_url)
DATABASE_URL = _raw_db_url


@router.post("/auth/register", response_model=AuthResponse)
def register(body: RegisterRequest):
    conn = psycopg2.connect(DATABASE_URL)
    try:
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
            conn.commit()

        token = create_token(user_id, body.username)
        return AuthResponse(user_id=user_id, username=body.username, token=token)
    finally:
        conn.close()


@router.post("/auth/login", response_model=AuthResponse)
def login(body: LoginRequest):
    conn = psycopg2.connect(DATABASE_URL)
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                "SELECT id, username, password_hash FROM users WHERE username = %s",
                (body.username,),
            )
            user = cur.fetchone()
            if not user or not verify_password(body.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid username or password")

        token = create_token(user["id"], user["username"])
        return AuthResponse(user_id=user["id"], username=user["username"], token=token)
    finally:
        conn.close()
