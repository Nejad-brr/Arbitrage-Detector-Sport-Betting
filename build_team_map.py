import json
import re
import unicodedata
import pandas as pd
from rapidfuzz import fuzz

# ── 1) Read the three odds CSVs from the project root ────────────────────────
file_paths = [
    'unibet_odds.csv',
    'zebet_odds.csv',
    'betclic_odds.csv',
]

# Make sure each file actually exists; if not, raise immediately.
missing = [fp for fp in file_paths if not pd.io.common.os.path.exists(fp)]
if missing:
    raise FileNotFoundError(
        f"Could not find these files in the project root: {missing}\n"
        "Make sure you have run each scraper so those CSVs exist."
    )

# Load them all and stack team1/team2
dfs = [pd.read_csv(fp) for fp in file_paths]
all_teams = pd.concat(dfs)[['team1', 'team2']].stack().dropna().unique().tolist()

# ── 2) Define a normalize() that strips accents, punctuation, lowercases ────
def normalize(name: str) -> str:
    """
    Lowercase, decompose accents, strip combining marks,
    drop any character that's not [a-z0-9 ].
    """
    if not isinstance(name, str):
        return ''

    # 1) NFKD‐decompose (so accents become combining marks)
    s = unicodedata.normalize('NFKD', name.lower())

    # 2) remove any combining diacritical marks (U+0300 to U+036F)
    s = re.sub(r'[\u0300-\u036f]', '', s)

    # 3) drop anything not a–z, 0–9, or space
    s = re.sub(r'[^0-9a-z ]', '', s)

    return s.strip()

# Build a dict: normalized_form → raw_original
unique_norm_to_raw = {}
for raw in all_teams:
    norm = normalize(raw)
    if norm and norm not in unique_norm_to_raw:
        unique_norm_to_raw[norm] = raw

teams_norm = list(unique_norm_to_raw.keys())

# ── 3) Cluster with token_set_ratio at a lower cutoff (e.g. 60) ─────────────
mapping = {}
seen = set()
threshold =  sixty = 60  # you can adjust between 55–70 if needed

for i, name in enumerate(teams_norm):
    if name in seen:
        continue

    # group := all other normalized names with token_set_ratio ≥ threshold
    group = [
        other
        for other in teams_norm
        if other not in seen
        and fuzz.token_set_ratio(name, other) >= threshold
    ]

    # pick which “raw original” is canonical: longest raw string (as heuristic)
    raw_variants = [unique_norm_to_raw[n] for n in group]
    canonical_raw = max(raw_variants, key=len)

    for variant_norm in group:
        mapping[variant_norm] = canonical_raw
        seen.add(variant_norm)

# ── 4) Write out to team_mapping.json ────────────────────────────────────────
with open('team_mapping.json', 'w', encoding='utf-8') as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(f"Wrote {len(mapping)} mappings to team_mapping.json")