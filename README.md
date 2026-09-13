# CoinMarketCap Crypto Price Alert

A Python-based CLI tool that monitors live cryptocurrency prices via the **CoinMarketCap WebSocket API**.  
It allows users to set price thresholds for selected tokens and sends **email alerts** when those thresholds are reached.
Here is a live link to the project demo ---->https://youtu.be/3ObLTfAXv5E

---

## 🚀 Features
- Interactive CLI menu for:
  - Entering your notification email
  - Selecting tokens to monitor (e.g., BTC, ETH)
  - Setting price thresholds
- Live price updates displayed in the terminal
- Email notifications when thresholds are met
- Configurable SMTP settings via `.env` file
- Supports major tokens (BTC, ETH, BNB, SOL, ADA, XRP, DOGE) with CoinMarketCap IDs

---

## 📦 Requirements
- Python 3.8+
- CoinMarketCap Pro API key
- SMTP credentials (e.g., Gmail, Outlook)

Install dependencies:
```bash
pip install -r requirements.txt
