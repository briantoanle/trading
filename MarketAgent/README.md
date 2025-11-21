# MarketAgent: Autonomous Financial Reasoning Engine

MarketAgent is a professional, scalable command-line interface (CLI) tool for autonomous stock market analysis. It leverages a "cynical hedge fund trader" AI persona to provide risk-averse analysis based on technical indicators and recent news sentiment.

The application is built with a modern Python stack, including Typer for the CLI, Rich for beautiful terminal UI, Pydantic for data validation, and a modular architecture for easy extension.

## Codebase Overview

- **app/analysis** – core logic that orchestrates LLM calls and turns market/news context into trade signals.
- **app/services** – integration layer for external data such as market prices (`market.py`) and news search (`news.py`).
- **app/cli** – Typer-powered commands and Rich layouts that render analysis results in the terminal.
- **app/models** – Pydantic schemas that validate and normalize market data, news items, and generated trade signals.
- **app/utils** – shared utilities for logging and retry logic.
- **tests/** – placeholder for automated tests.

## Features

- **AI-Powered Analysis**: Uses an LLM (compatible with NVIDIA NIM) to generate trading signals (Buy/Sell/Hold), confidence scores, and reasoning.
- **Rich Terminal UI**: Presents data in a clean, "cyberpunk" themed dashboard layout.
- **Live Dashboard**: A `dashboard` command provides a live-updating view of a stock watchlist.
- **Data-Driven**: Automatically fetches market data (from yfinance) and news (from DuckDuckGo Search) to form its analysis.
- **Modular Architecture**: Clean separation of concerns makes it easy to add new data sources, indicators, or commands.

## Installation

You can install MarketAgent using either Poetry or pip.

### Poetry (Recommended)

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd MarketAgent
    ```
2.  **Install dependencies:**
    This will create a virtual environment and install all required packages.
    ```bash
    poetry install
    ```

### pip

1.  **Clone the repository and create a virtual environment:**
    ```bash
    git clone <repository-url>
    cd MarketAgent
    python -m venv venv
    source venv/bin/activate
    ```
2.  **Install from `requirements.txt`:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The analysis engine requires an API key to communicate with the LLM.

1.  Create a file named `.env` in the root of the `MarketAgent` directory.
2.  Add your API key to the file as follows:

    ```env
    NVIDIA_API_KEY="YOUR_API_KEY_HERE"
    ```

MarketAgent is configured for NVIDIA NIM out-of-the-box but can be pointed to any OpenAI-compatible API by changing `NVIDIA_API_BASE` in `app/core/config.py`.

## Usage

Run all commands from within the project directory.

**With Poetry:** `poetry run market-agent <command>`
**With pip/venv:** `python -m app.main <command>`

### Analyze a Single Ticker

Run a full analysis on a single stock. The `--mock` flag is used here to show sample output without using the API.

```bash
poetry run market-agent analyze tsla --mock
```

**Output Description:**
The terminal will display a full-screen dashboard.
- The **header** shows "TSLA", its current price, and a "Trend" indicator (e.g., "Up" in green).
- The **main area** is split into two panels:
    - **Narrative (Recent News)** on the left shows a list of recent headlines.
    - **Reality (Technicals)** on the right displays the current RSI and 50-period EMA.
- The **footer** ("Hedge Fund Manager's Take") provides the AI's conclusion: a "Hold" signal in yellow, a confidence score, and a cynical reasoning like "Price is consolidating... waiting for a clearer catalyst."

### View the Live Dashboard

Launch a live-updating dashboard for a predefined watchlist.

```bash
poetry run market-agent dashboard --mock
```

**Output Description:**
The terminal clears and displays a table titled "Cyber-Trader Dashboard". The table has columns for Ticker, Price, Signal, Confidence, RSI, and Reasoning. It populates with data for NVDA, TSLA, SPY, and BTC-USD. The table content automatically refreshes every 5 minutes with new analysis.

---

## Developer Guide: Adding a New Indicator

The modular design makes it easy to add new technical indicators. Here's how to add a Moving Average Convergence Divergence (MACD) indicator:

### Step 1: Update the Market Fetcher

In `app/services/market.py`, simply add the `macd` calculation using the `pandas-ta` library.

```python
# In MarketFetcher.fetch_market_data()
# ... after fetching hist
hist.ta.rsi(length=14, append=True)
hist.ta.ema(length=50, append=True)
hist.ta.macd(fast=12, slow=26, signal=9, append=True) # Add this line
```

### Step 2: Update the Pydantic Model

In `app/models/schemas.py`, add the new fields to the `MarketData` model so the application can validate and use them.

```python
# In the MarketData model
class MarketData(BaseModel):
    # ... other fields
    ema_50: float = Field(..., description="50-period Exponential Moving Average")
    macd_line: float = Field(..., description="MACD Line")
    macd_histogram: float = Field(..., description="MACD Histogram")
    current_price: float
```
*(You would also need to pull these values from the DataFrame in `market.py` when creating the `MarketData` object)*.

### Step 3: Update the AI's Context

In `app/analysis/engine.py`, add the new MACD data to the `_format_context` method. This ensures the LLM receives the new indicator.

```python
# In AnalysisEngine._format_context()
tech_analysis = (
    # ... other lines
    f"50-Period EMA: {market_data.ema_50:.2f}\n"
    f"MACD Line: {market_data.macd_line:.2f}\n" # Add this
    f"MACD Histogram: {market_data.macd_histogram:.2f}\n" # And this
)
```

That's it. The new indicator is now part of the AI's analysis process. You can optionally add it to the Rich display in `app/cli/commands.py` for visualization.

```