import time
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

# URLs for each competition on Unibet
competition_urls_unibet = {
    'football': {
        'ligue1':             'https://www.unibet.fr/sport/football/france/ligue-1-mcdonalds?filter=Top+Paris&subFilter=R%C3%A9sultat+du+match',
        'premier-league':     'https://www.unibet.fr/sport/football/angleterre/premier-league?filter=Top+Paris&subFilter=R%C3%A9ultat+du+match',
        'serie-a':            'https://www.unibet.fr/sport/football/italie/serie-a?filter=Top+Paris&subFilter=Résultat+du+match',
        'laliga':             'https://www.unibet.fr/sport/football/espagne/laliga?filter=Top+Paris&subFilter=Résultat+du+match',
        'bundesliga':         'https://www.unibet.fr/sport/football/allemagne/bundesliga',
        'serie-a-brasil':     'https://www.unibet.fr/sport/football/bresil/serie-a?filter=Top+Paris&subFilter=Résultat+du+match',
        'super-lig':          'https://www.unibet.fr/sport/football/turquie/super-lig?filter=Top+Paris&subFilter=Résultat+du+match',
        'bundesliga-austria': 'https://www.unibet.fr/sport/football/autriche/bundesliga?filter=Top+Paris&subFilter=Résultat+du+match',
        'pro-league':         'https://www.unibet.fr/sport/football/belgique/pro-league?filter=Top+Paris&subFilter=Résultat+du+match',
        'a-league':           'https://www.unibet.fr/sport/football/australie/a-league',
    },
    'basketball': {
        'nba': 'https://www.unibet.fr/sport/basketball/etats-unis/nba?filter=Résultat&subFilter=Vainqueur+(Prolongations+incluses)',
    }
}


def get_unibet_games(url: str, driver: webdriver.Chrome, timeout: int = 10) -> list[dict]:
    """
    Scrolls through the given Unibet page and returns a list of match dicts with raw odds.
    """
    driver.get(url)

    # Wait for event cards to load
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "section[class^='eventcard--']"))
        )
    except TimeoutException:
        time.sleep(timeout)

    # Scroll to load all cards
    prev_count = -1
    while True:
        cards = driver.find_elements(By.CSS_SELECTOR, "section[class^='eventcard--']")
        if len(cards) == prev_count:
            break
        prev_count = len(cards)
        driver.execute_script("window.scrollBy(0, document.body.scrollHeight)")
        time.sleep(1)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    games = []

    for card in soup.select("section[class^='eventcard--']"):
        # Extract team names
        h_home = card.select_one('.home-team h2')
        h_away = card.select_one('.away-team h2')
        if h_home and h_away:
            team1 = h_home.get_text(strip=True)
            team2 = h_away.get_text(strip=True)
        else:
            h2s = card.select('div.row-container-desktop h2')
            if len(h2s) < 2:
                continue
            team1, team2 = h2s[0].get_text(strip=True), h2s[1].get_text(strip=True)

        # Extract odds
        oddboxes = card.select('section.oddbox')
        def parse_val(sec):
            sp = sec.select_one('.oddbox-value span')
            if not sp:
                return None
            try:
                return float(sp.get_text(strip=True).replace(',', '.'))
            except ValueError:
                return None

        if len(oddboxes) >= 3:
            o1, o2, o3 = (parse_val(sec) for sec in oddboxes[:3])
            odd1, odd_draw, odd2 = o1, o2, o3
        elif len(oddboxes) == 2:
            o1, o2 = (parse_val(sec) for sec in oddboxes[:2])
            odd1, odd_draw, odd2 = o1, None, o2
        else:
            continue

        games.append({
            'team1': team1,
            'team2': team2,
            'odd_team1_win': odd1,
            'odd_draw': odd_draw,
            'odd_team2_win': odd2,
        })

    return games


def get_unibet_df(headless: bool = True, timeout: int = 10) -> pd.DataFrame:
    """
    Launches headless Chrome, scrapes all configured competitions,
    and returns a pandas DataFrame of odds.
    """
    # Configure Chrome options
    options = Options()
    # Use standard headless mode for compatibility
    if headless:
        options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    # Enable remote debugging on a random port
    options.add_argument('--remote-debugging-port=0')

    # Install ChromeDriver on a random port to avoid collisions
    service = Service(ChromeDriverManager().install(), port=0)
    driver = webdriver.Chrome(service=service, options=options)

    try:
        all_rows = []
        for sport, comps in competition_urls_unibet.items():
            for comp_name, url in comps.items():
                print(f"Scraping Unibet → {sport} / {comp_name}", end=" ")
                matches = get_unibet_games(url, driver, timeout=timeout)
                print(f"found {len(matches)} matches")

                for m in matches:
                    m['sport'] = sport
                    m['competition'] = comp_name
                    m['key'] = f"{m['team1']} v {m['team2']}"
                all_rows.extend(matches)

        # Build DataFrame and ensure column consistency
        df = pd.DataFrame(all_rows)
        cols = [
            'team1', 'team2', 'key',
            'odd_team1_win', 'odd_draw', 'odd_team2_win',
            'sport', 'competition'
        ]
        for c in cols:
            if c not in df.columns:
                df[c] = pd.NA
        return df[cols]
    finally:
        driver.quit()


if __name__ == '__main__':
    df = get_unibet_df()
    df.to_csv('unibet_odds.csv', index=False, encoding='utf-8')
    print("✅ Saved unibet_odds.csv")
