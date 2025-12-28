"""Repository pattern implementation for data access."""
import logging
from datetime import datetime
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from sqlalchemy.sql import func

from fantrax_service.data.database import session_scope
from fantrax_service.data.models import PlayerModel, PlayerStatsModel, SyncLogModel
from fantrax_service.player import Player

logger = logging.getLogger(__name__)


class PlayerRepository:
    """Repository for player data access."""
    
    def get_player(self, player_id: str, session: Optional[Session] = None) -> Optional[PlayerModel]:
        """Get a player by ID."""
        if session:
            return session.query(PlayerModel).filter(PlayerModel.id == player_id).first()
        else:
            with session_scope() as sess:
                return sess.query(PlayerModel).filter(PlayerModel.id == player_id).first()
    
    def get_all_players(self, session: Optional[Session] = None) -> List[PlayerModel]:
        """Get all players."""
        if session:
            return session.query(PlayerModel).all()
        else:
            with session_scope() as sess:
                return sess.query(PlayerModel).all()
    
    def create_or_update_player(
        self,
        player_id: str,
        fantrax_data: Dict[str, Any],
        session: Optional[Session] = None
    ) -> PlayerModel:
        """Create or update a player with Fantrax data."""
        if session:
            return self._upsert_player(session, player_id, fantrax_data)
        else:
            with session_scope() as sess:
                return self._upsert_player(sess, player_id, fantrax_data)
    
    def _upsert_player(
        self,
        session: Session,
        player_id: str,
        fantrax_data: Dict[str, Any]
    ) -> PlayerModel:
        """Internal method to upsert a player."""
        # Extract basic fields from fantrax_data
        name = fantrax_data.get('name', '')
        team_name = fantrax_data.get('team_name')
        position = fantrax_data.get('rostered_position_short_name')
        
        # Try to get existing player
        player = session.query(PlayerModel).filter(PlayerModel.id == player_id).first()
        
        if player:
            # Update existing player
            player.name = name
            player.team_name = team_name
            player.position = position
            player.fantrax_data = fantrax_data
            player.last_updated = datetime.utcnow()
            session.merge(player)
        else:
            # Create new player
            player = PlayerModel(
                id=player_id,
                name=name,
                team_name=team_name,
                position=position,
                fantrax_data=fantrax_data,
                last_updated=datetime.utcnow()
            )
            session.add(player)
        
        return player
    
    def update_enriched_data(
        self,
        player_id: str,
        performance_score: Optional[float] = None,
        transfer_value: Optional[float] = None,
        session: Optional[Session] = None
    ) -> Optional[PlayerModel]:
        """Update enriched data for a player."""
        if session:
            return self._update_enriched(session, player_id, performance_score, transfer_value)
        else:
            with session_scope() as sess:
                return self._update_enriched(sess, player_id, performance_score, transfer_value)
    
    def _update_enriched(
        self,
        session: Session,
        player_id: str,
        performance_score: Optional[float],
        transfer_value: Optional[float]
    ) -> Optional[PlayerModel]:
        """Internal method to update enriched data."""
        player = session.query(PlayerModel).filter(PlayerModel.id == player_id).first()
        if not player:
            logger.warning(f"Player {player_id} not found for enriched data update")
            return None
        
        if performance_score is not None:
            player.performance_score = performance_score
        if transfer_value is not None:
            player.transfer_value = transfer_value
        
        session.merge(player)
        return player
    
    def merge_fantrax_data(
        self,
        fantrax_player_row: Dict[str, Any],
        session: Optional[Session] = None
    ) -> PlayerModel:
        """Merge Fantrax API data into database.
        
        This method accepts the raw fantrax_player_row dict from the API,
        creates a Player object to normalize it, then stores the normalized
        fantrax dict in the database.
        """
        # Create a Player object to normalize the fantrax data structure
        player_obj = Player(fantrax_player_row)
        player_id = player_obj.fantrax['id']
        
        # Upsert the player with fantrax data
        player_model = self.create_or_update_player(player_id, player_obj.fantrax, session)
        return player_model
    
    def get_enriched_player(
        self,
        player_id: str,
        session: Optional[Session] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a player with enriched data merged."""
        player_model = self.get_player(player_id, session)
        if not player_model:
            return None
        
        # Merge fantrax_data with enriched fields
        result = player_model.fantrax_data.copy() if player_model.fantrax_data else {}
        result['performance_score'] = float(player_model.performance_score) if player_model.performance_score else None
        result['transfer_value'] = float(player_model.transfer_value) if player_model.transfer_value else None
        result['last_updated'] = player_model.last_updated.isoformat() if player_model.last_updated else None
        
        return result


class PlayerStatsRepository:
    """Repository for player statistics."""
    
    def add_player_stat(
        self,
        player_id: str,
        gameweek: int,
        points: Optional[float] = None,
        stats: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None
    ) -> PlayerStatsModel:
        """Add a player statistic record."""
        if session:
            return self._add_stat(session, player_id, gameweek, points, stats)
        else:
            with session_scope() as sess:
                return self._add_stat(sess, player_id, gameweek, points, stats)
    
    def _add_stat(
        self,
        session: Session,
        player_id: str,
        gameweek: int,
        points: Optional[float],
        stats: Optional[Dict[str, Any]]
    ) -> PlayerStatsModel:
        """Internal method to add a stat."""
        stat = PlayerStatsModel(
            player_id=player_id,
            gameweek=gameweek,
            points=points,
            stats=stats
        )
        session.add(stat)
        return stat
    
    def get_player_stats(
        self,
        player_id: str,
        gameweek: Optional[int] = None,
        session: Optional[Session] = None
    ) -> List[PlayerStatsModel]:
        """Get player statistics, optionally filtered by gameweek."""
        if session:
            query = session.query(PlayerStatsModel).filter(PlayerStatsModel.player_id == player_id)
            if gameweek:
                query = query.filter(PlayerStatsModel.gameweek == gameweek)
            return query.order_by(PlayerStatsModel.gameweek.desc()).all()
        else:
            with session_scope() as sess:
                query = sess.query(PlayerStatsModel).filter(PlayerStatsModel.player_id == player_id)
                if gameweek:
                    query = query.filter(PlayerStatsModel.gameweek == gameweek)
                return query.order_by(PlayerStatsModel.gameweek.desc()).all()


class RosterRepository:
    """Repository for roster data access."""
    
    def __init__(self, player_repo: Optional[PlayerRepository] = None):
        self.player_repo = player_repo or PlayerRepository()
    
    def get_roster_players(
        self,
        player_ids: Optional[List[str]] = None,
        session: Optional[Session] = None
    ) -> List[PlayerModel]:
        """Get players for a roster, optionally filtered by player IDs."""
        if player_ids:
            if session:
                return session.query(PlayerModel).filter(PlayerModel.id.in_(player_ids)).all()
            else:
                with session_scope() as sess:
                    return sess.query(PlayerModel).filter(PlayerModel.id.in_(player_ids)).all()
        else:
            return self.player_repo.get_all_players(session)


class SyncLogRepository:
    """Repository for sync log data."""
    
    def log_sync(
        self,
        sync_type: str,
        status: str,
        records_updated: Optional[int] = None,
        error_message: Optional[str] = None,
        session: Optional[Session] = None
    ) -> SyncLogModel:
        """Log a synchronization operation."""
        if session:
            return self._log(session, sync_type, status, records_updated, error_message)
        else:
            with session_scope() as sess:
                return self._log(sess, sync_type, status, records_updated, error_message)
    
    def _log(
        self,
        session: Session,
        sync_type: str,
        status: str,
        records_updated: Optional[int],
        error_message: Optional[str]
    ) -> SyncLogModel:
        """Internal method to log sync."""
        log_entry = SyncLogModel(
            sync_type=sync_type,
            status=status,
            records_updated=records_updated,
            error_message=error_message
        )
        session.add(log_entry)
        return log_entry
    
    def get_recent_syncs(
        self,
        sync_type: Optional[str] = None,
        limit: int = 10,
        session: Optional[Session] = None
    ) -> List[SyncLogModel]:
        """Get recent sync log entries."""
        if session:
            query = session.query(SyncLogModel)
            if sync_type:
                query = query.filter(SyncLogModel.sync_type == sync_type)
            return query.order_by(SyncLogModel.synced_at.desc()).limit(limit).all()
        else:
            with session_scope() as sess:
                query = sess.query(SyncLogModel)
                if sync_type:
                    query = query.filter(SyncLogModel.sync_type == sync_type)
                return query.order_by(SyncLogModel.synced_at.desc()).limit(limit).all()

