"""
==============================================================================
Configuration Module (config.py)
==============================================================================

PURPOSE:
--------
This module manages all application configuration settings using environment
variables. It provides a centralized, type-safe way to access configuration
values throughout the application.

WHY WE USE THIS APPROACH:
-------------------------
1. **Separation of Concerns**: Configuration is separate from code, making it
   easy to change settings without modifying source code.

2. **Environment-Based Config**: Same code works in development, staging, and
   production by simply changing environment variables.

3. **Security**: Sensitive values (JWT secrets, API keys, database credentials)
   are never hardcoded in source files.

4. **Type Safety**: Pydantic validates and converts environment variables to
   the correct Python types automatically.

5. **Caching**: Using @lru_cache ensures settings are loaded only once, improving
   performance and ensuring consistency.

HOW IT WORKS:
-------------
1. On startup, Pydantic reads from .env file (for local development) or
   system environment variables (for production/Vercel).

2. Each setting has a default value as fallback if not provided.

3. get_settings() returns a cached Settings instance that can be imported
   anywhere in the application.

USAGE EXAMPLE:
--------------
    from app.config import get_settings

    settings = get_settings()
    print(settings.APP_NAME)  # "E-Commerce API"
    print(settings.JWT_SECRET_KEY)  # Value from environment
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# ==============================================================================
# PATH CONFIGURATION
# ==============================================================================
# Get the backend directory to locate the .env file
# __file__ = config.py
# dirname(__file__) = app/
# dirname(dirname(__file__)) = backend/
# This ensures .env is found regardless of where the script is run from
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_FILE_PATH = os.path.join(_BACKEND_DIR, ".env")


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Pydantic's BaseSettings class automatically:
    - Reads values from environment variables (case-insensitive)
    - Reads from .env file if it exists
    - Converts strings to appropriate Python types (int, bool, etc.)
    - Validates values and raises errors for invalid configurations

    Attributes are grouped by category for easier understanding:
    - Application: Basic app metadata
    - Server: Host and port configuration
    - JWT: JSON Web Token settings for authentication
    - Firebase: Google Firebase/Firestore database connection
    - CORS: Cross-Origin Resource Sharing settings
    - Email: SMTP configuration for transactional emails
    """

    # ==========================================================================
    # APPLICATION SETTINGS
    # ==========================================================================
    # These identify the application and are used in API documentation
    APP_NAME: str = "E-Commerce API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # Set True for development (enables hot reload, verbose errors)

    # ==========================================================================
    # SERVER SETTINGS
    # ==========================================================================
    # 0.0.0.0 allows connections from any IP (required for Docker/production)
    # For local development only, 127.0.0.1 is more secure
    HOST: str = "0.0.0.0"
    PORT: int = 8000  # Default FastAPI port; can be overridden in production

    # ==========================================================================
    # JWT (JSON Web Token) CONFIGURATION
    # ==========================================================================
    # JWT is used for stateless authentication. The server signs tokens with
    # the secret key, and clients include the token in requests to prove identity.
    #
    # IMPORTANT: Change JWT_SECRET_KEY in production! It should be a long,
    # random string. Generate one with: python -c "import secrets; print(secrets.token_hex(32))"
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"  # HMAC with SHA-256; industry standard for JWT
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours; adjust based on security needs

    # ==========================================================================
    # FIREBASE CONFIGURATION
    # ==========================================================================
    # Firebase Firestore is our NoSQL database. Connection can be configured
    # in three ways (see get_firebase_credentials method):
    # 1. JSON string containing full credentials (FIREBASE_CREDENTIALS_JSON)
    # 2. Path to credentials file (FIREBASE_CREDENTIALS_PATH)
    # 3. Individual environment variables (FIREBASE_PROJECT_ID, etc.)
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""  # Must include actual newlines, not escaped
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CLIENT_ID: str = ""
    FIREBASE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    FIREBASE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    FIREBASE_CREDENTIALS_PATH: str = ""  # For Docker: path to serviceAccountKey.json
    FIREBASE_CREDENTIALS_JSON: str = ""  # For Vercel: JSON string of credentials

    # ==========================================================================
    # CORS (Cross-Origin Resource Sharing) CONFIGURATION
    # ==========================================================================
    # CORS controls which domains can make requests to this API.
    # "*" allows all origins (convenient for development, use specific origins in production)
    # For production, set to comma-separated list: "https://myapp.com,https://www.myapp.com"
    CORS_ORIGINS: str = "*"

    # ==========================================================================
    # EMAIL CONFIGURATION (Brevo/Sendinblue SMTP)
    # ==========================================================================
    # We use Brevo (formerly Sendinblue) for sending transactional emails
    # (order confirmations, OTP codes, etc.)
    #
    # Why Brevo?
    # - Free tier: 300 emails/day
    # - Reliable delivery
    # - Easy SMTP integration
    # - Good analytics/tracking
    BREVO_API_KEY: str = ""  # For future API-based sending
    BREVO_SMTP_LOGIN: str = ""  # Usually your Brevo account email
    BREVO_SMTP_PASSWORD: str = ""  # SMTP key from Brevo dashboard
    SMTP_HOST: str = "smtp-relay.brevo.com"  # Brevo's SMTP server
    SMTP_PORT: int = 587  # TLS port; 465 for SSL
    SMTP_TLS: bool = True  # Use TLS encryption (recommended)
    SMTP_FROM_NAME: str = "ShopEase"  # Sender name shown to recipients
    SMTP_FROM_EMAIL: str = "noreply@shopease.com"  # Must be verified in Brevo
    EMAIL_ENABLED: bool = False  # Master switch; set True when email is configured

    @property
    def SMTP_USER(self) -> str:
        """
        Alias for BREVO_SMTP_LOGIN for compatibility.

        Some email libraries expect SMTP_USER variable. This property
        provides backwards compatibility without duplicate configuration.
        """
        return self.BREVO_SMTP_LOGIN

    @property
    def SMTP_PASSWORD(self) -> str:
        """Alias for BREVO_SMTP_PASSWORD for compatibility."""
        return self.BREVO_SMTP_PASSWORD

    def is_email_configured(self) -> bool:
        """
        Check if email is properly configured for sending.

        Returns True only if:
        - EMAIL_ENABLED is True (master switch)
        - SMTP login credentials are provided
        - From email address is set

        Use this check before attempting to send emails to avoid errors.
        """
        return bool(
            self.EMAIL_ENABLED and
            self.BREVO_SMTP_LOGIN and
            self.BREVO_SMTP_PASSWORD and
            self.SMTP_FROM_EMAIL
        )

    class Config:
        """
        Pydantic configuration for loading settings.

        - env_file: Path to .env file for local development
        - env_file_encoding: File encoding (UTF-8 for cross-platform compatibility)
        - extra: "ignore" means extra env vars won't cause errors
        """
        env_file = _ENV_FILE_PATH
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_cors_origins(self) -> list:
        """
        Parse CORS origins from comma-separated string to list.

        Examples:
            CORS_ORIGINS="*" -> ["*"] (allow all)
            CORS_ORIGINS="https://a.com,https://b.com" -> ["https://a.com", "https://b.com"]

        Returns:
            List of allowed origin URLs
        """
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def get_firebase_credentials(self) -> dict:
        """
        Build Firebase credentials dictionary from environment variables.

        Firebase Admin SDK needs credentials to authenticate. This method
        supports three configuration approaches, checked in order:

        1. FIREBASE_CREDENTIALS_JSON: Full credentials as JSON string
           - Best for serverless (Vercel, AWS Lambda) where files aren't persistent
           - Set in Vercel dashboard as environment variable

        2. FIREBASE_CREDENTIALS_PATH: Path to credentials JSON file
           - Best for Docker/traditional servers
           - File is copied into container or stored on server

        3. Individual environment variables: Each credential field separate
           - Fallback option; requires more configuration
           - Useful when you can't use JSON or files

        Returns:
            Dictionary with Firebase credentials suitable for firebase_admin.credentials.Certificate()
        """
        import json

        # Option 1: JSON string (for Vercel/serverless)
        # The full service account JSON is stored as a single environment variable
        if self.FIREBASE_CREDENTIALS_JSON:
            try:
                return json.loads(self.FIREBASE_CREDENTIALS_JSON)
            except json.JSONDecodeError:
                pass  # Fall through to other options

        # Option 2: Credentials file path (for Docker)
        # Returns special format that firebase.py recognizes
        if self.FIREBASE_CREDENTIALS_PATH and os.path.exists(self.FIREBASE_CREDENTIALS_PATH):
            return {"credential_path": self.FIREBASE_CREDENTIALS_PATH}

        # Option 3: Build from individual environment variables
        # Handle escaped newlines in private key (common issue in env vars)
        private_key = self.FIREBASE_PRIVATE_KEY
        if private_key:
            # Remove surrounding quotes if present (sometimes added by shells)
            private_key = private_key.strip('"').strip("'")
            # Replace escaped newlines with actual newlines
            # Environment variables often have \\n instead of actual line breaks
            private_key = private_key.replace("\\n", "\n")
            # Also handle double-escaped newlines (\\\\n -> \n)
            private_key = private_key.replace("\\\\n", "\n")

        # Return full credentials dictionary matching Google's service account format
        return {
            "type": "service_account",
            "project_id": self.FIREBASE_PROJECT_ID,
            "private_key_id": self.FIREBASE_PRIVATE_KEY_ID,
            "private_key": private_key,
            "client_email": self.FIREBASE_CLIENT_EMAIL,
            "client_id": self.FIREBASE_CLIENT_ID,
            "auth_uri": self.FIREBASE_AUTH_URI,
            "token_uri": self.FIREBASE_TOKEN_URI,
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{self.FIREBASE_CLIENT_EMAIL}"
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Uses @lru_cache to ensure Settings is instantiated only once.
    This is important because:
    1. Performance: Avoids re-reading environment variables on every call
    2. Consistency: All parts of the application see the same settings
    3. Validation: Environment variable errors are caught at startup

    Returns:
        Settings instance with all configuration loaded

    Usage:
        from app.config import get_settings
        settings = get_settings()
        print(settings.APP_NAME)
    """
    return Settings()
