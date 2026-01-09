# Nifty 50 Live Tracker

## Features
- **Live Tracking**: Fetches 1-minute data every 30 seconds (9:15-9:25 AM).
- **Auto-Save**: Saves results at 9:25 AM.
- **Advanced AI Forecasting**: Uses Hugging Face with technical signals and news.
- **Top 50 Nifty & Crypto**: Support for the entire Nifty 50 list.

## Setup
1. Add Hugging Face API Token to `.streamlit/secrets.toml`:
```toml
HF_TOKEN = "REPLACE_ME"
```
2. Run:
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```