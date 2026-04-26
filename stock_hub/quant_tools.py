import pandas as pd
import numpy as np

class QuantTools:
    @staticmethod
    def calculate_ema(df, period):
        return df['Close'].ewm(span=period, adjust=False).mean()

    @staticmethod
    def calculate_rsi(df, period=14):
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    @staticmethod
    def calculate_macd(df, slow=26, fast=12, signal=9):
        exp1 = df['Close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['Close'].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        hist = macd - signal_line
        return macd, signal_line, hist

    @staticmethod
    def calculate_atr(df, period=14):
        high_low = df['High'] - df['Low']
        high_close = np.abs(df['High'] - df['Close'].shift())
        low_close = np.abs(df['Low'] - df['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()

    @staticmethod
    def calculate_pivots(df):
        # Using previous day (iloc[-2] if latest is today)
        prev = df.iloc[-2] if len(df) > 1 else df.iloc[-1]
        p = (prev['High'] + prev['Low'] + prev['Close']) / 3
        s1 = (2 * p) - prev['High']
        r1 = (2 * p) - prev['Low']
        return p, s1, r1

    @staticmethod
    def get_fibonacci_target(df, ratio=0.618):
        high = df['High'].max()
        low = df['Low'].min()
        diff = high - low
        target = high + (diff * ratio)
        return target

    @staticmethod
    def calculate_dynamic_sl(ltp, atr):
        return ltp - (1.5 * atr)

    @staticmethod
    def check_volume_spike(df):
        avg_vol = df['Volume'].rolling(window=20).mean().iloc[-1]
        curr_vol = df['Volume'].iloc[-1]
        return curr_vol > (2 * avg_vol)
