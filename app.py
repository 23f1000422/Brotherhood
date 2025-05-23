import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time
import requests

# Updated Nifty 50 symbols with verified Yahoo Finance tickers
NIFTY_50_SYMBOLS = [
    'ADANIENT.NS', 'ADANIPORTS.NS', 'APOLLOHOSP.NS', 'ASIANPAINT.NS', 'AXISBANK.NS',
    'BAJAJ-AUTO.NS', 'BAJFINANCE.NS', 'BAJAJFINSV.NS', 'BHARTIARTL.NS', 'BPCL.NS',
    'BRITANNIA.NS', 'CIPLA.NS', 'COALINDIA.NS', 'DIVISLAB.NS', 'DRREDDY.NS',
    'EICHERMOT.NS', 'GRASIM.NS', 'HCLTECH.NS', 'HDFCBANK.NS', 'HDFCLIFE.NS',
    'HEROMOTOCO.NS', 'HINDALCO.NS', 'HINDUNILVR.NS', 'ICICIBANK.NS', 'ITC.NS',
    'INDUSINDBK.NS', 'INFY.NS', 'JSWSTEEL.NS', 'KOTAKBANK.NS', 'LT.NS', 'LTIM.NS',
    'M&M.NS', 'MARUTI.NS', 'NESTLEIND.NS', 'NTPC.NS', 'ONGC.NS', 'POWERGRID.NS',
    'RELIANCE.NS', 'SBILIFE.NS', 'SBIN.NS', 'SHRIRAMFIN.NS', 'SUNPHARMA.NS',
    'TCS.NS', 'TATACONSUM.NS', 'TATAMOTORS.NS', 'TATASTEEL.NS', 'TECHM.NS',
    'TITAN.NS', 'ULTRACEMCO.NS', 'WIPRO.NS'
]

def fetch_stock_data(symbol, max_retries=3):
    """Fetch data with retries and error handling"""
    for attempt in range(max_retries):
        try:
            data = yf.download(
                tickers=symbol,
                period="1d",
                interval="5m",
                progress=False,
                group_by='ticker',
                timeout=10
            )
            if not data.empty:
                return data
        except (requests.exceptions.HTTPError, KeyError) as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            st.error(f"Failed to fetch {symbol}: {str(e)}")
    return pd.DataFrame()

def analyze_stocks():
    """Analyze all stocks with error handling"""
    results = []
    
    for symbol in NIFTY_50_SYMBOLS:
        data = fetch_stock_data(symbol)
        if data.empty:
            continue
            
        try:
            df = data[symbol]
            open_price = df['Open'].iloc[0]
            high = df['High'].max()
            low = df['Low'].min()
            last_price = df['Close'].iloc[-1]
            pct_change = ((last_price - open_price) / open_price) * 100

            # Add 0.5% tolerance for floating point precision
            status = ""
            if (high > open_price) and (last_price >= high * 0.995):
                status = "High-High"
            elif (low < open_price) and (last_price <= low * 1.005):
                status = "Low-Low"

            results.append({
                "Symbol": symbol.replace(".NS", ""),
                "Open": open_price,
                "High": high,
                "Low": low,
                "LTP": last_price,
                "% Change": pct_change,
                "Status": status
            })
        except KeyError:
            continue
            
        time.sleep(1)  # Rate limiting
    
    return pd.DataFrame(results)

def main():
    st.title("🇮🇳 Nifty 50 Stock Screener")
    st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with st.spinner("Analyzing Nifty 50 stocks..."):
        df = analyze_stocks()
    
    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 High-High Stocks")
            high_df = df[df["Status"] == "High-High"].sort_values("% Change", ascending=False)
            st.dataframe(
                high_df.style.format({"Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "LTP": "{:.2f}", "% Change": "{:.2f}%"}),
                height=400
            )
        
        with col2:
            st.subheader("📉 Low-Low Stocks")
            low_df = df[df["Status"] == "Low-Low"].sort_values("% Change", ascending=True)
            st.dataframe(
                low_df.style.format({"Open": "{:.2f}", "High": "{:.2f}", "Low": "{:.2f}", "LTP": "{:.2f}", "% Change": "{:.2f}%"}),
                height=400
            )
        
        st.subheader("All Nifty 50 Stocks")
        st.dataframe(
            df.sort_values("% Change", ascending=False).style.format({"% Change": "{:.2f}%"}),
            height=600
        )
    else:
        st.error("Failed to fetch data. Possible solutions:")
        st.markdown("""
        1. Check internet connection
        2. Refresh the page
        3. Try again after 2-3 minutes
        """)

if __name__ == "__main__":
    main()
