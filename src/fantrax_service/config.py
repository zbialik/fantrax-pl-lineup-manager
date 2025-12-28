"""Configuration management for Fantrax Service."""
import os
from typing import Optional


class Config:
    """Application configuration."""
    
    # Database configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./fantrax_data.db"  # Default to SQLite for local dev
    )
    
    # Fantrax API configuration
    LEAGUE_ID: Optional[str] = os.getenv("LEAGUE_ID")
    TEAM_ID: Optional[str] = os.getenv("TEAM_ID")
    FANTRAX_COOKIE_FILE: Optional[str] = os.getenv("FANTRAX_COOKIE_FILE")
    
    # Data sync configuration
    SYNC_INTERVAL: int = int(os.getenv("SYNC_INTERVAL", "3600"))  # 1 hour default
    SYNC_ENABLED: bool = os.getenv("SYNC_ENABLED", "true").lower() == "true"
    
    # Gameweek manager configuration
    UPDATE_LINEUP_INTERVAL: int = int(os.getenv("UPDATE_LINEUP_INTERVAL", "600"))  # 10 minutes default
    
    # Feature flags
    TRANSFER_SERVICE_ENABLED: bool = os.getenv("TRANSFER_SERVICE_ENABLED", "false").lower() == "true"
    ANALYTICS_SERVICE_ENABLED: bool = os.getenv("ANALYTICS_SERVICE_ENABLED", "false").lower() == "true"
    PREDICTION_SERVICE_ENABLED: bool = os.getenv("PREDICTION_SERVICE_ENABLED", "false").lower() == "true"

