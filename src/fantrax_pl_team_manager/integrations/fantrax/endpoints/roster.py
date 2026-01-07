import json
from fantrax_pl_team_manager.domain.fantrax_player import FantraxPlayer, FantasyValue
from fantrax_pl_team_manager.domain.fantrax_roster import FantraxRoster
from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.integrations.fantrax.endpoints.players import get_player
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_player_mapper import FantraxPlayerMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.fantrax_premier_league_table_mapper import FantraxPremierLeagueTableMapper
from fantrax_pl_team_manager.integrations.fantrax.mappers.constants import *
from fantrax_pl_team_manager.protocols import HttpClient, Mapper

import logging

logger = logging.getLogger(__name__)

def get_roster(http: HttpClient, roster_mapper: Mapper[FantraxRoster], premier_league_table_mapper: FantraxPremierLeagueTableMapper, player_mapper: FantraxPlayerMapper, league_id:str, team_id: str) -> FantraxRoster:
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
    roster:FantraxRoster = roster_mapper.from_json(obj, league_id, http, premier_league_table_mapper, player_mapper)

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
