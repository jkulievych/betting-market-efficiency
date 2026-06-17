import pandas as pd
import glob
import os
import sys

# Add scrapers to path so we can import team_name_map
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.join(SCRIPT_DIR, '..')
sys.path.append(str(BASE_DIR))

from scrapers.team_name_map import normalise_team_name

# ── LOAD FOOTBALL-DATA ──
fd_files = glob.glob(os.path.join(BASE_DIR, 'data/raw/football_data/*.csv'))
fd_dfs = []
for f in fd_files:
    season = os.path.basename(f).replace('E0_', '').replace('.csv', '')
    df = pd.read_csv(f)
    df['season'] = season
    fd_dfs.append(df)

fd = pd.concat(fd_dfs, ignore_index=True)

# Keep only columns we need
fd = fd[['season', 'Date', 'HomeTeam', 'AwayTeam',
         'FTHG', 'FTAG', 'FTR',
         'B365H', 'B365D', 'B365A',
         'PSH', 'PSD', 'PSA']].copy()

fd = fd.rename(columns={
    'Date': 'date',
    'HomeTeam': 'home_team',
    'AwayTeam': 'away_team',
    'FTHG': 'home_goals',
    'FTAG': 'away_goals',
    'FTR': 'result',
})

# Normalise team names to match Understat
fd['home_team'] = fd['home_team'].map(normalise_team_name)
fd['away_team'] = fd['away_team'].map(normalise_team_name)

# Parse date
fd['date'] = pd.to_datetime(fd['date'], dayfirst=True)

print(f"Football-data: {len(fd)} matches loaded")
print(fd.head())

# ── LOAD UNDERSTAT ──
us_files = glob.glob(os.path.join(BASE_DIR, 'data/raw/understat/*.csv'))
us_dfs = []
for f in us_files:
    season = os.path.basename(f).replace('EPL_', '').replace('.csv', '')
    df = pd.read_csv(f)
    df['us_season'] = season
    us_dfs.append(df)

us = pd.concat(us_dfs, ignore_index=True)
us['date'] = pd.to_datetime(us['date'])
us['date'] = us['date'].dt.normalize()  # strip time component

print(f"Understat: {len(us)} team-match rows loaded")

# ── SPLIT INTO HOME AND AWAY ──
us_home = us[us['h_a'] == 'h'][['date', 'team', 'xG', 'xGA', 'xpts']].copy()
us_home = us_home.rename(columns={
    'team': 'home_team',
    'xG': 'home_xG',
    'xGA': 'away_xG',
    'xpts': 'home_xpts'
})

us_away = us[us['h_a'] == 'a'][['date', 'team', 'xpts']].copy()
us_away = us_away.rename(columns={
    'team': 'away_team',
    'xpts': 'away_xpts'
})

# ── JOIN ──
fd['date'] = fd['date'].dt.normalize()

silver = fd.merge(us_home, on=['date', 'home_team'], how='left')
silver = silver.merge(us_away, on=['date', 'away_team'], how='left')

print(f"Silver table: {len(silver)} rows")
print(f"Matches with missing xG: {silver['home_xG'].isna().sum()}")
print(silver[['date', 'home_team', 'away_team', 'home_xG', 'away_xG', 'home_goals', 'away_goals']].head(10))


# ── DE-MARGIN ODDS ──
# Convert raw odds to implied probabilities, then normalise to remove margin

for bookmaker, h, d, a in [('b365', 'B365H', 'B365D', 'B365A'),
                             ('ps', 'PSH', 'PSD', 'PSA')]:
    # Raw implied probabilities (sum > 1 due to bookmaker margin)
    silver[f'{bookmaker}_raw_h'] = 1 / silver[h]
    silver[f'{bookmaker}_raw_d'] = 1 / silver[d]
    silver[f'{bookmaker}_raw_a'] = 1 / silver[a]

    # Total implied probability (the overround/margin)
    total = silver[f'{bookmaker}_raw_h'] + silver[f'{bookmaker}_raw_d'] + silver[f'{bookmaker}_raw_a']

    # Normalise to get fair probabilities
    silver[f'{bookmaker}_prob_h'] = silver[f'{bookmaker}_raw_h'] / total
    silver[f'{bookmaker}_prob_d'] = silver[f'{bookmaker}_raw_d'] / total
    silver[f'{bookmaker}_prob_a'] = silver[f'{bookmaker}_raw_a'] / total

    # Drop intermediate raw columns
    silver.drop(columns=[f'{bookmaker}_raw_h', f'{bookmaker}_raw_d', f'{bookmaker}_raw_a'], inplace=True)

# Sanity check — each row's probabilities should sum to ~1.0
print("Probability sum check (should be ~1.0):")
print((silver['b365_prob_h'] + silver['b365_prob_d'] + silver['b365_prob_a']).describe())

# ── SAVE ──
output_path = os.path.join(BASE_DIR, 'data/silver/matches.csv')
os.makedirs(os.path.dirname(output_path), exist_ok=True)
silver.to_csv(output_path, index=False)
print(f"\nSilver table saved: {len(silver)} rows → data/silver/matches.csv")
print(silver[['date', 'home_team', 'away_team', 'home_xG', 'away_xG',
              'b365_prob_h', 'b365_prob_d', 'b365_prob_a']].head(5))