from app.cli.commands import app
from app.utils.resilience import setup_logging

def main():
    """
    Main entry point for the MarketAgent CLI application.
    """
    setup_logging()
    app()

if __name__ == "__main__":
    main()