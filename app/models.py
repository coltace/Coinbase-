from __future__ import annotations

import os
from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(64), primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False, default="")
    role = db.Column(db.String(32), nullable=False, default="user")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    balance_test = db.Column(db.Float, nullable=False, default=0.0)
    balance_usdt = db.Column(db.Float, nullable=False, default=0.0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class TransferIntent(db.Model):
    __tablename__ = "transfer_intents"

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(64), nullable=False)
    sender = db.Column(db.String(42), nullable=False)
    recipient = db.Column(db.String(42), nullable=False)
    amount_test = db.Column(db.Float, nullable=False, default=0.0)
    amount_usdt = db.Column(db.Float, nullable=False, default=0.0)
    amount_wei = db.Column(db.String(80), nullable=False, default="0")
    status = db.Column(db.String(32), nullable=False, default="pending")
    tx_hash = db.Column(db.String(66), nullable=True)
    block_number = db.Column(db.BigInteger, nullable=True)
    email_status = db.Column(db.String(32), nullable=False, default="not_sent")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(64), nullable=True)
    action = db.Column(db.String(128), nullable=False)
    resource_type = db.Column(db.String(64), nullable=True)
    resource_id = db.Column(db.String(128), nullable=True)
    ip_address = db.Column(db.String(64), nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


class DistributionRecord(db.Model):
    __tablename__ = "distribution_records"

    id = db.Column(db.String(64), primary_key=True)
    user_id = db.Column(db.String(64), nullable=False)
    recipient = db.Column(db.String(42), nullable=False)
    amount = db.Column(db.Float, nullable=False, default=0.0)
    status = db.Column(db.String(32), nullable=False, default="prepared")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))


def create_user(email, password, role="user"):
    email = email.strip().lower()
    if len(email) > 320 or "@" not in email:
        raise ValueError("Enter a valid email address.")
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters.")
    if User.query.filter_by(email=email).first():
        raise ValueError("An account with that email already exists.")
    user = User(
        id=os.urandom(16).hex(),
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
    )
    db.session.add(user)
    db.session.commit()
    return user


def verify_password(user, password):
    return bool(user and check_password_hash(user.password_hash, password))
