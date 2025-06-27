# Automated Sports Betting Arbitrage Detector (Legacy)

## Overview

This Python project automates detection of sports betting arbitrage opportunities by:

1. **Scraping** 1X2 odds from three major bookmakers (Unibet, Zébet, Betclic) using Selenium and BeautifulSoup.
2. **Normalizing & canonicalizing** team names across sources via `unidecode`, regex, and RapidFuzz fuzzy matching.
3. **Detecting** arbitrage by converting odds to implied probabilities, filtering profitable sums (<1), and allocating stakes for a given bankroll.
4. **Exporting** results to CSV and printing a console summary.

It supports both manual execution and fully automated scheduling (cron/launchd), with optional orchestration via Dagster and interactive Streamlit dashboards.

---

## Features

* **Multi‑Site Scraping**

  * Headless Chrome via Selenium WebDriver and BeautifulSoup-driven parsing.
  * Custom scraper modules (`Scrapers/*.py`) returning pandas DataFrames with uniform schema.

* **Data Normalization & Team Mapping**

  * `unidecode` + regex for stripping accents, punctuation, and whitespace.
  * RapidFuzz-based fuzzy clustering to reconcile abbreviations (e.g., “OKC Thunder” vs “Oklahoma City Thunder”).
  * Generates `team_mapping.json` for deterministic name mapping.

* **Arbitrage Detection**

  * Pandas pipeline: merge odds from all sites, compute implied probabilities, detect arbitrages (sum of inverses < 1).
  * Calculates optimal stake allocation and profit percentage for a fixed bankroll.

* **Automation & Orchestration**

  * **Shell script**: `run_arbitrage.sh` wraps the pipeline for manual or cron-based scheduling.
  * **Cron/launchd**: example crontab entry provided for hourly runs.
  * **Dagster**: optional `pipeline.py` defines `ops`, `job`, and `@schedule` for UI monitoring, retries, and hourly execution.

* **Interactive Dashboard (optional)**

  * Streamlit application displaying live arbitrages with filtering, profit thresholds, and CSV download.

---

## Repository Structure

```plaintext
Arbitrage_Detector_Bookmaker/
├── Scrapers/                # Individual site scrapers
│   ├── betclic_scraper.py   # → get_betclic_df()
│   ├── unibet_scraper.py    # → get_unibet_df()
│   └── zebet_scraper.py     # → get_zebet_df()

├── Arbitrage/               # Core arbitrage pipeline
│   └── main2.py             # load, normalize, merge, detect, export

├── build_team_map.py        # fuzzy-cluster unique names → team_mapping.json
├── pipeline.py              # Dagster orchestration definitions
├── run_arbitrage.sh         # shell wrapper for manual/cron execution
├── team_mapping.json        # auto-generated name mapping
├── requirements.txt         # pinned Python dependencies
├── setup.py                 # package metadata (optional)
└── README_legacy.md         # this legacy README with detailed instructions
```

---

## Getting Started

### Prerequisites

* **Python 3.12+**
* **Google Chrome** (for Selenium headless)
* **pip** installed in your environment

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Nejad-brr/Arbitrage-Detector-Sport-Betting.git
   cd Arbitrage-Detector-Sport-Betting
   ```
2. **Create & activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### 1) Manual Pipeline

```bash
# Generate team mapping (first run scrapers to create CSVs):
python build_team_map.py

# Detect arbitrage and export CSV:
python -m Arbitrage.main2
```

Outputs:

* `team_mapping.json` (only if you run `build_team_map.py`)
* `arbitrage_opportunities.csv` (every run of main2)

### 2) Shell Script & Cron

1. **Make it executable**

   ```bash
   chmod +x run_arbitrage.sh
   ```
2. **Add to crontab**

   ```cron
   # Run at minute 0 every hour:
   0 * * * * /full/path/to/Arbitrage_Detector_Bookmaker/run_arbitrage.sh >> /full/path/to/cron_log.txt 2>&1
   ```
3. **Check logs** in `cron_log.txt` and CSV outputs.

### 3) Launchd (macOS)

Create `~/Library/LaunchAgents/com.arbitrage.plist` referencing `run_arbitrage.sh`, then:

```bash
launchctl load ~/Library/LaunchAgents/com.arbitrage.plist
```

---

## Optional Orchestration: Dagster

1. **Set up home directory**

   ```bash
   export DAGSTER_HOME=~/dagster_home
   mkdir -p "$DAGSTER_HOME"
   ```
2. **Run Dagster**

   ```bash
   dagster dev -f pipeline.py
   ```
3. **Open UI** at [http://127.0.0.1:3000](http://127.0.0.1:3000)
4. **Launch** `arbitrage_job` or toggle `hourly_arbitrage_schedule`

---

## Optional Dashboard: Streamlit

```bash
pip install streamlit
streamlit run dashboard.py
```

Use the sidebar to adjust stake, profit thresholds, and refresh live data.

---

## Contributing & Extending

* **Add new bookmakers**: implement additional scraper modules under `Scrapers/`
* **New markets**: over/under, handicaps, 1.5 goal lines, etc.
* **Notifications**: integrate Slack/webhook or email alerts in `run_arbitrage.sh`
* **Historical analysis**: store snapshots in a database for backtesting

---

*Enjoy exploring arbitrage across bookmakers!*




