import os
import sqlite3
import pandas as pd
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
import google.generativeai as genai
import streamlit as st
try:
    from google.oauth2.credentials import Credentials
except ImportError:
    Credentials = None
from dotenv import load_dotenv

load_dotenv()

class LocalBrainDB:
    def __init__(self, db_path=os.path.join("stock_hub", "brotherhood_data.db")):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS history 
                            (id INTEGER PRIMARY KEY, role TEXT, content TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
                            
    def purge_history(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM history")
            
    def get_history(self, limit=10):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT role, content FROM history ORDER BY id DESC LIMIT ?", (limit,))
            return list(reversed(cur.fetchall()))
            
    def save_message(self, role, content):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO history (role, content) VALUES (?, ?)", (role, content))

brain_db = LocalBrainDB()

def get_db_context():
    try:
        db_path = os.path.join("stock_hub", "brotherhood_data.db")
        with sqlite3.connect(db_path) as conn:
            query = "SELECT * FROM processed_watchlist WHERE Date = (SELECT MAX(Date) FROM processed_watchlist)"
            df = pd.read_sql(query, conn)
            if not df.empty:
                return "CURRENT DAILY STOCK WATCHLIST ARRAY:\n" + df.to_string(index=False)
            return "No current daily watchlist available."
    except Exception as e:
        return f"Database access error: {e}"

def query_gemini(prompt):
    """
    PA ARCHITECTURE: The Core Oracle decoupled locally using standard google-generativeai.
    """
    api_key = None
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        api_key = os.environ.get("GOOGLE_API_KEY")

    if api_key:
        api_key = api_key.strip()

    if not api_key:
        return "System offline: Missing API Key."
        
    if api_key.startswith("AQ.") or api_key.startswith("ya29"):
        creds = Credentials(api_key) if Credentials else None
        genai.configure(credentials=creds, transport='rest')
    else:
        genai.configure(api_key=api_key, transport='rest')
    
    history_records = brain_db.get_history(limit=5)
    context = "\n".join([f"{h[0]}: {h[1]}" for h in history_records])
    
    db_state = get_db_context()
    
    full_prompt = (
        "You are the Brotherhood Oracle, a high-precision Systematic Momentum terminal. Read the SQL data provided and give professional, blunt, and practical financial advice based on MACD/RSI/EMA trends.\n"
        f"CONTEXT HISTORY:\n{context}\n\n"
        f"LIVE SQL DATABASE STATE:\n{db_state}\n\n"
        f"USER: {prompt}\n\n"
        "STRICT RULE: Do not use personal names or informal greetings. Data-centric responses only."
    )
    
    try:
        model = genai.GenerativeModel('gemini-flash-lite-latest')
        brain_db.save_message("user", prompt)
        response = model.generate_content(full_prompt)
        answer = response.text.strip()
        brain_db.save_message("assistant", answer)
        return answer
    except Exception as e:
        return f"Oracle Error: {e}"

def get_cross_domain_strategy():
    """
    KNOWLEDGE BRIDGE: Decoupled to query local sqlite.
    """
    try:
        db_path = os.path.join("stock_hub", "brotherhood_data.db")
        if not os.path.exists(db_path):
            return "Oracle: Database uninitialized. Proceed with caution."
            
        with sqlite3.connect(db_path) as conn:
            df = pd.read_sql("SELECT * FROM processed_watchlist WHERE Date = (SELECT MAX(Date) FROM processed_watchlist)", conn)
            
            total_potential = (df['Target'] - df['Price']).sum()
            if total_potential > 200:
                return f"Systematic Scan: Market shows value potential of ${round(total_potential,2)}+ based on current momentum benchmarks."
    except:
        pass
        
    return "Proprietary Momentum Scanner: Monitoring for breakout triggers."

def fetch_market_pulse():
    import yfinance as yf
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
                delta_sign = "+" if delta_val > 0 else ""
                results.append({
                    "symbol": ticker,
                    "name": name,
                    "value": last_close,
                    "delta_val": delta_val,
                    "delta_pct": round(delta_pct, 2)
                })
        except Exception as e:
            # Silent fallback for network latency
            pass
    return results

def fetch_sector_performance():
    import yfinance as yf
    sectors = {
        "^CNXIT": "IT",
        "^NSEBANK": "Bank",
        "^CNXPHARMA": "Pharma",
        "^CNXAUTO": "Auto",
        "^CNXMETAL": "Metal",
        "^CNXFMCG": "FMCG"
    }
    results = []
    for ticker, name in sectors.items():
        try:
            t = yf.Ticker(ticker)
            prices = t.history(period="5d") # Buffer for weekends
            if len(prices) >= 2:
                # basis: (Closing Price Today / Closing Price Previous Session) - 1
                change = ((prices['Close'].iloc[-1] - prices['Close'].iloc[-2]) / prices['Close'].iloc[-2]) * 100
                results.append({"Sector": name, "Performance (%)": round(change, 2)})
        except: pass
    return pd.DataFrame(results)

def fetch_trending_tickers():
    try:
        db_path = os.path.join("stock_hub", "brotherhood_data.db")
        with sqlite3.connect(db_path) as conn:
            query = """
                SELECT Ticker, Price, Volume, Change_Pct 
                FROM raw_signals 
                WHERE Date = (SELECT MAX(Date) FROM raw_signals)
                ORDER BY Volume DESC LIMIT 5
            """
            df = pd.read_sql(query, conn)
            if not df.empty: return df
            # Fallback for fresh DB: Mock data for visualization
            return pd.DataFrame([
                {"Ticker": "NIFTY_P", "Price": 22450, "Volume": 500000, "Change_Pct": 1.2},
                {"Ticker": "BANK_P", "Price": 48200, "Volume": 350000, "Change_Pct": -0.5},
                {"Ticker": "IT_P", "Price": 36000, "Volume": 420000, "Change_Pct": 0.8},
            ])
    except:
        return pd.DataFrame()

def fetch_top_movers():
    try:
        db_path = os.path.join("stock_hub", "brotherhood_data.db")
        with sqlite3.connect(db_path) as conn:
            query = """
                SELECT Ticker, Price, Change_Pct 
                FROM raw_signals 
                WHERE Date = (SELECT MAX(Date) FROM raw_signals)
                ORDER BY Change_Pct DESC LIMIT 5
            """
            df = pd.read_sql(query, conn)
            return df
    except:
        return pd.DataFrame()

def get_mf_returns_table():
    import yfinance as yf
    from datetime import datetime, timedelta
    mf_map = {
        '0P0000XW8F.BO': 'SBI Bluechip Fund',
        '0P0000XW95.BO': 'HDFC Top 100 Fund',
        '0P0000XW9L.BO': 'ICICI Pru Bluechip',
        '0P0000XW9M.BO': 'Nippon India Large Cap',
        '0P0000XWA0.BO': 'UTI Mastershare Fund'
    }
    
    rows = []
    for ticker, name in mf_map.items():
        try:
            t = yf.Ticker(ticker)
            hist = t.history(period="max")
            if hist.empty: continue
            
            curr = hist['Close'].iloc[-1]
            
            def calc_ret(years):
                days = int(years * 365)
                # target_date approx
                if len(hist) > days:
                    past_val = hist['Close'].iloc[-(days+1)]
                    ret = ((curr - past_val) / past_val) * 100
                    return f"{round(ret, 2)}%"
                return "N/A"
            
            rows.append({
                "Fund Name": name,
                "Current NAV": round(curr, 2),
                "1Y": calc_ret(1),
                "3Y": calc_ret(3),
                "5Y": calc_ret(5),
                "10Y": calc_ret(10),
                "15Y": calc_ret(15)
            })
        except: pass
    return pd.DataFrame(rows)

def generate_linkedin_content(content_type="market"):
    import streamlit as st
    api_key = None
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        api_key = os.environ.get("GOOGLE_API_KEY")

    if api_key:
        api_key = api_key.strip().strip("'").strip('"')

    if not api_key: return "API Key Missing."
    
    if api_key.startswith("AQ.") or api_key.startswith("ya29"):
        creds = Credentials(api_key) if Credentials else None
        genai.configure(credentials=creds, transport='rest')
    else:
        genai.configure(api_key=api_key, transport='rest')
    model = genai.GenerativeModel('gemini-flash-lite-latest')
    
    db_state = get_db_context()
    
    if content_type == "market":
        prompt = (
            "Draft a professional LinkedIn post based on this market data. "
            "Highlight the top 'Prime O-L Momentum' stocks and mention general sectoral trends. "
            "Use a professional, insight-driven tone. Include hashtags #Investing #FinTech #MarketInsights.\n\n"
            f"DATA:\n{db_state}"
        )
    else:
        prompt = (
            "Draft a professional LinkedIn post about Mutual Fund educational trends and the importance of SIP/Long-term investing. "
            "Make it informative and engaging. Include hashtags #MutualFunds #SIP #LongTermInvesting #FinancialLiteracy."
        )
        
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Generation Error: {e}"
