import json
import inspect
import math
from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Set, Optional, Callable, Tuple

from fantrax_pl_team_manager.exceptions import FantraxException
from fantrax_pl_team_manager.domain.constants import *

from fantrax_pl_team_manager.domain.fantasy_roster_player import FantasyRosterPlayer
from fantrax_pl_team_manager.services.fantasy_value_calculator import calculate_fantasy_value_for_gameweek
from fantrax_pl_team_manager.domain.booking_odds import BookingOddsHeadToHead
from typing import List

logger = logging.getLogger(__name__)


class FantasyRoster(List[FantasyRosterPlayer]):
    """A list of FantasyRosterPlayer objects with custom sorting capabilities.
    
    This class extends Python's list to provide a custom sort() method
    for sorting FantasyRosterPlayer objects.
    """
    
    def __init__(self, team_id: str, team_name: str, roster_limit_period: int, iterable: Optional[List[FantasyRosterPlayer]] = []):
        self.team_id = team_id
        self.team_name = team_name
        self.roster_limit_period = roster_limit_period
        super().__init__(iterable)
    
    @property
    def starters(self) -> List[FantasyRosterPlayer]:
        """Get all players currently in starting lineup.
        
        Returns:
            List[FantasyRosterPlayer]: List of starting players
        """
        return [player for player in self if player.rostered_starter]
    
    @property
    def reserves(self) -> List[FantasyRosterPlayer]:
        """Get all players currently on the bench.
        
        Returns:
            List[FantasyRosterPlayer]: List of reserve players
        """
        return [player for player in self if not player.rostered_starter]

    def print_player_names(self) -> None:
        """Print the names of all players in the roster."""
        for player in self:
            print(player.name)
    
    def get_roster_player(self, player_id:str) -> FantasyRosterPlayer:
        """Get a player by their Fantrax ID."""
        for player in self:
            if player.id == player_id:
                return player
        raise FantraxException(f"Player not found: {player_id}")
    
    def sort(self, *, key: Optional[Callable[[FantasyRosterPlayer], Any]] = None, reverse: bool = False) -> None:
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
 
    def valid_substitutions(self, swap_players: List[FantasyRosterPlayer], disable_min_position_counts_check: bool = False) -> Tuple[bool, Optional[str]]:
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
    
    def get_starters_at_risk_not_playing_in_gameweek(self) -> List[FantasyRosterPlayer]:
        """Get starters that are at risk of not playing in the gameweek.
        
        Returns:
            List[FantasyRosterPlayer]: List of starters that are at risk of not playing in the gameweek (benched, suspended, out, or uncertain gametime decision)
        """
        out = []
        for player in self.starters:
            if player.is_benched_or_suspended_or_out_in_gameweek or player.is_uncertain_gametime_decision_in_gameweek:
                out.append(player)
        return out

    def get_starters_by_position_short_name(self, position_short_name: str) -> List[FantasyRosterPlayer]:
        """Get starters by position short name.
        
        Parameters:
            position_short_name (str): Position short name
            
        Returns:
            List[FantasyRosterPlayer]: List of starters by position short name
        """
        if position_short_name not in [POSITION_KEY_GOALKEEPER, POSITION_KEY_DEFENDER, POSITION_KEY_MIDFIELDER, POSITION_KEY_FORWARD]:
            raise FantraxException(f"Invalid position: {position_short_name}")
        return [player for player in self.starters if player.rostered_position == position_short_name]
    
    def get_reserves_starting_or_expected_to_play(self) -> List[FantasyRosterPlayer]:
        """Get reserves that are starting or expected to play.
        
        Returns:
            List[FantasyRosterPlayer]: List of reserves that are expected to play
        """
        out = []
        for player in self.reserves:
            if (player.is_expected_to_play_in_gameweek or player.is_starting_in_gameweek) and not player.disable_lineup_change:
                out.append(player)
        return out

    def sort_players_by_gameweek_status_and_fantasy_value(self):
        """Sort players by gameweek status and fantasy value for gameweek."""
        logger.debug(f"Current list of players prior to running sort operation: {[p.name for p in self]}")
        # Organize roster into groups, each sorted by fantasy value for gameweek:
        # - starting or expected to play
        # - uncertain gametime decision
        # - benched, suspended, or out for this gameweek
        _players_starting_or_expected_to_play:List[FantasyRosterPlayer] = []
        _players_uncertain_gametime_decision:List[FantasyRosterPlayer] = []
        _players_benched_suspended_or_out:List[FantasyRosterPlayer] = []
        for player in self:
            if player.is_uncertain_gametime_decision_in_gameweek:
                _players_uncertain_gametime_decision.append(player)
            elif player.is_benched_or_suspended_or_out_in_gameweek:
                _players_benched_suspended_or_out.append(player)
            elif player.is_expected_to_play_in_gameweek or player.is_starting_in_gameweek:
                _players_starting_or_expected_to_play.append(player)
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
    
    def get_matches_for_this_gameweek(self) -> Set[List[str]]:
        """
        Get the matches for this gameweek.
        
        A match is a list of two teams, the first team is the home team and the second team is the away team.
        
        Returns:
            Set[List[str]]: Set of matches for this gameweek
        """
        out = set[tuple[str, str]]()
        for player in self:
            if not player.disable_lineup_change:
                if player.upcoming_game_home_or_away == 'home':
                    out.add(tuple([player.team_name, player.upcoming_game_opponent]))
                else:
                    out.add(tuple([player.upcoming_game_opponent, player.team_name]))
        return out
