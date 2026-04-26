# 🧬 BROTHERHOOD: Local Stock Research Nexus

**Brotherhood** is a high-performance local AI dashboard designed for autonomous stock research and portfolio tracking. It is a fully decoupled, lightweight system powered by Gemini 2.5 and SQLite.

## 📈 1. STOCKS HUB
A deterministic technical analysis engine that scans markets for high-probability setups.
- **The Raj Breakout Logic**: High-precision filtering based on **Open=Low (Bullish)** and **Open=High (Bearish)** criteria.
- **Strict Guardrails**: EMA200 systemic filter, MACD cross-verification, and RSI momentum audits.
- **SQLite Data Hub**: All market intelligence is persisted in `brotherhood_data.db`.
- **The Oracle Brain**: A conversational sidebar assistant with **Live SQL Read Access**. It analyzes the current database state to provide blunt, practical financial advice.

## 💼 2. PORTFOLIO MANAGER (New)
A placeholder for personal investment tracking.
- Currently in design phase.
- Planned integration with the Oracle for personalized risk audits.

---

## 🛠️ Architecture & Tech Stack
- **Dashboard**: Streamlit
- **Intelligence**: Google Gemini (via `google-generativeai`)
- **Engine**: Modular Python (`stock_engine.py`, `logic_handler.py`, `indicator_engine.py`)
- **Database**: SQLite 3

## 🛰️ Modularized Files (`stock_hub/`)
- `stock_engine.py`: The master conductor for research cycles and DB sync.
- `logic_handler.py`: Powers the Oracle Chatbot and SQL context injection.
- `indicator_engine.py`: Core technical logic (MACD, RSI, Raj Breakouts).
- `forecast_engine.py`: Predictive analysis using historical price trends.
- `quant_tools.py`: Shared mathematical utilities for technical indicators.

---

## 🚀 Execution
1. Ensure `.env` contains a valid `GOOGLE_API_KEY`.
2. Run the application:
   ```bash
   streamlit run app.py
   ```
3. Use the **Research Cycle** to populate fresh data via yFinance into the SQLite engine.

---
*Built for speed, privacy, and technical precision.*