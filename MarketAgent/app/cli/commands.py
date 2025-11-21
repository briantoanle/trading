import time
import typer
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.status import Status
from rich.table import Table
from rich.live import Live
from rich.text import Text
from typing_extensions import Annotated

from app.analysis.engine import AnalysisEngine
from app.models.schemas import TradeSignal, MarketData, NewsItem

# --- Setup ---
app = typer.Typer(name="market-agent", add_completion=False)
console = Console()
engine = AnalysisEngine()

# --- Styles ---
STYLE_THEME = {
    "buy": "bold green",
    "sell": "bold red",
    "hold": "bold yellow",
    "ticker": "cyan",
    "price": "white",
    "trend_up": "green",
    "trend_down": "red",
    "panel": "blue",
    "header": "bold magenta",
    "narrative": "dim cyan",
    "reality": "dim white",
    "reasoning": "white",
    "confidence_high": "bold green blink",
    "confidence_medium": "yellow",
    "confidence_low": "dim",
}

# --- Helper Functions ---
def get_signal_style(signal: str) -> str:
    return STYLE_THEME.get(signal.lower(), "white")

def get_confidence_style(confidence: float) -> str:
    if confidence > 0.85:
        return STYLE_THEME["confidence_high"]
    elif confidence > 0.6:
        return STYLE_THEME["confidence_medium"]
    return STYLE_THEME["confidence_low"]

# --- UI Generation ---
def generate_dashboard_layout(
    signal: TradeSignal, market_data: MarketData, news: list[NewsItem]
) -> Layout:
    """Creates the Rich layout for the analysis command."""
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(ratio=1, name="main"),
        Layout(size=10, name="footer"),
    )
    layout["main"].split_row(Layout(name="left"), Layout(name="right"))

    # Header
    trend_style = STYLE_THEME["trend_up"] if market_data.current_price > market_data.ema_50 else STYLE_THEME["trend_down"]
    header_text = Text(f"{market_data.ticker.upper()}", style=STYLE_THEME["ticker"])
    header_text.append(f" | Price: ${market_data.current_price:.2f} ", style=STYLE_THEME["price"])
    header_text.append(f"| Trend: {'Up' if market_data.current_price > market_data.ema_50 else 'Down'}", style=trend_style)
    layout["header"].update(Panel(header_text, title="Asset", border_style=STYLE_THEME["panel"]))

    # Narrative Panel (Left)
    news_text = Text()
    for item in news:
        news_text.append(f"- {item.headline}\n", style=STYLE_THEME["narrative"])
    layout["left"].update(Panel(news_text, title="Narrative (Recent News)", border_style=STYLE_THEME["panel"]))

    # Reality Panel (Right)
    reality_text = Text()
    reality_text.append(f"RSI: {market_data.rsi:.2f}\n", style=STYLE_THEME["reality"])
    reality_text.append(f"EMA (50): ${market_data.ema_50:.2f}", style=STYLE_THEME["reality"])
    layout["right"].update(Panel(reality_text, title="Reality (Technicals)", border_style=STYLE_THEME["panel"]))
    
    # Footer (AI Signal)
    signal_style = get_signal_style(signal.signal)
    confidence_style = get_confidence_style(signal.confidence)
    
    footer_text = Text(f"Signal: ", style=STYLE_THEME["header"])
    footer_text.append(f"{signal.signal}", style=signal_style)
    footer_text.append(f"\nConfidence: ", style=STYLE_THEME["header"])
    footer_text.append(f"{signal.confidence:.2%}", style=confidence_style)
    footer_text.append(f"\nReasoning: ", style=STYLE_THEME["header"])
    footer_text.append(f"{signal.reasoning}", style=STYLE_THEME["reasoning"])
    if signal.stop_loss:
        footer_text.append(f"\nStop Loss: ${signal.stop_loss:.2f}", style="dim red")

    layout["footer"].update(Panel(footer_text, title="Hedge Fund Manager's Take", border_style=STYLE_THEME["panel"]))
    
    return layout

# --- Typer Commands ---
@app.command()
def analyze(
    ticker: Annotated[str, typer.Argument(help="The stock ticker to analyze (e.g., 'AAPL').")],
    mock: Annotated[bool, typer.Option(help="Use mock data instead of calling the live API.")] = True,
):
    """
    Run a full analysis on a single stock ticker.
    """
    status = Status(f"[bold green]Analyzing {ticker.upper()}...[/bold green]", spinner="dots")
    status.start()
    
    analysis_result = engine.analyze_ticker(ticker, mock=mock)
    status.stop()

    if not analysis_result:
        console.print(f"[bold red]Could not perform analysis for {ticker}.[/bold red]")
        raise typer.Exit(1)
        
    signal, market_data, news = analysis_result
    layout = generate_dashboard_layout(signal, market_data, news)
    console.print(layout)

@app.command()
def dashboard(
    mock: Annotated[bool, typer.Option(help="Use mock data instead of calling the live API.")] = True,
):
    """
    Display a live-updating dashboard of a stock watchlist.
    """
    WATCHLIST = ["NVDA", "TSLA", "SPY", "BTC-USD"]
    
    def generate_table(results: dict) -> Table:
        table = Table(title="Cyber-Trader Dashboard", border_style="blue")
        table.add_column("Ticker", style=STYLE_THEME["ticker"], no_wrap=True)
        table.add_column("Price", justify="right")
        table.add_column("Signal", justify="center")
        table.add_column("Confidence", justify="right")
        table.add_column("RSI", justify="right")
        table.add_column("Reasoning", width=60)
        
        for ticker, data in results.items():
            if data:
                signal, market_data, _ = data
                signal_style = get_signal_style(signal.signal)
                table.add_row(
                    ticker.upper(),
                    f"${market_data.current_price:.2f}",
                    Text(signal.signal, style=signal_style),
                    f"{signal.confidence:.2%}",
                    f"{market_data.rsi:.2f}",
                    signal.reasoning,
                )
            else:
                 table.add_row(ticker.upper(), "[dim]Fetching...[/dim]")

        return table

    results = {ticker: None for ticker in WATCHLIST}

    with Live(generate_table(results), refresh_per_second=4, screen=True) as live:
        while True:
            for ticker in WATCHLIST:
                results[ticker] = engine.analyze_ticker(ticker, mock=mock)
                live.update(generate_table(results))
            
            # Countdown for 5 minutes
            for i in range(300, 0, -1):
                live.update(generate_table(results))
                # You could add a status to the table title here
                time.sleep(1)

