from __future__ import annotations

from ast import Tuple
import json
from typing import TYPE_CHECKING, List
from fantrax_pl_lineup_manager.services.fantrax_player import POSITION_MAP_BY_ID, POSITION_MAP_BY_SHORT_NAME, FantraxPlayer
from fantrax_pl_lineup_manager.exceptions import FantraxException
import logging

if TYPE_CHECKING:
    from fantrax_pl_lineup_manager.clients.fantraxclient import FantraxClient

logger = logging.getLogger(__name__)

class FantraxRoster:
    def __init__(self, client: FantraxClient, team_id: str):
        self.team_id = team_id
        self.client = client
        self.refresh_roster()
    
    def refresh_roster(self):
        """Get the roster for the team.
        
        Returns:
            FantraxRoster: The roster for the team
        """
        data = self.client._request("getTeamRosterInfo", teamId=self.team_id)
        self.players:List[FantraxPlayer] = []
        try:
            for table in data.get("tables", []):
                for row_item in table.get("rows", []):
                    if "scorer" in row_item:
                        player = FantraxPlayer(row_item)
                        self.players.append(player)
        except Exception as e:
            logger.error(f"Error processing roster rows: {e}")
            raise FantraxException(f"Error processing roster rows: {e}")

    def _to_dict(self):
        """Convert all attributes to a dictionary for JSON serialization."""
        return {
            'players': [player._to_dict() for player in self.players]
        }
    
    def __str__(self):
        """Return JSON representation of roster data."""
        return json.dumps(self._to_dict(), indent=2, default=str)
    
    def __repr__(self):
        """Return JSON representation of roster data."""
        return self.__str__()
    
    @property
    def starters(self) -> List[FantraxPlayer]:
        return [player for player in self.players if player.rostered_starter]
    @property
    def reserves(self) -> List[FantraxPlayer]:
        return [player for player in self.players if not player.rostered_starter]

    def get_player(self, player_id:str) -> FantraxPlayer:
        """Get a player by their Fantrax ID."""
        for player in self.players:
            if player.id == player_id:
                return player
        raise FantraxException(f"Player not found: {player_id}")

    def _sync_roster_with_fantrax(self):
        """Sync the roster with Fantrax.
        
        Returns:
            bool: True if roster was successfully synced
        """
        payload_data = {
            "rosterLimitPeriod": 19,
            "fantasyTeamId": self.team_id,
            "daily": False,
            "adminMode": False,
            "confirm": False,
            "applyToFuturePeriods": True,
            "fieldMap": {}
        }

        for player in self.players:
            payload_data["fieldMap"][player.id] = {
                "posId": player.rostered_position_id,
                "stId": player.rostered_status_id
            }
        
        try:
            logger.debug(f"payload_data: {json.dumps(payload_data, indent=2)}")
            self.client._request("confirmOrExecuteTeamRosterChanges", **payload_data)
            logger.info(f"Roster synced with Fantrax")
        except FantraxException as e:
            raise FantraxException(f"Failed to execute lineup changes: {e}")
    
    def valid_substitution(self, player1_id: str, player2_id: str) -> Tuple[bool, str]:
        """Check if a substitution is valid."""
        player1 = self.get_player(player1_id)
        player2 = self.get_player(player2_id)

        if player1.rostered_starter and not player2.rostered_starter:
            starter = player1
            reserve = player2
        elif not player1.rostered_starter and player2.rostered_starter:
            starter = player2
            reserve = player1
        else:
            # REQ: 1 player must be a starter and 1 player must be a reserve
            return (False, f"Player {player1.name} and {player2.name} are both starters or reserves")

        starter_position_counts = {}
        for position_short_name in POSITION_MAP_BY_ID.values():
            starter_position_counts[position_short_name] = len(self.get_starters_by_position_short_name(position_short_name))
        
        starter_position_counts[starter.rostered_position_short_name] -= 1 # starter will be moved to bench
        starter_position_counts[reserve.rostered_position_short_name] += 1 # reserve will be moved to starter

        # REQ: exactly 11 starters 
        if sum(starter_position_counts.values()) != 11:
            return (False, "Must have exactly 11 starters")
        
        # REQ: exactly 1 Goalkeeper
        if starter_position_counts.get('G', 0) != 1:
            return (False, "Must have exactly 1 Goalkeeper")
        
        # REQ: at least 3 Defenders
        if starter_position_counts.get('D', 0) < 3:
            return (False, "Must have at least 3 Defenders")
        
        # REQ: at least 3 Midfielders
        if starter_position_counts.get('M', 0) < 3:
            return (False, "Must have at least 3 Midfielders")
        
        # REQ: at least 1 Forwards
        if starter_position_counts.get('F', 0) < 1:
            return (False, "Must have at least 1 Forward")
        
        # REQ: at most 5 Defender
        if starter_position_counts.get('D', 0) > 5:
            return (False, "Must have at most 5 Defenders")
        
        # REQ: at most 5 Midfielders
        if starter_position_counts.get('M', 0) > 5:
            return (False, "Must have at most 5 Midfielders")
        
        # REQ: at most 3 Forwards
        if starter_position_counts.get('F', 0) > 3:
            return (False, "Must have at most 3 Forwards")
        
        return (True, None)

    def substitute_players(self, player1_id: str, player2_id: str):
        """Substitute two players.
        
        Parameters:
            player1_id (str): First player ID to substitute
            player2_id (str): Second player ID to substitute
        """
        player1 = self.get_player(player1_id)
        player2 = self.get_player(player2_id)

        valid_substitution = self.valid_substitution(player1_id, player2_id)
        if not valid_substitution[0]:
            raise FantraxException(valid_substitution[1])
        
        # Swap their statuses
        logger.info(f"Swapping {player1.name} and {player2.name}")
        player1.swap_starting_status()
        player2.swap_starting_status()
        self._sync_roster_with_fantrax()
    
    def get_starters_at_risk_not_playing_in_gameweek(self) -> List[FantraxPlayer]:
        """Get starters that are at risk of not playing in the gameweek.
        
        Returns:
            List[FantraxPlayer]: List of starters that are at risk of not playing in the gameweek (benched, suspended, out, or uncertain gametime decision)
        """
        out = []
        for player in self.starters:
            if player.is_benched_or_suspended_or_out_in_gameweek or player.is_uncertain_gametime_decision_in_gameweek:
                out.append(player)
        return out

    def get_starters_by_position_short_name(self, position_short_name: str) -> List[FantraxPlayer]:
        """Get starters by position short name.
        
        Parameters:
            position_short_name (str): Position short name
            
        Returns:
            List[FantraxPlayer]: List of starters by position short name
        """
        if position_short_name not in POSITION_MAP_BY_ID.values():
            raise FantraxException(f"Invalid position: {position_short_name}")
        return [player for player in self.starters if player.rostered_position_short_name == position_short_name and player.rostered_starter]
    
    def get_reserves_starting_or_expected_to_play(self) -> List[FantraxPlayer]:
        """Get reserves that are starting or expected to play.
        
        Returns:
            List[FantraxPlayer]: List of reserves that are expected to play
        """
        out = []
        for player in self.reserves:
            if player.is_expected_to_play_in_gameweek or player.is_starting_in_gameweek:
                out.append(player)
        return out

    def get_optimal_substitutions(self) -> List[Tuple[FantraxPlayer, FantraxPlayer]]:
        """Get optimal substitutions based on the current gameweek roster."""
        
        logger.debug(f"Getting starters at risk of not playing in gameweek")
        starters_at_risk_not_playing_in_gameweek = self.get_starters_at_risk_not_playing_in_gameweek()
        logger.info(f"Found {len(starters_at_risk_not_playing_in_gameweek)} starters at risk of not playing in gameweek: {[player.name for player in starters_at_risk_not_playing_in_gameweek]}")

        # Sort starters_at_risk_not_playing_in_gameweek by fantasy value for gameweek (lowest first)
        starters_at_risk_not_playing_in_gameweek.sort(key=lambda player: player.fantasy_value.value_for_gameweek)


        logger.debug(f"Getting reserves starting or expected to play")
        reserves_starting_or_expected_to_play = self.get_reserves_starting_or_expected_to_play()
        logger.info(f"Found {len(reserves_starting_or_expected_to_play)} reserves starting or expected to play: {[player.name for player in reserves_starting_or_expected_to_play]}")

        # Sort reserves_starting_or_expected_to_play by fantasy value for gameweek (highest first)
        reserves_starting_or_expected_to_play.sort(key=lambda player: player.fantasy_value.value_for_gameweek, reverse=True)

        # Pair each starter with the highest value reserve
        substitutions = []
        for starter in starters_at_risk_not_playing_in_gameweek:
            for reserve in reserves_starting_or_expected_to_play:
                _valid_substitution = self.valid_substitution(starter.id, reserve.id)
                if _valid_substitution[0]:
                    logger.info(f"Substitution is valid ({reserve.name} -> {starter.name})! Adding to list of substitutions and removing reserve from future consideration.")
                    substitutions.append((starter, reserve))
                    reserves_starting_or_expected_to_play.remove(reserve) # remove the reserve from the list to avoid pairing it with another starter
                    break # break out of the inner loop to avoid pairing the starter with another reserve
                else:
                    logger.info(f"Substitution invalid ({reserve.name} -> {starter.name}): {_valid_substitution[1]}")
        
        return substitutions