"""Utility functions for the customers app."""

from django.core.signing import TimestampSigner
from rest_framework.request import Request

from core.models import Settings


def build_verification_url(request: Request, user_email: str) -> str:
    """
    Build a verification URL using the configured app domain.

    Args:
        request: The current request object
        user_email: The email address to create a verification token for

    Returns:
        The complete verification URL
    """
    # Generate the verification token
    signer = TimestampSigner()
    token = signer.sign(user_email)

    # Get the app domain from settings
    settings = Settings.get_settings()

    if settings.app_domain:
        # Use the configured frontend domain
        base_url = settings.app_domain.rstrip("/")
        verification_url = f"{base_url}/verify-email?token={token}"
    else:
        # Fall back to the current request domain (backward compatibility)
        verification_url = f"{request.build_absolute_uri('/verify-email')}?token={token}"

    return verification_url


def send_verification_email_html(verification_url: str) -> str:
    """
    Generate the HTML content for verification emails.

    Args:
        verification_url: The verification URL to include in the email

    Returns:
        HTML string for the email body
    """
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            h1 {{
                color: #2c3e50;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #3498db;
                color: #ffffff;
                text-decoration: none;
                border-radius: 5px;
                font-weight: 600;
                margin: 20px 0;
            }}
            .button:hover {{
                background-color: #2980b9;
            }}
            .footer {{
                margin-top: 30px;
                font-size: 14px;
                color: #7f8c8d;
                border-top: 1px solid #ecf0f1;
                padding-top: 20px;
            }}
            .link {{
                color: #3498db;
                word-break: break-all;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Welcome! Verify Your Email Address</h1>
            <p>Thank you for signing up! You're just one step away from completing your registration.</p>
            <p>Please confirm your email address by clicking the button below:</p>
            <a href="{verification_url}" class="button">Verify Email Address</a>
            <p>Or copy and paste this link in your browser:</p>
            <p><a href="{verification_url}" class="link">{verification_url}</a></p>
            <div class="footer">
                <p>This verification link will expire in 24 hours.</p>
                <p>If you didn't create an account, you can safely ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """


def send_verification_email_plain(verification_url: str) -> str:
    """
    Generate the plain text content for verification emails.

    Args:
        verification_url: The verification URL to include in the email

    Returns:
        Plain text string for the email body
    """
    return (
        f"Welcome! Verify Your Email Address\n\n"
        f"Thank you for signing up! You're just one step away from completing your registration.\n\n"
        f"Please confirm your email address by clicking the following link:\n"
        f"{verification_url}\n\n"
        f"This verification link will expire in 24 hours.\n"
        f"If you didn't create an account, you can safely ignore this email."
    )
