import os
import json

from fantrax_service.clients.fantraxclient import FantraxClient

client = FantraxClient(os.getenv('LEAGUE_ID'),  os.getenv('TEAM_ID'), cookie_path=os.getenv('FANTRAX_COOKIE_FILE'))

# with open('team_qdsu6ri7mdjmj7y9.json','w') as f:
#     json.dump(client._request("getTeamRosterInfo", teamId=client.team_id),f,indent=4)
#     # json.dump(client._request("getTeamRosterInfo", teamId="qdsu6ri7mdjmj7y9")["tables"],f,indent=4)


# # Get roster info
roster = client.get_roster()
