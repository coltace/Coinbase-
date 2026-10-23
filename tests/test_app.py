# Coinbase

A secure Flask application for blockchain-related wallet workflows, testnet deposit handling and admin-driven token distribution. The project is intended for deployment on Render with PostgreSQL support and environment-based secrets.

## Repository

- GitHub repo: https://github.com/coltace/Coinbase-
- Default branch: `main`

## Requirements

- Python 3.11+
- Flask 3.x
- SQLAlchemy 2.x
- Web3.py for Ethereum RPC interaction
- PostgreSQL for production
- Render hosting with Gunicorn

## Local setup

1. Clone the repository:
   git clone https://github.com/coltace/Coinbase-.git
   cd Coinbase-
2. Create a virtual environment:
   python3 -m venv .venv
   source .venv/bin/activate
3. Install dependencies:
   pip install -r requirements.txt
4. Copy the environment template and fill real values:
   cp .env.example .env
5. Start the app locally:
   export FLASK_APP=wsgi.py
   flask run --host 0.0.0.0 --port 5000

## Environment configuration

Copy `.env.example` to `.env` and set the following values:

- `SECRET_KEY`
- `DATABASE_URL` (use PostgreSQL in Render)
- `APP_BASE_URL`
- `WEB3_RPC_URL`
- `CHAIN_ID`
- `DEPOSIT_CONFIRMATIONS`
- `RESEND_API_KEY` or other mail provider secrets
- `NOTIFY_EMAIL`
- `EMAIL_FROM`
- optional provider keys such as `STRIPE_API_KEY`, `PAYPAL_CLIENT_ID`, etc.

For Render, prefer a managed PostgreSQL database and set `DATABASE_URL` to the Render-provided value.

## Render deployment

Create a new Render Web Service pointing at this repository and use these values:

- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn wsgi:app --bind 0.0.0.0:$PORT`
- Health check path: `/health`

The repository includes a `render.yaml` file for the same configuration.

## Testing

Run the project tests with:

pytest

The test suite checks application startup, config loading, database setup and basic API behavior. Do not execute real blockchain transactions in tests.

## Security notes

- Keep all real secrets in environment variables.
- Do not commit `.env`, tokens, private keys, database credentials or wallet secrets.
- Production configuration should use PostgreSQL instead of a local SQLite file.

## Deployment notes

This project is a demo application intended for testnet and staging use. It does not store wallet seeds or private keys. All blockchain verification must be done against the configured RPC endpoint and chain ID.
