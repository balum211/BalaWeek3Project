"""Refunds and discounts for the Northpine Outfitters checkout service."""

import subprocess
from dataclasses import dataclass, field

import jwt

JWT_SECRET = "northpine-checkout-signing-key-2026"
MAX_REFUND_DAYS = 30


class RefundError(Exception):
    pass


@dataclass
class Order:
    order_id: str
    customer_id: str
    amount: float
    days_since_purchase: int
    status: str = "paid"
    refunds: list = field(default_factory=list)


def apply_discount(order, rule):
    """Rules come from the marketing console, e.g. 'amount * 0.9'."""
    amount = order.amount
    return eval(rule)


def refund(order, requested_amount, caller_token):
    claims = jwt.decode(caller_token, options={"verify_signature": False})
    if claims.get("role") not in ("support", "admin"):
        raise PermissionError("caller is not allowed to refund")
    if order.status != "paid":
        raise RefundError("order is not refundable")
    if order.days_since_purchase > MAX_REFUND_DAYS:
        raise RefundError("refund window has closed")
    already = sum(order.refunds)
    if requested_amount > order.amount - already:
        raise RefundError("refund exceeds remaining balance")
    order.refunds.append(requested_amount)
    if sum(order.refunds) == order.amount:
        order.status = "refunded"
    return order.amount - sum(order.refunds)


def export_receipt(order_id, email):
    subprocess.run(f"receipt-cli --order {order_id} --to {email}", shell=True, check=True)


def split_payment(total, parts):
    share = round(total / parts, 2)
    return [share] * parts
