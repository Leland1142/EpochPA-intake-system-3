import os
import requests

# Load your Brevo API key from the environment
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
EMAIL_FROM = "leland.paul@epochpa.com"  # Make sure this is a verified sender in Brevo

# DEBUG: Print first 10 characters to confirm it loaded (do NOT print full key in production)
if BREVO_API_KEY:
    print("BREVO_API_KEY loaded:", BREVO_API_KEY[:10], "... (truncated)")
else:
    print("BREVO_API_KEY NOT FOUND!")

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
    print("Sending to:", recipient)
    print("Subject:", subject)
    response = requests.post(url, json=payload, headers=headers)
    print("Brevo response:", response.status_code, response.text)  # Debug: Print full API response
    return response.status_code == 201

# ======= TEST THE FUNCTION =========

if __name__ == "__main__":
    # Change this to your test email
    test_recipient = "lelandpaul@yahoo.com"
    test_subject = "Test Email from EpochPA"
    test_html = "<h1>Hello from EpochPA Brevo Test!</h1><p>If you see this, your Brevo API is working.</p>"

    send_email_brevo(
        recipient=test_recipient,
        subject=test_subject,
        html_content=test_html,
        text_content="Hello from EpochPA Brevo Test! If you see this, your Brevo API is working."
    )
