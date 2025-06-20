import streamlit as st
import pandas as pd
import os
import subprocess

st.set_page_config(page_title="📈 Nifty 50 Screener", layout="centered")
st.title("📊 Nifty 50 Gap Breakout Report Viewer")

# 🔍 Find latest CSV
data_dir = "data"
files = sorted(os.listdir(data_dir), reverse=True)
if files:
    selected = st.selectbox("Choose a date", files)
    df = pd.read_csv(os.path.join(data_dir, selected))

    gap_ups = df[df["Status"] == "Gap Up Breakout"]
    gap_downs = df[df["Status"] == "Gap Down Breakdown"]

    st.write("### 🚀 Gap Ups")
    st.dataframe(gap_ups.reset_index(drop=True))

    st.write("### 📉 Gap Downs")
    st.dataframe(gap_downs.reset_index(drop=True))
else:
    st.info("No data files found yet.")

# 💥 Optional manual WhatsApp trigger
st.divider()
if st.button("📤 Send WhatsApp Now"):
    subprocess.run(["python", "send_gap_report.py"])
    st.success("Message sent via WhatsApp!")