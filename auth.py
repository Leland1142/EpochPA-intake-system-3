from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import secrets
import requests
import os

router = APIRouter()

# In‐memory user store
_users: dict[str, dict] = {}
_tokens: dict[str, str] = {}

AVAILITY_CLIENT_ID = os.getenv("AVAILITY_KEY", "your_availity_client_id")
AVAILITY_CLIENT_SECRET = os.getenv("AVAILITY_SECRET", "your_availity_client_secret")
AVAILITY_TOKEN_URL = "https://api.availity.com/availity/v1/token"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str

class ConfirmRequest(BaseModel):
    token: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/auth/register", status_code=201)
def register(req: RegisterRequest):
    if req.email in _users:
        raise HTTPException(400, "User already exists.")
    token = secrets.token_urlsafe(16)
    _tokens[token] = req.email
    _users[req.email] = {"password": req.password, "role": req.role, "confirmed": False}
    # TEMP: Return token in API response for testing
    return {
        "message": "Registration accepted — check your email to confirm.",
        "dev_token": token
    }


@router.post("/auth/confirm")
def confirm(req: ConfirmRequest):
    email = _tokens.get(req.token)
    if not email or email not in _users:
        raise HTTPException(400, "Invalid confirmation token.")
    _users[email]["confirmed"] = True
    return {"message": "Email confirmed! You can now log in."}

@router.post("/auth/login")
def login(req: LoginRequest):
    user = _users.get(req.email)
    if not user or user["password"] != req.password:
        raise HTTPException(401, "Invalid credentials.")
    if not user.get("confirmed"):
        raise HTTPException(403, "Email not confirmed.")
    
    # Get Availity OAuth2 token
    data = {
        "grant_type": "client_credentials",
        "client_id": AVAILITY_CLIENT_ID,
        "client_secret": AVAILITY_CLIENT_SECRET,
        "scope": "hipaa"
    }
    resp = requests.post(AVAILITY_TOKEN_URL, data=data)
    if resp.status_code != 200:
        raise HTTPException(500, f"Failed to get Availity token: {resp.text}")
    availity_token = resp.json().get("access_token")
    return {
        "user": {
            "email": req.email,
            "role": user["role"]
        },
        "availity_access_token": availity_token
    }
