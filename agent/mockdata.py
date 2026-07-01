from __future__ import annotations

from harness.types import Fixtures


def get_balance(fx: Fixtures, account: str, currency: str) -> float | None:
    acct = fx.accounts.get(account)
    if acct is None:
        return None
    return acct.balances.get(currency)


def get_fx(fx: Fixtures, base: str, quote: str) -> float | None:
    return fx.fx_rates.get(f"{base}_{quote}")


def get_fee(fx: Fixtures, kind: str) -> dict | None:
    return fx.fee_schedule.get(kind)


def get_payment(fx: Fixtures, pid: str) -> dict | None:
    return fx.payments.get(pid)


def get_dispute(fx: Fixtures, did: str) -> dict | None:
    return fx.disputes.get(did)
