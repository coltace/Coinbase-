import json
import secrets
import uuid
from functools import wraps

from flask import current_app, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import AuditLog, User


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def issue_csrf_token():
    token = session.get("csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["csrf_token"] = token
    return token


def csrf_required():
    expected = session.get("csrf_token")
    supplied = request.headers.get("X-CSRF-Token") or (request.get_json(silent=True) or {}).get("csrfToken")
    if not expected or not supplied or not secrets.compare_digest(expected, str(supplied)):
        return False
    return True


def require_auth(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user()
        if not user or not user.is_active:
            return jsonify({"error": "Authentication required."}), 401
        if request.method not in {"GET", "HEAD", "OPTIONS"} and not csrf_required():
            return jsonify({"error": "CSRF token required."}), 403
        return view(*args, **kwargs)
    return wrapped


def require_role(*roles):
    def decorator(view):
        @wraps(view)
        @require_auth
        def wrapped(*args, **kwargs):
            user = current_user()
            if user.role not in roles:
                return jsonify({"error": "Insufficient permissions."}), 403
            return view(*args, **kwargs)
        return wrapped
    return decorator


def audit(action, user_id=None, resource_type=None, resource_id=None, metadata=None):
    entry = AuditLog(
        id=uuid.uuid4().hex,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        ip_address=request.headers.get("X-Forwarded-For", request.remote_addr),
        metadata_json=json.dumps(metadata or {}, sort_keys=True),
    )
    db.session.add(entry)
    db.session.commit()
    return entry


def user_json(user):
    return {"id": user.id, "email": user.email, "role": user.role, "createdAt": user.created_at.isoformat()}


def create_user(email, password, role="user"):
    email = email.strip().lower()
    if len(email) > 320 or "@" not in email:
        raise ValueError("Enter a valid email address.")
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters.")
    if User.query.filter_by(email=email).first():
        raise ValueError("An account with that email already exists.")
    user = User(id=uuid.uuid4().hex, email=email, password_hash=generate_password_hash(password), role=role)
    db.session.add(user)
    db.session.commit()
    return user


def verify_password(user, password):
    return bool(user and check_password_hash(user.password_hash, password))
