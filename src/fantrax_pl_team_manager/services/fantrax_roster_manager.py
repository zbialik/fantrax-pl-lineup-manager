from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
from typing import TYPE_CHECKING, Dict, List, Tuple
from fantrax_pl_team_manager.services.fantrax_player import POSITION_MAP_BY_ID, POSITION_MAP_BY_SHORT_NAME, FantraxPlayer
from fantrax_pl_team_manager.services.fantrax_roster_player import FantraxRosterPlayer
from fantrax_pl_team_manager.exceptions import FantraxException
import logging

if TYPE_CHECKING:
    from fantrax_pl_team_manager.clients.fantrax_client import FantraxClient

logger = logging.getLogger(__name__)

class FantraxRosterManager:
    def __init__(self, client: FantraxClient, league_id: str, team_id: str, update_lineup_interval: int, run_once: bool = False):
        self.league_id = league_id
        self.team_id = team_id
        self.client = client
        self._running = False
        self.update_lineup_interval = update_lineup_interval
        self.run_once = run_once
        self.team_name = self.get_team_name()

        # The below gets set in refresh_premier_league_standings()
        self.premier_league_team_stats:Dict[str, Any] = None
        self.refresh_premier_league_team_stats()

        # The below gets set in refresh_roster()
        self.players:List[FantraxRosterPlayer] = None
        self.refresh_roster()
    
    async def run(self):
        """Run the roster manager."""
        self._running = True
        logger.info("Fantrax Roster Manager running")
        
        if self.run_once:
            logger.info("Running once, optimizing lineup")
            await asyncio.to_thread(self.optimize_lineup)
            return
        
        while self._running:
            try:
                await asyncio.to_thread(self.optimize_lineup)
            except Exception as e:
                logger.error(f"Error during lineup optimization: {e}", exc_info=True)
            
            await asyncio.sleep(self.update_lineup_interval)

    def get_team_name(self) -> str:
        """Get the name of the team."""
        logger.debug(f"Getting team name for team {self.team_id}")
        data = self.client.get_roster_data(self.league_id, self.team_id)
        fantasyTeams = data.get("fantasyTeams", [])
        for fantasyTeam in fantasyTeams:
            if fantasyTeam.get("id") == self.team_id:
                if fantasyTeam.get("name"):
                    return fantasyTeam["name"]
                else:
                    raise FantraxException(f"'name' not found in team object: {str(fantasyTeam)}")
        raise FantraxException(f"Team id not found in returned list of teams: {str(fantasyTeams)}")
    
    def refresh_premier_league_team_stats(self):
        """Refresh the Premier League standings by team name."""
        data = self.client.get_epl_league_stats()

        team_name_lookup = {team.get("id"): team.get("name") for team in data["miscData"]['teams']}

        _premier_league_team_stats = {}
        for row in data['tables'][0]['rows']:
            team_name = team_name_lookup.get(row['teamId'])
            _premier_league_team_stats[team_name] = {
                'rank': row['rank'],
                'stats': {}
            }
            for i in range(len(row['stats'])):
                stat_name = data['miscData']['headers'][i]['name']
                stat_value = row['stats'][i]
                _premier_league_team_stats[team_name]['stats'][stat_name] = stat_value
        
        self.premier_league_team_stats = _premier_league_team_stats

    def refresh_roster(self):
        """Get the roster for the team.
        
        Returns:
            FantraxRosterManager: The roster for the team
        """
        # Refresh premier league team stats
        self.refresh_premier_league_team_stats()

        logger.info(f"Refreshing roster for team {self.team_name}")
        data = self.client.get_roster_data(self.league_id, self.team_id)
        _players:List[FantraxRosterPlayer] = []
        try:
            for table in data.get("tables", []):
                for row_item in table.get("rows", []):
                    if "scorer" in row_item:
                        player = FantraxRosterPlayer(self.client, self.league_id, row_item, self.premier_league_team_stats)
                        _players.append(player)
            self.players:List[FantraxRosterPlayer] = _players
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
    def starters(self) -> List[FantraxRosterPlayer]:
        return [player for player in self.players if player.rostered_starter]
    @property
    def reserves(self) -> List[FantraxRosterPlayer]:
        return [player for player in self.players if not player.rostered_starter]

    def get_roster_player(self, player_id:str) -> FantraxRosterPlayer:
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
        payload = {
            'msgs': [
                {
                    'method': 'confirmOrExecuteTeamRosterChanges', 
                    'data': {
                        "rosterLimitPeriod": 20,
                        "fantasyTeamId": self.team_id,
                        "daily": False,
                        "adminMode": False,
                        "confirm": False,
                        "applyToFuturePeriods": True,
                        "fieldMap": {}
                    }
                }
            ],
        }

        for player in self.players:
            payload['msgs'][0]['data']['fieldMap'][player.id] = {
                "posId": player.rostered_position_id,
                "stId": player.rostered_status_id
            }
        
        try:
            logger.debug(f"payload_data: {json.dumps(payload, indent=2)}")
            self.client._request(payload, params={"leagueId": self.league_id})
            logger.info(f"Roster synced with Fantrax")
        except FantraxException as e:
            raise FantraxException(f"Failed to execute lineup changes: {e}")
    
    def valid_substitutions(self, swap_players: List[FantraxRosterPlayer], disable_min_position_counts_check: bool = False) -> Tuple[bool, str]:
        """
        Check if a list of substitutions is valid.
        
        Parameters:
            swap_players (List[FantraxRosterPlayer]): List of players to swap
            disable_min_position_counts_check (bool): Whether to disable checking if minimum position counts are met (useful for checking if a player can be promoted to starter)
            
        Returns:
            Tuple[bool, str]: True if the substitutions are valid, False otherwise
        """
        
        starter_position_counts = {}
        for position_short_name in POSITION_MAP_BY_ID.values():
            starter_position_counts[position_short_name] = len(self.get_starters_by_position_short_name(position_short_name))
        
        for player in swap_players:
            if player.disable_lineup_change:
                return (False, f"Player {player.name} is disabled from lineup changes")
            
            if player.rostered_starter:
                starter_position_counts[player.rostered_position_short_name] -= 1 # starter will be moved to bench
            else:
                starter_position_counts[player.rostered_position_short_name] += 1 # reserve will be moved to starter
        
        # REQ: at most 11 starters 
        if sum(starter_position_counts.values()) > 11:
            return (False, "Must have at most 11 starters")

        if not disable_min_position_counts_check:
            # REQ: at least 3 Defenders
            if starter_position_counts.get('D', 0) < 3:
                return (False, "Must have at least 3 Defenders")
            
            # REQ: at least 3 Midfielders
            if starter_position_counts.get('M', 0) < 3:
                return (False, "Must have at least 3 Midfielders")
            
            # REQ: at least 1 Forwards
            if starter_position_counts.get('F', 0) < 1:
                return (False, "Must have at least 1 Forward")
        
        # REQ: at most 1 Goalkeeper
        if starter_position_counts.get('G', 0) > 1:
            return (False, "Must have at most 1 Goalkeeper")
        
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
        if position_short_name not in POSITION_MAP_BY_ID.values():
            raise FantraxException(f"Invalid position: {position_short_name}")
        return [player for player in self.starters if player.rostered_position_short_name == position_short_name]
    
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
        
        # Organize roster into groups, each sorted by fantasy value for gameweek:
        # - starting or expected to play
        # - uncertain gametime decision
        # - benched, suspended, or out for this gameweek
        _players_starting_or_expected_to_play:List[FantraxRosterPlayer] = []
        _players_uncertain_gametime_decision:List[FantraxRosterPlayer] = []
        _players_benched_suspended_or_out:List[FantraxRosterPlayer] = []
        for player in self.players:
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
        _players = _players_starting_or_expected_to_play + _players_uncertain_gametime_decision + _players_benched_suspended_or_out
        self.players = _players

    def starting_lineup_by_position_short_name(self) -> Dict:
        """Get the starting lineup as a dictionary."""
        out = {}
        for position_short_name in POSITION_MAP_BY_ID.values():
            out[position_short_name] = [player.name for player in self.get_starters_by_position_short_name(position_short_name)]
        return out
    
    def optimize_lineup(self):
        """Optimize the lineup for the current roster."""

        logger.info(f"Starting optimize_lineup() for current roster")
        
        # Refresh the roster after updating the lineup
        self.refresh_roster()
        
        # Sort the players based on custom logic (gameweek status and fantasy value for gameweek)
        self.sort_players_by_gameweek_status_and_fantasy_value()

        # Reset all players as reserves unless they are locked from lineup changes
        logger.info(f"Resetting all players as reserves unless they are locked from lineup changes")
        for player in self.players:
            if not player.disable_lineup_change:
                player.change_to_reserve()

        # Iterate through players and promote to starter unless they are an invalid substitution
        logger.info(f"Iterating through players to promote to starter unless they are an invalid substitution")
        for player in self.players:
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

        # Sync the roster with Fantrax
        self._sync_roster_with_fantrax()
