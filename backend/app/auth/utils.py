"""
Authentication utilities: password hashing, JWT token management, and OTP handling.
"""
import random
import string
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt

from ..config import get_settings

# Setup logger
logger = logging.getLogger(__name__)

# In-memory OTP store (in production, use Redis or database)
otp_store: Dict[str, Dict[str, Any]] = {}

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    settings = get_settings()

    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload if valid, None otherwise
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def create_refresh_token(user_id: str) -> str:
    """
    Create a refresh token with longer expiration.

    Args:
        user_id: User ID to encode in the token

    Returns:
        Encoded JWT refresh token
    """
    return create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=7)
    )


# OTP Configuration
OTP_EXPIRY_MINUTES = 10
OTP_LENGTH = 6


def generate_otp() -> str:
    """
    Generate a 6-digit OTP.

    Returns:
        6-digit OTP string
    """
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def store_otp(email: str, otp: str, purpose: str) -> None:
    """
    Store OTP in memory with expiration.

    Args:
        email: User email address
        otp: Generated OTP code
        purpose: 'register' or 'login'
    """
    key = f"{email.lower()}:{purpose}"
    otp_store[key] = {
        "otp": otp,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        "attempts": 0,
    }


def verify_otp(email: str, otp: str, purpose: str) -> bool:
    """
    Verify OTP for given email.

    Args:
        email: User email address
        otp: OTP code to verify
        purpose: 'register' or 'login'

    Returns:
        True if OTP is valid, False otherwise
    """
    key = f"{email.lower()}:{purpose}"

    if key not in otp_store:
        return False

    stored = otp_store[key]

    # Check if expired
    if datetime.utcnow() > stored["expires_at"]:
        del otp_store[key]
        return False

    # Check attempts (max 3)
    if stored["attempts"] >= 3:
        del otp_store[key]
        return False

    # Increment attempts
    stored["attempts"] += 1

    # Verify OTP
    if stored["otp"] == otp:
        del otp_store[key]  # One-time use
        return True

    return False


def create_verification_token(email: str, purpose: str) -> str:
    """
    Create a verification token after successful OTP verification.

    Args:
        email: User email address
        purpose: 'register' or 'login'

    Returns:
        Encoded JWT verification token
    """
    return create_access_token(
        data={"email": email, "purpose": purpose, "type": "otp_verified"},
        expires_delta=timedelta(minutes=15)  # Short-lived token
    )


def verify_verification_token(token: str, expected_purpose: str) -> Optional[str]:
    """
    Verify a verification token and return the email.

    Args:
        token: JWT verification token
        expected_purpose: Expected purpose ('register' or 'login')

    Returns:
        Email if valid, None otherwise
    """
    payload = decode_access_token(token)

    if not payload:
        return None

    if payload.get("type") != "otp_verified":
        return None

    if payload.get("purpose") != expected_purpose:
        return None

    return payload.get("email")


async def send_otp_email(email: str, otp: str, purpose: str) -> bool:
    """
    Send OTP email to user using Brevo SMTP.

    Args:
        email: Recipient email address
        otp: OTP code to send
        purpose: 'register' or 'login'

    Returns:
        True if email sent successfully
    """
    settings = get_settings()

    subject = "Your ShopEase Verification Code"

    if purpose == "register":
        action = "complete your registration"
    else:
        action = "login to your account"

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #2874f0 0%, #1a5dc8 100%); padding: 20px; text-align: center; }}
            .header h1 {{ color: white; margin: 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 8px; margin-top: 20px; }}
            .otp-box {{ background: #2874f0; color: white; font-size: 32px; font-weight: bold;
                        letter-spacing: 8px; padding: 20px 40px; text-align: center;
                        border-radius: 8px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 20px; }}
            .warning {{ color: #dc3545; font-size: 14px; margin-top: 15px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{settings.SMTP_FROM_NAME}</h1>
            </div>
            <div class="content">
                <h2>Verification Code</h2>
                <p>Use the following code to {action}:</p>
                <div class="otp-box">{otp}</div>
                <p>This code will expire in <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.</p>
                <p class="warning">
                    If you didn't request this code, please ignore this email.
                    Never share this code with anyone.
                </p>
            </div>
            <div class="footer">
                <p>&copy; 2024 {settings.SMTP_FROM_NAME}. All rights reserved.</p>
                <p>This is an automated email. Please do not reply.</p>
            </div>
        </div>
    </body>
    </html>
    """

    # Check if email is configured
    if not settings.is_email_configured():
        logger.warning("="*50)
        logger.warning("EMAIL NOT CONFIGURED - Logging OTP instead")
        logger.warning(f"To: {email}")
        logger.warning(f"Subject: {subject}")
        logger.warning(f"OTP: {otp}")
        logger.warning(f"Purpose: {purpose}")
        logger.warning(f"Expires in: {OTP_EXPIRY_MINUTES} minutes")
        logger.warning("")
        logger.warning("To enable email, set these in .env:")
        logger.warning("  EMAIL_ENABLED=true")
        logger.warning("  BREVO_SMTP_LOGIN=your-brevo-smtp-login")
        logger.warning("  BREVO_SMTP_PASSWORD=your-brevo-smtp-password")
        logger.warning("  SMTP_FROM_EMAIL=your-verified-email@domain.com")
        logger.warning("="*50)
        return True  # Return true so the flow continues

    # Send email using Brevo SMTP
    try:
        logger.info(f"Sending OTP to {email} via Brevo SMTP...")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = email

        # Add plain text version
        plain_text = f"""
Your ShopEase Verification Code

Use the following code to {action}:

{otp}

This code will expire in {OTP_EXPIRY_MINUTES} minutes.

If you didn't request this code, please ignore this email.
Never share this code with anyone.
        """
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        # Connect to Brevo SMTP
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.set_debuglevel(0)  # Set to 1 for debugging
            server.ehlo()
            server.starttls()
            server.ehlo()

            # Login with Brevo credentials
            server.login(settings.BREVO_SMTP_LOGIN, settings.BREVO_SMTP_PASSWORD)

            # Send email
            server.sendmail(
                settings.SMTP_FROM_EMAIL,
                email,
                msg.as_string()
            )

        logger.info(f"OTP sent successfully to {email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication failed: {e}")
        logger.error("Check BREVO_SMTP_LOGIN and BREVO_SMTP_PASSWORD")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        logger.error(f"Recipient refused: {e}")
        return False
    except smtplib.SMTPSenderRefused as e:
        logger.error(f"Sender refused: {e}")
        logger.error("Make sure SMTP_FROM_EMAIL is verified in Brevo")
        return False
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send OTP email: {type(e).__name__}: {e}")
        return False
