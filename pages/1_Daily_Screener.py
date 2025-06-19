import streamlit as st
import pandas as pd
from datetime import datetime
from utils.stock_utils import fetch_stock_data, analyze_stocks
st.set_page_config(page_title="Nifty Screener", layout="wide")

st.title("📅 Daily Ticker Screener")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

with st.spinner("Analyzing Nifty 50 daily candles..."):
    df = analyze_stocks()

def highlight_status(row):
    if row["Status"] == "Gap Up Breakout":
        return ['background-color: #e8ffe8'] * len(row)
    elif row["Status"] == "Gap Down Breakdown":
        return ['background-color: #ffe8e8'] * len(row)
    return [''] * len(row)

if not df.empty:
    df_styled = df.style.apply(highlight_status, axis=1)
    st.dataframe(df_styled, use_container_width=True)
else:
    st.warning("No breakout detected today based on open gaps.")
