from datetime import timedelta
from .models import EmailVerification, PasswordReset, User
import secrets
from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail
from django.utils.timezone import now
import random
import requests
from requests.auth import HTTPBasicAuth
import mimetypes
import os
from rest_framework_simplejwt.tokens import RefreshToken


def generate_unique_phone():
    while True:
        phone = str(random.randint(11111111111, 99999999999))
        if not User.objects.filter(phone_number=phone).exists():
            return phone


def generate_otp():
    return f"{secrets.randbelow(10**6):06}"


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token), # type: ignore
    }


def send_email(user, email_type, otp=None):
    """
    Sends an email to the user for a specific purpose.
    
    Parameters:
    - user: The user object.
    - email_type: Purpose of the email. Accepts 'registration', 'password_reset', 'otp_regeneration'.
    - otp: Optional. OTP to include in the email. If not provided, generates a new one.
    """
    if not otp:
        otp = generate_otp()

    expiration_time = now() + timedelta(minutes=10)

    if email_type == 'registration':
        subject = "Verify Your Email Address"
        template_name = 'email_verification.html'
        EmailVerification.objects.create(
            user=user,
            otp=otp,
            expires_at=expiration_time,
        )
    elif email_type == 'password_reset':
        subject = "Password Reset Request"
        template_name = 'password_reset.html'
        PasswordReset.objects.update_or_create(
            user=user,
            defaults={
                'otp': otp,
                'expires_at': expiration_time,
                'is_used': False,
            }
        )
    elif email_type == 'otp_regeneration':
        subject = "Regenerate OTP"
        template_name = 'email_verification.html'
        EmailVerification.objects.create(
            user=user,
            otp=otp,
            expires_at=expiration_time,
        )
    else:
        raise ValueError("Invalid email_type specified.")

    # Render email content
    email_body = render_to_string(template_name, {'otp': otp, 'user': user})

    # Send the email
    send_mail(
        subject=subject,
        message="",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=email_body,
    )


def upload_to_imagekit(image_file):
    imagekit_api_key = os.getenv("IMAGEKIT_PRIVATE_KEY")
    print(imagekit_api_key)
    if not imagekit_api_key:
        raise RuntimeError("Missing ImageKit private key in env var")
    upload_url = "https://upload.imagekit.io/api/v1/files/upload"
    filename = image_file.name
    mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    files = {"file": (filename, image_file, mime)}
    payload = {
        "fileName": filename,
        'folder': '/Judgement-Calc/'
    }

    resp = requests.post(
        upload_url,
        files=files,
        data=payload,
        auth=HTTPBasicAuth(imagekit_api_key, "")
    )
    try:
        data = resp.json()
    except ValueError:
        raise Exception(f"Non-JSON response: {resp.status_code} {resp.text}")

    if resp.ok and "url" in data:
        return data["url"]
    else:
        err = data.get("error", {}).get("message", resp.text)
        raise Exception(f"Upload failed ({resp.status_code}): {err}")
