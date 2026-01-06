import json
from fantrax_pl_team_manager.domain.fantrax_player import FantraxPlayer, FantasyValue
from fantrax_pl_team_manager.domain.fantrax_roster import FantraxRoster
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.integrations.fantrax.endpoints.players import get_player
from fantrax_pl_team_manager.integrations.fantrax.endpoints.premier_league_table import get_premier_league_table
from fantrax_pl_team_manager.integrations.fantrax.mappers.constants import *
from fantrax_pl_team_manager.protocols import HttpClient, Mapper

import logging

logger = logging.getLogger(__name__)

def get_roster(http: HttpClient, roster_mapper: Mapper[FantraxRoster], premier_league_table_mapper: Mapper[PremierLeagueTable], player_mapper: Mapper[FantraxPlayer], league_id:str, team_id: str) -> FantraxRoster:
    """Get the roster info for a team.
    
    Parameters:
        team_id (str): Fantrax Team ID
    
    Returns:
        Dict: Roster info
    """
    payload = {
        'msgs': [
            {
                'method': 'getTeamRosterInfo', 
                'data': {
                    'leagueId': league_id, 
                    'teamId': team_id
                }
            }
        ]
    }
    
    obj = http.fantrax_request(payload, params={"leagueId": league_id})
    roster:FantraxRoster = roster_mapper.from_json(obj)
    premier_league_table:PremierLeagueTable = get_premier_league_table(http, premier_league_table_mapper)

    for player in roster:
        _player:FantraxPlayer = get_player(http, player_mapper, league_id, player.id)
        player.name = _player.name
        player.team_name = _player.team_name
        player.icon_statuses = _player.icon_statuses
        player.highlight_stats = _player.highlight_stats
        player.recent_gameweeks_stats = _player.recent_gameweeks_stats
        player.upcoming_game_opponent = _player.upcoming_game_opponent
        player.upcoming_game_home_or_away = _player.upcoming_game_home_or_away
        player.premier_league_table = premier_league_table
        player._update_fantasy_value_for_gameweek()

    return roster

def update_roster(http: HttpClient, league_id: str, team_id: str, roster: FantraxRoster) -> None:
    """Sync the roster with Fantrax by sending lineup changes.
    
    Raises:
        FantraxException: If roster sync fails
    """
    # TODO: Should handle via a FantraxRosterPlayerMapper.to_json_update_roster()
    payload = {
        'msgs': [
            {
                'method': 'confirmOrExecuteTeamRosterChanges', 
                'data': {
                    "rosterLimitPeriod": roster.roster_limit_period,
                    "fantasyTeamId": team_id,
                    "daily": False,
                    "adminMode": False,
                    "confirm": False,
                    "applyToFuturePeriods": True,
                    "fieldMap": {}
                }
            }
        ],
    }
    for player in roster:
        payload['msgs'][0]['data']['fieldMap'][player.id] = {
            "posId": POSITION_MAP_BY_SHORT_NAME.get(player.rostered_position),
            "stId": ROSTER_STATUS_STARTER if player.rostered_starter else ROSTER_STATUS_RESERVE
        }
    
    try:
        http.fantrax_request(payload, params={"leagueId": league_id})
        logger.info(f"Roster synced with Fantrax")
    except Exception as e:
        raise Exception(f"Failed to execute lineup changes: {e}")
