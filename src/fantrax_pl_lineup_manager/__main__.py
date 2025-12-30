import sys
import os
import asyncio
import logging

from fantrax_pl_lineup_manager.clients.fantraxclient import FantraxClient
from fantrax_pl_lineup_manager.services.gameweek_manager import GameweekManager

import argparse

if __name__ == "__main__":
    # Configure logging to output to stdout
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    parser = argparse.ArgumentParser(description="Fantrax Service")
    parser.add_argument("--league-id", type=str, default=os.getenv('LEAGUE_ID'), required=False)
    parser.add_argument("--team-id", type=str, default=os.getenv('TEAM_ID'), required=False)
    parser.add_argument("--cookie-path", type=str, default="deploy/fantraxloggedin.cookie", required=False)
    parser.add_argument("--update-lineup-interval", type=int, default=600, required=False)
    args = parser.parse_args()
    
    client = FantraxClient(args.league_id, cookie_path=args.cookie_path)    
    gameweek_manager = GameweekManager(client, args.team_id, args.update_lineup_interval)
    try:
        asyncio.run(gameweek_manager.run())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
