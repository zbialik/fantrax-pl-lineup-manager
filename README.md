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
python src/fantrax_service --league-id ${LEAGUE_ID} --team-id ${TEAM_ID} --cookie-path deploy/fantraxloggedin.cookie
```

## Development

### Setting up Development Environment

```bash
# Run the setup script
python setup_dev.py

# Or manually:
poetry install --with dev
poetry run pre-commit install
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=fantraxapi

# Run specific test categories
poetry run pytest -m unit
poetry run pytest -m integration
```

### Code Quality

```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Type checking
poetry run mypy fantraxapi

# Linting
poetry run flake8 fantraxapi
```

## API Reference

### Core Classes

- **`FantraxService`**: Main API client
- **`Team`**: Represents a fantasy team
- **`Player`**: Represents a player
- **`Roster`**: Team roster management
- **`Matchup`**: League matchups
- **`Standings`**: League standings

### Key Methods

#### FantraxService

```python
# Initialize API
api = FantraxService(league_id, session=session)

# Get teams
teams = api.teams
team = api.team(team_id)

# Roster management
roster = api.roster_info(team_id)
api.swap_players(team_id, player1_id, player2_id)

# League information
matchups = api.matchups(scoring_period)
standings = api.standings(scoring_period)
```

#### Roster Management

```python
# Get roster
roster = api.roster_info(team_id)

# Get starters and bench players
starters = roster.get_starters()
bench_players = roster.get_bench_players()

# Find players by name
player = roster.get_player_by_name("Player Name")
```

## Configuration

### Environment Variables

- `LEAGUE_ID`: Your Fantrax league ID
- `TEAM_ID`: Your team ID (optional, defaults to first team)
- `FANTRAX_COOKIE_FILE`: Path to your cookie file

### Cookie File

The cookie file is a pickled list of cookie dictionaries. You can create it using the provided bootstrap script or manually extract cookies from your browser.

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `poetry run pytest`
5. Format your code: `poetry run black .`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This library is not officially affiliated with Fantrax. Use at your own risk and in accordance with Fantrax's terms of service.

## Troubleshooting

### Common Issues

1. **Authentication errors**: Make sure your cookie file is valid and not expired
2. **League access**: Ensure you have access to the specified league
3. **Rate limiting**: The API may have rate limits; implement appropriate delays if needed

### Getting Help

- Check the [Issues](https://github.com/meisnate12/FantraxService/issues) page
- Review the example scripts
- Make sure you're using the latest version

## Changelog

### v1.0.0
- Initial release
- Basic API functionality
- Roster management
- Player substitutions
- Modern Python packaging with Poetry support