"""Data synchronization service for fetching and storing Fantrax data."""
import asyncio
import logging
from typing import Optional

from fantrax_service.clients.fantraxclient import FantraxClient
from fantrax_service.data.repositories import (
    PlayerRepository,
    RosterRepository,
    SyncLogRepository
)
from fantrax_service.data.database import session_scope
from fantrax_service.config import Config

logger = logging.getLogger(__name__)


class DataSyncService:
    """Service for synchronizing data from Fantrax API to database."""
    
    def __init__(self, client: FantraxClient):
        self.client = client
        self.player_repo = PlayerRepository()
        self.roster_repo = RosterRepository(self.player_repo)
        self.sync_log_repo = SyncLogRepository()
        self._running = False
    
    async def run(self, sync_interval: Optional[int] = None):
        """Run the data sync service, executing sync periodically."""
        sync_interval = sync_interval or Config.SYNC_INTERVAL
        self._running = True
        logger.info(f"Data Sync Service running with interval: {sync_interval} seconds")
        
        # Do an initial sync
        await asyncio.to_thread(self.sync_roster_data)
        
        while self._running:
            try:
                await asyncio.sleep(sync_interval)
                await asyncio.to_thread(self.sync_roster_data)
            except Exception as e:
                logger.error(f"Error during data sync: {e}", exc_info=True)
                try:
                    with session_scope() as session:
                        self.sync_log_repo.log_sync(
                            sync_type="roster",
                            status="failed",
                            error_message=str(e),
                            session=session
                        )
                except Exception as log_error:
                    logger.error(f"Error logging sync failure: {log_error}", exc_info=True)
    
    def stop(self):
        """Stop the data sync service."""
        self._running = False
        logger.info("Data Sync Service stopped")
    
    def sync_roster_data(self):
        """Synchronize roster data from Fantrax API to database."""
        logger.info("Starting roster data synchronization")
        records_updated = 0
        error_message = None
        status = "success"
        
        try:
            # Fetch roster from Fantrax API
            roster = self.client.get_roster()
            
            # Process each player
            with session_scope() as session:
                for player in roster.players.values():
                    try:
                        # Use the fantrax dict directly from the Player object
                        # The repository will handle creating/updating the player record
                        self.player_repo.create_or_update_player(
                            player.fantrax['id'],
                            player.fantrax,
                            session=session
                        )
                        records_updated += 1
                    except Exception as e:
                        logger.warning(f"Error processing player {player.fantrax.get('id', 'unknown')}: {e}", exc_info=True)
                        # Continue with other players
                
                # Log the sync operation
                self.sync_log_repo.log_sync(
                    sync_type="roster",
                    status=status,
                    records_updated=records_updated,
                    session=session
                )
            
            logger.info(f"Roster data synchronization completed. Updated {records_updated} players")
            
        except Exception as e:
            error_message = str(e)
            status = "failed"
            logger.error(f"Roster data synchronization failed: {e}", exc_info=True)
            
            # Log the failure
            try:
                with session_scope() as session:
                    self.sync_log_repo.log_sync(
                        sync_type="roster",
                        status=status,
                        records_updated=records_updated,
                        error_message=error_message,
                        session=session
                    )
            except Exception as log_error:
                logger.error(f"Error logging sync failure: {log_error}", exc_info=True)
    
    def sync_player_data(self, player_id: str):
        """Synchronize data for a specific player."""
        try:
            # This would require additional Fantrax API methods if available
            # For now, this is a placeholder for future implementation
            logger.warning(f"Individual player sync not yet implemented for player {player_id}")
        except Exception as e:
            logger.error(f"Error syncing player {player_id}: {e}", exc_info=True)
            raise

