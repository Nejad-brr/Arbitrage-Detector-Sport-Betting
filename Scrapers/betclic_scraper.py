import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from webdriver_manager.chrome import ChromeDriverManager
import re

# URLs des compétitions
competition_urls = {
    'football': {
        'ligue1':        'https://www.betclic.fr/football-s1/ligue-1-uber-eats-c4',
        'liga':          'https://www.betclic.fr/football-s1/espagne-liga-primera-c7',
        'bundesliga':    'https://www.betclic.fr/football-s1/allemagne-bundesliga-c5',
        'premier-league':'https://www.betclic.fr/football-s1/angl-premier-league-c3',
        'serie-a':       'https://www.betclic.fr/football-s1/italie-serie-a-c6',
        'primeira':      'https://www.betclic.fr/football-s1/portugal-primeira-liga-c32',
        'serie-a-brasil':'https://www.betclic.fr/football-s1/bresil-serie-a-c187',
        'a-league':      'https://www.betclic.fr/football-s1/australie-a-league-c1874',
        'bundesliga-austria':'https://www.betclic.fr/football-s1/autriche-bundesliga-c35',
        'division-1a':   'https://www.betclic.fr/football-s1/belgique-division-1a-c26',
        'super-lig':     'https://www.betclic.fr/football-s1/turquie-super-lig-c37',
    },
    'basketball': {
        'nba':       'https://www.betclic.fr/basket-ball-s4/nba-c13',
        'euroleague':'https://www.betclic.fr/basket-ball-s4/euroligue-c14',
    }
}


def init_driver(headless: bool = True) -> webdriver.Chrome:
    """
    Initialize ChromeDriver on a random debug port, headless by default.
    """
    options = Options()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--remote-debugging-port=0')  # random port

    # macOS Chrome path
    chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    options.binary_location = chrome_path

    service = Service(ChromeDriverManager().install(), port=0)
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def get_games(sport: str, competition: str, driver: webdriver.Chrome, timeout: int = 10) -> list[dict]:
    """
    Scrape match odds for a given sport/competition and return list of raw dicts.
    """
    url = competition_urls[sport][competition]
    driver.get(url)

    # Wait for page to load at least one match card
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.groupEvents_card'))
        )
    except Exception:
        time.sleep(timeout)

    # Scroll to load all dynamic content
    prev_count = -1
    while True:
        cards = driver.find_elements(By.CSS_SELECTOR, '.groupEvents_card')
        if len(cards) == prev_count:
            break
        prev_count = len(cards)
        driver.execute_script('window.scrollBy(0, document.body.scrollHeight)')
        time.sleep(1)

    html = BeautifulSoup(driver.page_source, 'html.parser')
    games = []

    for card in html.select('.groupEvents_card'):
        labels = card.select('.scoreboard_contestantLabel')
        if len(labels) < 2:
            continue
        team1 = labels[0].get_text(strip=True)
        team2 = labels[1].get_text(strip=True)

        # Attempt CSS-based odds extraction
        odds = []
        odds_btns = card.select('button.btn.is-odd, button.odds-button, span.odds')[:3]
        for btn in odds_btns:
            text = btn.get_text(strip=True).replace(',', '.')
            if re.match(r'^\d+\.?\d*$', text):
                odds.append(float(text))
            else:
                odds.append(None)

        # Fallback: regex-based extraction if odds list is all None or empty
        if len(odds) < 3 or all(o is None for o in odds):
            odds = []
            # find numeric patterns in card text
            nums = re.findall(r'\d+[\.,]\d+', card.get_text())
            for n in nums[:3]:
                odds.append(float(n.replace(',', '.')))
            while len(odds) < 3:
                odds.append(None)

        # Ensure correct length and ordering
        if sport == 'football':
            while len(odds) < 3:
                odds.append(None)
        else:
            # basketball: two outcomes, insert None for draw
            if len(odds) >= 2:
                odds = [odds[0], None, odds[1]]
            else:
                while len(odds) < 2:
                    odds.append(None)
                odds = [odds[0], None, odds[1]]

        games.append({
            'team1': team1,
            'team2': team2,
            'odd_team1_win': odds[0],
            'odd_draw':      odds[1],
            'odd_team2_win': odds[2],
        })

    return games


def get_betclic_df(headless: bool = True) -> pd.DataFrame:
    """
    Launch driver, iterate all competitions, return a unified DataFrame and save CSV.
    """
    driver = init_driver(headless=headless)
    all_rows = []

    try:
        for sport, comps in competition_urls.items():
            for comp in comps:
                print(f"📦 Scraping Betclic → {sport} / {comp}")
                games = get_games(sport, comp, driver)
                for g in games:
                    g['sport'] = sport
                    g['competition'] = comp
                all_rows.extend(games)
    finally:
        driver.quit()

    df = pd.DataFrame(all_rows)
    if df.empty:
        print("⚠️ No data scraped from Betclic.")
    else:
        print("Resulting DataFrame:")
        print(df)
    df.to_csv('betclic_odds.csv', index=False, encoding='utf-8')
    print("✅ Saved betclic_odds.csv")
    return df


if __name__ == '__main__':
    betclic_df = get_betclic_df()