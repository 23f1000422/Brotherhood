import yfinance as yf

def fetch_market_pulse_standalone():
    """
    Decoupled Pulse Engine to resolve Streamlit Cloud caching issues.
    Returns absolute values for price and points delta.
    """
    indices = {
        "^NSEI": "Nifty 50",
        "^NSEBANK": "Bank Nifty",
        "^BSESN": "Sensex"
    }
    results = []
    for ticker, name in indices.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="5d")
            if len(hist) >= 2:
                last_close = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2]
                delta_val = last_close - prev_close
                delta_pct = (delta_val / prev_close) * 100
                
                results.append({
                    "symbol": ticker,
                    "name": name,
                    "value": float(last_close),
                    "delta_val": float(delta_val),
                    "delta_pct": round(float(delta_pct), 2)
                })
        except:
            pass
    return results
