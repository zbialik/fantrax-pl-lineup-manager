# FantraxService

A Python service that manages a Fantrax Premier League team's starting lineup.

## Quick Start

### 1. Init venv

```bash
python -m venv
source venv/bin/activate
pip install -e
```

### 2. Set up Authentication

First, you need to extract your browser cookies from Fantrax:

```bash
# Or manually run the bootstrap script
pip install selenium webdriver-manager
python -m utils.bootstrap_cookie --league-id <league_id> --team-id <team_id> -o deploy/fantraxloggedin.cookie
```

This will create a cookie file that contains your authentication information.

### 3. Test Run Service

```bash
# Set environment variables
source deploy/.env # make sure this has 

# Run service
python -m fantrax_service --league-id ${LEAGUE_ID} --team-id ${TEAM_ID} --cookie-path deploy/fantraxloggedin.cookie
```
