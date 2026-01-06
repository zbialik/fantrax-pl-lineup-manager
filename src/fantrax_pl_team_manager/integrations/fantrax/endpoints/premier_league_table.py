from fantrax_pl_team_manager.domain.premier_league_table import PremierLeagueTable
from fantrax_pl_team_manager.protocols import HttpClient, Mapper

def get_premier_league_table(http: HttpClient, mapper: Mapper[PremierLeagueTable]) -> PremierLeagueTable:
    """Get the Premier League standings.
    
    Parameters:
        league_id (str): Fantrax League ID
    
    Returns:
        Dict: Premier League standings
    """
    payload = {
        "msgs": [
            {
                "method": "getStandingsSport",
                "data": {
                    "sportCode": "EPL",
                    "newView": True
                }
            }
        ]
    }
    obj = http.fantrax_request(payload)
    return mapper.from_json(obj)
