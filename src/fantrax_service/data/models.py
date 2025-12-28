"""SQLAlchemy database models."""
from sqlalchemy import Column, String, Integer, Numeric, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any

from fantrax_service.data.database import Base


class PlayerModel(Base):
    """Database model for players."""
    __tablename__ = "players"
    
    id = Column(String, primary_key=True)  # Fantrax player ID
    name = Column(String, nullable=False)
    team_name = Column(String, nullable=True)
    position = Column(String, nullable=True)
    
    # Fantrax data stored as JSONB (or JSON for SQLite)
    fantrax_data = Column(JSON, nullable=True)
    
    # Enriched data
    performance_score = Column(Numeric(precision=10, scale=2), nullable=True)
    transfer_value = Column(Numeric(precision=10, scale=2), nullable=True)
    last_updated = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    stats = relationship("PlayerStatsModel", back_populates="player", cascade="all, delete-orphan")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "team_name": self.team_name,
            "position": self.position,
            "fantrax_data": self.fantrax_data,
            "performance_score": float(self.performance_score) if self.performance_score else None,
            "transfer_value": float(self.transfer_value) if self.transfer_value else None,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class PlayerStatsModel(Base):
    """Database model for player statistics (time-series data)."""
    __tablename__ = "player_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    player_id = Column(String, ForeignKey("players.id", ondelete="CASCADE"), nullable=False)
    gameweek = Column(Integer, nullable=False)
    points = Column(Numeric(precision=10, scale=2), nullable=True)
    stats = Column(JSON, nullable=True)  # Flexible stats storage
    recorded_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships
    player = relationship("PlayerModel", back_populates="stats")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "player_id": self.player_id,
            "gameweek": self.gameweek,
            "points": float(self.points) if self.points else None,
            "stats": self.stats,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }


class SyncLogModel(Base):
    """Database model for tracking data synchronization operations."""
    __tablename__ = "sync_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sync_type = Column(String, nullable=False)  # e.g., "roster", "player_stats"
    status = Column(String, nullable=False)  # e.g., "success", "failed", "partial"
    records_updated = Column(Integer, nullable=True)
    error_message = Column(String, nullable=True)
    synced_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "sync_type": self.sync_type,
            "status": self.status,
            "records_updated": self.records_updated,
            "error_message": self.error_message,
            "synced_at": self.synced_at.isoformat() if self.synced_at else None,
        }

