from typing import List
from fantrax_pl_team_manager.domain.player_gameweek_stats import PlayerGameweekStats
from fantrax_pl_team_manager.integrations.fantrax.protocols import HttpClient, Mapper

def get_player_gameweek_stats(http: HttpClient, mapper: Mapper[List[PlayerGameweekStats]], league_id: str, player_id: str) -> List[PlayerGameweekStats]:
    """Get the player gameweek stats for a player.
    
    Parameters:
        player_id (str): Fantrax Player ID

    Returns:
        List[PlayerGameweekStats]: List of player gameweek stats
    """
    payload = {
        'msgs': [
            {
                'method': 'getPlayerProfile', 
                'data': {
                    'playerId': player_id,
                    'tab': "GAME_LOG_FANTASY",
                    'showDidNotPlays': True
                }
            }
        ],
    }

    # Required for some reason
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
    }
    obj = http.fantrax_request(payload, params={"leagueId": league_id}, headers=headers)
    return mapper.from_json(obj)
