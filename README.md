# Automated Sports Betting Arbitrage Detector

## Overview

This project scrapes real‑time 1X2 odds from three bookmakers (Unibet, Zébet, Betclic), normalizes and canonicalizes team names across sources, 
and identifies arbitrage (“sure‑bet”) opportunities by comparing implied probabilities. 
It can run on-demand or be fully automated via cron for hands‑off monitoring.

## Features

* **Multi‑site scraping** using Selenium & BeautifulSoup
* **Data normalization** (unidecode + regex) and **fuzzy matching** (RapidFuzz) to reconcile inconsistent team names
* **Arbitrage detection** with pandas: implied probabilities, filtering profitable sums < 1, stake allocation
* **CSV exports** for odds and arbitrage opportunities
* **Automation** via shell script + cron (or launchd) for hourly runs

## Repository Structure

```
Arbitrage_Detector_Bookmaker/
├── Scrapers/
│   ├── unibet_scraper.py
│   ├── zebet_scraper.py
│   └── betclic_scraper.py
├── Arbitrage/
│   └── main2.py
├── build_team_map.py
├── run_arbitrage.sh
├── team_mapping.json      # auto‑generated mapping of normalized→canonical names
├── requirements.txt
└── README.txt
```

## Requirements

* Python 3.12
* Google Chrome (macOS path: `/Applications/Google Chrome.app/...`)
* pip packages:

  ```
  selenium
  webdriver-manager
  beautifulsoup4
  pandas
  rapidfuzz
  ```

## Installation

1. Clone the repo:

   ```bash
   git clone <URL> Arbitrage_Detector_Bookmaker
   cd Arbitrage_Detector_Bookmaker
   ```
2. Create & activate a virtual environment:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### 1. Generate team mapping

Run sample scrapers once to produce `*_odds.csv` in root, then:

```bash
python build_team_map.py
```

This creates `team_mapping.json` for canonical names.

### 2. Run arbitrage detection manually

```bash
python -m Arbitrage.main2
```

Outputs:

* `arbitrage_opportunities.csv`
* Console log of any found opportunities

### 3. Automate hourly checks

Make the shell script executable:

```bash
chmod +x run_arbitrage.sh
```

Edit your crontab (`crontab -e`) and add:

```
0 * * * * /Users/rayan/Documents/Arbitrage_Detector_Bookmaker/run_arbitrage.sh >> cron_log.txt 2>&1
```

## Shell script: `run_arbitrage.sh`

```bash
#!/usr/bin/env bash
cd /Users/rayan/Documents/Arbitrage_Detector_Bookmaker || exit
source .venv/bin/activate
python -m Arbitrage.main2
```

## Extending the Project

* **Additional markets**: Over/Under, handicaps
* **Notifications**: Slack/webhooks, email alerts
* **Dashboard**: Streamlit for live data visualization
* **Historical analysis**: Store snapshots for back‑testing strategies

## Contact

For questions or contributions, reach out at `alinejadrayan@example.com`.
