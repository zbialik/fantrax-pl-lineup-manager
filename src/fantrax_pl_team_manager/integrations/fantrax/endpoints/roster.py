import json
from fantrax_pl_team_manager.domain.fantasy_roster import FantasyRoster
from fantrax_pl_team_manager.integrations.fantrax.endpoints.players import get_player
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_player_gameweek_stats_mapper import FantraxPlayerGameweekStatsMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_player_mapper import FantraxPlayerMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.constants import *
from fantrax_pl_team_manager.integrations.fantrax.protocols import HttpClient, Mapper

import logging

logger = logging.getLogger(__name__)

def get_roster(
    http: HttpClient, 
    roster_mapper: Mapper[FantasyRoster], 
    player_mapper: FantraxPlayerMapper, 
    player_gameweek_stats_mapper: FantraxPlayerGameweekStatsMapper, 
    league_id:str, 
    team_id: str,
    period: int = None, # defines gameweek (starts at 1)
    ) -> FantasyRoster:
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
                    'teamId': team_id,
                    'period': str(period) if period else None
                }
            }
        ]
    }
    
    obj = http.fantrax_request(payload, params={"leagueId": league_id})
    roster:FantasyRoster = roster_mapper.from_json(obj, league_id, http, player_mapper, player_gameweek_stats_mapper)

    return roster

def update_roster(http: HttpClient, league_id: str, team_id: str, roster: FantasyRoster) -> None:
    """Sync the roster with Fantrax by sending lineup changes.
    
    Raises:
        FantraxException: If roster sync fails
    """
    # TODO: Should handle via a FantasyRosterPlayerMapper.to_json_update_roster()
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
