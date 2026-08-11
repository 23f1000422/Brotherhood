import sys
import os
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import time
sys.path.append(os.getcwd())

import re
import pandas as pd
import sqlite3
import yfinance as yf
from datetime import datetime, timedelta
from stock_hub.indicator_engine import scan_advanced_signals
from stock_hub.quant_tools import QuantTools
from stock_hub.derivatives_engine import get_derivatives_strategy, get_atm_info

def clean_ascii(text):
    if not isinstance(text, str): return str(text)
    return re.sub(r'[^\x00-\x7f]', r'', text)

# TOP 50 VERIFIED LIQUID NSE F&O UNIVERSE
NIFTY_ACTIVE_BASKET = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS', 'ICICIBANK.NS',
    'BHARTIARTL.NS', 'SBIN.NS', 'ITC.NS', 'LT.NS', 'HINDUNILVR.NS',
    'AXISBANK.NS', 'KOTAKBANK.NS', 'M&M.NS', 'MARUTI.NS', 'SUNPHARMA.NS',
    'NTPC.NS', 'POWERGRID.NS', 'TITAN.NS', 'ULTRACEMCO.NS', 'BAJAJ-AUTO.NS',
    'ASIANPAINT.NS', 'COALINDIA.NS', 'ADANIENT.NS', 'ADANIPORTS.NS', 'JSWSTEEL.NS',
    'HCLTECH.NS', 'WIPRO.NS', 'ONGC.NS', 'GRASIM.NS', 'DIVISLAB.NS',
    'DRREDDY.NS', 'CIPLA.NS', 'EICHERMOT.NS', 'TECHM.NS', 'HEROMOTOCO.NS',
    'HINDALCO.NS', 'BRITANNIA.NS', 'NESTLEIND.NS', 'TATACONSUM.NS', 'APOLLOHOSP.NS',
    'SBILIFE.NS', 'HDFCLIFE.NS', 'BEL.NS', 'HAL.NS', 'VEDL.NS',
    'DLF.NS', 'PIDILITIND.NS', 'IOC.NS', 'GAIL.NS', 'HAVELLS.NS'
]

NIFTY_100 = NIFTY_ACTIVE_BASKET

class DatabaseManager:
    def __init__(self, db_path=None):
        from stock_hub.config import DB_PATH
        self.db_path = db_path if db_path else DB_PATH
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            
            # Check for column schema alignment
            try:
                cur = conn.execute("PRAGMA table_info(processed_watchlist)")
                cols = [row[1] for row in cur.fetchall()]
                if cols and ('Change_Pct' not in cols or 'Day_Range' not in cols or 'RR' not in cols):
                    conn.execute("DROP TABLE IF EXISTS processed_watchlist")
            except Exception:
                pass

            conn.execute("""
                CREATE TABLE IF NOT EXISTS processed_watchlist (
                    Date TEXT,
                    Ticker TEXT,
                    Direction TEXT,
                    Pattern TEXT,
                    Price REAL,
                    Change_Pct REAL,
                    Day_Range TEXT,
                    Target REAL,
                    SL REAL,
                    RR REAL,
                    RSI REAL,
                    MACD REAL,
                    EMA200 REAL,
                    Volume_Ratio REAL,
                    Action TEXT,
                    Agent_Review TEXT,
                    Timestamp TEXT,
                    PRIMARY KEY (Date, Ticker)
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS derivatives (
                    Date TEXT,
                    Ticker TEXT,
                    Price REAL,
                    PCR REAL,
                    RSI REAL,
                    Strike TEXT,
                    Premium TEXT,
                    Action TEXT,
                    Reason TEXT,
                    Timestamp TEXT,
                    PRIMARY KEY (Date, Ticker)
                )
            """)

    def save_processed_watchlist(self, records):
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        date_str = ist_now.strftime("%Y-%m-%d")
        exact_time = ist_now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_str = clean_ascii(exact_time)

        with sqlite3.connect(self.db_path) as conn:
            for r in records:
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO processed_watchlist 
                        (Date, Ticker, Direction, Pattern, Price, Change_Pct, Day_Range, Target, SL, RR, RSI, MACD, EMA200, Volume_Ratio, Action, Agent_Review, Timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date_str, r['Ticker'], r['Direction'], r['Pattern'], 
                        r['Price'], r['Change_Pct'], r.get('Day_Range', ''),
                        r['Target'], r['SL'], r.get('RR', 1.5), 
                        r['RSI'], r['MACD'], r['EMA200'], r.get('Volume_Ratio', 1.0),
                        r['Action'], r['Agent_Review'], timestamp_str
                    ))
                except Exception as e:
                    print(f"DB Error: {e}")

    def save_derivatives(self, options_data):
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        date_str = ist_now.strftime("%Y-%m-%d")
        exact_time = ist_now.strftime("%Y-%m-%d %H:%M:%S")
        timestamp_str = clean_ascii(exact_time)

        with sqlite3.connect(self.db_path) as conn:
            for sym, d in options_data.items():
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO derivatives (Date, Ticker, Price, PCR, RSI, Strike, Premium, Action, Reason, Timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        date_str, sym, d['price'], float(d['pcr']), d['rsi'], 
                        str(d['strike']), str(d['premium']), d['action'], d['reason'], timestamp_str
                    ))
                except Exception:
                    pass

def run_research_cycle(symbols=None):
    start_time = time.time()
    db = DatabaseManager()
    target_symbols = symbols if symbols else NIFTY_ACTIVE_BASKET
    
    print(f"[INIT] ACCURATE QUANT BREAKOUT SCAN | Target Universe: {len(target_symbols)}")
    
    # 1. Accurate Scan
    signals = scan_advanced_signals(target_symbols, max_workers=25)
    
    if signals:
        db.save_processed_watchlist(signals)

    # 2. Fast Derivatives Sync
    indices = ["^NSEI", "^NSEBANK", "^BSESN", "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "TCS.NS"]
    options_data = {}
    qt = QuantTools()
    for sym in indices:
        try:
            t = yf.Ticker(sym)
            fi = t.fast_info
            ltp = round(float(getattr(fi, 'last_price', 0) or 0), 2)
            if ltp <= 0: continue
            
            raw_df = yf.download(sym, period="60d", interval="1d", progress=False, auto_adjust=False, timeout=4)
            if raw_df.empty: continue
            df = QuantTools.sanitize_dataframe(raw_df)
            
            rsi = round(float(qt.calculate_rsi(df['Close']).iloc[-1]), 1)
            ema200 = float(qt.calculate_ema(df['Close'], 200).iloc[-1])
            trend = "BULLISH" if ltp >= ema200 else "BEARISH"
            
            strat = get_derivatives_strategy(sym, ltp, rsi=rsi, trend=trend)
            options_data[sym] = {
                "price": ltp,
                "pcr": strat['pcr'],
                "rsi": rsi,
                "action": strat['action'],
                "reason": strat['reason'],
                "strike": strat['strike'],
                "premium": strat['premium']
            }
        except Exception:
            pass
            
    db.save_derivatives(options_data)
    
    elapsed = time.time() - start_time
    print(f"[SUCCESS] ACCURATE QUANT SCAN COMPLETED IN {elapsed:.2f}s | Isolated {len(signals)} Breakout Candidates")
    return signals

if __name__ == "__main__":
    run_research_cycle()
