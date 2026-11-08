# CodeSentinel review report

**Source:** Sample: inventory_pipeline  
**Project:** `evals/inventory_pipeline`  
**Generated:** 2026-11-08T04:08:22+00:00  
**Verdict:** Changes requested  
**Quality score:** 27 / 100

## Summary

The review found 21 issue(s): 3 high, 8 medium, 9 low, 1 info. The most important one is "Identity comparison with a literal" in pipeline.py at line 25. Fix the high severity issues before merging.

| Critical | High | Medium | Low | Info |
|---:|---:|---:|---:|---:|
| 0 | 3 | 8 | 9 | 1 |

## Findings (highest priority first)

### 1. 🟠 High · Identity comparison with a literal

`pipeline.py:25` · Bug and anti pattern agent · rule B007 · source static · confidence 0.95

```
if record.get("qty") is "":
```

**Why it matters:** `is` checks object identity, not value. It works by accident for small ints and interned strings and fails otherwise.

**Fix:** Use == to compare values.

### 2. 🟠 High · List modified while iterating over it

`pipeline.py:26` · Bug and anti pattern agent · rule B012 · source static · confidence 0.90

```
records.remove(record)
```

**Why it matters:** `records` is changed while the loop iterates over it, so items get skipped or processed twice.

**Fix:** Iterate over a copy (`for x in list(records):`) or build a new list.

### 3. 🟠 High · Return inside finally swallows errors

`pipeline.py:52` · Bug and anti pattern agent · rule B008 · source static · confidence 0.90

```
return "unknown"
```

**Why it matters:** A return inside finally discards any exception raised in the try block.

**Fix:** Move the return out of the finally block.

### 4. 🟡 Medium · Mutable default argument

`pipeline.py:12` · Bug and anti pattern agent · rule B002 · source static · confidence 0.90

```
def fetch_stock(page, headers={}):
```

**Why it matters:** `fetch_stock` uses a mutable default. It is created once and shared across every call, so state leaks between calls.

**Fix:** Default to None and create the list or dict inside the function.

### 5. 🟡 Medium · Network call without a timeout

`pipeline.py:13` · Bug and anti pattern agent · rule B013 · source static · confidence 0.90

```
response = requests.get(WAREHOUSE_URL, params={"page": page}, headers=headers)
```

**Why it matters:** Without a timeout this call can hang forever and block the worker.

**Fix:** Pass an explicit `timeout=` (for example 10 seconds) and handle the timeout error.

### 6. 🟡 Medium · Bare or swallowed exception

`pipeline.py:43` · Bug and anti pattern agent · rule B001 · source static · confidence 0.90

```
except:
```

**Why it matters:** A bare `except:` also catches KeyboardInterrupt and SystemExit and hides real failures.

**Fix:** Catch the specific exception you expect and log or re raise everything else.

### 7. 🟡 Medium · File opened without a context manager

`pipeline.py:18` · Bug and anti pattern agent · rule B004 · source static · confidence 0.85

```
f = open(path)
```

**Why it matters:** The file handle is never guaranteed to close if an exception happens, which leaks descriptors.

**Fix:** Use `with open(...) as f:` so the file always closes.

### 8. 🟡 Medium · Public function has no test

`pipeline.py:23` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def normalise(records):
```

**Why it matters:** `normalise` (complexity 4, 2 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from pipeline import normalise

def test_normalise_happy_path():
    result = normalise(records=...)
    assert result == ...  # expected value

@pytest.mark.parametrize("case", [...])  # one case per branch
def test_normalise_branches(case):
    ...
```

</details>

### 9. 🟡 Medium · Function is too complex

`pipeline.py:55` · Bug and anti pattern agent · rule B005 · source static · confidence 0.85

```
def reconcile(local, remote, threshold=5, mode="strict"):
```

**Why it matters:** `reconcile` has cyclomatic complexity 12 across 17 lines, which makes it hard to test and easy to break.

**Fix:** Split it into smaller functions with one responsibility each.

### 10. 🟡 Medium · Public function has no test

`pipeline.py:55` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def reconcile(local, remote, threshold=5, mode="strict"):
```

**Why it matters:** `reconcile` (complexity 12, 7 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from pipeline import reconcile

def test_reconcile_happy_path():
    result = reconcile(local=..., remote=..., threshold=..., mode=...)
    assert result == ...  # expected value

@pytest.mark.parametrize("case", [...])  # one case per branch
def test_reconcile_branches(case):
    ...
```

</details>

### 11. 🟡 Medium · Float used for money values

`pipeline.py:35` · Bug and anti pattern agent · rule B011 · source static · confidence 0.75

```
total += float(r["unit_price"]) * r["qty"]
```

**Why it matters:** Binary floats cannot represent most decimal amounts exactly, so totals drift by fractions of a cent.

**Fix:** Use `decimal.Decimal` (or integer cents) for money.

### 12. 🔵 Low · No test files supplied

`pipeline.py:1` · Test coverage agent · rule T003 · source static · confidence 1.00

**Why it matters:** The change contains source code but no tests, so none of its behaviour is protected against regressions.

**Fix:** Add a pytest module next to the code. The findings below list the tests to write first.

### 13. 🔵 Low · Comparison to None with == or !=

`pipeline.py:27` · Bug and anti pattern agent · rule B003 · source static · confidence 0.95

```
elif record["qty"] == None:
```

**Why it matters:** Comparing to None with == can be fooled by objects that override `__eq__`.

**Fix:** Use `is None` or `is not None`.

### 14. 🔵 Low · Public function has no test

`pipeline.py:12` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def fetch_stock(page, headers={}):
```

**Why it matters:** `fetch_stock` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from pipeline import fetch_stock

def test_fetch_stock_happy_path():
    result = fetch_stock(page=..., headers=...)
    assert result == ...  # expected value
```

</details>

### 15. 🔵 Low · Public function has no test

`pipeline.py:17` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def load_skus(path):
```

**Why it matters:** `load_skus` (complexity 2, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from pipeline import load_skus

def test_load_skus_happy_path():
    result = load_skus(path=...)
    assert result == ...  # expected value
```

</details>

### 16. 🔵 Low · Public function has no test

`pipeline.py:32` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def stock_value(records):
```

**Why it matters:** `stock_value` (complexity 2, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from pipeline import stock_value

def test_stock_value_happy_path():
    result = stock_value(records=...)
    assert result == ...  # expected value
```

</details>

### 17. 🔵 Low · Public function has no test

`pipeline.py:39` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def write_report(records, path):
```

**Why it matters:** `write_report` (complexity 3, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from pipeline import write_report

def test_write_report_happy_path():
    result = write_report(records=..., path=...)
    assert result == ...  # expected value
```

</details>

### 18. 🔵 Low · Public function has no test

`pipeline.py:47` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def last_sync_status(log_path):
```

**Why it matters:** `last_sync_status` (complexity 2, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from pipeline import last_sync_status

def test_last_sync_status_happy_path():
    result = last_sync_status(log_path=...)
    assert result == ...  # expected value
```

</details>

### 19. 🔵 Low · Public function has no test

`pipeline.py:74` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def run_sync(batch_id):
```

**Why it matters:** `run_sync` (complexity 3, 1 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from pipeline import run_sync

def test_run_sync_happy_path():
    result = run_sync(batch_id=...)
    assert result == ...  # expected value
```

</details>

### 20. 🔵 Low · Mutable global state

`pipeline.py:75` · Bug and anti pattern agent · rule B009 · source static · confidence 0.70

```
global processed_batches
```

**Why it matters:** `global processed_batches` mutates module state, which breaks under concurrency and makes tests order dependent.

**Fix:** Pass state explicitly or wrap it in a class.

### 21. ⚪ Info · Unresolved TODO or FIXME

`pipeline.py:76` · Bug and anti pattern agent · rule B010 · source static · confidence 0.60

```
# TODO: add retry when the warehouse API returns 503
```

**Why it matters:** Unfinished work is marked in the code.

**Fix:** Resolve it or link it to a tracked ticket.

## Agent runs

| Agent | Mode | Model | Status | Tool calls | Cache | Seconds |
|---|---|---|---|---:|---|---:|
| Bug and anti pattern agent | static | none | ok | 0 | miss | 0.06 |
| Security agent | static | none | ok | 0 | miss | 0.07 |
| Test coverage agent | static | none | ok | 0 | miss | 0.08 |

_Generated by CodeSentinel, a LangGraph multi agent code reviewer. Generated in read only automatic mode. No human has reviewed this report yet._