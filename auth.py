from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import secrets
import requests
import os

from dotenv import load_dotenv
load_dotenv()  # Ensure .env file loads

router = APIRouter()

# In-memory user store
_users: dict[str, dict] = {}
_tokens: dict[str, str] = {}

# AVAILITY (leave as is)
AVAILITY_CLIENT_ID = os.getenv("AVAILITY_KEY", "your_availity_client_id")
AVAILITY_CLIENT_SECRET = os.getenv("AVAILITY_SECRET", "your_availity_client_secret")
AVAILITY_TOKEN_URL = "https://api.availity.com/availity/v1/token"

# === BREVO CONFIG ===
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM = "leland.paul@epochpa.com"  # Your company email

def send_email_brevo(recipient, subject, html_content, text_content=None):
    api_key = BREVO_API_KEY
    print("BREVO_API_KEY:", api_key)  # DEBUG: REMOVE after working
    url = "https://api.brevo.com/v3/smtp/email"
    payload = {
        "sender": {"name": "EpochPA", "email": EMAIL_FROM},
        "to": [{"email": recipient}],
        "subject": subject,
        "htmlContent": html_content,
    }
    if text_content:
        payload["textContent"] = text_content
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        print("Brevo response:", response.status_code, response.text)
        return response.status_code in (200, 201, 202)
    except Exception as e:
        print("Brevo error:", str(e))
        return False

# ========== MODELS ==========
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str   # Only allow 'provider' or 'rep'

class ConfirmRequest(BaseModel):
    token: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/auth/register", status_code=201)
def register(req: RegisterRequest):
    # Prevent self-registration as admin
    if req.role not in ["provider", "rep"]:
        raise HTTPException(400, "Invalid role. Only provider or rep allowed.")

    if req.email in _users:
        raise HTTPException(400, "User already exists.")

    token = secrets.token_urlsafe(16)
    _tokens[token] = req.email
    _users[req.email] = {
        "password": req.password,
        "role": req.role,
        "confirmed": False
    }
    # Build confirmation link (adjust URL to your frontend confirm page)
    confirm_url = f"https://epochpa.com/confirm?token={token}"
    # Email customization by role
    if req.role == "provider":
        subject = "Confirm your Provider Registration with EpochPA"
        html = f"""
        <h2>Welcome to EpochPA!</h2>
        <p>Thank you for registering as a provider. Please <a href="{confirm_url}">click here to confirm your email</a> and activate your account.</p>
        <p>If the above link doesn't work, copy and paste this URL into your browser:</p>
        <p>{confirm_url}</p>
        <p>If you did not request this, please ignore this email.</p>
        """
        text_content = f"""Thank you for registering with EpochPA.\nTo confirm your email and activate your account, click the following link or copy it into your browser:\n{confirm_url}"""
    else:  # rep
        subject = "Confirm your Rep Registration with EpochPA"
        html = f"""
        <h2>Welcome to EpochPA!</h2>
        <p>Thank you for joining as a Rep. Please <a href="{confirm_url}">click here to confirm your email</a> and activate your access.</p>
        <p>If the above link doesn't work, copy and paste this URL into your browser:</p>
        <p>{confirm_url}</p>
        <p>If you did not request this, please ignore this email.</p>
        """
        text_content = f"""Thank you for registering as a Rep with EpochPA.\nTo confirm your email and activate your access, click the following link or copy it into your browser:\n{confirm_url}"""
    email_sent = send_email_brevo(req.email, subject, html, text_content)
    if not email_sent:
        raise HTTPException(500, "Registration failed: could not send confirmation email. Please contact support.")

    return {
        "message": "Registration accepted — check your email to confirm.",
        # "dev_token": token  # Optionally return for testing only; remove in production!
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
    # Get Availity OAuth2 token (leave as-is for now)
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
