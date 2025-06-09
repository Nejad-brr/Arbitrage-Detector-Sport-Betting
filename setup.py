from setuptools import setup, find_packages

setup(
    name        = "arbitrage_detector_bookmaker",
    version     = "0.1.0",
    packages    = find_packages(),      # finds Scrapers and Arbitrage
    install_requires = [
        "pandas",
        "selenium",
        "beautifulsoup4",
        "webdriver-manager",
        # …any other libs…
    ],
    entry_points = {
        "console_scripts": [
            "run-arb = Arbitrage.main:main"
        ],
    },
)