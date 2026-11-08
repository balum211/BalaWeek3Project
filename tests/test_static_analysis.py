from codesentinel.models import CodeFile
from codesentinel.tools.static_analysis import run_static_analysis


def _rules(files, agent):
    return {(f.rule_id, f.line) for f in run_static_analysis([CodeFile(**f) for f in files], agent)}


def test_flask_security_findings(samples):
    found = _rules(samples("flask_user_api"), "security")
    for expected in [("S003", 13), ("S003", 14), ("S006", 25), ("S011", 32), ("S004", 34), ("S004", 44),
                     ("S009", 51), ("S005", 61), ("S010", 68), ("S001", 74), ("S008", 78)]:
        assert expected in found, expected


def test_pipeline_bug_findings(samples):
    found = _rules(samples("inventory_pipeline"), "bugs")
    for expected in [("B002", 12), ("B013", 13), ("B004", 18), ("B007", 25), ("B012", 26), ("B003", 27),
                     ("B011", 35), ("B001", 43), ("B008", 52), ("B005", 55), ("B009", 75), ("B010", 76)]:
        assert expected in found, expected


def test_payments_security_and_tests(samples):
    files = samples("payments_service")
    sec = _rules(files, "security")
    for expected in [("S003", 8), ("S001", 29), ("S012", 33), ("S002", 50)]:
        assert expected in sec, expected
    tests = run_static_analysis([CodeFile(**f) for f in files], "tests")
    untested = {f.evidence.split("(")[0].replace("def ", "") for f in tests if f.rule_id == "T001"}
    assert {"apply_discount", "refund", "export_receipt"} <= untested
    assert "split_payment" not in untested  # it has a test
    refund = next(f for f in tests if "refund" in f.evidence)
    assert "pytest.raises(RefundError)" in refund.suggested_test


def test_clean_code_has_no_security_findings():
    clean = CodeFile(path="clean.py", content="import secrets\n\ndef token():\n    return secrets.token_urlsafe(32)\n")
    assert run_static_analysis([clean], "security") == []


def test_placeholder_secrets_are_ignored():
    f = CodeFile(path="cfg.py", content='API_KEY = "your-api-key-here"\nPASSWORD = "changeme123"\n')
    assert run_static_analysis([f], "security") == []


def test_syntax_error_is_reported_not_raised():
    f = CodeFile(path="broken.py", content="def oops(:\n    pass\n")
    out = run_static_analysis([f], "bugs")
    assert out and out[0].rule_id == "B000"


def test_javascript_patterns():
    js = CodeFile(path="ui.js", language="javascript",
                  content='el.innerHTML = userInput;\nconst apiKey = "AbC123dEf456GhI789";\neval(code);\n')
    rules = {f.rule_id for f in run_static_analysis([js], "security")}
    assert {"S013", "S003", "S001"} <= rules
