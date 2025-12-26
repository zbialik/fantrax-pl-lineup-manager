
from pathlib import Path
import os
import json

from fantrax_service.clients.fantraxclient import FantraxClient

client = FantraxClient(os.getenv('LEAGUE_ID'),  os.getenv('TEAM_ID'), cookie_path=os.getenv('FANTRAX_COOKIE_FILE'))

with open('data.json','w') as f:
    json.dump(client._request("getTeamRosterInfo", teamId=client.team_id),f,indent=4)


# # Get roster info
# roster = client.roster_info()
