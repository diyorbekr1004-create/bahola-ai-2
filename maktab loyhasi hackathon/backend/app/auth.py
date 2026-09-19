import os
from fastapi import Header, HTTPException


def get_api_key(x_api_key: str = Header(None)):
    expected = os.getenv("TEACHER_API_KEY")
    if expected is None:
        # development mode: allow if header present
        if x_api_key:
            return x_api_key
        raise HTTPException(status_code=401, detail="Missing API key")
    if x_api_key != expected:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key
