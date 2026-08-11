import pandas as pd
import numpy as np
import math
from scipy.stats import norm

class QuantTools:
    @staticmethod
    def sanitize_dataframe(df):
        """
        Robustly flattens and standardizes yfinance DataFrames across all versions.
        Ensures columns are simple strings: ['Open', 'High', 'Low', 'Close', 'Volume'].
        """
        if df.empty:
            return df
        if isinstance(df.columns, pd.MultiIndex):
            # Inspect levels to locate the price metrics level
            found = False
            for lvl in range(df.columns.nlevels):
                vals = [str(x).strip().capitalize() for x in df.columns.get_level_values(lvl)]
                if 'Close' in vals or 'Open' in vals:
                    df.columns = vals
                    found = True
                    break
            if not found:
                df.columns = [str(x).strip().capitalize() for x in df.columns.get_level_values(0)]
        else:
            df.columns = [str(c).strip().capitalize() for c in df.columns]
            
        return df.loc[:, ~df.columns.duplicated()]

    @staticmethod
    def calculate_ema(df_or_series, period=200):
        series = df_or_series['Close'] if isinstance(df_or_series, pd.DataFrame) else df_or_series
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df_or_series, period=14):
        """
        Calculates Relative Strength Index (RSI) with zero-division safeguards.
        Supports both Series and DataFrame.
        """
        series = df_or_series['Close'] if isinstance(df_or_series, pd.DataFrame) else df_or_series
        if len(series) < 2:
            return pd.Series([50.0] * len(series), index=series.index)
            
        delta = series.diff()
        gain = delta.clip(lower=0.0)
        loss = -delta.clip(upper=0.0)
        
        # Exponential smoothing (Wilder's RSI)
        avg_gain = gain.ewm(alpha=1.0/period, min_periods=1, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0/period, min_periods=1, adjust=False).mean()
        
        # Zero-division safe RS calculation
        rs = np.where(avg_loss <= 1e-9, 
                      np.where(avg_gain > 1e-9, 1000.0, 1.0), 
                      avg_gain / np.maximum(avg_loss, 1e-9))
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
        # Explicit bounds clamp
        rsi = np.where(avg_loss <= 1e-9, np.where(avg_gain > 1e-9, 100.0, 50.0), rsi)
        rsi = np.where(avg_gain <= 1e-9, np.where(avg_loss > 1e-9, 0.0, 50.0), rsi)
        
        return pd.Series(rsi, index=series.index).fillna(50.0)

    @staticmethod
    def calculate_macd(df_or_series, slow=26, fast=12, signal=9):
        series = df_or_series['Close'] if isinstance(df_or_series, pd.DataFrame) else df_or_series
        exp1 = series.ewm(span=fast, adjust=False).mean()
        exp2 = series.ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        hist = macd - signal_line
        return macd, signal_line, hist

    @staticmethod
    def calculate_atr(df, period=14):
        df_clean = QuantTools.sanitize_dataframe(df.copy())
        high_low = df_clean['High'] - df_clean['Low']
        high_close = np.abs(df_clean['High'] - df_clean['Close'].shift())
        low_close = np.abs(df_clean['Low'] - df_clean['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period, min_periods=1).mean().fillna(method='bfill')

    @staticmethod
    def calculate_pivots(df):
        df_clean = QuantTools.sanitize_dataframe(df.copy())
        prev = df_clean.iloc[-2] if len(df_clean) > 1 else df_clean.iloc[-1]
        
        h = float(prev['High'].item() if hasattr(prev['High'], 'item') else prev['High'])
        l = float(prev['Low'].item() if hasattr(prev['Low'], 'item') else prev['Low'])
        c = float(prev['Close'].item() if hasattr(prev['Close'], 'item') else prev['Close'])
        
        p = (h + l + c) / 3.0
        s1 = (2.0 * p) - h
        s2 = p - (h - l)
        r1 = (2.0 * p) - l
        r2 = p + (h - l)
        return {
            "Pivot": round(p, 2),
            "S1": round(s1, 2),
            "S2": round(s2, 2),
            "R1": round(r1, 2),
            "R2": round(r2, 2)
        }

    @staticmethod
    def get_fibonacci_target(df, ratio=0.618, direction="BULLISH"):
        """
        Bidirectional Fibonacci target:
        - Bullish: High + (High - Low) * ratio
        - Bearish: Low - (High - Low) * ratio
        """
        df_clean = QuantTools.sanitize_dataframe(df.copy())
        high = float(df_clean['High'].max())
        low = float(df_clean['Low'].min())
        diff = max(high - low, 1e-4)
        
        if str(direction).upper() == "BEARISH":
            return round(low - (diff * ratio), 2)
        return round(high + (diff * ratio), 2)

    @staticmethod
    def calculate_dynamic_sl(ltp, atr, direction="BULLISH", multiplier=1.5):
        """
        Bidirectional dynamic stop loss:
        - Bullish: LTP - (1.5 * ATR)
        - Bearish: LTP + (1.5 * ATR)
        """
        sl_buffer = multiplier * float(atr)
        if str(direction).upper() == "BEARISH":
            return round(float(ltp) + sl_buffer, 2)
        return round(float(ltp) - sl_buffer, 2)

    @staticmethod
    def check_volume_spike(df, window=20, threshold=1.8):
        df_clean = QuantTools.sanitize_dataframe(df.copy())
        if len(df_clean) < 2: return False
        avg_vol = df_clean['Volume'].rolling(window=window, min_periods=1).mean().iloc[-1]
        curr_vol = df_clean['Volume'].iloc[-1]
        return float(curr_vol) > (threshold * float(avg_vol))

    # --- TRUE BLACK-SCHOLES OPTION GREEKS ENGINE ---
    @staticmethod
    def calculate_black_scholes_greeks(spot, strike, t_days=5, r=0.07, iv=0.20, option_type="CE"):
        """
        Calculates closed-form Black-Scholes Greeks: Delta, Gamma, Theta, Vega.
        t_days: Days to expiry
        r: Risk-free rate (7% default for India)
        iv: Implied volatility (e.g. 0.20 for 20%)
        """
        try:
            T = max(float(t_days) / 365.0, 1e-5)
            S = float(spot)
            K = float(strike)
            sigma = max(float(iv), 0.01)
            
            d1 = (np.log(S / K) + (r + 0.5 * (sigma ** 2)) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            # Premium
            if option_type.upper() == "CE":
                price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
                delta = norm.cdf(d1)
                theta = (- (S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r * T) * norm.cdf(d2)) / 365.0
            else: # PE
                price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
                delta = norm.cdf(d1) - 1.0
                theta = (- (S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) + r * K * np.exp(-r * T) * norm.cdf(-d2)) / 365.0
                
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            vega = (S * norm.pdf(d1) * np.sqrt(T)) / 100.0 # per 1% change in IV
            
            return {
                "premium": max(round(float(price), 2), 0.05),
                "delta": round(float(delta), 3),
                "gamma": round(float(gamma), 4),
                "theta": round(float(theta), 2),
                "vega": round(float(vega), 2),
                "iv_pct": round(sigma * 100, 1)
            }
        except Exception:
            return {
                "premium": 0.0,
                "delta": 0.5 if option_type.upper() == "CE" else -0.5,
                "gamma": 0.0,
                "theta": 0.0,
                "vega": 0.0,
                "iv_pct": 20.0
            }
