"""
schemas.py
----------
Validation, serialization, and standardized API response formatters.
"""

import re
from typing import Dict, Any, Tuple, Optional
from flask import jsonify, Response


def validate_email(email: str) -> bool:
    """Check if email matches standard format."""
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return bool(re.match(pattern, email.strip()))


def success_response(data: Any, message: Optional[str] = None, status_code: int = 200) -> Tuple[Response, int]:
    """Standardized successful JSON response."""
    payload: Dict[str, Any] = {
        "success": True,
        "data": data
    }
    if message:
        payload["message"] = message
    return jsonify(payload), status_code


def error_response(message: str, code: str = "BAD_REQUEST", status_code: int = 400) -> Tuple[Response, int]:
    """Standardized error JSON response."""
    payload = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }
    return jsonify(payload), status_code
