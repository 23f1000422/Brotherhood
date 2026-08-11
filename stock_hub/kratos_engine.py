import sys
import os
import yfinance as yf
import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from stock_hub.quant_tools import QuantTools
from stock_hub.sentiment_engine import LocalSentimentEngine
from stock_hub.derivatives_engine import get_derivatives_strategy, get_atm_info

# =============================================================================
# 🧠 KRATOS AI MULTI-AGENT QUANTITATIVE RESEARCH ENGINE
# =============================================================================

class OrderFlowAuditor:
    """
    Agent 1: Tape & Order Flow Auditor
    Evaluates institutional footprint, opening range validity, and trap risk.
    """
    @staticmethod
    def audit(df, open_p, day_h, day_l, ltp, vol, avg_vol):
        vol_surge = vol / max(avg_vol, 1.0)
        
        # Bull/Bear Trap Analysis
        day_range = max(day_h - day_l, 0.01)
        close_position = (ltp - day_l) / day_range # 0 = at low, 1 = at high
        
        if close_position >= 0.70 and vol_surge >= 1.2:
            status = "INSTITUTIONAL ACCUMULATION"
            trap_risk = "LOW (Buyers in firm control)"
            score = 88
        elif close_position <= 0.30 and vol_surge >= 1.2:
            status = "INSTITUTIONAL DISTRIBUTION"
            trap_risk = "HIGH (Aggressive supply overhead)"
            score = 25
        elif close_position > 0.50 and vol_surge < 0.8:
            status = "LOW-VOLUME REBOUND (Vulnerable)"
            trap_risk = "MEDIUM (Lack of institutional backing)"
            score = 55
        else:
            status = "NEUTRAL CONSOLIDATION"
            trap_risk = "MEDIUM"
            score = 50
            
        return {
            "status": status,
            "trap_risk": trap_risk,
            "vol_ratio": round(vol_surge, 2),
            "close_position_pct": round(close_position * 100, 1),
            "flow_score": score
        }

class SectorRotationAgent:
    """
    Agent 2: Macro & Sector Rotation Agent
    Assesses market regime and sectoral tailwinds.
    """
    @staticmethod
    def analyze_regime(symbol, df, ema200, ltp):
        is_above_ema = ltp >= ema200
        # 20-day vs 50-day short trend
        ema20 = float(df['Close'].ewm(span=20, adjust=False).mean().iloc[-1])
        ema50 = float(df['Close'].ewm(span=50, adjust=False).mean().iloc[-1])
        
        if is_above_ema and ema20 > ema50:
            regime = "EXPANSION (Bullish Trend)"
            alignment = "TAILWIND"
        elif not is_above_ema and ema20 < ema50:
            regime = "CONTRACTION (Bearish Trend)"
            alignment = "HEADWIND"
        elif is_above_ema and ema20 < ema50:
            regime = "PULLBACK IN UPTREND (Buy on Dip)"
            alignment = "NEUTRAL-BULLISH"
        else:
            regime = "COUNTER-TREND BOUNCE"
            alignment = "NEUTRAL-BEARISH"
            
        return {
            "market_regime": regime,
            "trend_alignment": alignment,
            "ema20": round(ema20, 2),
            "ema50": round(ema50, 2),
            "ema200": round(ema200, 2)
        }

class RiskExecutionArchitect:
    """
    Agent 3: Risk & Execution Architect
    Calculates multi-target scaling, dynamic ATR trailing stops, and position sizing.
    """
    @staticmethod
    def construct_trade_plan(direction, ltp, day_h, day_l, atr, risk_capital=25000):
        if direction == "BULLISH":
            t1 = round(ltp + 1.5 * atr, 2)
            t2 = round(ltp + 2.5 * atr, 2)
            t3 = round(ltp + 4.0 * atr, 2)
            sl = round(min(day_l, ltp - 1.2 * atr), 2)
            risk_per_share = max(ltp - sl, 0.5)
        else:
            t1 = round(ltp - 1.5 * atr, 2)
            t2 = round(ltp - 2.5 * atr, 2)
            t3 = round(ltp - 4.0 * atr, 2)
            sl = round(max(day_h, ltp + 1.2 * atr), 2)
            risk_per_share = max(sl - ltp, 0.5)
            
        rr_t1 = round(abs(t1 - ltp) / risk_per_share, 2)
        rr_t2 = round(abs(t2 - ltp) / risk_per_share, 2)
        
        # Volatility-Adjusted Max Position Sizing (Max 1% capital risk per trade)
        max_risk_allowed = risk_capital * 0.01
        recommended_qty = max(int(max_risk_allowed / risk_per_share), 1)
        
        return {
            "target1": t1,
            "target2": t2,
            "target3": t3,
            "stop_loss": sl,
            "risk_per_share": round(risk_per_share, 2),
            "rr_t1": rr_t1,
            "rr_t2": rr_t2,
            "recommended_qty": recommended_qty,
            "capital_required": round(recommended_qty * ltp, 2)
        }

class KratosAIEngine:
    """
    Kratos AI Central Quantitative Orchestrator.
    Synthesizes all specialized agents into a hedge-fund grade trade dossier.
    """
    def __init__(self):
        self.model = None
        self._init_llm()

    def _init_llm(self):
        try:
            import google.generativeai as genai
            import streamlit as st
            api_key = None
            try:
                api_key = st.secrets["GOOGLE_API_KEY"]
            except Exception:
                api_key = os.environ.get("GOOGLE_API_KEY")

            if api_key:
                api_key = str(api_key).strip().strip("'").strip('"')
                if api_key.startswith("AQ.") or api_key.startswith("ya29"):
                    from google.oauth2.credentials import Credentials
                    creds = Credentials(api_key)
                    genai.configure(credentials=creds, transport='rest')
                else:
                    genai.configure(api_key=api_key, transport='rest')
                self.model = genai.GenerativeModel('gemini-flash-lite-latest')
        except Exception:
            self.model = None

    def generate_kratos_dossier(self, symbol, risk_capital=25000):
        clean_sym = symbol.replace(".NS", "")
        raw_sym = symbol if symbol.endswith(".NS") or "^" in symbol else f"{symbol}.NS"
        
        try:
            t = yf.Ticker(raw_sym)
            df = t.history(period="1y", auto_adjust=False)
            if df.empty or len(df) < 30:
                return {"status": "error", "message": f"Insufficient historical telemetry for {symbol}"}
                
            df = QuantTools.sanitize_dataframe(df)
            
            curr_row = df.iloc[-1]
            prev_row = df.iloc[-2] if len(df) > 1 else curr_row
            
            o = round(float(curr_row['Open'].item() if hasattr(curr_row['Open'], 'item') else curr_row['Open']), 2)
            h = round(float(curr_row['High'].item() if hasattr(curr_row['High'], 'item') else curr_row['High']), 2)
            l = round(float(curr_row['Low'].item() if hasattr(curr_row['Low'], 'item') else curr_row['Low']), 2)
            c = round(float(curr_row['Close'].item() if hasattr(curr_row['Close'], 'item') else curr_row['Close']), 2)
            vol = float(curr_row['Volume'].item() if hasattr(curr_row['Volume'], 'item') else curr_row['Volume'])
            
            # Technical Indicators
            ema200 = round(float(QuantTools.calculate_ema(df['Close'], 200).iloc[-1]), 2)
            rsi = round(float(QuantTools.calculate_rsi(df['Close'], 14).iloc[-1]), 1)
            macd, macd_sig, macd_hist = QuantTools.calculate_macd(df['Close'])
            atr = round(float(QuantTools.calculate_atr(df, 14).iloc[-1]), 2)
            atr = max(atr, round(c * 0.008, 2))
            pivots = QuantTools.calculate_pivots(df)
            
            is_above_ema200 = c >= ema200
            direction = "BULLISH" if (is_above_ema200 and rsi < 70) or (c >= o and rsi <= 60) else "BEARISH"
            
            # 1. Agent 1: Order Flow Audit
            avg_vol = float(df['Volume'].rolling(20, min_periods=1).mean().iloc[-1])
            order_flow = OrderFlowAuditor.audit(df, o, h, l, c, vol, avg_vol)
            
            # 2. Agent 2: Sector & Macro Regime
            regime = SectorRotationAgent.analyze_regime(clean_sym, df, ema200, c)
            
            # 3. Agent 3: Risk & Execution Trade Plan
            trade_plan = RiskExecutionArchitect.construct_trade_plan(direction, c, h, l, atr, risk_capital)
            
            # 4. Agent 4: Derivatives Volatility & Greeks
            derivatives_data = get_derivatives_strategy(raw_sym, c, rsi=rsi, trend=direction)
            atm_details = get_atm_info(raw_sym, c)
            
            # 5. Local FinBERT Sentiment
            sentiment_data = LocalSentimentEngine.get_ticker_news_sentiment(clean_sym)
            
            # 6. Kratos AI Synthesis Thesis
            thesis, key_risks = self._synthesize_thesis(
                clean_sym, c, direction, rsi, ema200, trade_plan, order_flow, regime, sentiment_data
            )
            
            return {
                "status": "success",
                "engine": "Kratos AI Quant Multi-Agent",
                "symbol": clean_sym,
                "raw_symbol": raw_sym,
                "price": c,
                "open": o,
                "high": h,
                "low": l,
                "direction": direction,
                "ema200": ema200,
                "above_ema200": is_above_ema200,
                "rsi": rsi,
                "macd_hist": round(float(macd_hist.iloc[-1]), 2),
                "atr": atr,
                "target": trade_plan['target1'],
                "target2": trade_plan['target2'],
                "target3": trade_plan['target3'],
                "sl": trade_plan['stop_loss'],
                "risk_reward": trade_plan['rr_t1'],
                "trade_plan": trade_plan,
                "order_flow": order_flow,
                "regime": regime,
                "pivots": pivots,
                "sentiment": sentiment_data,
                "derivatives": derivatives_data,
                "atm_details": atm_details,
                "thesis": thesis,
                "key_risks": key_risks,
                "df_history": df.tail(60)
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def _synthesize_thesis(self, symbol, price, direction, rsi, ema200, plan, flow, regime, sentiment):
        if self.model:
            prompt = f"""
            You are Kratos AI, a Principal Quantitative Strategist at a tier-1 systematic hedge fund.
            Conduct an institutional trade thesis on {symbol}:
            
            Quantitative Telemetry:
            - Spot Price: Rs. {price:.2f} | Technical Bias: {direction}
            - RSI(14): {rsi:.1f} | 200 EMA Floor: Rs. {ema200:.2f}
            - Order Flow State: {flow['status']} (Trap Risk: {flow['trap_risk']})
            - Market Regime: {regime['market_regime']} ({regime['trend_alignment']})
            - News Sentiment: {sentiment.get('overall_sentiment', 'Neutral')} ({sentiment.get('sentiment_score', 0):+.2f})
            - Execution Targets: T1=Rs.{plan['target1']}, T2=Rs.{plan['target2']} | SL=Rs.{plan['stop_loss']} (R:R {plan['rr_t1']}x)
            
            Deliver:
            1. 2-sentence sharp, data-dense Quantitative Rationale.
            2. 2 bullet points detailing specific structural execution risk triggers.
            Format as JSON: {{"thesis": "...", "risks": ["Risk 1", "Risk 2"]}}
            """
            try:
                res = self.model.generate_content(prompt)
                txt = res.text.strip()
                if "{" in txt and "}" in txt:
                    clean_json = txt[txt.find("{"):txt.rfind("}")+1]
                    data = json.loads(clean_json)
                    return data.get("thesis", ""), data.get("risks", [])
            except Exception:
                pass

        # Deterministic Quant Fallback
        if direction == "BULLISH":
            thesis = (
                f"Kratos AI models detect {flow['status']} in {symbol} at Rs. {price:.2f} trading "
                f"within an active {regime['market_regime']}. Order flow alignment confirms favorable asymmetry "
                f"toward Tactical Target T1 of Rs. {plan['target1']:.2f} (R:R {plan['rr_t1']}x)."
            )
            risks = [
                f"Violation of structural volatility floor at Rs. {plan['stop_loss']:.2f} triggers instant trade liquidation.",
                f"Sudden liquidity trap if price falls below opening session low."
            ]
        else:
            thesis = (
                f"Kratos AI models identify {flow['status']} on {symbol} at Rs. {price:.2f} within a "
                f"{regime['market_regime']}. Sustained selling pressure projects downside expansion to Rs. {plan['target1']:.2f}."
            )
            risks = [
                f"Short squeeze or sudden reversal above structural ceiling at Rs. {plan['stop_loss']:.2f}.",
                f"Oversold exhaustion triggering rapid mean-reversion buying."
            ]

        return thesis, risks

    @staticmethod
    def generate_kratos_multi_chart(dossier):
        """
        Creates an Institutional Multi-Panel Interactive Technical Chart:
        - Panel 1: Price Action Candlesticks + 20/50/200 EMA + Target T1/T2/T3 & SL + ATR Channels
        - Panel 2: Volume Histogram with 20D Average Volume
        - Panel 3: RSI(14) Momentum Oscillator with 70/30 Bands
        """
        df = dossier.get("df_history", pd.DataFrame())
        if df.empty or len(df) < 5:
            return None
            
        plan = dossier.get("trade_plan", {})
        target1 = plan.get("target1", dossier.get("target", 0))
        target2 = plan.get("target2", dossier.get("target2", 0))
        target3 = plan.get("target3", target2)
        sl = plan.get("stop_loss", dossier.get("sl", 0))
        
        # Calculate Overlays
        ema20 = df['Close'].ewm(span=20, adjust=False).mean()
        ema50 = df['Close'].ewm(span=50, adjust=False).mean()
        rsi_series = QuantTools.calculate_rsi(df['Close'], 14)
        vol_avg = df['Volume'].rolling(20, min_periods=1).mean()
        
        # Color Volume Bars based on Close vs Open
        vol_colors = ['#10b981' if c >= o else '#ef4444' for c, o in zip(df['Close'], df['Open'])]

        # 3-Row Subplot Figure
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.60, 0.20, 0.20],
            subplot_titles=(f"📈 {dossier['symbol']} Price Action & Kratos Targets", "📊 Volume & Institutional Flow", "⚡ RSI (14) Momentum")
        )

        # Panel 1: Candlesticks
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name="Price",
            increasing_line_color="#10b981",
            decreasing_line_color="#ef4444"
        ), row=1, col=1)

        # EMAs
        fig.add_trace(go.Scatter(
            x=df.index, y=ema20,
            line=dict(color="#38bdf8", width=1.5),
            name="20 EMA"
        ), row=1, col=1)

        fig.add_trace(go.Scatter(
            x=df.index, y=ema50,
            line=dict(color="#f59e0b", width=1.5),
            name="50 EMA"
        ), row=1, col=1)

        # Horizontal Target Lines & SL
        if target1 > 0:
            fig.add_hline(y=target1, line_dash="dash", line_color="#10b981",
                          annotation_text=f"T1: ₹{target1:.2f}", annotation_position="top right", row=1, col=1)
        if target2 > 0:
            fig.add_hline(y=target2, line_dash="dot", line_color="#34d399",
                          annotation_text=f"T2: ₹{target2:.2f}", annotation_position="top right", row=1, col=1)
        if sl > 0:
            fig.add_hline(y=sl, line_dash="dash", line_color="#ef4444",
                          annotation_text=f"SL Floor: ₹{sl:.2f}", annotation_position="bottom right", row=1, col=1)

        # Panel 2: Volume
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['Volume'],
            marker_color=vol_colors,
            name="Volume"
        ), row=2, col=1)

        fig.add_trace(go.Scatter(
            x=df.index,
            y=vol_avg,
            line=dict(color="#94a3b8", width=1.2),
            name="20D Vol Avg"
        ), row=2, col=1)

        # Panel 3: RSI
        fig.add_trace(go.Scatter(
            x=df.index,
            y=rsi_series,
            line=dict(color="#a855f7", width=1.8),
            name="RSI (14)"
        ), row=3, col=1)

        fig.add_hline(y=70, line_dash="dot", line_color="#ef4444", row=3, col=1)
        fig.add_hline(y=30, line_dash="dot", line_color="#10b981", row=3, col=1)

        fig.update_layout(
            template="plotly_dark",
            height=680,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis_rangeslider_visible=False,
            paper_bgcolor="#0b0e14",
            plot_bgcolor="#0b0e14",
            showlegend=False
        )

        return fig

KratosEngine = KratosAIEngine
