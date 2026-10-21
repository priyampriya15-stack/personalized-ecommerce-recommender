"""
auth_helpers.py
---------------
JWT authentication utilities, token verification, and security decorators.
"""

from functools import wraps
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

import jwt
from flask import request, current_app, g

from backend.models.database_models import db, User
from backend.models.schemas import error_response


def generate_jwt_token(user_id: int, role: str) -> str:
    """Generate signed JWT token valid for configured hours."""
    now = datetime.now(timezone.utc)
    expiry_hours = current_app.config.get("JWT_ACCESS_TOKEN_EXPIRES_HOURS", 24)
    payload = {
        "sub": str(user_id),
        "role": str(role),
        "iat": now,
        "exp": now + timedelta(hours=expiry_hours)
    }
    secret = current_app.config["JWT_SECRET_KEY"]
    token = jwt.encode(payload, secret, algorithm="HS256")
    return token


def decode_jwt_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT token."""
    try:
        secret = current_app.config["JWT_SECRET_KEY"]
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_token_from_header() -> Optional[str]:
    """Extract Bearer token from HTTP Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    parts = auth_header.split(" ")
    if len(parts) == 2:
        return parts[1].strip()
    return None


def jwt_required(f):
    """Decorator requiring valid JWT token."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return error_response("Authentication token missing. Please log in.", "UNAUTHORIZED", 401)

        payload = decode_jwt_token(token)
        if not payload:
            return error_response("Invalid or expired authentication token.", "UNAUTHORIZED", 401)

        sub_val = payload.get("sub")
        user_id = int(sub_val) if (sub_val is not None and str(sub_val).isdigit()) else sub_val
        user = db.session.get(User, user_id) if user_id is not None else None
        if not user:
            return error_response("User account not found.", "UNAUTHORIZED", 401)

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator requiring admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return error_response("Authentication token missing. Please log in.", "UNAUTHORIZED", 401)

        payload = decode_jwt_token(token)
        if not payload:
            return error_response("Invalid or expired authentication token.", "UNAUTHORIZED", 401)

        sub_val = payload.get("sub")
        user_id = int(sub_val) if (sub_val is not None and str(sub_val).isdigit()) else sub_val
        user = db.session.get(User, user_id) if user_id is not None else None
        if not user:
            return error_response("User account not found.", "UNAUTHORIZED", 401)

        if user.role != "admin":
            return error_response("Admin privileges required.", "FORBIDDEN", 403)

        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function


def optional_jwt(f):
    """Decorator that optionally attaches current_user if valid token provided."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.current_user = None
        token = get_token_from_header()
        if token:
            payload = decode_jwt_token(token)
            if payload:
                sub_val = payload.get("sub")
                user_id = int(sub_val) if (sub_val is not None and str(sub_val).isdigit()) else sub_val
                user = db.session.get(User, user_id) if user_id is not None else None
                if user:
                    g.current_user = user
        return f(*args, **kwargs)
    return decorated_function
