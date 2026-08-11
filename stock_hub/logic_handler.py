import os
import re
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
from stock_hub.kratos_engine import KratosEngine

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
            query = "SELECT Ticker, Direction, Pattern, Price, Change_Pct, Target, SL, RR, RSI, Action FROM processed_watchlist WHERE Date = (SELECT MAX(Date) FROM processed_watchlist) LIMIT 12"
            df = pd.read_sql(query, conn)
            if not df.empty:
                return "ACTIVE QUANT WATCHLIST TELEMETRY:\n" + df.to_string(index=False)
            return "No current daily watchlist available."
    except Exception as e:
        return f"Database context offline: {e}"

def extract_ticker_from_prompt(prompt):
    """
    Parses prompt for known stock tickers or uppercase symbols.
    """
    clean_text = prompt.upper().replace(".NS", "")
    words = re.findall(r'\b[A-Z0-9&-]{2,15}\b', clean_text)
    
    # Common command words to ignore
    ignore_words = {
        "WHAT", "HOW", "WHY", "WHEN", "TELL", "GIVE", "SHOW", "ANALYSIS", "ANALYZE",
        "STOCK", "STOCKS", "PRICE", "TARGET", "STOP", "LOSS", "RISK", "TODAY",
        "MARKET", "NIFTY", "BANK", "OPTION", "CALL", "PUT", "BUY", "SELL", "HELP",
        "TRAP", "SCORE", "KRATOS", "ORACLE", "STATUS", "DAILY", "CHART"
    }
    
    for w in words:
        if w not in ignore_words and len(w) >= 3:
            return w
            
    return None

def query_gemini(prompt):
    """
    Directly routes queries to Kratos AI Multi-Agent Engine with real-time SQL context injection.
    """
    brain_db.save_message("user", prompt)
    ticker = extract_ticker_from_prompt(prompt)
    
    # Route 1: Target Stock Specific Multi-Agent Deep Audit
    if ticker:
        kratos = KratosEngine()
        dossier = kratos.generate_kratos_dossier(ticker)
        
        if dossier.get("status") == "success":
            plan = dossier['trade_plan']
            flow = dossier['order_flow']
            regime = dossier['regime']
            deriv = dossier['derivatives']
            sent = dossier['sentiment']
            
            response = (
                f"### 🧬 KRATOS AI MULTI-AGENT DOSSIER: **{dossier['symbol']}**\n\n"
                f"**Spot LTP:** ₹{dossier['price']:.2f} | **Bias:** `{dossier['direction']}`\n\n"
                f"**🏛️ Quant Rationale:**\n> {dossier['thesis']}\n\n"
                f"**🔍 Agent 1 (Order Flow & Trap Risk):**\n"
                f"• State: **{flow['status']}**\n"
                f"• Trap Risk: `{flow['trap_risk']}` | Volume Ratio: `{flow['vol_ratio']}x` | Flow Score: `{flow['flow_score']}/100`\n\n"
                f"**🌐 Agent 2 (Market Regime):**\n"
                f"• Regime: **{regime['market_regime']}** ({regime['trend_alignment']})\n"
                f"• 200 EMA Floor: ₹{dossier['ema200']:.2f} ({'Above' if dossier['above_ema200'] else 'Below'})\n\n"
                f"**🎯 Agent 3 (Execution Plan):**\n"
                f"• Target T1: **₹{plan['target1']:.2f}** (R:R {plan['rr_t1']}x)\n"
                f"• Target T2: **₹{plan['target2']:.2f}** (R:R {plan['rr_t2']}x)\n"
                f"• Dynamic SL: **₹{plan['stop_loss']:.2f}** (Risk/Share: ₹{plan['risk_per_share']:.2f})\n\n"
                f"**⚡ Agent 4 (Derivatives & Greeks):**\n"
                f"• Strike: `{deriv.get('strike', 'N/A')}` ({deriv.get('premium', '')})\n"
                f"• Delta (Δ): `{deriv.get('delta', 0):+.2f}` | Gamma: `{deriv.get('gamma', 0):.4f}` | Theta: `{deriv.get('theta', 0):.2f}`\n\n"
                f"**🧠 Agent 5 (FinBERT Sentiment):**\n"
                f"• Polarity: `{sent.get('overall_sentiment', 'Neutral')}` (Score: `{sent.get('sentiment_score', 0):+.2f}`)\n"
            )
            brain_db.save_message("assistant", response)
            return response

    # Route 2: Broad Market / General Inquiries with Live SQLite Injection
    api_key = None
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
    except Exception:
        api_key = os.environ.get("GOOGLE_API_KEY")

    db_state = get_db_context()
    
    if api_key:
        api_key = str(api_key).strip().strip("'").strip('"')
        if api_key.startswith("AQ.") or api_key.startswith("ya29"):
            creds = Credentials(api_key) if Credentials else None
            genai.configure(credentials=creds, transport='rest')
        else:
            genai.configure(api_key=api_key, transport='rest')
            
        history_records = brain_db.get_history(limit=4)
        context = "\n".join([f"{h[0]}: {h[1]}" for h in history_records])
        
        full_prompt = (
            "You are Kratos Oracle, the Lead Quantitative AI Architect for the Brotherhood Terminal.\n"
            "Answer the user query using the live quantitative telemetry and database state below.\n"
            "Be data-dense, professional, precise, and practical.\n\n"
            f"LIVE SQL DATABASE CONTEXT:\n{db_state}\n\n"
            f"USER QUERY: {prompt}\n"
        )
        try:
            model = genai.GenerativeModel('gemini-flash-lite-latest')
            res = model.generate_content(full_prompt)
            answer = res.text.strip()
            brain_db.save_message("assistant", answer)
            return answer
        except Exception:
            pass

    # Deterministic Fallback Market Briefing
    fallback_resp = (
        f"### 🧬 KRATOS ORACLE TELEMETRY BRIEFING\n\n"
        f"**Live Database State:**\n```\n{db_state}\n```\n"
        f"💡 **Tip:** Mention any specific ticker (e.g. *'Analyze SBIN'*, *'What is the trap risk on RELIANCE?'*) "
        f"to trigger full Kratos 5-Agent multi-model research."
    )
    brain_db.save_message("assistant", fallback_resp)
    return fallback_resp

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
            prices = t.history(period="5d", auto_adjust=False)
            if len(prices) >= 2:
                change = ((prices['Close'].iloc[-1] - prices['Close'].iloc[-2]) / prices['Close'].iloc[-2]) * 100
                results.append({"Sector": name, "Performance (%)": round(change, 2)})
        except Exception:
            pass
    return pd.DataFrame(results)

def fetch_trending_tickers():
    try:
        db_path = os.path.join("stock_hub", "brotherhood_data.db")
        with sqlite3.connect(db_path) as conn:
            query = """
                SELECT Ticker, Price, Change_Pct 
                FROM processed_watchlist 
                WHERE Date = (SELECT MAX(Date) FROM processed_watchlist)
                ORDER BY ABS(Change_Pct) DESC LIMIT 5
            """
            df = pd.read_sql(query, conn)
            return df
    except Exception:
        return pd.DataFrame()
