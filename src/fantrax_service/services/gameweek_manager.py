import asyncio
import logging

from fantrax_service.clients.fantraxclient import FantraxClient
from fantrax_service.roster import Roster

logger = logging.getLogger(__name__)


class GameweekManager:
    def __init__(self, client: FantraxClient, update_lineup_interval: int):
        self.client = client
        self.roster = client.get_roster()
        self._running = False
        self.update_lineup_interval = update_lineup_interval
    
    async def run(self):
        """Run the gameweek manager, executing optimize_lineup every 10 minutes."""
        self._running = True
        logger.info("Gameweek Manager running")
        
        while self._running:
            try:
                await asyncio.to_thread(self.update_lineup)
            except Exception as e:
                logger.error(f"Error during lineup optimization: {e}", exc_info=True)
            
            await asyncio.sleep(self.update_lineup_interval)
    
    def update_lineup(self):
        logger.info(f"Updating starting lineup based on reported currently reported rosters")
        
        # print(f"Roster: {self.roster}")
