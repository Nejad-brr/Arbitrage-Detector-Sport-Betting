from dagster import op, job, schedule, OpExecutionContext

@op
def scrape_op(context: OpExecutionContext) -> bool:
    """
    1) Call each bookmaker scraper to fetch odds and write their CSVs.
    2) Logs row counts for visibility.
    """
    context.log.info("▶ scrape_op: starting scrapers...")
    # Import and run each scraper (each writes its own *_odds.csv)
    from Scrapers.betclic_scraper import get_betclic_df
    from Scrapers.unibet_scraper import get_unibet_df
    from Scrapers.zebet_scraper import get_zebet_df

    df_bet = get_betclic_df()
    df_uni = get_unibet_df()
    df_zeb = get_zebet_df()

    context.log.info(f"✅ betclic scraped {len(df_bet)} rows")
    context.log.info(f"✅ unibet scraped  {len(df_uni)} rows")
    context.log.info(f"✅ zebet scraped   {len(df_zeb)} rows")

    return True

@op
def map_op(context: OpExecutionContext, _: bool) -> bool:
    """
    1) Build or refresh team_mapping.json by reading the *_odds.csv files.
    2) Logs mapping size for confirmation.
    """
    context.log.info("▶ map_op: generating team mapping...")
    from build_team_map import main as build_team_map
    # build_team_map writes team_mapping.json and logs internally
    build_team_map()
    context.log.info("✅ map_op: team_mapping.json updated")
    return True

@op
def detect_op(context: OpExecutionContext, _: bool) -> None:
    """
    1) Run the arbitrage detection logic (uses team_mapping.json).
    2) Writes arbitrage_opportunities.csv and logs summary.
    """
    context.log.info("▶ detect_op: starting arbitrage detection...")
    from Arbitrage.main2 import main as detect_main
    # detect_main() prints and writes CSV; we capture its return if available
    try:
        result = detect_main()
        context.log.info("✅ detect_op: completed arbitrage detection")
    except Exception as e:
        context.log.error(f"❌ detect_op failed: {e}")
        raise

@job
def arbitrage_job():
    # Wire execution order: scrape -> map -> detect
    flag = scrape_op()
    map_op(flag)
    detect_op(flag)

# Hourly schedule: on the hour, every hour
@schedule(cron_schedule="0 * * * *", job=arbitrage_job, execution_timezone="UTC")
def hourly_arbitrage_schedule(_context):
    return {}
