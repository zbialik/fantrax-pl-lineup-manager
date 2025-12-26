
from pathlib import Path
import os

from fantrax_service.clients.fantraxclient import FantraxClient

client = FantraxClient(os.getenv('LEAGUE_ID'),  os.getenv('TEAM_ID'), cookie_path=os.getenv('FANTRAX_COOKIE_FILE'))

# Get roster info
roster = client.roster_info()

# Count players on the roster
player_count = sum(1 for row in roster.rows if row.player is not None)
print(f"Player count: {player_count}")
