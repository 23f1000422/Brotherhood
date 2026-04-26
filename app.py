import streamlit as st
import os
import sys
import pandas as pd
import json
import sqlite3
from stock_hub.logic_handler import query_gemini, brain_db, fetch_market_pulse
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="Indigenous AI Cockpit", page_icon="🧬", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .status-card { background-color: #1a1c24; border: 1px solid #333; padding: 1.2rem; border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

def main():
    # --- MASTER AGENT CLEAN SLATE ---
    if "chat_purged" not in st.session_state:
        brain_db.purge_history()
        st.session_state.messages = [] 
        st.session_state.chat_purged = True
        st.rerun()

    # --- SIDEBAR: MASTER ORACLE ---
    st.sidebar.title("🛰️ MASTER ORACLE")
    
    st.sidebar.markdown("---")
    chat_container = st.sidebar.container(height=350, border=True)
    
    history = brain_db.get_history(limit=10)
    for role, content in history:
        with chat_container.chat_message(role):
            st.markdown(content)

    user_input = st.sidebar.chat_input("Speak to the Source...")
    if user_input:
        with chat_container.chat_message("user"):
            st.markdown(user_input)
        
        query_gemini(user_input)
        
        # We also clear session history to ensure clean UI
        if "messages" in st.session_state: st.session_state.messages = []
        st.rerun()

    tabs = st.tabs(["🖥️ MARKET TERMINAL", "🚀 STRATEGY & CONTENT HUB"])

    with tabs[0]:
        st.header("🖥️ Proprietary Market Terminal")
        db_path = os.path.join("stock_hub", "brotherhood_data.db")
        
        if os.path.exists(db_path):
            try:
                with sqlite3.connect(db_path) as conn:
                    latest_date_query = "SELECT MAX(Date) as max_date FROM processed_watchlist"
                    df_date = pd.read_sql(latest_date_query, conn)
                    latest_date = df_date['max_date'].iloc[0] if not df_date.empty and not pd.isna(df_date['max_date'].iloc[0]) else None
                    
                    if latest_date:
                        ts_query = f"SELECT MAX(Timestamp) as max_ts FROM processed_watchlist WHERE Date = '{latest_date}'"
                        try:
                            df_ts = pd.read_sql(ts_query, conn)
                            latest_ts = df_ts['max_ts'].iloc[0] if not df_ts.empty and not pd.isna(df_ts['max_ts'].iloc[0]) else "N/A"
                        except:
                            latest_ts = "N/A"
                            
                        st.markdown(f"**Terminal Sync: {latest_ts}**")
                        
                        # --- MARKET PULSE INDICES ---
                        pulse_data = fetch_market_pulse()
                        if pulse_data:
                            pulse_cols = st.columns(len(pulse_data))
                            for idx, p in enumerate(pulse_data):
                                with pulse_cols[idx]:
                                    st.metric(label=p['name'], value=p['value'], delta=p['delta'])
                        st.markdown("---")
                        
                        query = f"SELECT * FROM processed_watchlist WHERE Date = '{latest_date}'"
                        df = pd.read_sql(query, conn)
                        
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            if not df.empty:
                                top_ticker = df.iloc[0]['Ticker']
                                top_review = df.iloc[0]['Agent_Review']
                                st.success(f"**Top Momentum Pick: {top_ticker}**")
                                st.markdown(f"> {top_review}")
                            else:
                                st.info("No momentum picks identified for the current session.")
                        with col2:
                            st.metric("P-OL Tickers", len(df))
                            
                        st.write(f"### 📈 Watchlist Telemetry ({latest_date})")
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.info("Database is empty. Please trigger a research cycle.")
            except Exception as e:
                st.error(f"Database Error: {e}")
        else:
            st.info("Searching for Fresh Data... The engine operates locally.")
            if st.button("🚀 TRIGGER RESEARCH CYCLE NOW"):
                # Use current directory to ensure relative path works on any OS
                current_dir = os.path.dirname(os.path.abspath(__file__))
                hub_path = os.path.join(current_dir, "stock_hub")
                if hub_path not in sys.path: sys.path.append(hub_path)
                from stock_engine import run_research_cycle
                with st.spinner("Processing Markets..."):
                    run_research_cycle()
                    st.rerun()
        
        st.divider()
        st.subheader("📊 Systematic Derivatives & ATM Strategy")
        if os.path.exists(db_path):
            try:
                with sqlite3.connect(db_path) as conn:
                    deriv_date_query = "SELECT MAX(Date) as max_date FROM derivatives"
                    df_d_date = pd.read_sql(deriv_date_query, conn)
                    latest_d_date = df_d_date['max_date'].iloc[0] if not df_d_date.empty and not pd.isna(df_d_date['max_date'].iloc[0]) else None
                    if latest_d_date:
                        deriv_query = f"SELECT * FROM derivatives WHERE Date = '{latest_d_date}'"
                        opt_df = pd.read_sql(deriv_query, conn)
                        st.dataframe(opt_df, use_container_width=True)
                    else:
                        st.info("Derivatives analytics pending research cycle.")
            except Exception as e:
                st.error(f"Error loading Derivatives: {e}")

        st.divider()
        st.subheader("📚 Mutual Fund Insights")
        from stock_hub.logic_handler import get_mf_returns_table
        mf_data = get_mf_returns_table()
        if not mf_data.empty:
            st.dataframe(mf_data, use_container_width=True, hide_index=True)
            st.caption("Annualized performance benchmarks | Data source: Yahoo Finance")
        else:
            st.info("MF Performance telemetry offline.")

        st.markdown("---")
        with st.expander("📖 SYSTEMATIC STRATEGY GUARDRAILS"):
            st.markdown("""
            ### 🎯 Core Momentum Rules (Prime O-L)
            1. **Prime O-L (Open=Low/High)**: We only scalp tickers where the session open is equal to the low (Bullish) or high (Bearish) with a 0.05% tolerance.
            2. **The EMA200 Guard**: Never enter a BUY position if the price is below the 200-Day EMA. Momentum must be systemic.
            3. **RSI Precision**: 
               - **BUY**: RSI < 65 (Room to move)
               - **AVOID**: RSI > 75 (Overbought danger zone)
            4. **Exit Strategy**:
               - **Target**: Fibonacci 1.618 or Pivot R1.
               - **Stop Loss**: ATR-based dynamic floor (1.5x ATR).
            """)

    with tabs[1]:
        st.header("🚀 Strategy & Content Hub")
        
        # Row 1: Analytics
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📊 Sectoral Performance")
            from stock_hub.logic_handler import fetch_sector_performance
            sector_df = fetch_sector_performance()
            if not sector_df.empty:
                st.bar_chart(sector_df.set_index("Sector"))
                st.markdown("> **Basis**: Daily Pct Change.")
            else:
                st.info("Sector telemetry pending.")
        
        with col2:
            st.subheader("🔥 Volume Sentiment (Trending)")
            from stock_hub.logic_handler import fetch_trending_tickers
            trend_df = fetch_trending_tickers()
            if not trend_df.empty:
                # Color coding: Green for Bullish, Red for Bearish
                # We assume Trend contains 'Bullish' or 'Bearish'
                import plotly.express as px
                # Add a dummy color column
                trend_df['Color'] = trend_df['Change_Pct'].apply(lambda x: 'Positive' if x >= 0 else 'Negative')
                fig = px.bar(trend_df, x='Ticker', y='Volume', color='Color',
                             color_discrete_map={'Positive': '#228B22', 'Negative': '#DC143C'},
                             height=300)
                fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("> **Note**: Green = Bullish Momentum | Red = Bearish Rotation.")
            else:
                st.info("Trending data pending research cycle.")

        st.divider()
        
        st.divider()
        
        # Row 2: Controls
        st.subheader("🔗 Content Automation")
        c1, c2 = st.columns(2)
        from stock_hub.logic_handler import generate_linkedin_content
        with c1:
            if st.button("🚀 Gen Market Insight Post"):
                with st.spinner("Drafting Insight..."):
                    st.session_state.post1 = generate_linkedin_content("market")
        with c2:
            if st.button("📚 Gen MF Educational Post"):
                with st.spinner("Drafting Education..."):
                    st.session_state.post2 = generate_linkedin_content("mf")

        # Row 3: Output (Wide Container for Mobile Compatibility)
        if 'post1' in st.session_state or 'post2' in st.session_state:
            st.divider()
            st.subheader("📝 Strategic Content Window")
            st.info("💡 **Mobile Tip**: Use the 📋 icon on the top-right of the boxes below to copy contents instantly.")
            
            # We use columns for side-by-side on desktop, which stacks on mobile
            out_col1, out_col2 = st.columns(2)
            
            if 'post1' in st.session_state:
                with out_col1:
                    st.markdown("#### 🚀 Tactical Market Insight")
                    with st.container(height=400, border=True):
                        st.code(st.session_state.post1, language="markdown")
                    st.caption("Optimized for Prime O-L Sentiment")
            
            if 'post2' in st.session_state:
                with out_col2:
                    st.markdown("#### 📚 Educational Series")
                    with st.container(height=400, border=True):
                        st.code(st.session_state.post2, language="markdown")
                    st.caption("Optimized for Education Pivot")

if __name__ == "__main__":
    main()