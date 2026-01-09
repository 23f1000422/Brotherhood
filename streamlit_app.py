import streamlit as st
import pandas as pd
import os
import subprocess
import time
from datetime import datetime
import pytz
from utils.stock_utils import fetch_live_prices, NIFTY_50_SYMBOLS, send_email

st.set_page_config(page_title="📈 Nifty 50 Screener", layout="wide")
st.title("📊 Nifty 50 Gap Breakout & Live Tracker")

# Tabs for different modes
# Removed Tab 2 as per cleanup
st.markdown("### 🔴 Live 9:15-9:25 Tracker")

st.markdown("### ⏱️ Live Market Trend (30s Updates)")
st.info("Tracks real-time Nifty 50 trends. Stocks that cross their Open price (whipsaw) are removed to ensure only strong trends are shown.")

# Session State Initialization
if "tracking" not in st.session_state:
    st.session_state.tracking = False
if "data_history" not in st.session_state:
    st.session_state.data_history = pd.DataFrame(columns=["Symbol", "Open"])
if "blacklist" not in st.session_state:
    st.session_state.blacklist = set()
if "open_prices" not in st.session_state:
    st.session_state.open_prices = {}
if "valid_status" not in st.session_state:
    st.session_state.valid_status = {}

col1, col2 = st.columns([1, 4])
with col1:
    start_btn = st.button("▶️ Start Tracking")
with col2:
    stop_btn = st.button("⏹️ Stop")

if start_btn:
    st.session_state.tracking = True
    st.session_state.blacklist = set() # Reset blacklist on new run
    st.session_state.valid_status = {} # Reset valid status
    st.session_state.data_history = pd.DataFrame(columns=["Symbol", "Open"]) # Reset history
    with st.spinner("Fetching Open Prices..."):
        # Initial Fetch for Open Prices
        prices = fetch_live_prices(NIFTY_50_SYMBOLS)
        st.session_state.open_prices = prices.to_dict()
        
        # Initialize history
        initial_data = []
        for sym, price in st.session_state.open_prices.items():
            initial_data.append({"Symbol": sym, "Open": price})
        st.session_state.data_history = pd.DataFrame(initial_data)
        
        if prices.empty:
            st.error("⚠️ Failed to fetch Open prices. Check connection/market status.")
        else:
            st.success(f"✅ Initialized Tracking for {len(prices)} stocks.")

if stop_btn:
    st.session_state.tracking = False
    st.success("Stopped Tracking.")

# Live Loop
placeholder_high = st.empty()
placeholder_low = st.empty()
status_text = st.empty()

if st.session_state.tracking:
    while True:
        now = datetime.now(pytz.timezone("Asia/Kolkata"))
        current_time = now.strftime("%H:%M:%S")
        
        # 1. Fetch Current Prices
        live_prices = fetch_live_prices(NIFTY_50_SYMBOLS)
        
        # Update status TEXT after fetching so 'live_prices' is defined
        status_text.text(f"Last Update: {current_time} | Tracking Active (Updated: {len(live_prices)}/{len(st.session_state.open_prices)})")

        # 2. Update History & Check Whipsaws
        if not live_prices.empty:
            # Add new column for this timestamp
            col_name = f"{current_time}"
            
            strong_stocks = []
            weak_stocks = []

            for sym, current_price in live_prices.items():
                if sym not in st.session_state.open_prices:
                    continue
                    
                open_price = st.session_state.open_prices[sym]
                
                if sym not in st.session_state.valid_status:
                    # Initialize status on first significant move
                    if current_price > open_price:
                        st.session_state.valid_status[sym] = "High"
                    elif current_price < open_price:
                        st.session_state.valid_status[sym] = "Low"
                    else:
                        continue # Equal to open, wait for direction

                status = st.session_state.valid_status[sym]

                # If already marked choppy, skip
                if status == "Choppy":
                    continue

                # Check for Whipsaw (Crossing the Open Price)
                if status == "High" and current_price < open_price:
                    st.session_state.valid_status[sym] = "Choppy" # Mark as choppy forever
                    continue
                elif status == "Low" and current_price > open_price:
                    st.session_state.valid_status[sym] = "Choppy" # Mark as choppy forever
                    continue
                
                # Valid Status - Add to lists
                if status == "High":
                    strong_stocks.append({
                        "Symbol": sym, 
                        "Open": open_price, 
                        "Current": current_price, 
                        "Change %": round((current_price - open_price) / open_price * 100, 2)
                    })
                elif status == "Low":
                    weak_stocks.append({
                        "Symbol": sym, 
                        "Open": open_price, 
                        "Current": current_price, 
                        "Change %": round((open_price - current_price) / open_price * 100, 2)
                    }) 

            # DataFrame Construction
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

# --- Reports Removed (Cleanup) ---

            # Stop Condition & Email Trigger
            if now.hour == 9 and now.minute >= 25:
                st.session_state.tracking = False
                status_text.text("Market Open Tracking Ended (9:25 AM). Sending Email...")
                
                # Prepare final dataframes for email
                # We need to rebuild them one last time or use the displayed ones
                # Ideally, we should accumulate strong/weak stocks in session state or just re-calculate from current state
                
                final_strong = []
                final_weak = []
                
                # Re-evaluate all stocks one last time for the report
                if st.session_state.open_prices:
                    prices = fetch_live_prices(NIFTY_50_SYMBOLS)
                    for sym, current in prices.items():
                        if sym not in st.session_state.open_prices: continue
                        
                        open_p = st.session_state.open_prices[sym]
                        if sym in st.session_state.valid_status:
                            status = st.session_state.valid_status[sym]
                            if status == "High" and current > open_p:
                                final_strong.append({
                                    "Symbol": sym, "Open": open_p, "Current": current,
                                    "Change %": round((current - open_p) / open_p * 100, 2)
                                })
                            elif status == "Low" and current < open_p:
                                final_weak.append({
                                    "Symbol": sym, "Open": open_p, "Current": current,
                                    "Change %": round((open_p - current) / open_p * 100, 2)
                                })

                df_s_final = pd.DataFrame(final_strong)
                df_w_final = pd.DataFrame(final_weak)
                
                send_email(df_s_final, df_w_final)
                st.success("Tracking Ended & Email Sent.")
                break
            
            # Sleep 30s
            time.sleep(30)