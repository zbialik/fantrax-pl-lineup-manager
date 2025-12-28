# Data Layer Architecture

This directory contains the data persistence layer for the Fantrax Service.

## Structure

- `database.py` - Database connection management and session handling
- `models.py` - SQLAlchemy ORM models (PlayerModel, PlayerStatsModel, SyncLogModel)
- `repositories.py` - Repository pattern implementation for data access

## Usage

### Database Initialization

```python
from fantrax_service.data.database import init_db

# Initialize database tables
init_db()
```

### Using Repositories

```python
from fantrax_service.data.repositories import PlayerRepository
from fantrax_service.data.database import session_scope

player_repo = PlayerRepository()

# Get a player
player = player_repo.get_player("player_id")

# Create or update player with Fantrax data
player_repo.create_or_update_player("player_id", fantrax_data_dict)

# Update enriched data
player_repo.update_enriched_data("player_id", performance_score=85.5, transfer_value=10.2)

# Get enriched player data
enriched_data = player_repo.get_enriched_player("player_id")
```

## Configuration

Database connection is configured via the `DATABASE_URL` environment variable:

- SQLite (default): `sqlite:///./fantrax_data.db`
- PostgreSQL: `postgresql://user:pass@localhost/dbname`

See `fantrax_service/config.py` for all configuration options.

