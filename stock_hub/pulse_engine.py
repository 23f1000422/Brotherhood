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
            # Try getting 1d first, if empty, try 5d
            hist = t.history(period="1d")
            if hist.empty:
                hist = t.history(period="5d")
            
            if not hist.empty:
                last_price = hist['Close'].iloc[-1]
                # If hist is just 1 row, we need more to calculate delta
                if len(hist) < 2:
                    h5 = t.history(period="5d")
                    if len(h5) >= 2:
                        prev_close = h5['Close'].iloc[-2]
                    else:
                        prev_close = last_price # Fallback
                else:
                    prev_close = hist['Close'].iloc[-2]

                # LAST RESORT: Check for real-time info if market is open
                # If the last history index is from a previous day, Ticker.info might have today's price
                from datetime import datetime, timedelta
                ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
                today_str = ist_now.strftime("%Y-%m-%d")
                
                if hist.index[-1].strftime("%Y-%m-%d") != today_str:
                    try:
                        # Only try info if history is lagging (info is slow)
                        info_price = t.info.get('regularMarketPrice')
                        if info_price and info_price > 0 and info_price != last_price:
                            prev_close = last_price # The old last close becomes prev_close
                            last_price = info_price
                    except: pass

                delta_val = last_price - prev_close
                delta_pct = (delta_val / prev_close) * 100 if prev_close != 0 else 0
                
                results.append({
                    "symbol": ticker,
                    "name": name,
                    "value": float(last_price),
                    "delta_val": float(delta_val),
                    "delta_pct": round(float(delta_pct), 2)
                })
        except Exception as e:
            print(f"Pulse Error for {ticker}: {e}")
            pass
    return results

