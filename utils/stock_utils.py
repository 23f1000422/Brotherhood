import yfinance as yf
import pandas as pd
import time
import requests
import streamlit as st

NIFTY_50_SYMBOLS = [
    'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS',
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BHARTIARTL.NS', 'BPCL.NS',
    'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DIVISLAB.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
    'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS',
    'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS',
    'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS',
    'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SHRIRAMFIN.NS', 'SUNPHARMA.NS',
    'TCS.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TECHM.NS',
    'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS'
]

def fetch_stock_data(symbol, interval="1d", period="5d", max_retries=3):
    for attempt in range(max_retries):
        try:
            data = yf.download(
                tickers=symbol,
                period=period,
                interval=interval,
                progress=False,
                group_by='ticker',
                timeout=10
            )

            if symbol in data.columns:
                data = data[symbol]

            # 🧹 Fix duplicate columns by resetting to single-level names
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(-1)

            # Remove completely duplicate-named columns (defensive)
            data = data.loc[:, ~data.columns.duplicated()]

             # 👉 Verify necessary columns exist
            required_cols = ['Open', 'High', 'Low', 'Close']
            if not all(col in data.columns for col in required_cols):
                st.warning(f"{symbol}: Required columns missing after processing. Got: {list(data.columns)}")
                return pd.DataFrame()

            return data

        except Exception as e:
            st.error(f"Error fetching {symbol}: {e}")
            time.sleep(2 ** attempt)

    return pd.DataFrame()

def analyze_stocks(interval="1d", period="5d"):
    results = []

    for symbol in NIFTY_50_SYMBOLS:
        data = fetch_stock_data(symbol, interval=interval, period=period)
        if data.empty or len(data) < 2:
            continue

        # Grab last 2 trading days
        yesterday = data.iloc[-2]
        today = data.iloc[-1]

        open_today = today['Open']
        high_yesterday = yesterday['High']
        low_yesterday = yesterday['Low']

        status = ""
        gap_pct = None

        if open_today > high_yesterday:
            status = "Gap Up Breakout"
            gap_pct = ((open_today - high_yesterday) / high_yesterday) * 100
        elif open_today < low_yesterday:
            status = "Gap Down Breakdown"
            gap_pct = ((low_yesterday - open_today) / low_yesterday) * 100



        if status:  # only include if condition met
            results.append({
                "Symbol": symbol.replace(".NS", ""),
                "Yesterday High": high_yesterday,
                "Yesterday Low": low_yesterday,
                "Today Open": open_today,
                "Gap Percentage": f"{gap_pct:.2f}%" if gap_pct is not None else None,
                "Status": status
            })

        time.sleep(0.5)

    return pd.DataFrame(results)