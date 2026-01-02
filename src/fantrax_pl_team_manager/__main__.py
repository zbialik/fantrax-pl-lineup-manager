import sys
import os
import asyncio
import logging

from fantrax_pl_team_manager.clients.fantrax_client import FantraxClient
from fantrax_pl_team_manager.services.fantrax_roster_manager import FantraxRosterManager

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
    parser.add_argument("--run-once", action="store_true", default=False, required=False)
    args = parser.parse_args()
    
    client = FantraxClient(cookie_path=args.cookie_path)
    roster_manager = FantraxRosterManager(client, args.league_id, args.team_id, args.update_lineup_interval, run_once=args.run_once)
    try:
        asyncio.run(roster_manager.run())
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
