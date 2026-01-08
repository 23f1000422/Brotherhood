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

def fetch_live_prices(symbols=NIFTY_50_SYMBOLS):
    """
    Fetches the latest available price (Close of the last minute candle) for the given symbols.
    Returns a Series: {Symbol: Price}
    """
    try:
        # Fetch 1-minute data 
        # LIVE MARKET: '1d' is best.
        # AFTER MARKET (TESTING): '1d' sometimes returns empty if market is closed long ago? 
        # We will try '1d' first, if empty, try '5d' to ensure we get *some* data for testing.
        
        ticker_str = " ".join(symbols)
        
        def get_data(period):
            return yf.download(
                tickers=ticker_str,
                period=period,
                interval="1m",
                group_by='ticker',
                progress=False,
                threads=True,
                timeout=10,
                auto_adjust=False
            )

        data = get_data("1d")
        
        if data.empty:
             # Fallback for testing after hours if 1d fails
            data = get_data("5d")

        latest_prices = {}
        
        if data.empty:
            return pd.Series()

        # Handle single ticker case vs multi-ticker case
        if len(symbols) == 1:
            symbol = symbols[0]
            if not data.empty:
                # Get the last valid close price
                val = data["Close"].iloc[-1].item()
                latest_prices[symbol] = val
        else:
            # Multi-ticker
            
            # Check if flat columns (only 1 ticker valid despite asking for many)
            # If flat, columns would be [Open, High, ...] without Ticker level
            is_flat = not isinstance(data.columns, pd.MultiIndex)
            
            if is_flat and len(symbols) > 1:
                if 'Close' in data.columns:
                     pass
            
            for symbol in symbols:
                try:
                    # Case 1: Standard MultiIndex (Ticker, OHLC) due to group_by='ticker'
                    if (isinstance(data.columns, pd.MultiIndex) and symbol in data.columns.levels[0]):
                        symbol_data = data[symbol]
                        if not symbol_data.empty:
                            valid_closes = symbol_data["Close"].dropna()
                            if not valid_closes.empty:
                                latest_prices[symbol] = valid_closes.iloc[-1].item()
                    # Case 2: Standard flat
                    elif symbol in data.columns:
                         val = data[symbol].dropna().iloc[-1]
                         latest_prices[symbol] = val
                except Exception:
                    continue
        
        return pd.Series(latest_prices)
    except Exception as e:
        print(f"Error fetching live prices: {e}")
        return pd.Series()