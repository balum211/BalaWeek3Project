# CodeSentinel review report

**Source:** fportantier/vulpy: bad/libuser.py  
**Project:** `fportantier/vulpy`  
**Generated:** 2026-11-08T04:08:23+00:00  
**Verdict:** Blocked: critical issues must be fixed  
**Quality score:** 30 / 100

## Summary

The review found 9 issue(s): 3 critical, 6 low. The most important one is "SQL built from string formatting" in bad/libuser.py at line 12. Do not merge until the critical issues are fixed.

| Critical | High | Medium | Low | Info |
|---:|---:|---:|---:|---:|
| 3 | 0 | 0 | 6 | 0 |

## Escalations

- ⚠️ 3 critical issue(s) found. A senior reviewer must acknowledge them before anything is posted.

## Findings (highest priority first)

### 1. 🔴 Critical · SQL built from string formatting

`bad/libuser.py:12` · Security agent · rule S004 · CWE-89 · source static · confidence 0.90

```
user = c.execute("SELECT * FROM users WHERE username = '{}' and password = '{}'".format(username, password)).fetchone()
```

**Why it matters:** User controlled values are spliced into the SQL text, which allows SQL injection.

**Fix:** Use parameterised queries, for example `cursor.execute("... WHERE id = ?", (user_id,))`.

### 2. 🔴 Critical · SQL built from string formatting

`bad/libuser.py:25` · Security agent · rule S004 · CWE-89 · source static · confidence 0.90

```
c.execute("INSERT INTO users (username, password, failures, mfa_enabled, mfa_secret) VALUES ('%s', '%s', '%d', '%d', '%s')" %(username, password, 0, 0, ''))
```

**Why it matters:** User controlled values are spliced into the SQL text, which allows SQL injection.

**Fix:** Use parameterised queries, for example `cursor.execute("... WHERE id = ?", (user_id,))`.

### 3. 🔴 Critical · SQL built from string formatting

`bad/libuser.py:53` · Security agent · rule S004 · CWE-89 · source static · confidence 0.90

```
c.execute("UPDATE users SET password = '{}' WHERE username = '{}'".format(password, username))
```

**Why it matters:** User controlled values are spliced into the SQL text, which allows SQL injection.

**Fix:** Use parameterised queries, for example `cursor.execute("... WHERE id = ?", (user_id,))`.

### 4. 🔵 Low · No test files supplied

`bad/libuser.py:1` · Test coverage agent · rule T003 · source static · confidence 1.00

**Why it matters:** The change contains source code but no tests, so none of its behaviour is protected against regressions.

**Fix:** Add a pytest module next to the code. The findings below list the tests to write first.

### 5. 🔵 Low · Public function has no test

`bad/libuser.py:5` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def login(username, password):
```

**Why it matters:** `login` (complexity 2, 1 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from libuser import login

def test_login_happy_path():
    result = login(username=..., password=...)
    assert result == ...  # expected value
```

</details>

### 6. 🔵 Low · Public function has no test

`bad/libuser.py:20` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def create(username, password):
```

**Why it matters:** `create` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from libuser import create

def test_create_happy_path():
    result = create(username=..., password=...)
    assert result == ...  # expected value
```

</details>

### 7. 🔵 Low · Public function has no test

`bad/libuser.py:31` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def userlist():
```

**Why it matters:** `userlist` (complexity 3, 1 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from libuser import userlist

def test_userlist_happy_path():
    result = userlist()
    assert result == ...  # expected value
```

</details>

### 8. 🔵 Low · Public function has no test

`bad/libuser.py:46` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def password_change(username, password):
```

**Why it matters:** `password_change` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from libuser import password_change

def test_password_change_happy_path():
    result = password_change(username=..., password=...)
    assert result == ...  # expected value
```

</details>

### 9. 🔵 Low · Public function has no test

`bad/libuser.py:59` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def password_complexity(password):
```

**Why it matters:** `password_complexity` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from libuser import password_complexity

def test_password_complexity_happy_path():
    result = password_complexity(password=...)
    assert result == ...  # expected value
```

</details>

## Agent runs

| Agent | Mode | Model | Status | Tool calls | Cache | Seconds |
|---|---|---|---|---:|---|---:|
| Bug and anti pattern agent | static | none | ok | 0 | miss | 0.05 |
| Security agent | static | none | ok | 0 | miss | 0.07 |
| Test coverage agent | static | none | ok | 0 | miss | 0.08 |

_Generated by CodeSentinel, a LangGraph multi agent code reviewer. Generated in read only automatic mode. No human has reviewed this report yet._