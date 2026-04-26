import sys
import os
import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

sys.path.append(os.getcwd())

WEIGHTS_PATH = "data/model_weights.json"

class ForecastEngine:
    def __init__(self, mode="gemini"):
        load_dotenv()
        self.mode = mode
        self.weights = self._load_weights()
        
        
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            if api_key.startswith("AQ.") or api_key.startswith("ya29"):
                from google.oauth2.credentials import Credentials
                creds = Credentials(api_key)
                if "GOOGLE_API_KEY" in os.environ:
                    del os.environ["GOOGLE_API_KEY"]
                genai.configure(credentials=creds)
            else:
                genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-flash-lite-latest')
        else:
            self.model = None

    def _load_weights(self):
        if os.path.exists(WEIGHTS_PATH):
            try:
                with open(WEIGHTS_PATH, "r") as f:
                    return json.load(f)
            except: return {}
        return {}

    def _save_weights(self):
        os.makedirs(os.path.dirname(WEIGHTS_PATH), exist_ok=True)
        with open(WEIGHTS_PATH, "w") as f:
            json.dump(self.weights, f, indent=2)

    def train_on_error(self, symbol, predicted, actual):
        """
        Simulates 'backpropagation' by adjusting the bias for a symbol.
        New Bias = Old Bias + Learning Rate * (Error)
        """
        lr = 0.05
        error = (actual - predicted) / actual
        
        if symbol not in self.weights:
            self.weights[symbol] = {"bias": 1.0, "total_samples": 0}
            
        old_bias = self.weights[symbol]["bias"]
        new_bias = old_bias + (lr * error)
        
        self.weights[symbol]["bias"] = round(float(new_bias), 4)
        self.weights[symbol]["total_samples"] += 1
        self._save_weights()
        print(f"🧠 LEARNING [{symbol}] | New Bias: {new_bias:.4f} (Error: {error:.2%})")

    def get_forecast(self, symbol, data):
        """
        Predicts next periods and applies the learned bias.
        """
        raw_predictions = self._gemini_forecast(symbol, data)
        bias = self.weights.get(symbol, {}).get("bias", 1.0)
        
        # Apply learned bias to the forecasts
        biased_predictions = [round(p * bias, 2) for p in raw_predictions]
        return biased_predictions

    def _gemini_forecast(self, symbol, data):
        if not self.model or data.empty:
            return []
            
        # Ensure data is a flat list of floats
        if isinstance(data, pd.DataFrame):
            data = data.iloc[:, 0]
        prices = data.tolist()
        prompt = (
            f"You are a Quant strategist. Historical prices for {symbol}: {prices[-20:]}. "
            "Predict the next 5 closing prices. Output ONLY the numbers, separated by commas."
        )
        
        try:
            response = self.model.generate_content(prompt)
            prediction = [float(x.strip()) for x in response.text.split(',')]
            return prediction[:5]
        except Exception:
            last_price = prices[-1]
            trend = (prices[-1] - prices[-5]) / 5
            return [round(last_price + trend * i, 2) for i in range(1, 6)]

    def calculate_pivots(self, high, low, close):
        p = (high + low + close) / 3
        r1 = (2 * p) - low
        s1 = (2 * p) - high
        return {
            "Pivot": round(p, 2),
            "R1": round(r1, 2),
            "S1": round(s1, 2),
            "Target": round(r1 + (r1-p), 2)
        }
