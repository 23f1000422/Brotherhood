# Nifty 50 Live Tracker

## Overview
A real-time Streamlit application that tracks Nifty 50 stocks between **9:15 AM and 9:25 AM**. It identifies strong trends by filtering for stocks that consistently stay above or below their opening price. Stocks that reverse direction (whipsaw) are automatically removed.

## Features
- **Live Tracking**: Fetches 1-minute data every 30 seconds.
- **Trend Filtering**: Segregates stocks into "Strong" (Above Open) and "Weak" (Below Open).
- **Whipsaw Detection**: Removes stocks that cross their opening price to reduce noise.
- **Email Reports**: Automatically sends an email with the final list of Strong/Weak stocks at 9:25 AM.

## Setup & Deployment

### 1. Requirements
- Python 3.9+
- Streamlit Account (for cloud deployment)
- Gmail App Password (for email alerts)

### 2. Local Installation
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

### 3. Streamlit Cloud Configuration (Secrets)
To enable email notifications, you must configure secrets in Streamlit Cloud:

1.  Go to your app dashboard on Streamlit Cloud.
2.  Click on "Settings" -> "Secrets".
3.  Add the following TOML configuration:

```toml
[email]
sender = "your_email@gmail.com"
password = "your_app_password" 
receiver = "receiver_email@gmail.com"
```

> **Note**: For `password`, use a **Gmail App Password**, not your regular login password.

## Project Structure
- `streamlit_app.py`: Main application logic.
- `utils/stock_utils.py`: Helper functions for live data fetching and email sending.
- `requirements.txt`: Python dependencies.

## Usage
1.  Open the app.
2.  Click **Start Tracking** before 9:15 AM (or during market hours).
3.  The app tracks live prices.
4.  At 9:25 AM, it stops tracking and sends an email report to the configured receiver.