# Coinbase Sepolia Testnet Platform

Coinbase is a testnet-only Flask application for authenticated Sepolia ETH transfer intents and administrator-controlled PTC test-token distributions.

The application never handles wallet seed phrases or private keys. Users and administrators sign blockchain transactions in their own wallet, such as MetaMask.

Important: This project uses Sepolia testnet assets only. PTC is a test token and is not real money, a security, or a withdrawal promise.

## Repository

- GitHub repository: https://github.com/coltace/Coinbase
- Expected deployment branch: `main`

## Features

- User registration and login.
- Password hashing.
- HTTP-only, SameSite-protected sessions.
- CSRF protection for authenticated mutation requests.
- User-specific transfer records.
- Admin role authorization.
- Admin-only PTC distribution preparation.
- Audit logs for authentication, transfers, and token distributions.
- Rate limiting for sensitive endpoints.
- Database, RPC, and PTC contract health checks.
- Confirmation email notifications through Resend.
- Sepolia ETH transaction verification.
- Sepolia ERC-20 Transfer event verification.
- Restricted-transfer PTC smart contract.
- GitHub Actions tests and package builds.
- Optional PyPI Trusted Publishing for tagged releases.
