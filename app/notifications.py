from __future__ import annotations

import requests
from flask import current_app


def send_confirmation_email(transfer):
    api_key = current_app.config.get("RESEND_API_KEY", "").strip()
    notify_email = current_app.config.get("NOTIFY_EMAIL", "").strip()
    if not api_key or not notify_email:
        return "disabled"
    payload = {
        "from": current_app.config.get("EMAIL_FROM", "CoinPilot <onboarding@resend.dev>"),
        "to": [notify_email],
        "subject": "CoinPilot Transfer Confirmed",
        "text": f"From: {transfer.user_id}\nTo: {transfer.recipient}\nAmount: {transfer.amount_test} test + {transfer.amount_usdt} USDT\nTx: {transfer.tx_hash}",
    }
    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=15,
    )
    response.raise_for_status()
    return "sent"
