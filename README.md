# FantraxService

A Python service that manages a Fantrax Premier League team's starting lineup.

## Quick Start

### 1. Init venv

```bash
python -m venv
source venv/bin/activate
pip install --no-cache-dir -e .
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
# Init local DB for testing
docker run --name fantrax-postgres \
  -e POSTGRES_USER=fantrax_user \
  -e POSTGRES_PASSWORD=fantrax_password \
  -e POSTGRES_DB=fantrax_db \
  -p 5432:5432 \
  -d postgres:16

# Init the DB
alembic revision --autogenerate -m "Initial migration"


# Set environment variables
set -e
source deploy/.env
set +e

# Run service
python -m fantrax_service --league-id ${LEAGUE_ID} --team-id ${TEAM_ID} --cookie-path deploy/fantraxloggedin.cookie
```
