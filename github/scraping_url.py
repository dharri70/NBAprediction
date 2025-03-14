import requests
import pandas as pd
from bs4 import BeautifulSoup, Comment
from datetime import datetime

# ✅ Replace with a valid NBA box score URL
URL = "https://www.basketball-reference.com/boxscores/202410220BOS.html"

def fetch_nba_game(url):
    """Fetch and parse the webpage."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"⚠️ Failed to retrieve data. HTTP Status: {response.status_code}")
        return None
    return BeautifulSoup(response.text, 'html.parser')

def extract_nba_stats(soup):
    """Extract Game Metadata, Basic, Advanced, and Four Factors stats for both teams."""

    # ✅ Extract Home & Away Teams
    teams = soup.select("div.scorebox strong a")
    away_team = teams[0].text.strip()
    home_team = teams[1].text.strip()

    # ✅ Extract Game Date
    game_date_element = soup.select_one("div.scorebox_meta div")  # Get the first div inside scorebox_meta
    if game_date_element:
        game_date_text = game_date_element.text.strip()  # Example: "7:30 PM, October 22, 2024"
        game_date_cleaned = game_date_text.split(", ", 1)[-1]  # Keep only "October 22, 2024"
        game_date_obj = datetime.strptime(game_date_cleaned, "%B %d, %Y")  # Convert to date format
        game_date = game_date_obj.strftime("%Y-%m-%d")  # Store as YYYY-MM-DD format
    else:
        game_date = "N/A"  # If game date is missing, store "N/A"

    # ✅ Determine NBA Season
    if game_date != "N/A":
        if game_date_obj.month >= 10:
            season = f"{game_date_obj.year}-{game_date_obj.year + 1}"
        else:
            season = f"{game_date_obj.year - 1}-{game_date_obj.year}"
    else:
        season = "N/A"

    # ✅ Debugging Output
    print("Extracted Game Date:", game_date)
    print("Detected NBA Season:", season)

    # ✅ Extract Basic Team Totals
    team_totals = {}
    total_tables = soup.select("table[id^='box-'][id$='-game-basic']")
    for table in total_tables:
        team_id = table['id'].split('-')[1].upper()  # Extract team abbreviation
        row = table.select_one("tfoot tr")
        if row:
            team_totals[team_id] = {td["data-stat"]: td.text for td in row.find_all("td")}

    print("✅ Basic Team Totals Extracted:", team_totals)  # Debugging

    # ✅ Extract Advanced Stats
    advanced_stats = {}
    adv_tables = soup.select("table[id^='box-'][id$='-game-advanced']")
    for table in adv_tables:
        team_id = table['id'].split('-')[1].upper()
        row = table.select_one("tfoot tr")
        if row:
            advanced_stats[team_id] = {td["data-stat"]: td.text for td in row.find_all("td")}

    print("✅ Advanced Stats Extracted:", advanced_stats)  # Debugging

    # ✅ Extract Four Factors
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    hidden_soup = None  # Initialize a variable to hold parsed HTML

    # ✅ Look for "four_factors" inside comments
    for comment in comments:
        if "four_factors" in comment:
            hidden_soup = BeautifulSoup(comment, "html.parser")  # Convert the comment into HTML
            break  # Stop after finding the table

    four_factors = {}
    if hidden_soup:
        ff_table = hidden_soup.find("table", {"id": "four_factors"})  # Extract the table
        if ff_table:
            rows = ff_table.select("tbody tr")  # Get all rows (each team)
            for row in rows:
                # ✅ Extract the team abbreviation from <a> inside <th>
                team_name_element = row.find("th").find("a")
                team_id = team_name_element.text.strip() if team_name_element else "Unknown"

                # ✅ Extract all Four Factors using data-stat attributes
                stats = {td["data-stat"]: td.text.strip() for td in row.find_all("td")}

                # ✅ Store stats under team abbreviation
                four_factors[team_id] = stats

    print("✅ Extracted Four Factors:", four_factors)  # Debugging

    # ✅ Extract Points Per Quarter (Handling Hidden Comment)
    points_per_quarter = {}

    # 🔹 Find all comments (hidden HTML elements)
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))

    # ✅ Search for "line_score" inside hidden comments
    hidden_soup = None
    for comment in comments:
        if "line_score" in comment:
            hidden_soup = BeautifulSoup(comment, "html.parser")  # Convert to HTML
            break  # Stop after finding the table

    # ✅ Extract Quarter Scores from the Hidden Table
    line_score_table = None
    if hidden_soup:
        line_score_table = hidden_soup.find("table", {"id": "line_score"})  # Extract from hidden table

    if line_score_table:
        rows = line_score_table.find_all("tr")  # Get all rows

        for row in rows:
            team_element = row.find("th", {"data-stat": "team"})  # Find team name
            cols = row.find_all("td")

            if team_element and len(cols) >= 5:  # Ensure valid row
                team = team_element.text.strip()
                points_per_quarter[team] = {
                    "Q1": cols[0].text.strip(),
                    "Q2": cols[1].text.strip(),
                    "Q3": cols[2].text.strip(),
                    "Q4": cols[3].text.strip(),
                    "Total": cols[4].text.strip()
                }

    # ✅ Debugging: Print Extracted Data
    print("✅ Points Per Quarter Extracted:", points_per_quarter)

    # ✅ Helper function to safely get stats by `data-stat`
    def get_stat(stats_dict, key):
        return stats_dict.get(key, "N/A")

    # ✅ Combine All Data
    game_data = []
    for team_id in team_totals.keys():
        game_data.append({
            "Game Date": game_date,
            "NBA Season": season,
            "Home Team": home_team,
            "Away Team": away_team,
            "Team": team_id,
            # ✅ Basic Stats
            "FG": get_stat(team_totals.get(team_id, {}), "fg"),
            "FGA": get_stat(team_totals.get(team_id, {}), "fga"),
            "FG%": get_stat(team_totals.get(team_id, {}), "fg_pct"),
            "3P": get_stat(team_totals.get(team_id, {}), "fg3"),
            "3PA": get_stat(team_totals.get(team_id, {}), "fg3a"),
            "3P%": get_stat(team_totals.get(team_id, {}), "fg3_pct"),
            "FT": get_stat(team_totals.get(team_id, {}), "ft"),
            "FTA": get_stat(team_totals.get(team_id, {}), "fta"),
            "FT%": get_stat(team_totals.get(team_id, {}), "ft_pct"),
            "ORB": get_stat(team_totals.get(team_id, {}), "orb"),
            "DRB": get_stat(team_totals.get(team_id, {}), "drb"),
            "TRB": get_stat(team_totals.get(team_id, {}), "trb"),
            "AST": get_stat(team_totals.get(team_id, {}), "ast"),
            "STL": get_stat(team_totals.get(team_id, {}), "stl"),
            "BLK": get_stat(team_totals.get(team_id, {}), "blk"),
            "TOV": get_stat(team_totals.get(team_id, {}), "tov"),
            "PF": get_stat(team_totals.get(team_id, {}), "pf"),
            "PTS": get_stat(team_totals.get(team_id, {}), "pts"),
            # ✅ Four Factors
            "Pace": get_stat(four_factors.get(team_id, {}), "pace"),
            "eFG% (FF)": get_stat(four_factors.get(team_id, {}), "efg_pct"),
            "TOV% (FF)": get_stat(four_factors.get(team_id, {}), "tov_pct"),
            "ORB% (FF)": get_stat(four_factors.get(team_id, {}), "orb_pct"),
            "FT/FGA": get_stat(four_factors.get(team_id, {}), "ft_rate"),
            "ORtg (FF)": get_stat(four_factors.get(team_id, {}), "off_rtg"),
            # ✅ Points Per Quarter
            "Q1 Points": points_per_quarter.get(team_id, {}).get("Q1", "N/A"),
            "Q2 Points": points_per_quarter.get(team_id, {}).get("Q2", "N/A"),
            "Q3 Points": points_per_quarter.get(team_id, {}).get("Q3", "N/A"),
            "Q4 Points": points_per_quarter.get(team_id, {}).get("Q4", "N/A"),
            "Total Points": points_per_quarter.get(team_id, {}).get("Total", "N/A"),
        })

    return pd.DataFrame(game_data)

# ✅ Fetch and parse the game page
soup = fetch_nba_game(URL)
if soup:
    df = extract_nba_stats(soup)
    print("✅ Extracted NBA Game Data:")
    print(df)

    # ✅ Save to CSV
    df.to_csv("nba_game_data.csv", index=False)
    print("✅ Data saved to nba_game_data.csv")