import requests
from bs4 import BeautifulSoup
from datetime import datetime

# Get today's date in the format used in the table (e.g., 'Mon, Mar 10, 2025')
today = datetime.today().strftime('%a, %b %d, %Y')

# Define the URL for the current month
url = "https://www.basketball-reference.com/leagues/NBA_2025_games-march.html"

# Request the webpage
response = requests.get(url)
response.raise_for_status()  # Ensure we got a successful response

# Parse the HTML
soup = BeautifulSoup(response.text, 'html.parser')

# Find all rows in the table
rows = soup.find_all('tr')

# Extract today's games
games_today = []
for row in rows:
    date_cell = row.find('th', {'data-stat': 'date_game'})
    if date_cell:
        game_date = date_cell.text.strip()
        if game_date == today:
            visitor_team = row.find('td', {'data-stat': 'visitor_team_name'}).text.strip()
            home_team = row.find('td', {'data-stat': 'home_team_name'}).text.strip()
            games_today.append((visitor_team, home_team))

# Output results
if games_today:
    print("Today's NBA Games:")
    for game in games_today:
        print(f"{game[0]} vs. {game[1]}")
else:
    print("No games found for today.")