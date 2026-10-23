cat > app/notifications.py << 'EOF'
from decimal import Decimal
import requests
from flask import current_app

WEI_PER_ETH = Decimal(10**18)

def send_confirmation_email(transfer):
    api_key = current_app.config["RESEND_API_KEY"]
    notify_email = current_app.config["NOTIFY_EMAIL"]
    if not api_key or not notify_email: return "disabled"
    payload = {
        "from": current_app.config["EMAIL_FROM"],
        "to": [notify_email],
        "subject": "CoinPilot Transfer Confirmed",
        "text": f"From: {transfer.user_id}\nTo: {transfer.recipient}\nAmount: {transfer.amount_test} test + {transfer.amount_usdt} USDT\nTx: {transfer.tx_hash}"
    }
    response = requests.post("https://api.resend.com/emails", headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, json=payload, timeout=15)
    response.raise_for_status()
    return "sent"
EOF
