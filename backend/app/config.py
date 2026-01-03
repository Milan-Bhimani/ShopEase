"""
Application configuration using environment variables.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
import os

# Get the backend directory (where .env file is located)
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_ENV_FILE_PATH = os.path.join(_BACKEND_DIR, ".env")


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "E-Commerce API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # JWT Configuration
    JWT_SECRET_KEY: str = "your-super-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Firebase Configuration
    FIREBASE_PROJECT_ID: str = ""
    FIREBASE_PRIVATE_KEY_ID: str = ""
    FIREBASE_PRIVATE_KEY: str = ""
    FIREBASE_CLIENT_EMAIL: str = ""
    FIREBASE_CLIENT_ID: str = ""
    FIREBASE_AUTH_URI: str = "https://accounts.google.com/o/oauth2/auth"
    FIREBASE_TOKEN_URI: str = "https://oauth2.googleapis.com/token"
    FIREBASE_CREDENTIALS_PATH: str = ""  # Alternative: path to JSON credentials file
    FIREBASE_CREDENTIALS_JSON: str = ""  # Alternative: JSON string of credentials (for Vercel)

    # CORS
    CORS_ORIGINS: str = "*"  # Comma-separated list of origins

    # Brevo SMTP Configuration
    BREVO_API_KEY: str = ""
    BREVO_SMTP_LOGIN: str = ""
    BREVO_SMTP_PASSWORD: str = ""
    SMTP_HOST: str = "smtp-relay.brevo.com"
    SMTP_PORT: int = 587
    SMTP_TLS: bool = True
    SMTP_FROM_NAME: str = "ShopEase"
    SMTP_FROM_EMAIL: str = "noreply@shopease.com"
    EMAIL_ENABLED: bool = False

    @property
    def SMTP_USER(self) -> str:
        """Alias for BREVO_SMTP_LOGIN for compatibility."""
        return self.BREVO_SMTP_LOGIN

    @property
    def SMTP_PASSWORD(self) -> str:
        """Alias for BREVO_SMTP_PASSWORD for compatibility."""
        return self.BREVO_SMTP_PASSWORD

    def is_email_configured(self) -> bool:
        """Check if email is properly configured."""
        return bool(
            self.EMAIL_ENABLED and
            self.BREVO_SMTP_LOGIN and
            self.BREVO_SMTP_PASSWORD and
            self.SMTP_FROM_EMAIL
        )

    class Config:
        env_file = _ENV_FILE_PATH
        env_file_encoding = "utf-8"
        extra = "ignore"

    def get_cors_origins(self) -> list:
        """Parse CORS origins from comma-separated string."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def get_firebase_credentials(self) -> dict:
        """
        Build Firebase credentials dictionary from environment variables.
        Returns credentials dict for firebase_admin initialization.
        """
        import json

        # Option 1: JSON string (for Vercel/serverless)
        if self.FIREBASE_CREDENTIALS_JSON:
            try:
                return json.loads(self.FIREBASE_CREDENTIALS_JSON)
            except json.JSONDecodeError:
                pass

        # Option 2: Credentials file path (for Docker)
        if self.FIREBASE_CREDENTIALS_PATH and os.path.exists(self.FIREBASE_CREDENTIALS_PATH):
            return {"credential_path": self.FIREBASE_CREDENTIALS_PATH}

        # Option 3: Build from individual environment variables
        private_key = self.FIREBASE_PRIVATE_KEY
        # Handle escaped newlines in private key
        if private_key:
            # Remove surrounding quotes if present
            private_key = private_key.strip('"').strip("'")
            # Replace escaped newlines with actual newlines
            private_key = private_key.replace("\\n", "\n")
            # Also handle double-escaped newlines
            private_key = private_key.replace("\\\\n", "\n")

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
    """Get cached settings instance."""
    return Settings()
