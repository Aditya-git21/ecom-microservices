import os
import secrets

from dotenv import load_dotenv
from fastapi import Header, HTTPException, status

load_dotenv()

INTERNAL_API_KEY = os.getenv("INTERNAL_API_KEY")
if not INTERNAL_API_KEY:
    raise RuntimeError("INTERNAL_API_KEY is not set")


def require_internal_key(x_internal_key: str | None = Header(default=None)):
    """Allow the request only if it carries the correct X-Internal-Key header."""
    if x_internal_key is None or not secrets.compare_digest(
        x_internal_key.encode(), INTERNAL_API_KEY.encode()
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing internal key",
        )
