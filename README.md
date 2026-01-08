# Nifty 50 Live Market Tracker

A real-time Streamlit application to track Nifty 50 stocks during the market opening (9:15 AM - 9:25 AM) and analyze Gap Up/Down trends.

## Features

- **⏱️ Live Market Tracking**: Updates stock prices every 30 seconds to capture trends right after market open.
- **🚀 Gap Breakout Detection**: Identifies stocks opening with significant gaps (Gap Up/Gap Down).
- **📉 Whipsaw Filtering**: Automatically removes stocks that reverse their trend (cross their Open price) to ensure only strong trends are displayed.
- **📄 Historical Reports**: View past daily reports of Gap Up/Down breakouts from saved CSV data.
- **User-Friendly Interface**: Simple start/stop controls and clear categorization of "Strong" vs "Weak" stocks.

## Installation

1.  **Clone the repository**:
    ```bash
    git clone <repository-url>
    cd Brotherhood
    ```

2.  **Create and activate a virtual environment** (optional but recommended):
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

You can run the application using the underlying Streamlit command or the provided batch script.

### Option 1: Using Streamlit
Run the following command in your terminal:
```bash
streamlit run streamlit_app.py
```

### Option 2: Using Batch Script (Windows)
Double-click `run_tracker.bat` or run it from the command line. This script automatically activates the virtual environment and starts the app.

## Project Structure

- `streamlit_app.py`: Main application file containing the UI and logic.
- `utils/stock_utils.py`: Helper functions for fetching live stock prices and analysis.
- `data/`: Directory where daily reports and CSV data are stored.
- `run_tracker.bat`: Convenience script for Windows users to launch the app.

## License

[MIT](LICENSE)