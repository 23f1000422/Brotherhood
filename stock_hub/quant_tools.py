import pandas as pd
import numpy as np
import math

# Resilient Scipy / Pure-Math Normal Distribution Fallback
try:
    from scipy.stats import norm
except Exception:
    class NormMathFallback:
        @staticmethod
        def cdf(x):
            if isinstance(x, (pd.Series, np.ndarray, list)):
                return np.array([0.5 * (1.0 + math.erf(float(v) / math.sqrt(2.0))) for v in x])
            return 0.5 * (1.0 + math.erf(float(x) / math.sqrt(2.0)))
        
        @staticmethod
        def pdf(x):
            if isinstance(x, (pd.Series, np.ndarray, list)):
                return np.array([(1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * float(v) * float(v)) for v in x])
            return (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * float(x) * float(x))
            
    norm = NormMathFallback()

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
            found = False
            for lvl in range(df.columns.nlevels):
                cols = df.columns.get_level_values(lvl)
                if any(c in ['Close', 'High', 'Low', 'Open', 'Volume'] for c in cols):
                    df.columns = cols
                    found = True
                    break
            if not found:
                df.columns = df.columns.get_level_values(0)
                
        # Drop duplicates and coerce numerics
        df = df.loc[:, ~df.columns.duplicated()].copy()
        for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
        df = df.bfill().ffill().dropna()
        return df

    @staticmethod
    def calculate_ema(series, span=200):
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def calculate_rsi(series, period=14):
        """
        Pure Vectorized Wilder's RSI with explicit zero-division guard.
        """
        delta = series.diff()
        gain = (delta.where(delta > 0, 0.0))
        loss = (-delta.where(delta < 0, 0.0))
        
        avg_gain = gain.ewm(alpha=1.0/period, min_periods=1, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1.0/period, min_periods=1, adjust=False).mean()
        
        rs = np.where(avg_loss <= 1e-9, 
                      np.where(avg_gain > 1e-9, 1000.0, 1.0), 
                      avg_gain / np.maximum(avg_loss, 1e-9))
        rsi = 100.0 - (100.0 / (1.0 + rs))
        
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
        return tr.rolling(window=period, min_periods=1).mean().bfill().fillna(0.0)

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
    def calculate_black_scholes_greeks(spot=None, strike=None, t_days=5, r=0.07, iv=0.20, option_type="CE", 
                                        S=None, K=None, T=None, sigma=None):
        """
        Analytical Black-Scholes Greeks Calculation with 100% resilient keyword flexibility.
        """
        try:
            S_val = float(spot if spot is not None else (S if S is not None else 100.0))
            K_val = float(strike if strike is not None else (K if K is not None else 100.0))
            
            if T is not None:
                T_val = float(T)
            else:
                T_val = max(float(t_days) / 365.0, 1.0 / 365.0)
                
            sigma_val = float(iv if iv is not None else (sigma if sigma is not None else 0.20))
            r_val = float(r if r is not None else 0.07)
            
            opt_type = str(option_type).upper()
            is_call = "C" in opt_type or "CALL" in opt_type
            
            if S_val <= 0 or K_val <= 0 or T_val <= 0 or sigma_val <= 0:
                return {
                    "premium": "₹10.00", "price": 10.0, "delta": 0.50, 
                    "gamma": 0.001, "theta": -0.5, "vega": 0.1, "iv_pct": round(sigma_val * 100, 1)
                }

            d1 = (math.log(S_val / K_val) + (r_val + 0.5 * sigma_val ** 2) * T_val) / (sigma_val * math.sqrt(T_val))
            d2 = d1 - sigma_val * math.sqrt(T_val)
            
            pdf_d1 = norm.pdf(d1)
            
            if is_call:
                price = S_val * norm.cdf(d1) - K_val * math.exp(-r_val * T_val) * norm.cdf(d2)
                delta = norm.cdf(d1)
                theta = (- (S_val * pdf_d1 * sigma_val) / (2 * math.sqrt(T_val)) 
                         - r_val * K_val * math.exp(-r_val * T_val) * norm.cdf(d2)) / 365.0
            else:
                price = K_val * math.exp(-r_val * T_val) * norm.cdf(-d2) - S_val * norm.cdf(-d1)
                delta = norm.cdf(d1) - 1.0
                theta = (- (S_val * pdf_d1 * sigma_val) / (2 * math.sqrt(T_val)) 
                         + r_val * K_val * math.exp(-r_val * T_val) * norm.cdf(-d2)) / 365.0
                         
            gamma = pdf_d1 / (S_val * sigma_val * math.sqrt(T_val))
            vega = (S_val * math.sqrt(T_val) * pdf_d1) / 100.0
            
            final_price = max(round(float(price), 2), 0.05)
            
            return {
                "premium": f"₹{final_price:.2f}",
                "price": final_price,
                "delta": round(float(delta), 4),
                "gamma": round(float(gamma), 6),
                "theta": round(float(theta), 4),
                "vega": round(float(vega), 4),
                "iv_pct": round(sigma_val * 100, 1)
            }
        except Exception:
            return {
                "premium": "₹10.00", "price": 10.0, "delta": 0.50, 
                "gamma": 0.001, "theta": -0.5, "vega": 0.1, "iv_pct": 20.0
            }
