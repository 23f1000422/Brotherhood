import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import pytz
from utils.stock_utils import fetch_live_prices, NIFTY_50_SYMBOLS, fetch_stock_data
from utils.ai_agent import get_ai_forecast
import yfinance as yf

st.set_page_config(page_title="📈 Nifty 50 Screener", layout="wide")
st.title("📊 Nifty 50 Gap Breakout & Live Tracker")

# Ensure data directory exists
if not os.path.exists("data"):
    os.makedirs("data")

# Tabs for different modes
tab1, tab2, tab3 = st.tabs(["🔴 Live Tracker", "🤖 forecast_nifty", "₿ forcast_crypto"])

with tab1:
    st.markdown("### ⏱️ Live Market Trend (30s Updates)")
    st.info("Tracks real-time Nifty 50 trends. Stocks that cross their Open price (whipsaw) are removed.")

    # Link to latest report
    data_files = sorted([f for f in os.listdir("data") if f.endswith(".csv")], reverse=True)
    if data_files:
        if st.button("📊 View Latest 9:25 AM Report"):
            latest_file = data_files[0]
            df_latest = pd.read_csv(os.path.join("data", latest_file))
            st.markdown(f"#### 📅 Report: {latest_file.split('_')[1].replace('.csv', '')}")
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🚀 Strong Stocks")
                st.dataframe(df_latest[df_latest["Status"] == "High"], use_container_width=True)
            with col_b:
                st.subheader("📉 Weak Stocks")
                st.dataframe(df_latest[df_latest["Status"] == "Low"], use_container_width=True)
            st.divider()

    # Session State Initialization
    if "tracking" not in st.session_state:
        st.session_state.tracking = False
    if "saved_today" not in st.session_state:
        st.session_state.saved_today = False
    if "blacklist" not in st.session_state:
        st.session_state.blacklist = set()
    if "open_prices" not in st.session_state:
        st.session_state.open_prices = {}
    if "valid_status" not in st.session_state:
        st.session_state.valid_status = {}

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        start_tracking = st.button("▶️ Start Tracking")
    with col_btn2:
        stop_tracking = st.button("⏹️ Stop")

    if start_tracking:
        st.session_state.tracking = True
        st.session_state.blacklist = set() 
        st.session_state.valid_status = {} 
        st.session_state.saved_today = False 
        with st.spinner("Fetching Open Prices..."):
            prices = fetch_live_prices(NIFTY_50_SYMBOLS)
            st.session_state.open_prices = prices.to_dict()
            if prices.empty:
                st.error("⚠️ Failed to fetch Open prices.")
            else:
                st.success(f"✅ Initialized Tracking for {len(prices)} stocks.")

    if stop_tracking:
        st.session_state.tracking = False

    # UI Placeholders
    placeholder_high = st.empty()
    placeholder_low = st.empty()
    status_text = st.empty()

    if st.session_state.tracking:
        while True:
            now = datetime.now(pytz.timezone("Asia/Kolkata"))
            current_time = now.strftime("%H:%M:%S")
            
            live_prices = fetch_live_prices(NIFTY_50_SYMBOLS)
            status_text.text(f"Last Update: {current_time} | Tracking Active ({len(live_prices)} stocks)")

            if not live_prices.empty:
                strong_stocks = []
                weak_stocks = []

                for sym, current_price in live_prices.items():
                    if sym not in st.session_state.open_prices:
                        continue
                        
                    open_price = st.session_state.open_prices[sym]
                    
                    if sym not in st.session_state.valid_status:
                        if current_price > open_price:
                            st.session_state.valid_status[sym] = "High"
                        elif current_price < open_price:
                            st.session_state.valid_status[sym] = "Low"
                        else:
                            continue

                    status = st.session_state.valid_status[sym]
                    if status == "Choppy":
                        continue

                    if (status == "High" and current_price < open_price) or \
                       (status == "Low" and current_price > open_price):
                        st.session_state.valid_status[sym] = "Choppy"
                        continue
                    
                    if status == "High":
                        strong_stocks.append({
                            "Symbol": sym, "Open": open_price, "Current": current_price, 
                            "Change %": round((current_price - open_price) / open_price * 100, 2)
                        })
                    elif status == "Low":
                        weak_stocks.append({
                            "Symbol": sym, "Open": open_price, "Current": current_price, 
                            "Change %": round((open_price - current_price) / open_price * 100, 2)
                        }) 

                df_strong = pd.DataFrame(strong_stocks)
                df_weak = pd.DataFrame(weak_stocks)
                
                with placeholder_high.container():
                    st.write("### 🚀 Strong Stocks (Above Open)")
                    if not df_strong.empty:
                        st.dataframe(df_strong.sort_values("Change %", ascending=False), height=300)
                    else:
                        st.write("No stocks strictly above open.")

                with placeholder_low.container():
                    st.write("### 📉 Weak Stocks (Below Open)")
                    if not df_weak.empty:
                        st.dataframe(df_weak.sort_values("Change %", ascending=False), height=300)
                    else:
                        st.write("No stocks strictly below open.")

            # Auto-Save at exactly 9:25 AM
            if now.hour == 9 and now.minute == 25 and not st.session_state.saved_today:
                final_results = []
                for sym, current in live_prices.items():
                    if sym in st.session_state.open_prices:
                        open_p = st.session_state.open_prices[sym]
                        status = st.session_state.valid_status.get(sym, "Choppy")
                        if status != "Choppy":
                           final_results.append({
                               "Symbol": sym, "Open": open_p, "Final": current,
                               "Change %": round((current - open_p) / open_p * 100, 2) if status == "High" else round((open_p - current) / open_p * 100, 2),
                               "Status": status
                           })
                if final_results:
                    filename = f"data/report_{now.strftime('%Y-%m-%d')}.csv"
                    pd.DataFrame(final_results).to_csv(filename, index=False)
                    st.session_state.saved_today = True
                    st.session_state.tracking = False 
                    break
            time.sleep(30)

# --- TAB 2: forecast_nifty ---
with tab2:
    st.markdown("### 🤖 AI Nifty Forecasting (Top 50)")
    selected_stock = st.selectbox("Choose a Stock", NIFTY_50_SYMBOLS)
    if st.button(f"🔍 AI Forecast {selected_stock}"):
        with st.spinner("Analyzing..."):
            hist = fetch_stock_data(selected_stock, period="60d", interval="1d")
            if not hist.empty:
                result = get_ai_forecast(selected_stock, hist)
                st.markdown("#### 🤖 AI Analyst Response")
                st.write(result)
            else:
                st.error("Data fetch failed.")

# --- TAB 3: forcast_crypto ---
with tab3:
    st.markdown("### ₿ AI Crypto Forecasting")
    cryptos = ["BTC-USD", "ETH-USD", "SOL-USD", "BNB-USD", "XRP-USD", "DOGE-USD"]
    selected_crypto = st.selectbox("Choose a Crypto", cryptos)
    if st.button(f"🔍 AI Forecast {selected_crypto}"):
        with st.spinner("Analyzing..."):
            hist_crypto = fetch_stock_data(selected_crypto, period="60d", interval="1d")
            if not hist_crypto.empty:
                result_crypto = get_ai_forecast(selected_crypto, hist_crypto)
                st.markdown("#### 🤖 AI Analyst Response")
                st.write(result_crypto)
            else:
                st.error("Data fetch failed.")