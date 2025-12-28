import asyncio
import logging
from typing import Dict

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
        logger.info(f"Updating fantrax lineup based on reported current gameweek rosters")
        
        # Get all players
        all_players = list(self.roster.players.values())
        
        # Identify problematic starters (rostered_starter=True with gameweek_status in ['benched', 'out'])
        problematic_starters = [
            player for player in all_players
            if player.fantrax.get('rostered_starter') and 
               player.fantrax.get('gameweek_status') in ['benched', 'out']
        ]
        
        # Get all reserves (rostered_starter=False with gameweek_status in ['starting', 'expected-to-play'])
        reserves = [
            player for player in all_players
            if not player.fantrax.get('rostered_starter') and
                player.fantrax.get('gameweek_status') in ['starting', 'expected-to-play']
        ]
        
        # Get current starters for position counting
        current_starters = [
            player for player in all_players
            if player.fantrax.get('rostered_starter')
        ]
        
        # Count positions in current starting lineup
        def count_positions(players):
            counts = {'G': 0, 'D': 0, 'M': 0, 'F': 0}
            for player in players:
                pos = player.fantrax.get('rostered_position')
                if pos in counts:
                    counts[pos] += 1
            return counts
        
        current_position_counts = count_positions(current_starters)
        
        # Helper function to check if a lineup would be valid after substitutions
        def would_be_valid_after_substitutions(substitutions):
            # Create a copy of position counts
            new_counts = current_position_counts.copy()
            
            # Apply substitutions
            for player_out_id, player_in_id in substitutions:
                player_out = self.roster.get_player(player_out_id)
                player_in = self.roster.get_player(player_in_id)
                
                if player_out and player_in:
                    pos_out = player_out.fantrax.get('rostered_position')
                    pos_in = player_in.fantrax.get('rostered_position')
                    
                    if pos_out in new_counts:
                        new_counts[pos_out] -= 1
                    if pos_in in new_counts:
                        new_counts[pos_in] += 1
            
            # Check constraints
            total = sum(new_counts.values())
            return (
                total == 11 and
                new_counts['G'] == 1 and
                new_counts['D'] >= 3 and
                new_counts['M'] >= 3 and
                new_counts['F'] >= 1
            )
        
        # Helper function to score a reserve player (higher is better)
        def score_reserve(player):
            status = player.fantrax.get('gameweek_status')
            # Prefer 'starting' > 'expected-to-play' > others
            if status == 'starting':
                return 3
            elif status == 'expected-to-play':
                return 2
            elif status in ['benched', None]:
                return 1
            else:  # 'out' or other
                return 0
        
        # Find optimal substitutions
        substitutions = []
        used_reserve_ids = set()
        
        # Sort problematic starters to prioritize critical positions first
        # Priority: G > D > M > F (since G must be exactly 1, D and M need at least 3)
        position_priority = {'G': 4, 'D': 3, 'M': 2, 'F': 1}
        
        problematic_starters_sorted = sorted(
            problematic_starters,
            key=lambda p: position_priority.get(p.fantrax.get('rostered_position'), 0),
            reverse=True
        )
        
        for player_out in problematic_starters_sorted:
            player_out_id = player_out.fantrax['id']
            required_position = player_out.fantrax.get('rostered_position')
            
            if not required_position:
                logger.warning(f"Player {player_out_id} has no position, skipping")
                continue
            
            # Find best available reserve with matching position
            matching_reserves = [
                r for r in reserves
                if r.fantrax['id'] not in used_reserve_ids and
                   r.fantrax.get('rostered_position') == required_position
            ]
            
            if not matching_reserves:
                logger.warning(
                    f"No available reserve found for {player_out.fantrax.get('name')} "
                    f"({required_position}) with gameweek_status {player_out.fantrax.get('gameweek_status')}"
                )
                continue
            
            # Sort by score (best first)
            matching_reserves.sort(key=score_reserve, reverse=True)
            
            # Try each reserve until we find one that maintains valid lineup
            found_substitution = False
            for player_in in matching_reserves:
                # Test if this substitution would maintain valid lineup
                test_substitutions = substitutions + [(player_out_id, player_in.fantrax['id'])]
                
                if would_be_valid_after_substitutions(test_substitutions):
                    substitutions.append((player_out_id, player_in.fantrax['id']))
                    used_reserve_ids.add(player_in.fantrax['id'])
                    found_substitution = True
                    logger.info(
                        f"Substitution: {player_out.fantrax.get('name')} ({required_position}) "
                        f"[{player_out.fantrax.get('gameweek_status')}] -> "
                        f"{player_in.fantrax.get('name')} ({required_position}) "
                        f"[{player_in.fantrax.get('gameweek_status')}]"
                    )
                    break
            
            if not found_substitution:
                logger.warning(
                    f"Could not find valid substitution for {player_out.fantrax.get('name')} "
                    f"({required_position}) that maintains lineup validity"
                )
        
        # Return list of substitutions as [playerId_out, playerId_in] pairs
        return substitutions