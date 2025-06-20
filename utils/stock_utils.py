import yfinance as yf
import pandas as pd
import time

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
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(-1)
            data = data.loc[:, ~data.columns.duplicated()]
            if not all(col in data.columns for col in ['Open', 'High', 'Low']):
                return pd.DataFrame()
            return data
        except Exception:
            time.sleep(2 ** attempt)
    return pd.DataFrame()

def analyze_stocks():
    results = []
    for symbol in NIFTY_50_SYMBOLS:
        data = fetch_stock_data(symbol)
        if data.empty or len(data) < 2:
            continue
        today = data.iloc[-1]
        yesterday = data.iloc[-2]
        open_today = today["Open"]
        high_yesterday = yesterday["High"]
        low_yesterday = yesterday["Low"]
        if open_today > high_yesterday:
            status = "Gap Up Breakout"
            gap = ((open_today - high_yesterday) / high_yesterday) * 100
        elif open_today < low_yesterday:
            status = "Gap Down Breakdown"
            gap = ((low_yesterday - open_today) / low_yesterday) * 100
        else:
            continue
        results.append({
            "Symbol": symbol.replace(".NS", ""),
            "Yesterday High": round(high_yesterday, 2),
            "Yesterday Low": round(low_yesterday, 2),
            "Today Open": round(open_today, 2),
            "Gap %": round(gap, 2),
            "Status": status
        })
        time.sleep(0.5)
    return pd.DataFrame(results)