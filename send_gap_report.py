from utils.stock_utils import analyze_stocks
from twilio.rest import Client
from datetime import datetime
import pandas as pd
import pytz, os, json

# Timezone aware timestamp
IST = pytz.timezone("Asia/Kolkata")
now = datetime.now(IST)
today = now.strftime("%Y-%m-%d")

# Read config
with open("config.json") as f:
    cfg = json.load(f)

# Run breakout scan
df = analyze_stocks()
if df.empty:
    print("No breakouts today.")
    exit()

# Save file
os.makedirs("data", exist_ok=True)
df.to_csv(f"data/breakouts_{today}.csv", index=False)

# Format message
gap_ups = df[df["Status"] == "Gap Up Breakout"]
gap_downs = df[df["Status"] == "Gap Down Breakdown"]

def format_table(d):
    return "\n".join(f"{row['Symbol']}: {row['Gap %']}% ({row['Status']})" for _, row in d.iterrows())

message_body = f"""📊 Nifty 50 Gap Report – {today}

📈 Gap Ups:
{format_table(gap_ups) if not gap_ups.empty else 'None'}

📉 Gap Downs:
{format_table(gap_downs) if not gap_downs.empty else 'None'}
"""

# Send WhatsApp via Twilio
client = Client(cfg["twilio_sid"], cfg["twilio_token"])
client.messages.create(
    body=message_body,
    from_=cfg["whatsapp_from"],
    to=cfg["whatsapp_to"]
)

print("✅ WhatsApp message sent.")

# Convert to HTML
html = df.to_html(index=False)
html_path = f"reports/{today}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(f"<h2>Nifty Gap Report – {today}</h2>")
    f.write(html)

# Auto-push to GitHub
import subprocess
subprocess.run(["git", "add", html_path])
subprocess.run(["git", "commit", "-m", f"Add {today} gap report"])
subprocess.run(["git", "push"])