"""
Arbitrage Detector

Pipeline:
1. Scrape odds from each bookmaker via get_*_df()
2. Normalize team names & generate canonical match_id
3. Merge all odds into a single DataFrame pivoted by site
4. Compute implied probabilities and detect arbitrage
5. Calculate optimal stakes for a given bankroll
6. Display & export results
"""

import pandas as pd
from unidecode import unidecode

from Scrapers.winamax_scraper import get_winamax_df
from Scrapers.betclic_scraper import get_betclic_df
from Scrapers.unibet_scraper import get_unibet_df
from Scrapers.zebet_scraper import get_zebet_df


def normalize_name(name: str) -> str:
    """Lowercase, strip, remove accents and punctuation for matching."""
    if not isinstance(name, str):
        return ''
    name = unidecode(name.lower()).strip()
    # optionally remove punctuation
    return ''.join(ch for ch in name if ch.isalnum() or ch.isspace())


def build_master_df():
    # 1) scrape
    dfs = {
        'winamax': get_winamax_df(),
        'betclic': get_betclic_df(),
        'unibet':  get_unibet_df(),
        'zebet':   get_zebet_df(),
    }

    # 2) prepare each
    records = []
    for site, df in dfs.items():
        df = df.copy()
        # normalize team names
        df['team1_norm'] = df['team1'].map(normalize_name)
        df['team2_norm'] = df['team2'].map(normalize_name)
        # canonical match id
        df['match_id'] = df.apply(
            lambda row: '_vs_'.join(sorted([row['team1_norm'], row['team2_norm']])),
            axis=1
        )
        df['site'] = site
        records.append(df)

    raw = pd.concat(records, ignore_index=True)

    # 3) pivot so each site is columns
    # e.g. odd_team1_win_winamax, odd_draw_unibet, etc.
    pivot = raw.pivot_table(
        index=['match_id', 'team1_norm', 'team2_norm', 'sport', 'competition'],
        columns='site',
        values=['odd_team1_win', 'odd_draw', 'odd_team2_win'],
        aggfunc='first'
    )
    # flatten columns
    pivot.columns = [f"{stat}_{site}" for stat, site in pivot.columns]
    pivot = pivot.reset_index()
    return pivot


def detect_arbitrage(df_master: pd.DataFrame, bankroll: float = 1000) -> pd.DataFrame:
    """
    For each row, compute implied probabilities sum.
    Football: sum = 1/O1 + 1/OD + 1/O2
    Basketball: sum = 1/O1 + 1/O2  (no draw)
    If sum < 1 → arbitrage opportunity.
    Return DataFrame of opportunities with computed stakes & profit.
    """
    opps = []
    for idx, row in df_master.iterrows():
        sport = row['sport']
        # gather odds across sites
        if sport == 'football':
            odds = [(col, row[col]) for col in row.index if 'odd_team1_win_' in col]
            odds += [(col, row[col]) for col in row.index if 'odd_draw_' in col]
            odds += [(col, row[col]) for col in row.index if 'odd_team2_win_' in col]
        else:
            # assume basketball
            odds = [(col, row[col]) for col in row.index if 'odd_team1_win_' in col]
            odds += [(col.replace('odd_team1_win', 'odd_team2_win'), row[col.replace('odd_team1_win', 'odd_team2_win')])]
        # filter out None/NaN
        odds = [(site, o) for site, o in odds if pd.notna(o) and o > 1]
        if sport == 'football' and len(odds) < 3:
            continue
        if sport != 'football' and len(odds) < 2:
            continue

        # pick best odds for each outcome
        if sport == 'football':
            # best home, draw, away
            best_home = max([(s, o) for s, o in odds if 'odd_team1_win' in s], key=lambda x: x[1])
            best_draw = max([(s, o) for s, o in odds if 'odd_draw' in s], key=lambda x: x[1])
            best_away = max([(s, o) for s, o in odds if 'odd_team2_win' in s], key=lambda x: x[1])
            sel = [best_home, best_draw, best_away]
            inv_sum = sum(1/o for _, o in sel)
        else:
            best_home = max([(s, o) for s, o in odds if 'odd_team1_win' in s], key=lambda x: x[1])
            best_away = max([(s, o) for s, o in odds if 'odd_team2_win' in s], key=lambda x: x[1])
            sel = [best_home, best_away]
            inv_sum = sum(1/o for _, o in sel)

        if inv_sum < 1:
            # arbitrage!
            profit_pct = (1 - inv_sum) * 100
            # compute stakes
            stakes = {key: bankroll*(1/o)/inv_sum for key, o in sel}
            opps.append({
                'match_id': row['match_id'],
                'team1': row['team1_norm'],
                'team2': row['team2_norm'],
                'sport': sport,
                'competition': row['competition'],
                'profit_pct': profit_pct,
                'selections': sel,
                'stakes': stakes,
            })

    return pd.DataFrame(opps)


def main():
    master = build_master_df()
    arb = detect_arbitrage(master, bankroll=1000)
    print(f"Found {len(arb)} arbitrage opportunities:")
    print(arb[['match_id','sport','competition','profit_pct']])
    arb.to_csv('arbitrage_opportunities.csv', index=False)
    print("✅ Saved arbitrage_opportunities.csv")


if __name__=='__main__':
    main()