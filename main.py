import asyncio
import json
from dotenv import load_dotenv
import os
import websockets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

# === User Input Menu ===
notification_email = input("Enter your notification email: ")
tokens = [token.strip().upper() for token in input("Enter tokens to monitor (comma separated, e.g. BTC,ETH): ").split(',') if token.strip()]
thresholds = {token: float(input(f"Set notification price for {token}: ")) for token in tokens}

print("\nMonitoring setup complete:")
print(f"Notification email: {notification_email}")
print("Tokens and thresholds:")
for t, p in thresholds.items():
    print(f"  {t}: {p}")


def display_prices(prices):
    lines = [
        "Live token prices (press Ctrl+C to stop)",
        "",
        f"{'Token':<10} {'Price':>18} {'Threshold':>18} {'Status':>12}",
        "-" * 62,
    ]
    for token in tokens:
        price = prices.get(token)
        threshold = thresholds[token]
        if price is None:
            price_text = "waiting..."
            status = "WAITING"
        else:
            price_text = f"{price:,.8f}"
            status = "ALERT" if price >= threshold else "watching"
        lines.append(f"{token:<10} {price_text:>18} {threshold:>18,.8f} {status:>12}")
    lines.append(f"\nLast update: {asyncio.get_event_loop().time():.1f}")
    print("\033[2J\033[H" + "\n".join(lines), flush=True)

# === Email Sending Function ===
def send_email(to_email, subject, body):
    # Configure your SMTP settings
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_email = os.getenv("SMTP_USERNAME")
    sender_password = os.getenv("SMTP_PASSWORD")

    if not sender_email or not sender_password:
        print("Email not sent: SMTP_USERNAME and SMTP_PASSWORD are required")
        return

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Error sending email: {e}")

# === WebSocket Subscription ===
API_KEY = os.getenv("CMC_API_KEY")  # replace with your CoinMarketCap Pro API key
URI = "wss://pro-stream.coinmarketcap.com/v1"
CRYPTO_IDS = {
    "BTC": 1,
    "ETH": 1027,
    "BNB": 1839,
    "SOL": 5426,
    "ADA": 2010,
    "XRP": 52,
    "DOGE": 74,
}

async def subscribe():
    prices = {token: None for token in tokens}
    alerted_tokens = set()
    display_prices(prices)
    unknown_tokens = [token for token in tokens if token not in CRYPTO_IDS]
    if unknown_tokens:
        raise ValueError(
            "Unsupported token symbol(s): " + ", ".join(unknown_tokens) +
            ". Add their CoinMarketCap IDs to CRYPTO_IDS."
        )

    token_by_id = {CRYPTO_IDS[token]: token for token in tokens}
    headers = {"X-CMC_PRO_API_KEY": API_KEY}
    async with websockets.connect(URI, additional_headers=headers) as ws:
        await ws.send(json.dumps({
            "id": 1,
            "method": "subscribe",
            "channel": "market@crypto_latest_price",
            "params": {"crypto_ids": list(token_by_id)},
        }))

        print("\nListening for price updates...\n")

        while True:
            message = await ws.recv()
            data = json.loads(message)

            if data.get("type") == "error" or data.get("status", {}).get("error_message"):
                error_message = data.get("msg") or data.get("status", {}).get("error_message", "Unknown error")
                print(f"\nCoinMarketCap error: {error_message}")
                continue

            if data.get("type") == "ack":
                print(f"\nSubscription active: {data.get('msg', 'ok')} ({data.get('sub_count', 0)} token(s))")
                continue

            ticker = data.get("data")
            if isinstance(ticker, dict) and "cid" in ticker:
                try:
                    symbol = token_by_id.get(int(ticker["cid"]))
                except (TypeError, ValueError):
                    symbol = None
                raw_price = ticker.get("p")

                if symbol and raw_price is not None:
                    price = float(raw_price)
                    prices[symbol] = price
                    display_prices(prices)

                    if price >= thresholds[symbol] and symbol not in alerted_tokens:
                        alert_msg = f"{symbol} hit {price} (threshold {thresholds[symbol]})"
                        print(f"Notify {notification_email}: {alert_msg}")
                        await asyncio.to_thread(send_email, notification_email, f"{symbol} Price Alert", alert_msg)
                        alerted_tokens.add(symbol)
                    elif price < thresholds[symbol]:
                        alerted_tokens.discard(symbol)

# === Run Event Loop ===
if __name__ == "__main__":
    asyncio.run(subscribe())
