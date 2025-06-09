import time
import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# ── 1) Zebet URLs ─────────────────────────────────────────────────────────────
competition_urls_zebet = {
    'football': {
        "ligue1":        "https://www.zebet.fr/paris-football/france/ligue-1-mcdonalds",
        "premier-league":"https://www.zebet.fr/paris-football/angleterre/premier-league",
        "laliga":        "https://www.zebet.fr/paris-football/espagne/laliga",
        "bundesliga":    "https://www.zebet.fr/paris-football/allemagne/bundesliga-1",
        "serie-a":       "https://www.zebet.fr/paris-football/italie/serie-a",
        "d1-belgique":   "https://www.zebet.fr/paris-football/belgique/d1-belgique",
        "d1-autriche":   "https://www.zebet.fr/paris-football/autriche/d1-autriche",
        "d1-australie":  "https://www.zebet.fr/paris-football/australie/d1-australie",
        "d1-bresil":     "https://www.zebet.fr/paris-football/bresil/d1-bresil",
        "d1-turquie":    "https://www.zebet.fr/paris-football/turquie/d1-turquie",
    },
    'basketball': {
        "nba":           "https://www.zebet.fr/paris-basketball/usa/nba",
    }
}

# ── 2) Headless ChromeDriver setup ────────────────────────────────────────────
def init_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# ── 3) Scrape one Zebet URL ────────────────────────────────────────────────────
def get_zebet_games(url: str, driver: webdriver.Chrome, timeout: int = 10) -> list[dict]:
    driver.get(url)

    # wait for event info to appear (else fall back to blind sleep)
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.psel-event-info__container"))
        )
    except TimeoutException:
        print(f"⚠️ Timeout loading {url}, sleeping {timeout}s…")
        time.sleep(timeout)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    games = []

    for card in soup.select("psel-event-main.psel-event"):
        # — Teams
        names = card.select("div.psel-scoreboard span.psel-opponent__name")
        if len(names) < 2:
            continue
        team1 = names[0].get_text(strip=True)
        team2 = names[1].get_text(strip=True)

        # — Odds
        spans = card.select("td.psel-market__outcome span.psel-outcome__data")
        odds = []
        for s in spans[:3]:
            txt = s.get_text(strip=True).replace(",", ".")
            try:
                odds.append(float(txt))
            except ValueError:
                odds.append(None)
        while len(odds) < 3:
            odds.append(None)

        games.append({
            "team1":         team1,
            "team2":         team2,
            "odd_team1_win": odds[0],
            "odd_draw":      odds[1],
            "odd_team2_win": odds[2],
        })

    return games

# ── 4) Main orchestration & export ────────────────────────────────────────────
def main():
    driver = init_driver(headless=True)
    all_rows = []

    try:
        for sport, comps in competition_urls_zebet.items():
            for comp_name, url in comps.items():
                print(f"Scraping Zebet → {sport} / {comp_name}")
                matches = get_zebet_games(url, driver)

                # tag each row exactly like the others
                for m in matches:
                    m["sport"]       = sport
                    m["competition"] = comp_name
                    m["key"]         = f"{m['team1']} v {m['team2']}"

                all_rows.extend(matches)
    finally:
        driver.quit()

    # — Build a DataFrame with the exact same 8-column layout —
    df = pd.DataFrame(all_rows)
    cols = [
        "team1", "team2", "key",
        "odd_team1_win", "odd_draw", "odd_team2_win",
        "sport", "competition"
    ]
    # add any missing columns (fills with NaN), then reorder
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA
    df = df[cols]

    print(df)
    df.to_csv("zebet_odds.csv", index=False, encoding="utf-8")
    print("✅ Saved zebet_odds.csv")
    return df

get_zebet_df = main

if __name__ == "__main__":
    zebet_df = get_zebet_df()
    print(zebet_df)