import json
import os

CONFIG_PATH = "config.json"
DB_PATH = r"D:\Brotherhood\stock_hub\brotherhood_data.db"

class QuantConfig:
    DEFAULT = {
        "RSI_BUY": 65,
        "RSI_SELL": 75,
        "EMA_PERIOD": 20,
        "FIB_RATIO": 0.618,
        "INDEX_MAPPING": {
            "^NSEI": "NIFTY",
            "^NSEBANK": "BANK NIFTY",
            "^BSESN": "SENSEX"
        }
    }

    @classmethod
    def load(cls):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r') as f:
                    return {**cls.DEFAULT, **json.load(f)}
            except:
                return cls.DEFAULT
        return cls.DEFAULT

    @classmethod
    def save(cls, data):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            json.dump(data, f, indent=4)
