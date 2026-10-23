import os


def normalize_database_url(url: str) -> str:
    if not url:
        return "sqlite:///coinbase.db"
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


def _as_bool(value, default=False):
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-demo-key-change-this")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(
        os.getenv("DATABASE_URL", "sqlite:///coinbase.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    APP_BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5000").rstrip("/")
    WEB3_RPC_URL = os.getenv("WEB3_RPC_URL", os.getenv("SEPOLIA_RPC_URL", "")).strip()
    CHAIN_ID = int(os.getenv("CHAIN_ID", "11155111"))
    DEPOSIT_CONFIRMATIONS = int(os.getenv("DEPOSIT_CONFIRMATIONS", "2"))

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _as_bool(os.getenv("SESSION_COOKIE_SECURE"), False)

    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
    NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "").strip()
    EMAIL_FROM = os.getenv("EMAIL_FROM", "Coinbase <noreply@example.com>").strip()

    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    ADMIN_BALANCE_USDT = float(os.getenv("ADMIN_BALANCE_USDT", "88988998098"))
    ADMIN_BALANCE_TEST = float(os.getenv("ADMIN_BALANCE_TEST", "1000000"))
    MIN_CONFIRMATIONS = int(os.getenv("MIN_CONFIRMATIONS", "1"))
