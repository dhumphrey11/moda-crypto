from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Firebase Configuration
    firebase_project_id: str
    firebase_client_email: str
    firebase_private_key: str
    firebase_storage_bucket: str
    google_application_credentials: Optional[str] = None

    # API Keys
    coingecko_api_key: Optional[str] = None
    moralis_api_key: Optional[str] = None
    covalent_api_key: Optional[str] = None
    lunarcrush_api_key: Optional[str] = None
    coinmarketcal_api_key: Optional[str] = None
    cryptopanic_api_key: Optional[str] = None
    coinbase_api_key: Optional[str] = None
    coinbase_api_secret: Optional[str] = None

    # Application Settings
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    # ML Model Settings
    model_retrain_days: int = 7
    min_composite_score: float = 0.85
    max_position_size: float = 0.10
    max_token_allocation: float = 0.15

    # Paper Trading Settings
    initial_cash: float = 10000.0
    min_liquidity_usd: float = 50000.0

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Fix Firebase private key formatting
        if self.firebase_private_key:
            self.firebase_private_key = self.firebase_private_key.replace(
                '\\n', '\n')


# Global settings instance
settings = Settings()
