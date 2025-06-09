import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager

# ── Competition URLs ─────────────────────────────────────────────────────────
competition_urls = {
    'football': {
        'ligue1':           'https://www.winamax.fr/paris-sportifs/sports/1/7/4',
        'liga':             'https://www.winamax.fr/paris-sportifs/sports/1/32/36',
        'bundesliga':       'https://www.winamax.fr/paris-sportifs/sports/1/30/42',
        'premier-league':   'https://www.winamax.fr/paris-sportifs/sports/1/1/1',
        'serie-a':          'https://www.winamax.fr/paris-sportifs/sports/1/31/33',
        'primeira':         'https://www.winamax.fr/paris-sportifs/sports/1/44/52',
        'serie-a-brasil':   'https://www.winamax.fr/paris-sportifs/sports/1/13/83',
        'a-league':         'https://www.winamax.fr/paris-sportifs/sports/1/34/144',
        'bundesliga-austria':'https://www.winamax.fr/paris-sportifs/sports/1/17/29',
        'division-1a':      'https://www.winamax.fr/paris-sportifs/sports/1/33/38',
        'super-lig':        'https://www.winamax.fr/paris-sportifs/sports/1/46/62',
    },
    'basketball': {
        'nba':            'https://www.winamax.fr/paris-sportifs/sports/2/800000076/177',
        'euroleague':     'https://www.winamax.fr/paris-sportifs/sports/2/800000034/153',
    }
}

def init_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument('--headless')
        opts.add_argument('--disable-gpu')
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    svc = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=svc, options=opts)

def get_games(url, driver, timeout=10):
    driver.get(url)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR,
            "div.card-wrapper[data-testid^='match-card-']"))
    )
    # scroll to load them all
    prev = -1
    while True:
        cards = driver.find_elements(By.CSS_SELECTOR,
            "div.card-wrapper[data-testid^='match-card-']")
        if len(cards) == prev:
            break
        prev = len(cards)
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight)")
        time.sleep(0.5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    games = []
    for card in soup.select("div.card-wrapper[data-testid^='match-card-']"):
        labs = card.select("div.sc-bCrHVQ.joHNYk")
        if len(labs) < 2:
            continue
        team1, team2 = labs[0].get_text(strip=True), labs[1].get_text(strip=True)

        spans = card.select("div.bet-group-outcome-odd span.sc-eBAZHg.hwSYXh")
        if len(spans) < 2:
            continue

        texts = [s.get_text(strip=True).replace(',', '.') for s in spans]
        try:
            if len(texts) >= 3:
                odd1, odd_draw, odd2 = map(float, texts[:3])
            else:
                # basketball / 2-way markets
                odd1, odd2 = map(float, texts[:2])
                odd_draw = None
        except ValueError:
            continue

        games.append({
            'team1': team1,
            'team2': team2,
            'odd_team1_win': odd1,
            'odd_draw': odd_draw,
            'odd_team2_win': odd2
        })

    return games

def get_winamax_df():
    driver = init_driver()
    rows = []
    try:
        for sport, comps in competition_urls.items():
            for comp_name, url in comps.items():
                try:
                    matches = get_games(url, driver)
                except Exception:
                    matches = []
                for m in matches:
                    m['sport'] = sport
                    m['competition'] = comp_name
                    m['key'] = f"{m['team1']} v {m['team2']}"
                    rows.append(m)
    finally:
        driver.quit()

    df = pd.DataFrame(rows)
    # enforce the exact same column order as your Betclic one:
    cols = [
      'team1','team2','key',
      'odd_team1_win','odd_draw','odd_team2_win',
      'sport','competition'
    ]
    for c in cols:
        if c not in df.columns:
            df[c] = pd.NA

    return df[cols]

if __name__ == '__main__':
    winamax_df = get_winamax_df()
    print(winamax_df)
    winamax_df.to_csv('all_winamax_odds.csv', index=False)