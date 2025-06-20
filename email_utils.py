import os
import requests

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM = "leland.paul@epochpa.com"  # Or whatever you want the sender to be

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
    print("Brevo response:", response.status_code, response.text)  # For debugging
    return response.status_code == 201
