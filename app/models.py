cat > app/models.py << 'EOF'
from datetime import datetime, timezone
from .extensions import db

class User(db.Model):
    id = db.Column(db.String(42), primary_key=True)
    balance_test = db.Column(db.Float, default=0.0)
    balance_usdt = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class TransferIntent(db.Model):
    id = db.Column(db.String(32), primary_key=True)
    user_id = db.Column(db.String(42), nullable=False)
    recipient = db.Column(db.String(42), nullable=False)
    amount_test = db.Column(db.Float, nullable=False)
    amount_usdt = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    tx_hash = db.Column(db.String(66), unique=True, nullable=True)
    block_number = db.Column(db.BigInteger, nullable=True)
    email_status = db.Column(db.String(20), nullable=False, default="not_sent")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
EOF
