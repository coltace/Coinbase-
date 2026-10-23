from __future__ import annotations

from flask_sqlalchemy import SQLAlchemy

try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    limiter = Limiter(key_func=get_remote_address, default_limits=[])
except Exception:  # pragma: no cover
    class _NoopLimiter:
        def __init__(self, *args, **kwargs):
            pass

        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator

    limiter = _NoopLimiter()


db = SQLAlchemy()
