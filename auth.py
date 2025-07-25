from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr
from fastapi.responses import HTMLResponse
from sqlmodel import Field, SQLModel, Session, create_engine, select
import secrets
import requests
import os

from dotenv import load_dotenv
load_dotenv()

router = APIRouter()

# ========== DATABASE SETUP ==========
DB_FILE = "epochpa.db"
engine = create_engine(f"sqlite:///{DB_FILE}", echo=False)

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role: str
    confirmed: bool = False
    confirmation_token: str | None = None

SQLModel.metadata.create_all(engine)

# AVAILITY (leave as is)
AVAILITY_CLIENT_ID = os.getenv("AVAILITY_KEY", "your_availity_client_id")
AVAILITY_CLIENT_SECRET = os.getenv("AVAILITY_SECRET", "your_availity_client_secret")
AVAILITY_TOKEN_URL = "https://api.availity.com/availity/v1/token"

# === BREVO CONFIG ===
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM = "leland.paul@epochpa.com"

def send_email_brevo(recipient, subject, html_content, text_content=None):
    api_key = BREVO_API_KEY
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
        return response.status_code in (200, 201, 202)
    except Exception as e:
        print("Brevo error:", str(e))
        return False

# ========== MODELS ==========
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    role: str   # Only 'provider' or 'rep'

class ConfirmRequest(BaseModel):
    token: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/auth/register", status_code=201)
def register(req: RegisterRequest):
    if req.role not in ["provider", "rep"]:
        raise HTTPException(400, "Invalid role. Only provider or rep allowed.")
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == req.email)).first()
        if user:
            raise HTTPException(400, "User already exists.")
        token = secrets.token_urlsafe(16)
        user = User(
            email=req.email,
            password=req.password,
            role=req.role,
            confirmed=False,
            confirmation_token=token
        )
        session.add(user)
        session.commit()
        confirm_url = f"https://epochpa-backend.onrender.com/intake/auth/confirm?token={token}"
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
        else:
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
            "message": "Registration accepted — check your email to confirm."
        }

@router.get("/auth/confirm", response_class=HTMLResponse)
def confirm_email(token: str = Query(...)):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.confirmation_token == token)).first()
        if not user:
            return HTMLResponse(
                "<h2>Invalid or expired token.</h2>", status_code=400
            )
        user.confirmed = True
        user.confirmation_token = None
        session.add(user)
        session.commit()
        return """
        <html>
            <head><title>EpochPA – Email Confirmed</title></head>
            <body>
                <h2>Email Confirmed!</h2>
                <p>Your provider account is now active. You can <a href="https://epochpa-intake-system-3-sdk3jwsvemc7olkziw83ie.streamlit.app/">log in here</a>.</p>
            </body>
        </html>
        """

@router.post("/auth/confirm")
def confirm_post(req: ConfirmRequest):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.confirmation_token == req.token)).first()
        if not user:
            raise HTTPException(400, "Invalid confirmation token.")
        user.confirmed = True
        user.confirmation_token = None
        session.add(user)
        session.commit()
        return {"message": "Email confirmed! You can now log in."}

@router.post("/auth/login")
def login(req: LoginRequest):
    print("LOGIN ATTEMPT:", req.email, req.password)  # Debug print
    try:
        with Session(engine) as session:
            user = session.exec(select(User).where(User.email == req.email)).first()
            print("FOUND USER:", user)  # Debug print
            if not user or user.password != req.password:
                print("LOGIN FAILED for:", req.email)  # Debug print
                raise HTTPException(401, "Invalid credentials.")
            if not user.confirmed:
                print("LOGIN NOT CONFIRMED for:", req.email)  # Debug print
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
                print("AVAILITY TOKEN FAILED:", resp.text)  # Debug print
                raise HTTPException(500, f"Failed to get Availity token: {resp.text}")
            availity_token = resp.json().get("access_token")
            print("LOGIN SUCCESSFUL for:", req.email)  # Debug print
            return {
                "user": {
                    "email": req.email,
                    "role": user.role
                },
                "availity_access_token": availity_token
            }
    except Exception as e:
        print("EXCEPTION DURING LOGIN:", repr(e))  # Exception print
        raise
