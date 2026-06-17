import requests
import pandas as pd
import time
import os

# At the top of the script, after imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', 'data', 'raw', 'understat')
os.makedirs(OUTPUT_DIR, exist_ok=True)
HEADERS = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'X-Requested-With': 'XMLHttpRequest',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.3 Safari/605.1.15'
}

def scrape_understat_season(league='EPL', season='2021'):
    url = f"https://understat.com/getLeagueData/{league}/{season}"
    headers = {**HEADERS, 'Referer': f'https://understat.com/league/{league}/{season}'}

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    rows = []
    for team_id, team_data in data['teams'].items():
        team_name = team_data['title']
        for match in team_data['history']:
            rows.append({
                'team': team_name,
                'team_id': team_id,
                'date': match['date'],
                'h_a': match['h_a'],
                'xG': match['xG'],
                'xGA': match['xGA'],
                'scored': match['scored'],
                'missed': match['missed'],
                'result': match['result'],
                'xpts': match['xpts']
            })

    return pd.DataFrame(rows)


if __name__ == '__main__':
    for season in ['2021', '2022', '2023', '2024', '2025']:
        print(f"Scraping season {season}...")
        df = scrape_understat_season('EPL', season)
        df.to_csv(os.path.join(OUTPUT_DIR, f'EPL_{season}.csv'), index=False)
        print(f"Saved {len(df)} team-match rows for {season}")
        time.sleep(1)