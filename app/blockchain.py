from __future__ import annotations

import json
from decimal import Decimal

import requests
from flask import current_app

SEPOLIA_CHAIN_ID = 11155111


class RpcError(Exception):
    pass


def rpc_call(method: str, params: list):
    url = current_app.config.get("SEPOLIA_RPC_URL", "").strip()
    if not url:
        raise RpcError("SEPOLIA_RPC_URL is not configured.")
    try:
        response = requests.post(url, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params}, timeout=15)
        response.raise_for_status()
        body = response.json()
    except Exception as exc:  # pragma: no cover - network dependent
        raise RpcError("Sepolia RPC failed.") from exc
    if body.get("error"):
        raise RpcError("RPC error.")
    return body.get("result")


def hex_to_int(value):
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        raise ValueError("Expected hex integer.")
    return int(value, 16)


def get_sepolia_transaction(tx_hash: str):
    chain_id = hex_to_int(rpc_call("eth_chainId", []))
    if chain_id != SEPOLIA_CHAIN_ID:
        raise RpcError("Not Sepolia.")
    receipt = rpc_call("eth_getTransactionReceipt", [tx_hash])
    if receipt is None:
        return {"receipt": None}
    transaction = rpc_call("eth_getTransactionByHash", [tx_hash])
    if transaction is None:
        raise RpcError("Transaction not found.")
    latest_block = hex_to_int(rpc_call("eth_blockNumber", []))
    receipt_block = hex_to_int(receipt["blockNumber"])
    confirmations = latest_block - receipt_block + 1
    return {"receipt": receipt, "transaction": transaction, "confirmations": confirmations, "block_number": receipt_block}


def get_binance_price():
    try:
        response = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=USDTTEST", timeout=10)
        response.raise_for_status()
        payload = response.json()
        return float(payload["price"])
    except Exception:
        return 0.0
