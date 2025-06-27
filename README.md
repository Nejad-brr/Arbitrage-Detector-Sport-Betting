Automated Sports Betting Arbitrage Detector

A full-stack Python project to scrape real-time odds from Unibet, Zébet, and Betclic, normalize team names, detect arbitrage opportunities, and orchestrate the end-to-end pipeline with Dagster.

Features

Multi-site scraping: Selenium & BeautifulSoup to extract 1X2 odds.

Data normalization: unidecode + regex + RapidFuzz fuzzy matching for consistent team names.

Arbitrage detection: Pandas-driven implied probability calculations, stake allocation, and CSV export.

Workflow orchestration: Dagster ops, job, and schedule for UI-based monitoring, retry logic, and hourly execution.

Automation: Optionally run on-demand via shell script or hands-off via Dagster schedules.

Optional dashboard: Streamlit integration for interactive filtering, CSV download, and live monitoring.

Repository Structure

Arbitrage_Detector_Bookmaker/
├── Scrapers/                    # Individual scraper modules
│   ├── betclic_scraper.py      
│   ├── unibet_scraper.py       
│   └── zebet_scraper.py        
├── Arbitrage/                   # Core arbitrage logic
│   └── main2.py
├── build_team_map.py            # Generates team_mapping.json
├── pipeline.py                  # Dagster orchestration definition
├── run_arbitrage.sh             # Shell script to run pipeline manually
├── team_mapping.json            # Auto-generated mapping of normalized→canonical names
├── requirements.txt             # Python dependencies
└── README.md                    # This file

Setup

Clone the repo

git clone https://github.com/Nejad-brr/Arbitrage-Detector-Sport-Betting.git
cd Arbitrage-Detector-Sport-Betting

Create & activate virtual environment

python3 -m venv .venv
source .venv/bin/activate

Install dependencies

pip install -r requirements.txt

Usage

1. Generate team mapping

Run each scraper once to produce *_odds.csv in the project root, then:

python build_team_map.py

Creates team_mapping.json for canonical team names.

2. Run arbitrage detection manually

python -m Arbitrage.main2

Outputs arbitrage_opportunities.csv

Prints detected opportunities to console

3. Run via Shell Script

chmod +x run_arbitrage.sh
./run_arbitrage.sh

4. Orchestrate with Dagster

Set DAGSTER_HOME

mkdir -p ~/dagster_home
export DAGSTER_HOME=~/dagster_home

Launch UI & daemon

dagster dev -f pipeline.py

Open http://127.0.0.1:3000 in your browser.

Launch arbitrage_job manually or enable hourly_arbitrage_schedule for automatic runs.

5. Optional: Interactive Dashboard (Streamlit)

Install

pip install streamlit

Run

streamlit run dashboard.py

Use the sidebar to set your stake and profit threshold, then click Refresh.

Git Workflow

Create a feature branch

git checkout -b main2

Stage & commit

git add .
git commit -m "feat: add Dagster pipeline and update README"

Push

git push -u origin main2

Extending the Project

Add support for additional markets (Over/Under, handicaps)

Integrate notifications (Slack, email) on profitable arbitrages

Store historical snapshots for back-testing


