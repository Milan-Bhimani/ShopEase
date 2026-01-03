"""
==============================================================================
Authentication Utilities (utils.py)
==============================================================================

PURPOSE:
--------
This module provides core authentication utilities:
1. Password hashing and verification (using bcrypt)
2. JWT token creation and validation
3. OTP (One-Time Password) generation, storage, and verification
4. OTP email sending

SECURITY CONCEPTS EXPLAINED:
----------------------------

1. PASSWORD HASHING (bcrypt)
   - Passwords are NEVER stored as plain text
   - bcrypt adds a random "salt" to each password before hashing
   - This means identical passwords have different hashes
   - bcrypt is intentionally slow to prevent brute-force attacks

2. JWT (JSON Web Tokens)
   - Stateless authentication: server doesn't need to store sessions
   - Token contains user ID and expiration time
   - Token is signed with a secret key to prevent tampering
   - Client sends token in Authorization header for each request

3. OTP (One-Time Password)
   - 6-digit code sent to user's email
   - Expires after 10 minutes for security
   - Maximum 3 verification attempts to prevent brute-force
   - Deleted after successful verification (single-use)

JWT TOKEN STRUCTURE:
--------------------
    Header: {"alg": "HS256", "typ": "JWT"}
    Payload: {"sub": "user_id", "exp": 1234567890, "iat": 1234567800}
    Signature: HMACSHA256(header + "." + payload, secret_key)

    Result: xxxxx.yyyyy.zzzzz (base64-encoded, separated by dots)

AUTHENTICATION FLOWS:
---------------------

1. Registration:
   - User submits email, password, name
   - Password is hashed with bcrypt
   - User document created in Firestore
   - JWT token returned to client

2. Login with Password:
   - User submits email, password
   - Find user by email
   - Verify password against stored hash
   - If valid, return JWT token

3. Login with OTP:
   - User submits email (pre-login step)
   - System generates 6-digit OTP
   - OTP sent to user's email
   - User submits email + OTP
   - OTP verified, JWT token returned
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

# Setup logger for debugging and monitoring
logger = logging.getLogger(__name__)

# ==============================================================================
# OTP STORAGE
# ==============================================================================
# In-memory storage for OTPs
# Structure: {"email:purpose": {"otp": "123456", "created_at": datetime, ...}}
#
# IMPORTANT: This is NOT suitable for production with multiple servers!
# For production, use:
# - Redis (recommended): Fast, supports expiration natively
# - Database: Store OTPs in a "pending_otps" collection
# - Memcached: Similar to Redis, good for ephemeral data
otp_store: Dict[str, Dict[str, Any]] = {}


# ==============================================================================
# PASSWORD HASHING CONFIGURATION
# ==============================================================================
# CryptContext handles password hashing with bcrypt
#
# Why bcrypt?
# - Industry standard for password hashing
# - Automatically handles salting (random data added to password)
# - Configurable "work factor" to slow down hashing (prevents brute-force)
# - "deprecated='auto'" means old hash formats are automatically upgraded
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==============================================================================
# PASSWORD FUNCTIONS
# ==============================================================================
def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    The hash includes:
    - Algorithm identifier ($2b$)
    - Cost factor (12 by default)
    - Random salt (22 characters)
    - Hash output (31 characters)

    Example output: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.aVoQHBNzLQo.6e"

    Args:
        password: Plain text password from user input

    Returns:
        Hashed password string (60 characters for bcrypt)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    This function:
    1. Extracts the salt from the stored hash
    2. Hashes the plain password with that salt
    3. Compares the result with the stored hash

    Uses constant-time comparison to prevent timing attacks.

    Args:
        plain_password: Password entered by user (plain text)
        hashed_password: Hash stored in database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==============================================================================
# JWT TOKEN FUNCTIONS
# ==============================================================================
def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.

    The token contains:
    - sub (subject): Usually the user ID
    - exp (expiration): When the token expires
    - iat (issued at): When the token was created
    - Any additional data passed in

    Args:
        data: Dictionary of claims to include in token
              Must include "sub" for user identification
        expires_delta: Custom expiration time (optional)
                      Defaults to JWT_ACCESS_TOKEN_EXPIRE_MINUTES from settings

    Returns:
        Encoded JWT token string

    Example:
        token = create_access_token(data={"sub": "user123"})
        # Returns: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    """
    settings = get_settings()

    # Create a copy to avoid modifying the original dict
    to_encode = data.copy()

    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )

    # Add standard JWT claims
    to_encode.update({
        "exp": expire,        # Expiration time (checked automatically by jwt.decode)
        "iat": datetime.utcnow(),  # Issued at time
    })

    # Create signed JWT
    # HS256 = HMAC with SHA-256 (symmetric encryption)
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate a JWT access token.

    This function:
    1. Verifies the signature using the secret key
    2. Checks that the token hasn't expired
    3. Returns the payload if valid

    Args:
        token: JWT token string from Authorization header

    Returns:
        Decoded payload dictionary if valid, containing:
        - sub: User ID
        - exp: Expiration timestamp
        - iat: Issued at timestamp
        - Any custom claims
        Returns None if token is invalid or expired
    """
    settings = get_settings()

    try:
        # decode() automatically verifies signature and expiration
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        # Catches: ExpiredSignatureError, InvalidSignatureError, etc.
        return None


def create_refresh_token(user_id: str) -> str:
    """
    Create a refresh token with longer expiration.

    Refresh tokens are used to get new access tokens without
    re-authenticating. They have:
    - Longer expiration (7 days vs 24 hours)
    - "type": "refresh" claim to distinguish from access tokens

    Security note: Refresh tokens should be stored securely (httpOnly cookie)
    and revoked when user logs out.

    Args:
        user_id: User ID to encode in the token

    Returns:
        Encoded JWT refresh token
    """
    return create_access_token(
        data={"sub": user_id, "type": "refresh"},
        expires_delta=timedelta(days=7)
    )


# ==============================================================================
# OTP CONFIGURATION
# ==============================================================================
# OTP settings - adjust based on security requirements
OTP_EXPIRY_MINUTES = 10  # How long OTP is valid
OTP_LENGTH = 6           # Number of digits (6 is standard)


# ==============================================================================
# OTP FUNCTIONS
# ==============================================================================
def generate_otp() -> str:
    """
    Generate a random 6-digit OTP.

    Uses Python's random.choices() which is suitable for OTPs.
    For higher security (e.g., cryptographic keys), use secrets module.

    Returns:
        6-digit string like "123456"
    """
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def store_otp(email: str, otp: str, purpose: str) -> None:
    """
    Store OTP in memory with expiration and attempt tracking.

    The key format "email:purpose" allows same email to have
    different OTPs for different purposes (register vs login).

    Args:
        email: User's email address (lowercased for consistency)
        otp: Generated OTP code
        purpose: 'register' or 'login' - distinguishes OTP usage
    """
    key = f"{email.lower()}:{purpose}"
    otp_store[key] = {
        "otp": otp,
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
        "attempts": 0,  # Track failed verification attempts
    }


def verify_otp(email: str, otp: str, purpose: str) -> bool:
    """
    Verify OTP for given email and purpose.

    Security measures:
    1. OTPs expire after OTP_EXPIRY_MINUTES (10 minutes)
    2. Maximum 3 attempts before OTP is invalidated
    3. OTP is deleted after successful verification (one-time use)

    Args:
        email: User's email address
        otp: OTP code entered by user
        purpose: 'register' or 'login'

    Returns:
        True if OTP is valid, False otherwise
    """
    key = f"{email.lower()}:{purpose}"

    # Check if OTP exists for this email/purpose
    if key not in otp_store:
        return False

    stored = otp_store[key]

    # Check if expired
    if datetime.utcnow() > stored["expires_at"]:
        del otp_store[key]  # Clean up expired OTP
        return False

    # Check attempt limit (prevent brute-force)
    if stored["attempts"] >= 3:
        del otp_store[key]  # Too many attempts, require new OTP
        return False

    # Increment attempts before verification
    stored["attempts"] += 1

    # Verify OTP matches
    if stored["otp"] == otp:
        del otp_store[key]  # One-time use - delete after success
        return True

    return False


# ==============================================================================
# VERIFICATION TOKEN FUNCTIONS
# ==============================================================================
def create_verification_token(email: str, purpose: str) -> str:
    """
    Create a short-lived token after successful OTP verification.

    This token proves that the user verified their email via OTP.
    It can be used to complete registration or login.

    Why use a token instead of just proceeding?
    - Allows the verification and completion steps to be separate API calls
    - Provides a time window (15 minutes) to complete the process
    - More secure than keeping OTP in memory for extended time

    Args:
        email: User's email address
        purpose: 'register' or 'login'

    Returns:
        Encoded JWT verification token (valid for 15 minutes)
    """
    return create_access_token(
        data={"email": email, "purpose": purpose, "type": "otp_verified"},
        expires_delta=timedelta(minutes=15)  # Short-lived for security
    )


def verify_verification_token(token: str, expected_purpose: str) -> Optional[str]:
    """
    Verify a verification token and return the email.

    Validates that:
    1. Token is valid and not expired
    2. Token type is "otp_verified" (not a regular access token)
    3. Token purpose matches expected purpose

    Args:
        token: JWT verification token
        expected_purpose: Expected purpose ('register' or 'login')

    Returns:
        Email address if valid, None otherwise
    """
    payload = decode_access_token(token)

    if not payload:
        return None

    # Ensure this is a verification token, not a regular access token
    if payload.get("type") != "otp_verified":
        return None

    # Ensure purpose matches (can't use a 'register' token to login)
    if payload.get("purpose") != expected_purpose:
        return None

    return payload.get("email")


# ==============================================================================
# OTP EMAIL SENDING
# ==============================================================================
async def send_otp_email(email: str, otp: str, purpose: str) -> bool:
    """
    Send OTP email to user using Brevo SMTP.

    This function:
    1. Checks if email is configured (EMAIL_ENABLED)
    2. If not configured, logs the OTP for development
    3. If configured, sends via Brevo SMTP

    The email includes:
    - Branded header with ShopEase logo colors
    - Large, easy-to-read OTP code
    - Expiration time warning
    - Security notice about not sharing the code

    Args:
        email: Recipient email address
        otp: OTP code to send
        purpose: 'register' or 'login' - customizes email text

    Returns:
        True if email sent (or logged in dev mode), False on error
    """
    settings = get_settings()

    subject = "Your ShopEase Verification Code"

    # Customize message based on purpose
    if purpose == "register":
        action = "complete your registration"
    else:
        action = "login to your account"

    # HTML email template with inline CSS for email client compatibility
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

    # Development mode: Log OTP instead of sending email
    # This is useful when email isn't configured during development
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
        return True  # Return true so the app flow continues

    # Production: Send email via Brevo SMTP
    try:
        logger.info(f"Sending OTP to {email} via Brevo SMTP...")

        # Create multipart message (HTML + plain text)
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
        msg["To"] = email

        # Plain text version for email clients that don't support HTML
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

        # Connect to Brevo SMTP with timeout
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            server.set_debuglevel(0)  # Set to 1 for SMTP debugging
            server.ehlo()             # Identify ourselves to the server
            server.starttls()         # Upgrade to TLS encryption
            server.ehlo()             # Re-identify after TLS

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

    # Handle specific SMTP errors with helpful messages
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
