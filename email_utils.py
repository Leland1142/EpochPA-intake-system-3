import os
import requests

# Load your Brevo API key from the environment
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM = "leland.paul@epochpa.com"  # Ensure this is a verified sender in Brevo

def send_email_brevo(recipient, subject, html_content, text_content=None):
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
        "api-key": BREVO_API_KEY,
        "Content-Type": "application/json",
        "accept": "application/json"
    }
    response = requests.post(url, json=payload, headers=headers)
    print("Brevo response:", response.status_code, response.text)  # Debug: Print full API response
    return response.status_code == 201

def send_registration_confirmation_email(recipient_email, token):
    # This is your new backend Render URL, not epochpa.com
    confirm_url = f"https://epochpa-backend.onrender.com/confirm?token={token}"
    subject = "Confirm your Provider Registration with EpochPA"
    html_content = f"""
    <h2>Welcome to EpochPA!</h2>
    <p>Thank you for registering as a provider. Please 
    <a href="{confirm_url}">click here to confirm your email</a> and activate your account.</p>
    <p>If the above link doesn't work, copy and paste this URL into your browser:</p>
    <p>{confirm_url}</p>
    <p>If you did not request this, please ignore this email.</p>
    """
    text_content = (
        f"Thank you for registering as a provider with EpochPA.\n"
        f"Please confirm your email by visiting: {confirm_url}\n"
        f"If you did not request this, you can ignore this email."
    )
    return send_email_brevo(
        recipient=recipient_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content
    )

# ======= TEST THE FUNCTION =========

if __name__ == "__main__":
    # Change this to your test email and sample token for testing
    test_recipient = "lelandpaul@yahoo.com"
    sample_token = "ExhgvczMrO9YAftTEHYPYQ"
    send_registration_confirmation_email(test_recipient, sample_token)
