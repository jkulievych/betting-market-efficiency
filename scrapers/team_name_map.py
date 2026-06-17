# Maps football-data.co.uk team names → Understat team names
TEAM_NAME_MAP = {
    'Man City': 'Manchester City',
    'Man United': 'Manchester United',
    'Newcastle': 'Newcastle United',
    "Nott'm Forest": 'Nottingham Forest',
    'Wolves': 'Wolverhampton Wanderers',
}


def normalise_team_name(name):
    """Convert a football-data team name to its Understat equivalent."""
    return TEAM_NAME_MAP.get(name, name)