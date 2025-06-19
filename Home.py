import streamlit as st

st.set_page_config(page_title="Nifty Screener", layout="wide")
st.title("📊 Welcome to Nifty 50 Screener")
st.markdown("""
This multi-page Streamlit app lets you explore:
- **Daily High-High/Low-Low Breakouts**
- Future strategies like moving averages, RSI, or trend reversal scans

Use the sidebar to switch pages.
""")