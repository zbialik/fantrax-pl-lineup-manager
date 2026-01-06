import json
import inspect
import math
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Set, Optional, Callable, Tuple
from decimal import Decimal, InvalidOperation

from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.exceptions import FantraxException
from fantrax_pl_team_manager.domain.constants import *

from fantrax_pl_team_manager.domain.fantrax_roster_player import FantraxRosterPlayer

logger = logging.getLogger(__name__)


class FantraxRoster(List[FantraxRosterPlayer]):
    """A list of FantraxRosterPlayer objects with custom sorting capabilities.
    
    This class extends Python's list to provide a custom sort() method
    for sorting FantraxRosterPlayer objects.
    """
    
    def __init__(self, team_id: str, team_name: str, roster_limit_period: int, premier_league_table: PremierLeagueTable = None, iterable: Optional[List[FantraxRosterPlayer]] = []):
        self.team_id = team_id
        self.team_name = team_name
        self.roster_limit_period = roster_limit_period
        self.premier_league_table:PremierLeagueTable = premier_league_table
        super().__init__(iterable)
    
    @property
    def starters(self) -> List[FantraxRosterPlayer]:
        """Get all players currently in starting lineup.
        
        Returns:
            List[FantraxRosterPlayer]: List of starting players
        """
        return [player for player in self if player.rostered_starter]
    
    @property
    def reserves(self) -> List[FantraxRosterPlayer]:
        """Get all players currently on the bench.
        
        Returns:
            List[FantraxRosterPlayer]: List of reserve players
        """
        return [player for player in self if not player.rostered_starter]

    def get_roster_player(self, player_id:str) -> FantraxRosterPlayer:
        """Get a player by their Fantrax ID."""
        for player in self:
            if player.id == player_id:
                return player
        raise FantraxException(f"Player not found: {player_id}")
    
    def sort(self, *, key: Optional[Callable[[FantraxRosterPlayer], Any]] = None, reverse: bool = False) -> None:
        """Sort the roster in place.
        
        Args:
            key: Optional key function that extracts a comparison key from each player.
                 If not provided, a default sorting will be used.
            reverse: If True, sort in descending order
        """
        if key is None:
            # Default sorting behavior - can be customized as needed
            super().sort(key=key, reverse=reverse)
        else:
            super().sort(key=key, reverse=reverse)
 
    def valid_substitutions(self, swap_players: List[FantraxRosterPlayer], disable_min_position_counts_check: bool = False) -> Tuple[bool, Optional[str]]:
        """Check if a list of substitutions is valid.
        
        Validates that the proposed substitutions would result in a valid lineup
        according to position requirements (min/max counts per position).
        
        Parameters:
            swap_players: List of players to swap between starter and reserve
            disable_min_position_counts_check: Whether to disable checking minimum
                position counts (useful when checking if a player can be promoted
                to starter incrementally)
            
        Returns:
            Tuple containing:
                - bool: True if substitutions are valid, False otherwise
                - Optional[str]: Error message if invalid, None if valid
        """
        
        starter_position_counts:Dict[str, int] = {
            POSITION_KEY_GOALKEEPER: 0,
            POSITION_KEY_DEFENDER: 0,
            POSITION_KEY_MIDFIELDER: 0,
            POSITION_KEY_FORWARD: 0
        }
        for player in self.starters:
            starter_position_counts[player.rostered_position] += 1
        
        for player in swap_players:
            if player.disable_lineup_change:
                return (False, f"Player {player.name} is disabled from lineup changes")
            
            if player.rostered_starter:
                starter_position_counts[player.rostered_position] -= 1 # starter will be moved to bench
            else:
                starter_position_counts[player.rostered_position] += 1 # reserve will be moved to starter
        
        # REQ: at most MIN_STARTERS starters 
        if sum(starter_position_counts.values()) > MIN_STARTERS:
            return (False, f"Must have at most {MIN_STARTERS} starters")

        if not disable_min_position_counts_check:
            # REQ: at least MIN_DEFENDERS Defenders
            if starter_position_counts.get('D', 0) < MIN_DEFENDERS:
                return (False, f"Must have at least {MIN_DEFENDERS} Defenders")
            
            # REQ: at least MIN_MIDFIELDERS Midfielders
            if starter_position_counts.get('M', 0) < MIN_MIDFIELDERS:
                return (False, f"Must have at least {MIN_MIDFIELDERS} Midfielders")
            
            # REQ: at least MIN_FORWARDS Forwards
            if starter_position_counts.get('F', 0) < MIN_FORWARDS:
                return (False, f"Must have at least {MIN_FORWARDS} Forward")
        
        # REQ: at most MAX_GOALKEEPERS Goalkeeper
        if starter_position_counts.get('G', 0) > MAX_GOALKEEPERS:
            return (False, f"Must have at most {MAX_GOALKEEPERS} Goalkeeper")
        
        # REQ: at most MAX_DEFENDERS Defenders
        if starter_position_counts.get('D', 0) > MAX_DEFENDERS:
            return (False, f"Must have at most {MAX_DEFENDERS} Defenders")
        
        # REQ: at most MAX_MIDFIELDERS Midfielders
        if starter_position_counts.get('M', 0) > MAX_MIDFIELDERS:
            return (False, f"Must have at most {MAX_MIDFIELDERS} Midfielders")
        
        # REQ: at most MAX_FORWARDS Forwards
        if starter_position_counts.get('F', 0) > MAX_FORWARDS:
            return (False, f"Must have at most {MAX_FORWARDS} Forwards")
        
        return (True, None)
    
    def get_starters_at_risk_not_playing_in_gameweek(self) -> List[FantraxRosterPlayer]:
        """Get starters that are at risk of not playing in the gameweek.
        
        Returns:
            List[FantraxRosterPlayer]: List of starters that are at risk of not playing in the gameweek (benched, suspended, out, or uncertain gametime decision)
        """
        out = []
        for player in self.starters:
            if player.is_benched_or_suspended_or_out_in_gameweek or player.is_uncertain_gametime_decision_in_gameweek:
                out.append(player)
        return out

    def get_starters_by_position_short_name(self, position_short_name: str) -> List[FantraxRosterPlayer]:
        """Get starters by position short name.
        
        Parameters:
            position_short_name (str): Position short name
            
        Returns:
            List[FantraxRosterPlayer]: List of starters by position short name
        """
        if position_short_name not in [POSITION_KEY_GOALKEEPER, POSITION_KEY_DEFENDER, POSITION_KEY_MIDFIELDER, POSITION_KEY_FORWARD]:
            raise FantraxException(f"Invalid position: {position_short_name}")
        return [player for player in self.starters if player.rostered_position == position_short_name]
    
    def get_reserves_starting_or_expected_to_play(self) -> List[FantraxRosterPlayer]:
        """Get reserves that are starting or expected to play.
        
        Returns:
            List[FantraxRosterPlayer]: List of reserves that are expected to play
        """
        out = []
        for player in self.reserves:
            if (player.is_expected_to_play_in_gameweek or player.is_starting_in_gameweek) and not player.disable_lineup_change:
                out.append(player)
        return out

    def sort_players_by_gameweek_status_and_fantasy_value(self):
        """Sort players by gameweek status and fantasy value for gameweek."""
        logger.info(f"Current list of players prior to running sort operation: {[p.name for p in self]}")
        # Organize roster into groups, each sorted by fantasy value for gameweek:
        # - starting or expected to play
        # - uncertain gametime decision
        # - benched, suspended, or out for this gameweek
        _players_starting_or_expected_to_play:List[FantraxRosterPlayer] = []
        _players_uncertain_gametime_decision:List[FantraxRosterPlayer] = []
        _players_benched_suspended_or_out:List[FantraxRosterPlayer] = []
        for player in self:
            if player.is_expected_to_play_in_gameweek or player.is_starting_in_gameweek:
                _players_starting_or_expected_to_play.append(player)
            elif player.is_uncertain_gametime_decision_in_gameweek:
                _players_uncertain_gametime_decision.append(player)
            elif player.is_benched_or_suspended_or_out_in_gameweek:
                _players_benched_suspended_or_out.append(player)
            else:
                logger.error(f"Player {player.name} has an unaccounted for status. (Icon statuses: {player.icon_statuses})")
                _players_benched_suspended_or_out.append(player)
        _players_starting_or_expected_to_play.sort(key=lambda player: player.fantasy_value.value_for_gameweek, reverse=True)
        _players_uncertain_gametime_decision.sort(key=lambda player: player.fantasy_value.value_for_gameweek, reverse=True)
        _players_benched_suspended_or_out.sort(key=lambda player: player.fantasy_value.value_for_gameweek, reverse=True)

        # Combine the groups into a single list
        logger.debug(f"Players starting or expected to play: {_players_starting_or_expected_to_play}")
        logger.debug(f"Players with uncertain gametime decision: {_players_uncertain_gametime_decision}")
        logger.debug(f"Players benched, suspended, or out: {_players_benched_suspended_or_out}")
        _players = _players_starting_or_expected_to_play + _players_uncertain_gametime_decision + _players_benched_suspended_or_out
        self[:] = _players
        logger.info(f"Sorted list of players by gameweek status and fantasy value: {[p.name for p in self]}")

    def starting_lineup_by_position_short_name(self) -> Dict:
        """Get the starting lineup as a dictionary."""
        out = {}
        for position_short_name in [POSITION_KEY_GOALKEEPER, POSITION_KEY_DEFENDER, POSITION_KEY_MIDFIELDER, POSITION_KEY_FORWARD]:
            out[position_short_name] = [player.name for player in self.get_starters_by_position_short_name(position_short_name)]
        return out
    
    def optimize_lineup(self):
        """Optimize the lineup for the current roster."""

        logger.info(f"Starting optimize_lineup() for current roster")
        
        # Sort the players based on custom logic (gameweek status and fantasy value for gameweek)
        self.sort_players_by_gameweek_status_and_fantasy_value()

        # Reset all players as reserves unless they are locked from lineup changes
        logger.info(f"Resetting all players as reserves unless they are locked from lineup changes")
        for player in self:
            if not player.disable_lineup_change:
                player.change_to_reserve()
        
        # Iterate through players and promote to starter unless they are an invalid substitution
        logger.info(f"Iterating through players to promote to starter unless they are an invalid substitution")
        for player in self:
            if player.disable_lineup_change:
                logger.info(f"Player {player.name} is locked from lineup changes, skipping")
            else:
                vs = self.valid_substitutions([player], disable_min_position_counts_check=True)
                if vs[0]:
                    logger.info(f"Promoting {player.name} to starter")
                    player.change_to_starter()
                else:
                    logger.info(f"Player {player.name} cannot be promoted to starter: {vs[1]}")
        
        logger.info(f"Starting lineup optimized to: ")
        print(json.dumps(self.starting_lineup_by_position_short_name(), indent=2))
