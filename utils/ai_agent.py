import pandas as pd
import pandas_ta as ta
from huggingface_hub import InferenceClient
import streamlit as st
from datetime import datetime
import yfinance as yf

# Model selection for reasoning
MODEL_ID = "Qwen/Qwen2.5-7B-Instruct"

def get_ai_forecast(symbol, df):
    """
    Analyzes stock data, signals, and news to provide a forecast.
    """
    try:
        # 1. Calculate Technical Indicators & Signals
        data = df.copy()
        
        # EMA Crossovers
        data.ta.ema(length=20, append=True)
        data.ta.ema(length=50, append=True)
        data.ta.rsi(length=14, append=True)
        data.ta.macd(append=True)
        
        # Generate Simple Buy/Sell Signals
        last_row = data.iloc[-1]
        prev_row = data.iloc[-2]
        
        signals = []
        if last_row['RSI_14'] < 30: signals.append("RSI Oversold (POTENTIAL BUY)")
        elif last_row['RSI_14'] > 70: signals.append("RSI Overbought (POTENTIAL SELL)")
        
        if prev_row['EMA_20'] < prev_row['EMA_50'] and last_row['EMA_20'] > last_row['EMA_50']:
            signals.append("Golden Cross - EMA 20 crossed above 50 (BULLISH BUY)")
        elif prev_row['EMA_20'] > prev_row['EMA_50'] and last_row['EMA_20'] < last_row['EMA_50']:
            signals.append("Death Cross - EMA 20 crossed below 50 (BEARISH SELL)")

        # 2. Fetch News
        news_summary = "No recent news found."
        try:
            ticker = yf.Ticker(symbol)
            news = ticker.news[:3]
            if news:
                news_summary = "\n".join([f"- {item['title']}" for item in news])
        except:
            pass

        # 3. Prepare Data Summary
        recent = data.tail(14).copy()
        recent['Date'] = recent.index.strftime('%Y-%m-%d')
        cols_to_round = ['Open', 'High', 'Low', 'Close', 'EMA_20', 'EMA_50', 'RSI_14']
        available_cols = [c for c in cols_to_round if c in recent.columns]
        recent[available_cols] = recent[available_cols].round(2)
        data_str = recent[['Date'] + available_cols].to_string(index=False)
        
        # 4. Construct the Prompt
        prompt = f"""
        You are an advanced AI Financial Strategist. 
        Analyze the following data for {symbol} and provide a precise forecast.
        
        TECHNICAL DATA (Last 14 Days):
        {data_str}
        
        DYNAMIC SIGNALS:
        {', '.join(signals) if signals else 'No immediate technical breakout signals.'}
        
        LATEST NEWS/SENTIMENT:
        {news_summary}
        
        TASK:
        1. Evaluate if the current momentum is Overextended or Healthy based on RSI and Price action.
        2. Correlate the News Sentiment with the Technical Trend.
        3. Predict a TARGET PRICE RANGE for the next 48 hours.
        4. Provide 'Buying Zone' and 'Selling Zone' based on Support/Resistance.
        
        FORMAT:
        - Sentiment: [Bullish/Bearish/Neutral]
        - Buying Zone: [Value range]
        - Selling Zone: [Value range]
        - Forecast Result: [Value] to [Value]
        - Strategy Reasoning: [Deep 3-4 sentence analysis]
        """

        if "HF_TOKEN" not in st.secrets:
            return "❌ HF_TOKEN not found. Add it to .streamlit/secrets.toml"
            
        client = InferenceClient(api_key=st.secrets["HF_TOKEN"])
        response = ""
        for message in client.chat_completion(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            stream=True,
        ):
            response += message.choices[0].delta.content
        return response

    except Exception as e:
        return f"❌ Error: {str(e)}"
