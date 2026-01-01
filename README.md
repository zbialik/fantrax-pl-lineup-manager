# FantraxService

A Python service that manages a Fantrax Premier League team's starting lineup.

## Quick Start

### 1. Init venv

```bash
python -m venv
source venv/bin/activate
pip install -e .
```

### 2. Set up Authentication

First, you need to extract your browser cookies from Fantrax:

```bash
# Or manually run the bootstrap script
pip install selenium webdriver-manager

python -m utils.bootstrap_cookie --league-id o90qdw15mc719reh --team-id jassfpe6mc719rep -o deploy/fantraxloggedin.cookie
```

This will create a cookie file that contains your authentication information.

### 3. Test Run Service

```bash
# Run service
python -m fantrax_pl_team_manager --league-id o90qdw15mc719reh --team-id jassfpe6mc719rep --cookie-path deploy/fantraxloggedin.cookie
```
