import os
from typing import Optional

import requests
from loguru import logger

from app.models.schemas import TradeSignal


class TelegramNotifier:
    """Sends trading alerts to a Telegram chat using a bot token and chat ID."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("CHAT_ID")

    def _format_message(self, signal: TradeSignal, ticker: str) -> str:
        emoji_map = {
            "Buy": "🚀",
            "Sell": "🔻",
            "Hold": "🤝",
        }
        emoji = emoji_map.get(signal.signal, "📈")
        confidence_pct = signal.confidence * 100
        stop_loss_text = (
            f" | Stop Loss: ${signal.stop_loss:.2f}" if signal.stop_loss is not None else ""
        )
        return (
            f"{emoji} {signal.signal.upper()} Signal: {ticker.upper()} | "
            f"Confidence: {confidence_pct:.0f}%{stop_loss_text}\n"
            f"Reason: {signal.reasoning}"
        )

    def send_alert(self, signal: TradeSignal, ticker: str) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.error("Telegram bot token or chat ID is missing. Skipping alert.")
            return False

        message = self._format_message(signal, ticker)
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown",
        }

        try:
            response = requests.post(url, data=payload, timeout=10)
            response.raise_for_status()
            logger.success(f"Sent Telegram alert for {ticker}: {signal.signal}")
            return True
        except requests.RequestException as exc:
            logger.error(f"Failed to send Telegram alert: {exc}")
            return False
