from fantrax_pl_team_manager.domain.fantasy_player import FantasyPlayer
from fantrax_pl_team_manager.integrations.fantrax.protocols import HttpClient, Mapper

def get_player(http: HttpClient, mapper: Mapper[FantasyPlayer], league_id: str, player_id: str) -> FantasyPlayer:
    """Get the player profile info for a player.
    
    Parameters:
        player_id (str): Fantrax Player ID

    Returns:
        Dict: Roster info
    """
    payload = {
        'msgs': [
            {
                'method': 'getPlayerProfile', 
                'data': {
                    'playerId': player_id
                }
            }
        ],
    }

    # Required for some reason
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
    }
    obj = http.fantrax_request(payload, params={"leagueId": league_id}, headers=headers)
    return mapper.from_json(obj, player_id)
