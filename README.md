# Automated Sports Betting Arbitrage Detector

Full‑stack Python project to:

1. Scrape real‑time 1X2 odds from Unibet, Zébet, and Betclic
2. Normalize & canonicalize team names across sources
3. Detect arbitrage (“sure‑bet”) opportunities via implied probability math
4. Orchestrate and schedule the pipeline with Dagster

---

## Features

* **Multi‑site Scraping**: Headless Selenium + BeautifulSoup to extract odds
* **Data Normalization**: `unidecode`, regex, and RapidFuzz fuzzy matching
* **Arbitrage Logic**: Pandas for implied probabilities, filtering, stake allocation
* **Workflow Orchestration**: Dagster `ops` + `job` + `schedule` for hourly runs with retries, logs, and UI monitoring
* **Automation Options**: Manual via `run_arbitrage.sh` or hands‑off via Dagster schedules
* **Interactive Dashboard**: (Optional) Streamlit app for filtering, CSV download, and live view

---

## Repo Layout

```
Arbitrage_Detector_Bookmaker/
├── Scrapers/                # site‑specific scraping modules
│   ├── betclic_scraper.py   # → get_betclic_df()
│   ├── unibet_scraper.py    # → get_unibet_df()
│   └── zebet_scraper.py     # → get_zebet_df()

├── Arbitrage/               # core arbitrage logic
│   └── main2.py             # pipeline: load, normalize, merge, detect, export

├── build_team_map.py        # fuzzy clustering to generate team_mapping.json
├── pipeline.py              # Dagster definitions: ops, job, schedule
├── run_arbitrage.sh         # shell wrapper to run the full pipeline
├── team_mapping.json        # auto‑generated normalized→canonical map
├── requirements.txt         # project dependencies
└── README.md                # this file
```

---

## Quick Start

1. **Clone & Prep**

   ```bash
   git clone https://github.com/Nejad-brr/Arbitrage-Detector-Sport-Betting.git
   cd Arbitrage-Detector-Sport-Betting
   python3 -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Generate Team Map**

   ```bash
   python build_team_map.py
   ```

   This reads `*_odds.csv` and writes `team_mapping.json`.

3. **Run Detection**

   ```bash
   python -m Arbitrage.main2
   ```

   Outputs `arbitrage_opportunities.csv` and console summary.

4. **Shell Script (optional)**

   ```bash
   chmod +x run_arbitrage.sh
   ./run_arbitrage.sh
   ```

5. **Orchestrate with Dagster**

   ```bash
   export DAGSTER_HOME=~/dagster_home
   mkdir -p "$DAGSTER_HOME"
   dagster dev -f pipeline.py
   ```

   * Visit [http://127.0.0.1:3000](http://127.0.0.1:3000)
   * Launch **arbitrage\_job** or enable **hourly\_arbitrage\_schedule**

6. **Interactive UI (Streamlit)**

   ```bash
   pip install streamlit
   streamlit run dashboard.py
   ```

---

## Extending & Scaling

* Add new markets (Over/Under, handicaps)
* Integrate Slack/email/webhook notifications
* Persist historical snapshots for back‑testing

---

