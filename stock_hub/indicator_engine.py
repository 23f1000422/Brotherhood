import sys
import os
sys.path.append(os.getcwd())
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures

def calculate_rsi(prices, period=14):
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss if loss.all() else 0
    return 100 - (100 / (1 + rs))

def calculate_ema(prices, period=200):
    return prices.ewm(span=period, adjust=False).mean()

def calculate_macd(prices, slow=26, fast=12, signal=9):
    exp1 = prices.ewm(span=fast, adjust=False).mean()
    exp2 = prices.ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    return macd, signal_line

def get_pa_prediction(symbol, data):
    """
    RSI-based price action prediction.
    RSI < 40: Buy
    RSI > 70: Sell
    Otherwise: Neutral
    """
    try:
        rsi_vals = calculate_rsi(data)
        curr_rsi = float(rsi_vals.iloc[-1])
        
        macd, signal = calculate_macd(data)
        curr_macd = float(macd.iloc[-1])
        curr_sig = float(signal.iloc[-1])
        
        if curr_rsi < 40:
            prediction = "🟢 BUY (Oversold)"
        elif curr_rsi > 70:
            prediction = "SELL (Overbought)"
        else:
            prediction = "NEUTRAL"
            
        reasoning = f"RSI @ {curr_rsi:.1f}. MACD is {'Bullish' if curr_macd > curr_sig else 'Bearish'}."
        return prediction, reasoning
    except:
        return "N/A", "Technical data unavailable."

def scan_advanced_signals(symbols):
    """
    Scans for technical signals and implements the Prime O-L Momentum (Open=Low/High).
    """
    print(f"[SCAN] PRIME O-L MOMENTUM SCAN | Nifty 100 | Symbols: {len(symbols)}...")
    
    def process_symbol(symbol):
        try:
            # period="5d" to handle weekend/Friday gaps
            df = yf.download(symbol, period="5d", interval="1d", progress=False)
            if df.empty: return None
            
            # Using latest session (Friday if today is Saturday)
            last_row = df.iloc[-1]
            o, h, l, c = last_row['Open'].item(), last_row['High'].item(), last_row['Low'].item(), last_row['Close'].item()
            
            # RAJ BREAKOUT LOGIC
            # Bullish: Open == Low
            # Bearish: Open == High
            # Float comparison with small tolerance
            is_bullish = abs(o - l) < (o * 0.0005)
            is_bearish = abs(o - h) < (o * 0.0005)
            
            if not (is_bullish or is_bearish):
                return None
                
            trend = "Bullish (Open=Low)" if is_bullish else "Bearish (Open=High)"
            high_open_pct = round(((h - o) / o) * 100, 2)
            
            prediction, reasoning = get_pa_prediction(symbol, df['Close'])
            
            # EMA 200
            ema200 = calculate_ema(df['Close'], 200).iloc[-1]
            is_above_ema200 = c > ema200
            
            # Additional DB mapping metrics
            prev_c = df.iloc[-2]['Close'].item() if len(df) > 1 else c
            change_pct = round(((c - prev_c) / prev_c) * 100, 2) if prev_c else 0.0
            vol = float(last_row['Volume'].item()) if 'Volume' in last_row else 0.0
            
            return {
                "Symbol": symbol,
                "Open": round(o, 2),
                "High": round(h, 2),
                "Low": round(l, 2),
                "Close": round(c, 2),
                "Price": round(c, 2),
                "Volume": vol,
                "Change_Pct": change_pct,
                "EMA200": round(ema200, 2),
                "Above_EMA200": is_above_ema200,
                "High_Open_Pct": high_open_pct,
                "Trend": trend,
                "PA_Prediction": prediction,
                "Reasoning": reasoning
            }
        except: return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor:
        results = [r for r in list(executor.map(process_symbol, symbols)) if r]
        
    return sorted(results, key=lambda x: abs(x['High_Open_Pct']), reverse=True)
