from typing import Any, Dict, Mapping, List
from fantrax_pl_team_manager.domain.fantrax_roster import FantraxRoster
from fantrax_pl_team_manager.domain.fantrax_roster_player import FantraxRosterPlayer
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.exceptions import FantraxException
from fantrax_pl_team_manager.integrations.fantrax.endpoints.players import get_player
from fantrax_pl_team_manager.integrations.fantrax.endpoints.premier_league_table import get_premier_league_table
from fantrax_pl_team_manager.integrations.fantrax.mappers.constants import *
from fantrax_pl_team_manager.protocols import HttpClient, Mapper
from fantrax_pl_team_manager.domain.fantrax_player import FantraxPlayer
import logging


logger = logging.getLogger(__name__)

class FantraxRosterMapper:
    def from_json(self, dto: Mapping[str, Any], league_id: str, http: HttpClient, premier_league_table_mapper: Mapper[PremierLeagueTable], player_mapper: Mapper[FantraxPlayer]) -> FantraxRoster:

        def _acquire_player_info(player:FantraxPlayer, league_id: str, http: HttpClient, player_mapper: Mapper[FantraxPlayer]) -> None:
            """Retrieve player information from Fantrax."""
            _player:FantraxPlayer = get_player(http, player_mapper, league_id, player.id)
            player.name = _player.name
            player.team_name = _player.team_name
            player.icon_statuses = _player.icon_statuses
            player.highlight_stats = _player.highlight_stats
            player.gameweek_stats = _player.gameweek_stats
            player.upcoming_game_opponent = _player.upcoming_game_opponent
            player.upcoming_game_home_or_away = _player.upcoming_game_home_or_away
            player.premier_league_table = premier_league_table
            player._update_fantasy_value_for_gameweek()
        data = dto["responses"][0]["data"]
        team_id = data.get("myTeamIds")[0]
        logger.debug(f"Mapped Team ID: {str(team_id)}")
        team_name = self._get_team_name(data, team_id)
        roster_limit_period = data.get("displayedSelections", {}).get("displayedPeriod")
        if not roster_limit_period:
            raise FantraxException(f"Roster limit period not found in data: {str(data)}")
        else:
            logger.debug(f"Mapped roster limit period: {roster_limit_period}")
        roster:FantraxRoster = FantraxRoster(team_id=team_id, team_name=team_name, roster_limit_period=roster_limit_period)
        premier_league_table:PremierLeagueTable = get_premier_league_table(http, premier_league_table_mapper)
        
        try:
            for table in data.get("tables", []):
                for row_item in table.get("rows", []):
                    logger.debug(f"Row item for rostered player: {str(row_item)}")
                    if row_item['statusId'] == ROSTER_STATUS_STARTER:
                        rostered_starter = True
                    elif row_item['statusId'] == ROSTER_STATUS_RESERVE:
                        rostered_starter = False
                    else:
                        raise FantraxException(f"Invalid roster status id: {row_item['statusId']} (determines if player is a starter or reserve)")
                    if "scorer" in row_item:
                        player = FantraxRosterPlayer(
                            id=row_item['scorer']['scorerId'], 
                            rostered_starter = rostered_starter, 
                            rostered_position = POSITION_MAP_BY_ID.get(row_item['posId']), 
                            disable_lineup_change = row_item['scorer'].get("disableLineupChange",False)
                        )
                        _acquire_player_info(player, league_id, http, player_mapper)
                        roster.append(player)
        except Exception as e:
            logger.error(f"Error processing roster rows: {e}")
            raise FantraxException(f"Error processing roster rows: {e}")
        
        return roster
    
    def _get_team_name(self, data: Dict[str, Any], team_id: str) -> str:
        """Get the name of the team."""
        logger.debug(f"Getting team name for team {team_id}")
        fantasyTeams = data.get("fantasyTeams", [])
        for fantasyTeam in fantasyTeams:
            if fantasyTeam.get("id") == team_id:
                if fantasyTeam.get("name"):
                    return fantasyTeam["name"]
                else:
                    raise FantraxException(f"'name' not found in team object: {str(fantasyTeam)}")
        raise FantraxException(f"Team id not found in returned list of teams: {str(fantasyTeams)}")
