# CodeSentinel review report

**Source:** Sample: flask_user_api  
**Project:** `evals/flask_user_api`  
**Generated:** 2026-11-08T04:08:22+00:00  
**Verdict:** Blocked: critical issues must be fixed  
**Quality score:** 5 / 100

## Summary

The review found 21 issue(s): 5 critical, 5 high, 1 medium, 10 low. The most important one is "Hardcoded secret" in app.py at line 13. Do not merge until the critical issues are fixed.

| Critical | High | Medium | Low | Info |
|---:|---:|---:|---:|---:|
| 5 | 5 | 1 | 10 | 0 |

## Escalations

- ⚠️ 5 critical issue(s) found. A senior reviewer must acknowledge them before anything is posted.

## Findings (highest priority first)

### 1. 🔴 Critical · Hardcoded secret

`app.py:13` · Security agent · rule S003 · CWE-798 · source static · confidence 0.90

```
app.config["SECRET_KEY"] = "f9c2a71be04d4c1e9b7d"
```

**Why it matters:** `SECRET_KEY` holds a literal credential in source control, where anyone with repo access can read it.

**Fix:** Load it from an environment variable or a secrets manager and rotate the exposed value.

### 2. 🔴 Critical · Hardcoded secret

`app.py:14` · Security agent · rule S003 · CWE-798 · source static · confidence 0.90

```
STRIPE_API_KEY = "sk_live_51HxQ2aK8mVnR3tYpLw0Zb"
```

**Why it matters:** `STRIPE_API_KEY` holds a literal credential in source control, where anyone with repo access can read it.

**Fix:** Load it from an environment variable or a secrets manager and rotate the exposed value.

### 3. 🔴 Critical · SQL built from string formatting

`app.py:34` · Security agent · rule S004 · CWE-89 · source static · confidence 0.90

```
query = f"SELECT id, role FROM users WHERE username = '{username}' AND password = '{hash_password(password)}'"
```

**Why it matters:** `query` is assembled with string formatting and then executed, which allows SQL injection.

**Fix:** Build the query with placeholders and pass values as parameters.

### 4. 🔴 Critical · SQL built from string formatting

`app.py:44` · Security agent · rule S004 · CWE-89 · source static · confidence 0.90

```
row = db.execute("SELECT id, email, phone, address FROM users WHERE id = %s" % user_id).fetchone()
```

**Why it matters:** User controlled values are spliced into the SQL text, which allows SQL injection.

**Fix:** Use parameterised queries, for example `cursor.execute("... WHERE id = ?", (user_id,))`.

### 5. 🔴 Critical · Use of eval or exec

`app.py:74` · Security agent · rule S001 · CWE-95 · source static · confidence 0.90

```
return jsonify({"result": eval(formula)})
```

**Why it matters:** Evaluating strings as code lets anyone who controls the input run arbitrary Python.

**Fix:** Use `ast.literal_eval` for literals or a real parser for expressions.

### 6. 🟠 High · Weak hash algorithm

`app.py:25` · Security agent · rule S006 · CWE-328 · source static · confidence 0.90

```
return hashlib.md5(password.encode()).hexdigest()
```

**Why it matters:** MD5 and SHA1 are broken for security use and are trivially brute forced for passwords.

**Fix:** Use `hashlib.sha256` for integrity, and bcrypt, scrypt or argon2 for passwords.

### 7. 🟠 High · Insecure randomness for a secret value

`app.py:51` · Security agent · rule S009 · CWE-338 · source static · confidence 0.90

```
reset_token = str(random.randint(100000, 999999))
```

**Why it matters:** The `random` module is predictable and must not generate secrets or tokens.

**Fix:** Use `secrets.token_urlsafe()` or `secrets.choice()`.

### 8. 🟠 High · Unsafe deserialization

`app.py:61` · Security agent · rule S005 · CWE-502 · source static · confidence 0.90

```
prefs = pickle.loads(bytes.fromhex(blob))
```

**Why it matters:** Unpickling untrusted data can execute arbitrary code.

**Fix:** Use JSON or another data only format for untrusted input.

### 9. 🟠 High · Path traversal from user input

`app.py:68` · Security agent · rule S010 · CWE-22 · source static · confidence 0.90

```
return send_file(os.path.join(UPLOAD_DIR, request.args.get("file")))
```

**Why it matters:** A path is built from request data, so `../` sequences can reach files outside the intended folder.

**Fix:** Use `werkzeug.utils.secure_filename` and confirm the resolved path stays inside the base directory.

### 10. 🟠 High · Debug mode enabled

`app.py:78` · Security agent · rule S008 · CWE-489 · source static · confidence 0.90

```
app.run(host="0.0.0.0", debug=True)
```

**Why it matters:** Debug mode exposes an interactive debugger that allows remote code execution.

**Fix:** Read debug from configuration and keep it off in production.

### 11. 🟡 Medium · Sensitive data written to logs

`app.py:32` · Security agent · rule S011 · CWE-532 · source static · confidence 0.70

```
log.info(f"Login attempt for {username} with password {password}")
```

**Why it matters:** A secret or personal value appears to be written to logs, where it is retained and widely readable.

**Fix:** Mask or drop the sensitive field before logging.

### 12. 🔵 Low · No test files supplied

`app.py:1` · Test coverage agent · rule T003 · source static · confidence 1.00

**Why it matters:** The change contains source code but no tests, so none of its behaviour is protected against regressions.

**Fix:** Add a pytest module next to the code. The findings below list the tests to write first.

### 13. 🔵 Low · Comparison to None with == or !=

`app.py:36` · Bug and anti pattern agent · rule B003 · source static · confidence 0.95

```
if row == None:
```

**Why it matters:** Comparing to None with == can be fooled by objects that override `__eq__`.

**Fix:** Use `is None` or `is not None`.

### 14. 🔵 Low · Public function has no test

`app.py:20` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def get_db():
```

**Why it matters:** `get_db` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import get_db

def test_get_db_happy_path():
    result = get_db()
    assert result == ...  # expected value
```

</details>

### 15. 🔵 Low · Public function has no test

`app.py:24` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def hash_password(password):
```

**Why it matters:** `hash_password` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import hash_password

def test_hash_password_happy_path():
    result = hash_password(password=...)
    assert result == ...  # expected value
```

</details>

### 16. 🔵 Low · Public function has no test

`app.py:29` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def login():
```

**Why it matters:** `login` (complexity 2, 1 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import login

def test_login_happy_path():
    result = login()
    assert result == ...  # expected value
```

</details>

### 17. 🔵 Low · Public function has no test

`app.py:42` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def get_user(user_id):
```

**Why it matters:** `get_user` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import get_user

def test_get_user_happy_path():
    result = get_user(user_id=...)
    assert result == ...  # expected value
```

</details>

### 18. 🔵 Low · Public function has no test

`app.py:49` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def password_reset():
```

**Why it matters:** `password_reset` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import password_reset

def test_password_reset_happy_path():
    result = password_reset()
    assert result == ...  # expected value
```

</details>

### 19. 🔵 Low · Public function has no test

`app.py:59` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def load_preferences():
```

**Why it matters:** `load_preferences` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import load_preferences

def test_load_preferences_happy_path():
    result = load_preferences()
    assert result == ...  # expected value
```

</details>

### 20. 🔵 Low · Public function has no test

`app.py:66` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def download():
```

**Why it matters:** `download` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import download

def test_download_happy_path():
    result = download()
    assert result == ...  # expected value
```

</details>

### 21. 🔵 Low · Public function has no test

`app.py:72` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def admin_stats():
```

**Why it matters:** `admin_stats` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import admin_stats

def test_admin_stats_happy_path():
    result = admin_stats()
    assert result == ...  # expected value
```

</details>

## Agent runs

| Agent | Mode | Model | Status | Tool calls | Cache | Seconds |
|---|---|---|---|---:|---|---:|
| Bug and anti pattern agent | static | none | ok | 0 | miss | 0.12 |
| Security agent | static | none | ok | 0 | miss | 0.16 |
| Test coverage agent | static | none | ok | 0 | miss | 0.19 |

_Generated by CodeSentinel, a LangGraph multi agent code reviewer. Generated in read only automatic mode. No human has reviewed this report yet._