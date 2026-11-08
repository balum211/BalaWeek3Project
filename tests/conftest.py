import os
import sys
import tempfile
from pathlib import Path

# Isolate every test run: its own data dir, and no real LLM calls.
_TMP = tempfile.mkdtemp(prefix="codesentinel_tests_")
os.environ["CS_DATA_DIR"] = _TMP
os.environ["CS_PROVIDER"] = "static"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def load_sample(name: str) -> list[dict]:
    return [{"path": p.name, "content": p.read_text(encoding="utf-8")} for p in sorted((ROOT / "samples" / name).glob("*.py"))]


@pytest.fixture
def samples():
    return load_sample


@pytest.fixture(autouse=True)
def _no_model_override():
    from codesentinel.llm import set_model_override

    set_model_override(None)
    yield
    set_model_override(None)
