cat > app/config.py << 'EOF'
import os

def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-demo-key-change-this")
    SQLALCHEMY_DATABASE_URI = normalize_database_url(os.getenv("DATABASE_URL", "sqlite:///coinpilot.db"))
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    SEPOLIA_RPC_URL = os.getenv("SEPOLIA_RPC_URL", "").strip()
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
    BINANCE_API_SECRET = os.getenv("BINANCE_API_SECRET", "")
    BINANCE_URL = os.getenv("BINANCE_URL", "https://api.binance.com")
    RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
    NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "").strip()
    EMAIL_FROM = os.getenv("EMAIL_FROM", "CoinPilot <onboarding@resend.dev>").strip()
    ADMIN_BALANCE_USDT = float(os.getenv("ADMIN_BALANCE_USDT", "88988998098"))
    ADMIN_BALANCE_TEST = float(os.getenv("ADMIN_BALANCE_TEST", "1000000"))
    MIN_CONFIRMATIONS = 1
EOF
