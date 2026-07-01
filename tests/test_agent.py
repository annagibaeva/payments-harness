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
