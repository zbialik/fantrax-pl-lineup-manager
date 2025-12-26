import sys
from pathlib import Path
import os

from fantrax_service.clients.fantraxclient import FantraxClient
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fantrax Service")
    parser.add_argument("--league-id", type=str, default=os.getenv('LEAGUE_ID'), required=False)
    parser.add_argument("--team-id", type=str, default=os.getenv('TEAM_ID'), required=False)
    parser.add_argument("--cookie-path", type=str, default=os.getenv('FANTRAX_COOKIE_FILE'), required=False)
    args = parser.parse_args()
    service = FantraxClient(args.league_id, args.team_id, cookie_path=args.cookie_path)                    
    # Get roster info
    roster = service.roster_info()
    
    # Count players on the roster
    player_count = sum(1 for row in roster.rows if row.player is not None)
    print(f"Player count: {player_count}")
