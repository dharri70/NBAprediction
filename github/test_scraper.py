import time
import pymssql  # Use pymssql for MS SQL Server
import pandas as pd
from bs4 import BeautifulSoup, Comment
import requests
from datetime import datetime

# ✅ MS SQL Server RDS Configuration
DB_HOST = "db-nbadata.croa2u08kkti.us-east-1.rds.amazonaws.com"
DB_NAME = "nba_data"
DB_USER = "admin"
DB_PASSWORD = "db-nbaData"
TABLE_NAME = "nba.game_urls"  # Your table storing URLs

# ✅ Function to fetch 10 pending URLs
def fetch_urls():
    """Fetch 10 URLs from RDS where scraped_status = 0."""
    conn = pymssql.connect(server=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()

    query = f"SELECT TOP 10 game_url FROM {TABLE_NAME} WHERE scraped_status = 0 AND id BETWEEN 20807 AND 20822"
    cursor.execute(query)
    urls = [row[0] for row in cursor.fetchall()]

    conn.close()
    return urls

# ✅ Function to update RDS after scraping
def mark_as_scraped(url):
    """Update RDS table to mark a URL as scraped."""
    conn = pymssql.connect(server=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
    cursor = conn.cursor()

    query = f"UPDATE {TABLE_NAME} SET scraped_status = 1 WHERE game_url = %s"
    cursor.execute(query, (url,))
    conn.commit()
    conn.close()

# ✅ Function to fetch and parse NBA game webpage
def fetch_nba_game(url):
    """Fetch and parse the webpage."""
    response = requests.get(url)
    if response.status_code != 200:
        print(f"⚠️ Failed to retrieve data. HTTP Status: {response.status_code}")
        return None
    return BeautifulSoup(response.text, 'html.parser')

# ✅ Function to extract all NBA game data
def extract_nba_stats(soup, url):
    """Extract Game Metadata, Basic, Advanced, Four Factors, and Points Per Quarter."""

    # ✅ Extract Home & Away Teams
    teams = soup.select("div.scorebox strong a")
    away_team = teams[0].text.strip() if teams else "N/A"
    home_team = teams[1].text.strip() if teams else "N/A"

    # ✅ Extract Game Date
    game_date_element = soup.select_one("div.scorebox_meta div")
    if game_date_element:
        game_date_text = game_date_element.text.strip()
        try:
            game_date_cleaned = game_date_text.split(", ", 1)[-1]
            game_date_obj = datetime.strptime(game_date_cleaned, "%B %d, %Y")
            game_date = game_date_obj.strftime("%Y-%m-%d")
        except ValueError:
            print(f"⚠️ Unexpected date format: '{game_date_text}', defaulting to 'N/A'")
            game_date = "N/A"
            game_date_obj = None
    else:
        print("⚠️ Game Date Not Found")
        game_date = "N/A"
        game_date_obj = None

    # ✅ Determine NBA Season
    if game_date_obj:
        if game_date_obj.month >= 10:
            season = f"{game_date_obj.year}-{game_date_obj.year + 1}"
        else:
            season = f"{game_date_obj.year - 1}-{game_date_obj.year}"
    else:
        season = "N/A"  # Default to 'N/A' if the date is not valid

    # ✅ Extract Basic Team Totals
    team_totals = {}
    total_tables = soup.select("table[id^='box-'][id$='-game-basic']")
    for table in total_tables:
        team_id = table['id'].split('-')[1].upper()
        row = table.select_one("tfoot tr")
        if row:
            team_totals[team_id] = {td["data-stat"]: td.text for td in row.find_all("td")}

    # ✅ Extract Advanced Stats
    advanced_stats = {}
    adv_tables = soup.select("table[id^='box-'][id$='-game-advanced']")
    for table in adv_tables:
        team_id = table['id'].split('-')[1].upper()
        row = table.select_one("tfoot tr")
        if row:
            advanced_stats[team_id] = {td["data-stat"]: td.text for td in row.find_all("td")}

    # ✅ Extract Four Factors (Inside a Comment)
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    hidden_soup = None

    for comment in comments:
        if "four_factors" in comment:
            hidden_soup = BeautifulSoup(comment, "html.parser")
            break

    four_factors = {}
    if hidden_soup:
        ff_table = hidden_soup.find("table", {"id": "four_factors"})
        if ff_table:
            rows = ff_table.select("tbody tr")
            for row in rows:
                team_name_element = row.find("th").find("a")
                team_id = team_name_element.text.strip() if team_name_element else "Unknown"
                stats = {td["data-stat"]: td.text.strip() for td in row.find_all("td")}
                four_factors[team_id] = stats

    # ✅ Extract Points Per Quarter (Inside a Comment)
    points_per_quarter = {}

    for comment in comments:
        if "line_score" in comment:
            hidden_soup = BeautifulSoup(comment, "html.parser")
            break

    line_score_table = None
    if hidden_soup:
        line_score_table = hidden_soup.find("table", {"id": "line_score"})

    if line_score_table:
        rows = line_score_table.find_all("tr")
        for row in rows:
            team_element = row.find("th", {"data-stat": "team"})
            cols = row.find_all("td")
            if team_element and len(cols) >= 5:
                team = team_element.text.strip()
                points_per_quarter[team] = {
                    "Q1": cols[0].text.strip(),
                    "Q2": cols[1].text.strip(),
                    "Q3": cols[2].text.strip(),
                    "Q4": cols[3].text.strip(),
                    "Total": cols[4].text.strip()
                }

    # ✅ Create DataFrame for CSV Output
    game_data = []
    for team_id in team_totals.keys():
        game_data.append({
            "Game URL": url,
            "Game Date": game_date,
            "NBA Season": season,
            "Home Team": home_team,
            "Away Team": away_team,
            "Team": team_id,

            # ✅ Basic Stats
            "FG": team_totals.get(team_id, {}).get("fg", "N/A"),
            "FGA": team_totals.get(team_id, {}).get("fga", "N/A"),
            "FG%": team_totals.get(team_id, {}).get("fg_pct", "N/A"),
            "3P": team_totals.get(team_id, {}).get("fg3", "N/A"),
            "3PA": team_totals.get(team_id, {}).get("fg3a", "N/A"),
            "3P%": team_totals.get(team_id, {}).get("fg3_pct", "N/A"),
            "FT": team_totals.get(team_id, {}).get("ft", "N/A"),
            "FTA": team_totals.get(team_id, {}).get("fta", "N/A"),
            "FT%": team_totals.get(team_id, {}).get("ft_pct", "N/A"),
            "ORB": team_totals.get(team_id, {}).get("orb", "N/A"),
            "DRB": team_totals.get(team_id, {}).get("drb", "N/A"),
            "TRB": team_totals.get(team_id, {}).get("trb", "N/A"),
            "AST": team_totals.get(team_id, {}).get("ast", "N/A"),
            "STL": team_totals.get(team_id, {}).get("stl", "N/A"),
            "BLK": team_totals.get(team_id, {}).get("blk", "N/A"),
            "TOV": team_totals.get(team_id, {}).get("tov", "N/A"),
            "PF": team_totals.get(team_id, {}).get("pf", "N/A"),
            "PTS": team_totals.get(team_id, {}).get("pts", "N/A"),

            # ✅ Advanced Stats
            "TS%": advanced_stats.get(team_id, {}).get("ts_pct", "N/A"),
            "eFG%": advanced_stats.get(team_id, {}).get("efg_pct", "N/A"),
            "3PAr": advanced_stats.get(team_id, {}).get("fg3a_per_fga_pct", "N/A"),
            "FTr": advanced_stats.get(team_id, {}).get("fta_per_fga_pct", "N/A"),
            "ORB%": advanced_stats.get(team_id, {}).get("orb_pct", "N/A"),
            "DRB%": advanced_stats.get(team_id, {}).get("drb_pct", "N/A"),
            "TRB%": advanced_stats.get(team_id, {}).get("trb_pct", "N/A"),
            "AST%": advanced_stats.get(team_id, {}).get("ast_pct", "N/A"),
            "STL%": advanced_stats.get(team_id, {}).get("stl_pct", "N/A"),
            "BLK%": advanced_stats.get(team_id, {}).get("blk_pct", "N/A"),
            "TOV%": advanced_stats.get(team_id, {}).get("tov_pct", "N/A"),
            "USG%": advanced_stats.get(team_id, {}).get("usg_pct", "N/A"),
            "ORtg": advanced_stats.get(team_id, {}).get("off_rtg", "N/A"),
            "DRtg": advanced_stats.get(team_id, {}).get("def_rtg", "N/A"),

            # ✅ Four Factors
            "Pace": four_factors.get(team_id, {}).get("pace", "N/A"),
            "eFG% (FF)": four_factors.get(team_id, {}).get("efg_pct", "N/A"),
            "TOV% (FF)": four_factors.get(team_id, {}).get("tov_pct", "N/A"),
            "ORB% (FF)": four_factors.get(team_id, {}).get("orb_pct", "N/A"),
            "FT/FGA": four_factors.get(team_id, {}).get("ft_rate", "N/A"),
            "ORtg (FF)": four_factors.get(team_id, {}).get("off_rtg", "N/A"),

            # ✅ Points Per Quarter
            "Q1 Points": points_per_quarter.get(team_id, {}).get("Q1", "N/A"),
            "Q2 Points": points_per_quarter.get(team_id, {}).get("Q2", "N/A"),
            "Q3 Points": points_per_quarter.get(team_id, {}).get("Q3", "N/A"),
            "Q4 Points": points_per_quarter.get(team_id, {}).get("Q4", "N/A"),
            "Total Points": points_per_quarter.get(team_id, {}).get("Total", "N/A"),
        })

    return pd.DataFrame(game_data)

# ✅ Start the Scraper
start_time = time.time()
urls = fetch_urls()
for url in urls:
    soup = fetch_nba_game(url)
    if soup:
        df = extract_nba_stats(soup, url)
        df.to_csv(f"/mnt/efs/{url.split('/')[-1]}.csv", index=False)
        mark_as_scraped(url)
    time.sleep(3.5)  # Enforce 3-second delay

# ✅ Log Execution Time
end_time = time.time()
print(f"✅ Scraping Completed in {round(end_time - start_time, 2)} seconds")
