import asyncio
import logging
from typing import List, Tuple

from fantrax_pl_lineup_manager.clients.fantraxclient import FantraxClient
from fantrax_pl_lineup_manager.services.fantrax_player import FantraxPlayer
from fantrax_pl_lineup_manager.services.fantrax_roster import FantraxRoster

logger = logging.getLogger(__name__)


class GameweekManager:
    def __init__(self, client: FantraxClient, team_id: str, update_lineup_interval: int, run_once: bool = False):
        self.roster:FantraxRoster = FantraxRoster(client, team_id)
        self._running = False
        self.update_lineup_interval = update_lineup_interval
        self.run_once = run_once
            
    async def run(self):
        """Run the gameweek manager, executing optimize_lineup every 10 minutes."""
        self._running = True
        logger.info("Gameweek Manager running")
        
        if self.run_once:
            logger.info("Running once, making substitutions")
            await asyncio.to_thread(self.make_substitutions)
            return
        
        while self._running:
            try:
                await asyncio.to_thread(self.make_substitutions)
            except Exception as e:
                logger.error(f"Error during lineup optimization: {e}", exc_info=True)
            
            await asyncio.sleep(self.update_lineup_interval)
    
    def make_substitutions(self):
        """Make substitutions for the current gameweek roster."""

        logger.info(f"Refreshing roster")
        self.roster.refresh_roster()

        logger.info(f"Starting make_substitutions() for current gameweek roster")
        
        # Find optimal substitutions
        substitutions: List[Tuple[FantraxPlayer, FantraxPlayer]] = self.roster.get_optimal_substitutions()
        
        logger.info(f"Found {len(substitutions)} optimal substitutions: {[substitution[1].name + ' -> ' + substitution[0].name for substitution in substitutions]}")
        for substitution in substitutions:
            logger.info(f"Substituting {substitution[1].name} for {substitution[0].name}")

            # Substitute the players
            self.roster.substitute_players(substitution[1].id, substitution[0].id)
    