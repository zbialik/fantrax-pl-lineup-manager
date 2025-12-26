import sys
from pathlib import Path
import os

# Add src directory to path for imports (when running as python src/fantrax_service)
src_dir = Path(__file__).parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from fantrax_service.fantraxservice import FantraxService
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fantrax Service")
    parser.add_argument("--league-id", type=str, default=os.getenv('LEAGUE_ID'), required=False)
    parser.add_argument("--team-id", type=str, default=os.getenv('TEAM_ID'), required=False)
    parser.add_argument("--cookie-path", type=str, default=os.getenv('FANTRAX_COOKIE_FILE'), required=False)
    args = parser.parse_args()
    service = FantraxService(args.league_id, args.team_id, cookie_path=args.cookie_path)                    
    # Get roster info
    roster = service.roster_info()
    
    # Count players on the roster
    player_count = sum(1 for row in roster.rows if row.player is not None)
    print(f"Player count: {player_count}")
