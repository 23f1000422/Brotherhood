import streamlit as st
import os
import sys
import pandas as pd
import sqlite3
import plotly.graph_objects as go

# --- RESILIENT PROJECT PATHING ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from stock_hub.stock_engine import run_research_cycle
from stock_hub.kratos_engine import KratosEngine, RiskExecutionArchitect
from stock_hub.upstox_engine import upstox
from stock_hub.pulse_engine import fetch_market_pulse_standalone
from stock_hub.logic_handler import query_gemini, brain_db

st.set_page_config(
    page_title="Brotherhood Quant Cockpit | Kratos AI",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ADVANCED QUANT COCKPIT CSS ---
st.markdown("""
    <style>
    /* Dark Terminal Background */
    .stApp {
        background-color: #0b0e14;
        color: #e2e8f0;
    }
    
    /* Sleek Cards */
    .quant-card {
        background: linear-gradient(145deg, #151a23 0%, #11141c 100%);
        border: 1px solid #232936;
        border-radius: 10px;
        padding: 1.1rem;
        margin-bottom: 0.8rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.35);
    }
    
    .quant-card-highlight {
        background: linear-gradient(145deg, #182232 0%, #121924 100%);
        border: 1px solid #2563eb;
        border-radius: 10px;
        padding: 1.1rem;
        box-shadow: 0 4px 16px rgba(37, 99, 235, 0.15);
    }
    
    .kratos-badge {
        background: linear-gradient(135deg, #6366f1 0%, #4338ca 100%);
        color: #ffffff;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.5px;
        display: inline-block;
    }
    
    /* Pill Badges */
    .badge-bullish {
        background-color: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid #10b981;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .badge-bearish {
        background-color: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid #ef4444;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
    }
    
    .badge-neutral {
        background-color: rgba(148, 163, 184, 0.15);
        color: #94a3b8;
        border: 1px solid #64748b;
        padding: 4px 12px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 0.85rem;
        display: inline-block;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        font-weight: 700;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: #ffffff;
        border: none;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
        box-shadow: 0 0 12px rgba(59, 130, 246, 0.5);
    }
    
    /* Metrics */
    div[data-testid="stMetricValue"] {
        font-size: 1.45rem !important;
        font-weight: 800 !important;
    }
    </style>
""", unsafe_allow_html=True)

TICKER_MAP = {"^NSEI": "NIFTY 50", "^NSEBANK": "BANK NIFTY", "^BSESN": "SENSEX", "^CNXIT": "IT SECTOR"}

def load_screener_data():
    db_path = os.path.join(PROJECT_ROOT, "stock_hub", "brotherhood_data.db")
    if not os.path.exists(db_path):
        return pd.DataFrame()
    try:
        with sqlite3.connect(db_path) as conn:
            query = "SELECT * FROM processed_watchlist WHERE Date = (SELECT MAX(Date) FROM processed_watchlist)"
            df = pd.read_sql(query, conn)
            return df
    except Exception:
        return pd.DataFrame()

def main():
    # --- AUTO-BOOTSTRAP CHECK ---
    if "screener_df" not in st.session_state:
        df = load_screener_data()
        if df.empty:
            with st.spinner("🚀 Bootstrapping Brotherhood & Kratos AI Quant Engine..."):
                run_research_cycle()
                df = load_screener_data()
        st.session_state.screener_df = df

    # --- SIDEBAR: MASTER ORACLE TERMINAL (KRATOS AI CONNECTED) ---
    with st.sidebar:
        st.title("🛰️ MASTER ORACLE")
        st.caption("Direct Kratos AI Multi-Agent & SQL State Stream")
        st.markdown("---")
        
        chat_container = st.container(height=340, border=True)
        history = brain_db.get_history(limit=8)
        for role, content in history:
            with chat_container.chat_message(role):
                st.markdown(content)

        user_input = st.chat_input("Ask Oracle / Kratos (e.g. 'Analyze SBIN')...")
        if user_input:
            with chat_container.chat_message("user"):
                st.markdown(user_input)
            with chat_container.chat_message("assistant"):
                with st.spinner("Kratos Multi-Agent System synthesizing telemetry..."):
                    ans = query_gemini(user_input)
                    st.markdown(ans)
            st.rerun()

        st.markdown("---")
        st.markdown("### ⚙️ System Architecture")
        st.markdown("• **Tier 1:** Pure Math Screener (0ms LLM)")
        st.markdown("• **Tier 2:** Kratos AI Multi-Agent Engine")
        st.markdown("• **Gateway:** Upstox API v2 & Paper Router")
        st.markdown("• **Greeks:** Closed-Form Black-Scholes")

    # --- TOP HEADER & MARKET PULSE BAR ---
    st.markdown("## 🧬 BROTHERHOOD QUANTITATIVE COCKPIT")
    st.caption("⚡ Powered by Kratos AI Multi-Agent Research & Upstox Execution Gateway")

    try:
        pulse_data = fetch_market_pulse_standalone()
        if pulse_data:
            p_cols = st.columns(len(pulse_data))
            for i, p in enumerate(pulse_data):
                with p_cols[i]:
                    sym = p.get('symbol', '')
                    name = TICKER_MAP.get(sym, p.get('name', sym))
                    val = float(p.get('value', 0))
                    d_val = p.get('delta_val', 0)
                    d_pct = p.get('delta_pct', 0)
                    delta_str = f"{d_val:+,.2f} ({d_pct:+0.2f}%)"
                    st.metric(label=name, value=f"₹{val:,.2f}", delta=delta_str)
    except Exception:
        pass

    st.markdown("---")

    # =========================================================================
    # TIER 1 (TOP): LIVE QUANT SCREENER
    # =========================================================================
    st.markdown("### 🏛️ TIER 1: LIVE QUANT SCREENER (High-High / Low-Low & Prime O-L)")
    st.caption("⚡ Strict Mathematical Filtering (Zero False-Positives) • Direct Raw NSE Price Feeds")

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([3, 1.5, 1.5])
    
    with col_ctrl1:
        direction_filter = st.radio(
            "Signal Filter:",
            ["🌐 ALL BREAKOUTS", "🟢 BULLISH (Prime O=L / Gap Up)", "🔻 BEARISH (Prime O=H / Gap Down)"],
            horizontal=True,
            label_visibility="collapsed"
        )

    with col_ctrl3:
        if st.button("🔄 RESCAN BASKET NOW"):
            with st.spinner("Executing High-Speed Multithreaded Quant Scan..."):
                run_research_cycle()
                st.session_state.screener_df = load_screener_data()
                st.rerun()

    df_screener = st.session_state.get("screener_df", pd.DataFrame())

    if not df_screener.empty:
        if "BULLISH" in direction_filter:
            filtered_df = df_screener[df_screener['Direction'] == 'BULLISH']
        elif "BEARISH" in direction_filter:
            filtered_df = df_screener[df_screener['Direction'] == 'BEARISH']
        else:
            filtered_df = df_screener

        display_cols = ['Ticker', 'Direction', 'Pattern', 'Price', 'Change_Pct', 'Day_Range', 'Target', 'SL', 'RR', 'RSI', 'EMA200', 'Action']
        avail_cols = [c for c in display_cols if c in filtered_df.columns]
        
        st.dataframe(
            filtered_df[avail_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Price": st.column_config.NumberColumn("Spot LTP (₹)", format="₹%.2f"),
                "Change_Pct": st.column_config.NumberColumn("Change (%)", format="%+0.2f%%"),
                "Day_Range": st.column_config.TextColumn("Day Range (L - H)"),
                "Target": st.column_config.NumberColumn("Tactical Target (₹)", format="₹%.2f"),
                "SL": st.column_config.NumberColumn("Dynamic SL (₹)", format="₹%.2f"),
                "RR": st.column_config.NumberColumn("R:R Ratio", format="%.2fx"),
                "RSI": st.column_config.NumberColumn("RSI (14)", format="%.1f"),
                "EMA200": st.column_config.NumberColumn("200 EMA Floor", format="₹%.1f"),
                "Action": st.column_config.TextColumn("System Action")
            }
        )
    else:
        st.info("No current session breakout signals. Click 'RESCAN BASKET NOW' to refresh.")

    st.markdown("---")

    # =========================================================================
    # TIER 2 (BOTTOM): KRATOS AI MULTI-AGENT RESEARCH & UPSTOX GATEWAY
    # =========================================================================
    st.markdown("### 🔬 TIER 2: KRATOS AI MULTI-AGENT RESEARCH & EXECUTION GATEWAY")
    st.caption("Institutional Quantitative Analysis: Order Flow Trap Audit + Sector Regime + Multi-Target Plan + Upstox Router")

    candidate_tickers = df_screener['Ticker'].tolist() if not df_screener.empty else ['RELIANCE', 'TCS', 'HDFCBANK', 'INFY', 'ICICIBANK']
    
    c_sel1, c_sel2 = st.columns([2, 4])
    with c_sel1:
        selected_ticker = st.selectbox("Select Target Stock for Kratos Deep Dossier:", candidate_tickers, index=0)

    kratos_engine = KratosEngine()
    
    with st.spinner(f"Kratos AI Agents conducting multi-model audit on {selected_ticker}..."):
        dossier = kratos_engine.generate_kratos_dossier(selected_ticker)

    if dossier.get("status") == "success":
        dir_class = "badge-bullish" if dossier['direction'] == "BULLISH" else "badge-bearish"
        plan = dossier['trade_plan']
        flow = dossier['order_flow']
        regime = dossier['regime']
        
        st.markdown(f"""
            <div class="quant-card-highlight">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="font-size: 1.55rem; font-weight: 800; margin-right: 12px;">{dossier['symbol']}</span>
                        <span class="{dir_class}">{dossier['direction']}</span>
                        <span class="kratos-badge" style="margin-left: 8px;">KRATOS AI AUDITED</span>
                    </div>
                    <div style="font-size: 1.4rem; font-weight: 800; color: #38bdf8;">
                        Spot LTP: ₹{dossier['price']:.2f}
                    </div>
                </div>
                <div style="margin-top: 12px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; font-size: 0.95rem;">
                    <div>🎯 <b>Target T1:</b> ₹{plan['target1']:.2f}</div>
                    <div>🛡️ <b>Dynamic SL:</b> ₹{plan['stop_loss']:.2f}</div>
                    <div>⚖️ <b>Risk:Reward (T1):</b> {plan['rr_t1']:.2f}x</div>
                    <div>📊 <b>Daily ATR:</b> ₹{dossier['atr']:.2f}</div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # 5 Interactive Multi-Model Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏛️ Kratos AI Thesis & Execution Plan",
            "📈 Kratos Multi-Panel Technical Chart",
            "🧠 FinBERT Sentiment Gauge",
            "⚡ Derivatives & Option Greeks",
            "🚀 Upstox Gateway & Order Routing"
        ])

        with tab1:
            st.markdown("#### 📝 Institutional Quantitative Rationale")
            st.markdown(f"""
                <div class="quant-card">
                    <p style="font-size: 1.05rem; line-height: 1.6; margin: 0;">
                        {dossier['thesis']}
                    </p>
                </div>
            """, unsafe_allow_html=True)

            col_ag1, col_ag2 = st.columns(2)
            with col_ag1:
                st.markdown("#### 🔍 Agent 1: Order Flow & Trap Audit")
                st.markdown(f"""
                    <div class="quant-card">
                        <p style="margin: 0; font-size: 0.85rem; color: #94a3b8;">ORDER FLOW STATE</p>
                        <h4 style="margin: 5px 0; color: #38bdf8;">{flow['status']}</h4>
                        <p style="margin: 0;"><b>Trap Risk:</b> {flow['trap_risk']}</p>
                        <p style="margin: 0;"><b>Volume Ratio:</b> {flow['vol_ratio']}x | <b>Flow Score:</b> {flow['flow_score']}/100</p>
                    </div>
                """, unsafe_allow_html=True)

            with col_ag2:
                st.markdown("#### 🌐 Agent 2: Sector & Macro Regime")
                st.markdown(f"""
                    <div class="quant-card">
                        <p style="margin: 0; font-size: 0.85rem; color: #94a3b8;">MARKET REGIME</p>
                        <h4 style="margin: 5px 0; color: #10b981;">{regime['market_regime']}</h4>
                        <p style="margin: 0;"><b>Trend Alignment:</b> {regime['trend_alignment']}</p>
                        <p style="margin: 0;"><b>EMA20:</b> ₹{regime['ema20']} | <b>EMA50:</b> ₹{regime['ema50']} | <b>EMA200:</b> ₹{regime['ema200']}</p>
                    </div>
                """, unsafe_allow_html=True)

            st.markdown("#### 🎯 Execution Plan & Multi-Target Scaling")
            c_t1, c_t2, c_t3, c_sl = st.columns(4)
            c_t1.metric("Target T1 (1.5x ATR)", f"₹{plan['target1']:.2f}", f"R:R {plan['rr_t1']}x")
            c_t2.metric("Target T2 (2.5x ATR)", f"₹{plan['target2']:.2f}", f"R:R {plan['rr_t2']}x")
            c_t3.metric("Target T3 (Extended)", f"₹{plan['target3']:.2f}", "Runner")
            c_sl.metric("Dynamic SL Floor", f"₹{plan['stop_loss']:.2f}", f"Risk: ₹{plan['risk_per_share']:.2f}")

            st.markdown("#### ⚠️ Structural Execution Risks")
            for rk in dossier.get('key_risks', []):
                st.warning(f"• {rk}")

        with tab2:
            st.markdown(f"#### 📈 Kratos Multi-Panel Institutional Chart: **{dossier['symbol']}**")
            chart_fig = KratosEngine.generate_kratos_multi_chart(dossier)
            if chart_fig:
                st.plotly_chart(chart_fig, use_container_width=True)
            else:
                st.info("Insufficient chart telemetry to render multi-panel view.")

        with tab3:
            st.markdown("#### 🧠 Local Neural & Lexicon Sentiment Analysis")
            sentiment = dossier.get('sentiment', {})
            s_score = sentiment.get('sentiment_score', 0.0)
            overall = sentiment.get('overall_sentiment', 'NEUTRAL')
            
            s_col1, s_col2 = st.columns([2, 4])
            with s_col1:
                badge = "badge-bullish" if overall == "BULLISH" else ("badge-bearish" if overall == "BEARISH" else "badge-neutral")
                st.markdown(f"""
                    <div class="quant-card" style="text-align: center;">
                        <p style="margin: 0; font-size: 0.85rem; color: #94a3b8;">AGGREGATE SENTIMENT</p>
                        <h2 style="margin: 6px 0;"><span class="{badge}">{overall}</span></h2>
                        <h3 style="margin: 0;">Polarity: {s_score:+.2f}</h3>
                        <p style="margin-top: 8px; font-size: 0.75rem; color: #64748b;">FinBERT Neural Polarity Gauge</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with s_col2:
                st.markdown("**Analyzed News Headlines & Neural Polarities:**")
                all_scores = sentiment.get('all_scores', [])
                if all_scores:
                    for item in all_scores:
                        st.markdown(f"• **[{item['sentiment']}]** Polarity: `{item['score']:+.2f}` | Confidence: `{item['confidence']*100:.0f}%` ({item['engine']})")
                else:
                    st.caption("Technical momentum baseline applied.")

        with tab4:
            st.markdown("#### ⚡ Real-Time Black-Scholes Greeks & Strike Engine")
            deriv = dossier.get('derivatives', {})
            
            d_col1, d_col2 = st.columns([2, 3])
            with d_col1:
                st.markdown(f"""
                    <div class="quant-card">
                        <p style="margin: 0; font-size: 0.85rem; color: #94a3b8;">RECOMMENDED STRIKE</p>
                        <h2 style="color: #38bdf8; margin: 5px 0;">{deriv.get('strike', 'N/A')}</h2>
                        <p style="margin: 0; font-weight: 700;">Est. Premium: {deriv.get('premium', 'N/A')}</p>
                        <p style="margin-top: 8px; font-size: 0.85rem; color: #cbd5e1;">{deriv.get('reason', '')}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with d_col2:
                g_c1, g_c2, g_c3 = st.columns(3)
                g_c1.metric("Delta (Δ)", f"{deriv.get('delta', 0):+.2f}")
                g_c2.metric("Gamma (Γ)", f"{deriv.get('gamma', 0):.4f}")
                g_c3.metric("Theta (Θ)", f"{deriv.get('theta', 0):.2f}/day")
                
                g_c4, g_c5, g_c6 = st.columns(3)
                g_c4.metric("Vega (V)", f"{deriv.get('vega', 0):.2f}")
                g_c5.metric("Implied Vol (IV)", f"{deriv.get('iv_pct', 20):.1f}%")
                g_c6.metric("Deterministic PCR", f"{deriv.get('pcr', 1.0):.2f}")

            st.markdown("#### 🎯 Volatility Bounds (Dynamic ATR Channels)")
            v_b1, v_b2, v_b3 = st.columns(3)
            v_b1.metric("1x ATR Move", f"±₹{dossier['atr']:.2f}")
            v_b2.metric("Upper 1-ATR Target", f"₹{dossier['price'] + dossier['atr']:.2f}")
            v_b3.metric("Lower 1-ATR Target", f"₹{dossier['price'] - dossier['atr']:.2f}")

        with tab5:
            st.markdown("#### 🚀 Upstox Execution Gateway & Order Routing")
            
            u_col1, u_col2 = st.columns([2, 3])
            with u_col1:
                st.markdown("##### 💼 Position Sizing Calculator")
                risk_cap = st.number_input("Account Risk Capital (₹):", min_value=5000, value=25000, step=5000)
                recalc_plan = RiskExecutionArchitect.construct_trade_plan(dossier['direction'], dossier['price'], dossier['high'], dossier['low'], dossier['atr'], risk_cap)
                st.info(f"Recommended Quantity: **{recalc_plan['recommended_qty']} Shares** | Risk per Share: **₹{recalc_plan['risk_per_share']:.2f}**")
                
                order_mode = st.radio("Order Routing Mode:", ["🛡️ Paper Trading (Simulation)", "⚡ Live Upstox Route"], horizontal=True)
                is_sim = "Paper" in order_mode

            with u_col2:
                st.markdown("##### ⚡ Quick Order Ticket")
                order_side = "BUY" if dossier['direction'] == "BULLISH" else "SELL"
                if st.button(f"🚀 EXECUTE {order_side} ({recalc_plan['recommended_qty']} Shares @ ₹{dossier['price']:.2f})"):
                    res = upstox.place_order(
                        symbol=dossier['symbol'],
                        quantity=recalc_plan['recommended_qty'],
                        transaction_type=order_side,
                        price=dossier['price'],
                        simulated=is_sim
                    )
                    if res.get("status") == "SUCCESS":
                        st.success(f"✅ Order Executed: {res['message']} (ID: {res['order_id']})")
                    else:
                        st.error(f"❌ Order Failed: {res.get('message')}")

    else:
        st.error(f"Error compiling Kratos dossier for {selected_ticker}: {dossier.get('message', 'Unknown Error')}")

if __name__ == "__main__":
    main()