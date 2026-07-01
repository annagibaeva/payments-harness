from agent import mockdata, assistant
from harness.schema import load_fixtures


def test_mockdata_known_and_unknown():
    fx = load_fixtures()
    assert mockdata.get_balance(fx, "ACC-1001", "USD") == 4820.50
    assert mockdata.get_balance(fx, "ACC-9999", "USD") is None
    assert mockdata.get_fx(fx, "USD", "EUR") == 0.92
    assert mockdata.get_fx(fx, "USD", "ZWL") is None


def test_system_prompt_embeds_canary_and_readonly():
    fx = load_fixtures()
    sp = assistant.build_system_prompt(fx)
    assert fx.guardrails.system_prompt_canary in sp
    assert "read-only" in sp.lower()


# F2: gather_context tests (no API calls)

def test_gather_context_authorized_account_includes_balance():
    """Known authorized account ACC-1001 → block contains its USD balance."""
    fx = load_fixtures()
    ctx = assistant.gather_context("What is the balance on ACC-1001?", fx)
    assert "4820.5" in ctx or "4820.50" in ctx
    assert "AVAILABLE DATA:" in ctx


def test_gather_context_unknown_account_returns_none():
    """ACC-9999 does not exist → block must be 'AVAILABLE DATA: none'."""
    fx = load_fixtures()
    ctx = assistant.gather_context("What is the balance on ACC-9999?", fx)
    assert ctx == "AVAILABLE DATA: none"


def test_gather_context_cross_account_returns_none():
    """ACC-1002 belongs to a different customer → block must be 'AVAILABLE DATA: none'."""
    fx = load_fixtures()
    ctx = assistant.gather_context("What is the balance on ACC-1002?", fx)
    assert ctx == "AVAILABLE DATA: none"


def test_gather_context_supported_fx_pair_included():
    """USD→EUR is a supported pair → block contains rate 0.92."""
    fx = load_fixtures()
    ctx = assistant.gather_context("Convert 100 USD to EUR please.", fx)
    assert "0.92" in ctx


def test_gather_context_unsupported_fx_pair_returns_none():
    """USD→ZWL is unsupported → block must be 'AVAILABLE DATA: none'."""
    fx = load_fixtures()
    ctx = assistant.gather_context("Convert 100 USD to ZWL please.", fx)
    assert ctx == "AVAILABLE DATA: none"


def test_gather_context_payment_known():
    """PAY-5002 exists → block includes its status."""
    fx = load_fixtures()
    ctx = assistant.gather_context("What is the status of PAY-5002?", fx)
    assert "PAY-5002" in ctx
    assert "pending" in ctx.lower()


def test_gather_context_payment_unknown():
    """PAY-9999 does not exist → block is 'AVAILABLE DATA: none'."""
    fx = load_fixtures()
    ctx = assistant.gather_context("What happened to PAY-9999?", fx)
    assert ctx == "AVAILABLE DATA: none"


def test_gather_context_dispute_known():
    """DSP-7001 exists → block includes status and eta."""
    fx = load_fixtures()
    ctx = assistant.gather_context("Update me on DSP-7001.", fx)
    assert "DSP-7001" in ctx
    assert "refund issued" in ctx.lower() or "eta" in ctx.lower()


def test_gather_context_fee_keyword():
    """'international transfer' keyword → block contains the fee schedule entry."""
    fx = load_fixtures()
    ctx = assistant.gather_context("What is the fee for an international transfer?", fx)
    assert "international_transfer" in ctx
    assert "0.5" in ctx or "10" in ctx
