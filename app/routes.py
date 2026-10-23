cat > app/routes.py << 'EOF'
import re
import uuid
import hmac
import hashlib
from decimal import Decimal
from flask import Blueprint, current_app, jsonify, render_template, request
from .blockchain import RpcError, get_sepolia_transaction, hex_to_int, get_binance_price
from .extensions import db
from .models import User, TransferIntent
from .notifications import send_confirmation_email

bp = Blueprint("main", __name__)
ADDRESS_RE = re.compile(r"^0x[a-fA-F0-9]{40}$")
TX_HASH_RE = re.compile(r"^0x[a-fA-F0-9]{64}$")

def transfer_json(transfer):
    return {"id": transfer.id, "user_id": transfer.user_id, "recipient": transfer.recipient,
            "amountTest": transfer.amount_test, "amountUsdt": transfer.amount_usdt,
            "status": transfer.status, "txHash": transfer.tx_hash, "blockNumber": transfer.block_number,
            "emailStatus": transfer.email_status, "createdAt": transfer.created_at.isoformat()}

def json_error(message, status_code):
    return jsonify({"error": message}), status_code

def attempt_notification(transfer):
    if transfer.email_status == "sent": return
    try:
        transfer.email_status = send_confirmation_email(transfer)
    except:
        current_app.logger.exception("Email failed.")
        transfer.email_status = "failed"
    db.session.commit()

@bp.get("/")
def index():
    admin = User.query.get_or_404("ADMIN_DEFAULT")
    if not admin:
        admin = User(id="ADMIN_DEFAULT", balance_test=current_app.config["ADMIN_BALANCE_TEST"], balance_usdt=current_app.config["ADMIN_BALANCE_USDT"])
        db.session.add(admin)
        db.session.commit()
    return render_template("index.html")

@bp.get("/healthz")
def health_check(): return jsonify({"status": "ok"})

@bp.post("/api/deposit/test")
def deposit_test():
    data = request.get_json(silent=True)
    if not isinstance(data, dict): return json_error("Send JSON.", 400)
    user_id = str(data.get("user_id", "")).strip()
    amount = float(data.get("amount", 0))
    if amount <= 0: return json_error("Invalid amount.", 400)
    user = User.query.get(user_id)
    if not user: return json_error("User not found.", 404)
    user.balance_test += amount
    db.session.commit()
    return jsonify({"success": True, "newBalance": user.balance_test})

@bp.post("/api/deposit/usdt")
def deposit_usdt():
    data = request.get_json(silent=True)
    if not isinstance(data, dict): return json_error("Send JSON.", 400)
    user_id = str(data.get("user_id", "")).strip()
    amount = float(data.get("amount", 0))
    if amount <= 0: return json_error("Invalid amount.", 400)
    user = User.query.get(user_id)
    if not user: return json_error("User not found.", 404)
    user.balance_usdt += amount
    db.session.commit()
    return jsonify({"success": True, "newBalance": user.balance_usdt})

@bp.post("/api/send")
def send():
    data = request.get_json(silent=True)
    if not isinstance(data, dict): return json_error("Send JSON.", 400)
    sender = str(data.get("sender", "")).strip()
    recipient = str(data.get("recipient", "")).strip()
    amount_test = float(data.get("amountTest", 0))
    amount_usdt = float(data.get("amountUsdt", 0))
    if not ADDRESS_RE.fullmatch(sender) or not ADDRESS_RE.fullmatch(recipient):
        return json_error("Invalid addresses.", 400)
    if amount_test <= 0 and amount_usdt <= 0: return json_error("Amount required.", 400)
    user = User.query.get(sender)
    if not user: return json_error("Sender not found.", 404)
    if user.balance_test < amount_test or user.balance_usdt < amount_usdt:
        return json_error("Insufficient balance.", 400)
    transfer = TransferIntent(id=uuid.uuid4().hex, user_id=sender, recipient=recipient.lower(),
                              amount_test=amount_test, amount_usdt=amount_usdt, status="pending")
    db.session.add(transfer)
    db.session.commit()
    return jsonify(transfer_json(transfer)), 201

@bp.post("/api/transfers/<transfer_id>/verify")
def verify_transfer(transfer_id):
    transfer = db.session.get(TransferIntent, transfer_id)
    if not transfer: return json_error("Not found.", 404)
    data = request.get_json(silent=True)
    tx_hash = str(data.get("txHash", "")).strip().lower()
    if not TX_HASH_RE.fullmatch(tx_hash): return json_error("Invalid tx.", 400)
    if transfer.status == "failed": return json_error("Failed. Prepare new.", 409)
    if transfer.status == "confirmed":
        attempt_notification(transfer)
        return jsonify(transfer_json(transfer))
    try:
        chain_data = get_sepolia_transaction(tx_hash)
    except RpcError as exc:
        current_app.logger.warning("Verification error: %s", exc)
        return json_error("Try again shortly.", 503)
    receipt = chain_data["receipt"]
    if receipt is None: return jsonify({**transfer_json(transfer), "message": "Not mined yet."})
    transaction = chain_data["transaction"]
    actual_sender = str(transaction.get("from", "")).lower()
    actual_recipient = str(transaction.get("to", "")).lower()
    try:
        actual_value_wei = hex_to_int(transaction.get("value"))
        receipt_status = hex_to_int(receipt.get("status"))
    except (TypeError, ValueError): return json_error("Read error.", 502)
    if actual_sender != transfer.sender or actual_recipient != transfer.recipient or actual_value_wei != int(transfer.amount_wei):
        return json_error("Mismatch.", 400)
    transfer.tx_hash = tx_hash
    transfer.block_number = chain_data["block_number"]
    if receipt_status != 1:
        transfer.status = "failed"
        db.session.commit()
        return jsonify({**transfer_json(transfer), "message": "Failed."})
    transfer.status = "confirmed"
    db.session.commit()
    attempt_notification(transfer)
    return jsonify({**transfer_json(transfer), "confirmations": chain_data["confirmations"], "requiredConfirmations": current_app.config["MIN_CONFIRMATIONS"]})
EOF
