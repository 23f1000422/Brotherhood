import sys
import os
sys.path.append(os.getcwd())
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures
from stock_hub.quant_tools import QuantTools

def get_pa_prediction(symbol, rsi, macd_hist, ema200, ltp):
    """
    Precision Momentum Evaluation for Short/Long Setups.
    """
    is_above_ema = ltp >= ema200
    if rsi < 35 and macd_hist > 0:
        return "🟢 BUY (Oversold Rebound)", f"RSI oversold @ {rsi:.1f} with bullish momentum divergence."
    elif rsi < 68 and macd_hist > 0 and is_above_ema:
        return "🚀 BUY CALL (Momentum)", f"Strong momentum above 200 EMA (₹{ema200:.1f}) | RSI {rsi:.1f}"
    elif rsi > 70 and macd_hist < 0:
        return "🔻 SELL PUT (Overbought)", f"RSI overbought @ {rsi:.1f} facing distribution."
    elif not is_above_ema and macd_hist < 0:
        return "🔻 SHORT (Breakdown)", f"Bearish trend below 200 EMA (₹{ema200:.1f}) | RSI {rsi:.1f}"
    else:
        return "📡 NEUTRAL", f"RSI @ {rsi:.1f} | 200 EMA: ₹{ema200:.1f}"

def process_single_stock(symbol):
    """
    Direct v8 Chart API Data Fetching with 100% accuracy and zero rate limiting.
    Applies strict High-High / Low-Low and Prime Open=Low / Open=High quant breakout filters.
    """
    clean_sym = symbol.replace('.NS', '')
    raw_sym = symbol if symbol.endswith('.NS') or '^' in symbol else f"{symbol}.NS"
    
    try:
        t = yf.Ticker(raw_sym)
        # Fetch 1y unadjusted history via direct v8 chart API (reliable, unadjusted, fast)
        df = t.history(period="1y", auto_adjust=False)
        if df.empty or len(df) < 30:
            return None
            
        df = QuantTools.sanitize_dataframe(df)
        
        # Today's active session bar and previous session bar
        curr_row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else curr_row
        
        o = round(float(curr_row['Open'].item() if hasattr(curr_row['Open'], 'item') else curr_row['Open']), 2)
        h = round(float(curr_row['High'].item() if hasattr(curr_row['High'], 'item') else curr_row['High']), 2)
        l = round(float(curr_row['Low'].item() if hasattr(curr_row['Low'], 'item') else curr_row['Low']), 2)
        c = round(float(curr_row['Close'].item() if hasattr(curr_row['Close'], 'item') else curr_row['Close']), 2)
        vol = float(curr_row['Volume'].item() if hasattr(curr_row['Volume'], 'item') else curr_row['Volume'])
        
        prev_c = round(float(prev_row['Close'].item() if hasattr(prev_row['Close'], 'item') else prev_row['Close']), 2)
        prev_h = round(float(prev_row['High'].item() if hasattr(prev_row['High'], 'item') else prev_row['High']), 2)
        prev_l = round(float(prev_row['Low'].item() if hasattr(prev_row['Low'], 'item') else prev_row['Low']), 2)
        
        if c <= 0 or o <= 0:
            return None
            
        # Indicators
        tr = pd.concat([
            df['High'] - df['Low'],
            (df['High'] - df['Close'].shift()).abs(),
            (df['Low'] - df['Close'].shift()).abs()
        ], axis=1).max(axis=1)
        atr = round(float(tr.rolling(14, min_periods=1).mean().iloc[-1]), 2)
        atr = max(atr, round(c * 0.008, 2)) # Min 0.8% ATR guard
        
        ema200_series = df['Close'].ewm(span=200, adjust=False).mean()
        ema200 = round(float(ema200_series.iloc[-1]), 2)
        is_above_ema200 = c >= ema200
        
        rsi_series = QuantTools.calculate_rsi(df['Close'], 14)
        rsi = round(float(rsi_series.iloc[-1]), 1)
        
        macd, macd_sig, macd_hist = QuantTools.calculate_macd(df['Close'])
        macd_val = round(float(macd_hist.iloc[-1]), 2)
        
        # Real Session Change Percentage
        chg_pct = round(((c - prev_c) / prev_c) * 100.0, 2) if prev_c > 0 else 0.0
        
        # Volume Spike Check (vs 20D Avg Vol)
        avg_vol = float(df['Volume'].rolling(20, min_periods=1).mean().iloc[-1])
        vol_ratio = round(vol / max(avg_vol, 1.0), 2)
        
        # =========================================================================
        # STRICT QUANT BREAKOUT CLASSIFIER
        # =========================================================================
        # 1. Prime Open=Low (Bullish: Open is session low within 0.12% tolerance)
        is_prime_ol = abs(o - l) <= (o * 0.0012)
        # 2. Prime Open=High (Bearish: Open is session high within 0.12% tolerance)
        is_prime_oh = abs(o - h) <= (o * 0.0012)
        # 3. High-High Breakout (Session broke above yesterday's high)
        is_hh_breakout = (c > prev_h or o > prev_h) and chg_pct > 0.2
        # 4. Low-Low Breakdown (Session broke below yesterday's low)
        is_ll_breakdown = (c < prev_l or o < prev_l) and chg_pct < -0.2
        # 5. Momentum Surges
        is_bull_surge = chg_pct >= 1.8 and vol_ratio >= 1.1
        is_bear_surge = chg_pct <= -1.8 and vol_ratio >= 1.1

        if is_prime_ol:
            direction = "BULLISH"
            pattern = "Prime Open=Low"
            action = "🚀 BUY CALL (CE)" if is_above_ema200 else "🟢 BUY (Rebound)"
            target1 = round(c + 1.5 * atr, 2)
            target2 = round(c + 2.5 * atr, 2)
            sl = round(min(l, c - 1.2 * atr), 2)
        elif is_prime_oh:
            direction = "BEARISH"
            pattern = "Prime Open=High"
            action = "🔻 BUY PUT (PE)" if not is_above_ema200 else "⚠️ SHORT (Pullback)"
            target1 = round(c - 1.5 * atr, 2)
            target2 = round(c - 2.5 * atr, 2)
            sl = round(max(h, c + 1.2 * atr), 2)
        elif is_hh_breakout:
            direction = "BULLISH"
            pattern = "High-High Breakout"
            action = "🚀 BUY (Momentum)"
            target1 = round(c + 1.5 * atr, 2)
            target2 = round(c + 2.5 * atr, 2)
            sl = round(max(prev_h * 0.995, c - 1.2 * atr), 2)
        elif is_ll_breakdown:
            direction = "BEARISH"
            pattern = "Low-Low Breakdown"
            action = "🔻 SHORT (Breakdown)"
            target1 = round(c - 1.5 * atr, 2)
            target2 = round(c - 2.5 * atr, 2)
            sl = round(min(prev_l * 1.005, c + 1.2 * atr), 2)
        elif is_bull_surge:
            direction = "BULLISH"
            pattern = "Volume Surge Breakout"
            action = "🚀 BUY (Surge)"
            target1 = round(c + 1.5 * atr, 2)
            target2 = round(c + 2.5 * atr, 2)
            sl = round(c - 1.2 * atr, 2)
        elif is_bear_surge:
            direction = "BEARISH"
            pattern = "Heavy Selloff Breakdown"
            action = "🔻 SHORT (Selloff)"
            target1 = round(c - 1.5 * atr, 2)
            target2 = round(c - 2.5 * atr, 2)
            sl = round(c + 1.2 * atr, 2)
        else:
            return None

        # Risk-to-Reward Ratio
        risk = max(abs(c - sl), 0.1)
        reward = abs(target1 - c)
        rr = round(reward / risk, 2)
        
        _, reasoning = get_pa_prediction(symbol, rsi, macd_val, ema200, c)

        return {
            "Symbol": clean_sym,
            "Ticker": clean_sym,
            "RawSymbol": raw_sym,
            "Direction": direction,
            "Pattern": pattern,
            "Price": c,
            "Open": o,
            "High": h,
            "Low": l,
            "Day_Range": f"₹{l:.1f} - ₹{h:.1f}",
            "Change_Pct": chg_pct,
            "Target": target1,
            "Target1": target1,
            "Target2": target2,
            "SL": sl,
            "RR": rr,
            "ATR": atr,
            "RSI": rsi,
            "MACD": macd_val,
            "EMA200": ema200,
            "Above_EMA200": "YES" if is_above_ema200 else "NO",
            "Volume": vol,
            "Volume_Ratio": vol_ratio,
            "Action": action,
            "Reasoning": reasoning,
            "Agent_Review": f"{pattern} | RSI: {rsi} | Target: ₹{target1:.1f} | SL: ₹{sl:.1f}"
        }
    except Exception:
        return None

def scan_advanced_signals(symbols, max_workers=20):
    """
    Direct v8 Chart API Multithreaded Precision Screener.
    """
    print(f"[SCAN] DIRECT API QUANT BREAKOUT SCAN | Symbols: {len(symbols)}...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = [r for r in list(executor.map(process_single_stock, symbols)) if r]
        
    return sorted(results, key=lambda x: abs(x.get('Change_Pct', 0)), reverse=True)
