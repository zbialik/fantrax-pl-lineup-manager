#!/usr/bin/env python3
"""
Bootstrap script for extracting Fantrax authentication cookies.

This script opens a Chrome browser window, navigates to Fantrax login,
and captures the authentication cookies after login.
"""

import pickle
import time
import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from fantrax_pl_lineup_manager.fantrax_roster import FantraxRoster

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from fantrax_pl_lineup_manager.clients.fantraxclient import FantraxClient
from fantrax_pl_lineup_manager.exceptions import FantraxException, Unauthorized

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError as e:
    print(f"❌ Missing required dependency: {e}")
    print("Please install selenium and webdriver-manager:")
    print("  pip install selenium webdriver-manager")
    sys.exit(1)

def bootstrap_cookies(
    output_path: Optional[str] = None,
    wait_time: int = 30,
    headless: bool = False
) -> str:
    """
    Bootstrap Fantrax authentication cookies.
        
    Returns:
        Path to the saved cookie file
        
    Raises:
        Exception: If cookie extraction fails
    """
    
    print("🚀 Starting Fantrax cookie bootstrap...")
    print("=" * 50)
    
    try:
        # Set up Chrome driver
        service = Service(ChromeDriverManager().install())
        options = Options()
        options.add_argument("--window-size=1920,1600")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # A user-agent is suggested in the wrapper docs
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36"
        )
        
        if headless:
            options.add_argument("--headless")
        
        print("🌐 Opening Chrome browser...")
        with webdriver.Chrome(service=service, options=options) as driver:
            driver.get("https://www.fantrax.com/login")
            print("✅ Browser opened and navigated to Fantrax login")
            print(f"⏳ Please log in to Fantrax. I'll capture cookies in {wait_time} seconds...")
            print("   (Make sure you're logged in before the time expires)")
            
            # Wait for user to log in
            time.sleep(wait_time)
            
            # Check if user is logged in by looking for specific cookies
            cookies = driver.get_cookies()
            
            # Save cookies
            output_file = Path(output_path)
            with open(output_file, "wb") as f:
                pickle.dump(cookies, f)
            
            print(f"✅ Saved {len(cookies)} cookies to {output_file.absolute()}")
            print("🎉 Cookie bootstrap complete!")
            
            return str(output_file.absolute())
            
    except Exception as e:
        print(f"❌ Error during cookie bootstrap: {e}")
        raise


def main():
    """Main entry point for the bootstrap script."""
    
    parser = argparse.ArgumentParser(
        description="Bootstrap Fantrax authentication cookies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  python -m utils.bootstrap_cookie --league-id <LEAGUE_ID> --team-id <TEAM_ID>
  python -m utils.bootstrap_cookie --wait 15 --league-id <LEAGUE_ID> --team-id <TEAM_ID>
  python -m utils.bootstrap_cookie -o deploy/fantraxloggedin.cookie --league-id <LEAGUE_ID> --team-id <TEAM_ID>
        """
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path for cookies (default: deploy/fantraxloggedin.cookie)",
        default="deploy/fantraxloggedin.cookie"
    )
    
    parser.add_argument(
        "--wait", "-w",
        type=int,
        default=30,
        help="Time to wait for login in seconds (default: 30)"
    )
    
    parser.add_argument(
        "--league-id",
        type=str,
        required=True,
        default=os.getenv('LEAGUE_ID'),
        help="Fantrax League ID"
    )
    
    parser.add_argument(
        "--team-id",
        type=str,
        required=True,
        default=os.getenv('TEAM_ID'),
        help="Fantrax Team ID"
    )
    
    args = parser.parse_args()
    
    try:
        cookie_file = bootstrap_cookies(
            output_path=args.output,
            wait_time=args.wait
        )
        
        if cookie_file:
            # Test the cookie file by initializing FantraxClient and checking roster
            print(f"\n🔍 Testing cookie file...")
            try:
                # Get league_id and team_id from args (they're required)
                league_id = args.league_id
                team_id = args.team_id
                
                if not league_id or not team_id:
                    print("⚠️  Skipping cookie test: league-id and team-id are required")
                else:
                    # Initialize FantraxClient with the cookie file
                    client = FantraxClient(league_id, team_id, cookie_path=cookie_file)
                    
                    # Get roster info
                    roster = FantraxRoster(client, team_id)
                    
                    # Count players on the roster
                    player_count = len(roster.players)
                    
                    print(f"✅ Cookie file verified successfully!")
                    print(f"   Team ID: ({roster.team_id})")
                    print(f"   FantraxPlayers found: {player_count}")
                    
                    if player_count > 1:
                        print(f"   ✅ FantraxRoster is valid:")
                        print(f"{roster}")
                    else:
                        print(f"   ⚠️  Warning: Only {player_count} player(s) found on roster")
                        print(f"   This might indicate an authentication issue")
                    
            except Unauthorized as e:
                print(f"❌ Authentication failed: {e}")
                print(f"   The cookie file may be invalid or expired")
            except FantraxException as e:
                print(f"❌ Error testing cookie: {e}")
                print(f"   Please verify your league-id and team-id are correct")
            except Exception as e:
                print(f"❌ Unexpected error testing cookie: {e}")
                print(f"   Cookie file saved, but verification failed")
            
            print(f"\n📝 Usage:")
            print(f"   export FANTRAX_COOKIE_FILE='{cookie_file}'")
            print(f"   python example_substitution.py --cookie-path '{cookie_file}'")
            
    except KeyboardInterrupt:
        print("\n❌ Bootstrap cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Bootstrap failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

