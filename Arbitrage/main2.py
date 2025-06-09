import logging
import json
import pandas as pd
from rapidfuzz import process

# ── Scraper imports ──────────────────────────────────────────────────────────
from Scrapers.betclic_scraper import get_betclic_df
from Scrapers.unibet_scraper import get_unibet_df
from Scrapers.zebet_scraper import get_zebet_df

# ── Configure logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ── 1) Load team_mapping.json (normalized_variant → canonical_raw_name) ─────
try:
    with open("../team_mapping.json", "r", encoding="utf-8") as f:
        TEAM_MAP = json.load(f)
    logging.info(f"Loaded team mapping with {len(TEAM_MAP)} entries")
except FileNotFoundError:
    TEAM_MAP = {}
    logging.warning("⚠️  team_mapping.json not found. Team names will not be canonicalized.")

# ── 2) Helper to canonicalize a normalized string via TEAM_MAP ───────────────
def canonicalize_normalized(n: str) -> str:
    """
    Given a normalized team name (lowercase, no accents/punctuation),
    return the canonical raw name if present in TEAM_MAP; otherwise return n itself.
    """
    if not isinstance(n, str) or n == "":
        return n
    return TEAM_MAP.get(n, n)

# ── 3) Vectorized normalization function (lowercase, strip accents/punctuation) ─
def normalize_series(series: pd.Series) -> pd.Series:
    """
    Vectorized normalization for a pandas Series of raw strings:
      - .str.lower()
      - .str.normalize('NFKD') and remove combining marks
      - regex to drop anything not [0-9a-z ] 
      - .str.strip()
    """
    s = (
        series
        .fillna("")
        .str.lower()
        .str.normalize("NFKD")
        # remove combining diacriticals (U+0300–U+036F)
        .str.replace(r"[\u0300-\u036f]", "", regex=True)
        # keep only a–z, 0–9, and space
        .str.replace(r"[^0-9a-z ]", "", regex=True)
        .str.strip()
    )
    return s

# ── 4) prepare_df: normalize → canonicalize → key → tag by bookmaker ────────
def prepare_df(df: pd.DataFrame, bookmaker: str) -> pd.DataFrame:
    """
    1) Normalizes raw 'team1'/'team2' columns to 'team1_norm'/'team2_norm'.
    2) Canonicalizes those to 'team1_can'/'team2_can' via TEAM_MAP.
    3) Builds an order-insensitive 'key' from the canonical names.
    4) Tags each row with the given bookmaker.
    """
    df = df.copy()

    # 1) Vectorized normalization
    df["team1_norm"] = normalize_series(df["team1"])
    df["team2_norm"] = normalize_series(df["team2"])

    # 2) Canonicalize using the JSON
    df["team1_can"] = df["team1_norm"].map(canonicalize_normalized)
    df["team2_can"] = df["team2_norm"].map(canonicalize_normalized)

    # 3) Build order-insensitive match key
    df["key"] = (
        df[["team1_can", "team2_can"]]
        .apply(lambda row: "_vs_".join(sorted(row)), axis=1)
    )

    # 4) Tag by bookmaker
    df["bookmaker"] = bookmaker
    return df

# ── 5) Detect arbitrage (same as your refactored logic) ───────────────────────
def detect_arbitrage(combined: pd.DataFrame, total_stake: float = 100.0) -> pd.DataFrame:
    """
    1) Melt the combined DataFrame so each row is (key, outcome, odd, bookmaker).
    2) Group by (key, outcome) and pick the row with max odd.
    3) Pivot back to wide form (one row per key, columns for odd_X, odd_draw, odd_2, and bookmaker_X, etc.)
    4) Compute implied probabilities, filter where sum < 1, compute stakes/profit.
    5) Rename columns to 'team1','team2', etc., for final output.
    """
    # 1) melt
    m = combined.melt(
        id_vars=["key", "team1_can", "team2_can", "sport", "competition", "bookmaker"],
        value_vars=["odd_team1_win", "odd_draw", "odd_team2_win"],
        var_name="outcome",
        value_name="odd"
    ).dropna(subset=["odd"])

    # 2) best odd per (key, outcome)
    idx = m.groupby(["key", "outcome"])["odd"].idxmax()
    best_rows = m.loc[idx].reset_index(drop=True)

    # 3) pivot to wide
    best = best_rows.pivot(
        index=["key", "team1_can", "team2_can", "sport", "competition"],
        columns="outcome",
        values=["odd", "bookmaker"]
    )
    best.columns = [f"{stat}_{outcome}" for stat, outcome in best.columns]
    best = best.reset_index()

    # 4) implied probabilities & arbitrage sum
    best["inv_team1"] = 1.0 / best["odd_odd_team1_win"]
    best["inv_draw"]  = 1.0 / best["odd_odd_draw"]
    best["inv_team2"] = 1.0 / best["odd_odd_team2_win"]
    best["arb_sum"]   = best["inv_team1"] + best["inv_draw"] + best["inv_team2"]

    arbs = best[best["arb_sum"] < 1].copy()
    if arbs.empty:
        return arbs

    # 5) compute profit % and stakes
    arbs["profit_pct"]  = (1.0 / arbs["arb_sum"] - 1.0) * 100.0
    arbs["stake_team1"] = total_stake * arbs["inv_team1"] / arbs["arb_sum"]
    arbs["stake_draw"]  = total_stake * arbs["inv_draw"]  / arbs["arb_sum"]
    arbs["stake_team2"] = total_stake * arbs["inv_team2"] / arbs["arb_sum"]

    # rename for final output: team1_can→team1, team2_can→team2, etc.
    arbs = arbs.rename(columns={
        "team1_can": "team1",
        "team2_can": "team2",
        "bookmaker_odd_team1_win": "bookmaker_team1",
        "bookmaker_odd_draw":      "bookmaker_draw",
        "bookmaker_odd_team2_win": "bookmaker_team2"
    })

    columns_out = [
        "team1", "team2", "sport", "competition",
        "profit_pct","bookmaker_team1","bookmaker_draw","bookmaker_team2",
        "stake_team1","stake_draw","stake_team2"
    ]
    return arbs[columns_out]

# ── 6) Main entry point: run scrapers, canonicalize, detect arbitrage ───────
def main(total_stake: float = 100.0):
    frames = []
    for name, fn in {
        "betclic": get_betclic_df,
        "unibet":  get_unibet_df,
        "zebet":   get_zebet_df
    }.items():
        try:
            df_raw = fn()                      # this returns a DataFrame from each scraper
            df_prepared = prepare_df(df_raw, name)
            frames.append(df_prepared)
            logging.info(f"Loaded {len(df_raw)} rows from {name}")
        except Exception as e:
            logging.error(f"Scraper '{name}' failed: {e}")

    if not frames:
        logging.error("No data loaded from any scraper. Exiting.")
        return

    combined = pd.concat(frames, ignore_index=True)
    logging.info(f"Combined odds; total rows: {len(combined)}")

    arbs = detect_arbitrage(combined, total_stake)
    if arbs.empty:
        logging.info("No arbitrage opportunities found.")
    else:
        logging.info(f"Found {len(arbs)} arbitrage opportunities.")
        print(arbs.to_string(index=False))
        arbs.to_csv('arbitrage_opportunities.csv', index=False)
        logging.info("✅ Saved 'arbitrage_opportunities.csv'")

# ── 7) Standard Python entry point ───────────────────────────────────────────
if __name__ == '__main__':
    main()