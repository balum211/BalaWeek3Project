# CodeSentinel review report

**Source:** we45/Vulnerable-Flask-App: app/app.py  
**Project:** `we45/Vulnerable-Flask-App`  
**Generated:** 2026-11-08T04:08:25+00:00  
**Verdict:** Blocked: critical issues must be fixed  
**Quality score:** 7 / 100

## Summary

The review found 26 issue(s): 4 critical, 2 high, 8 medium, 12 low. The most important one is "Hardcoded secret" in app/app.py at line 27. Do not merge until the critical issues are fixed.

| Critical | High | Medium | Low | Info |
|---:|---:|---:|---:|---:|
| 4 | 2 | 8 | 12 | 0 |

## Escalations

- ⚠️ 4 critical issue(s) found. A senior reviewer must acknowledge them before anything is posted.

## Findings (highest priority first)

### 1. 🔴 Critical · Hardcoded secret

`app/app.py:27` · Security agent · rule S003 · CWE-798 · source static · confidence 0.90

```
app.config['SECRET_KEY_HMAC_2'] = 'am0r3C0mpl3xK3y'
```

**Why it matters:** `SECRET_KEY_HMAC_2` holds a literal credential in source control, where anyone with repo access can read it.

**Fix:** Load it from an environment variable or a secrets manager and rotate the exposed value.

### 2. 🔴 Critical · Hardcoded secret

`app/app.py:63` · Security agent · rule S003 · CWE-798 · source static · confidence 0.90

```
user.password = 'admin123'
```

**Why it matters:** `user.password` holds a literal credential in source control, where anyone with repo access can read it.

**Fix:** Load it from an environment variable or a secrets manager and rotate the exposed value.

### 3. 🔴 Critical · JWT signature not verified

`app/app.py:97` · Security agent · rule S012 · CWE-347 · source static · confidence 0.90

```
decoded = jwt.decode(token, verify = False)
```

**Why it matters:** Tokens are decoded without verifying the signature, so anyone can forge them.

**Fix:** Verify the signature with an explicit allow list of algorithms.

### 4. 🔴 Critical · SQL built from string formatting

`app/app.py:261` · Security agent · rule S004 · CWE-89 · source static · confidence 0.90

```
str_query = "SELECT first_name, last_name, username FROM customer WHERE username = '%s';" % search_term
```

**Why it matters:** `str_query` is assembled with string formatting and then executed, which allows SQL injection.

**Fix:** Build the query with placeholders and pass values as parameters.

### 5. 🟠 High · Weak hash algorithm

`app/app.py:141` · Security agent · rule S006 · CWE-328 · source static · confidence 0.90

```
hash_pass = hashlib.md5(password).hexdigest()
```

**Why it matters:** MD5 and SHA1 are broken for security use and are trivially brute forced for passwords.

**Fix:** Use `hashlib.sha256` for integrity, and bcrypt, scrypt or argon2 for passwords.

### 6. 🟠 High · Unsafe deserialization

`app/app.py:329` · Security agent · rule S005 · CWE-502 · source static · confidence 0.90

```
ydata = yaml.load(y)
```

**Why it matters:** `yaml.load` without SafeLoader can construct arbitrary Python objects.

**Fix:** Use `yaml.safe_load`.

### 7. 🟡 Medium · Bare or swallowed exception

`app/app.py:193` · Bug and anti pattern agent · rule B001 · source static · confidence 0.90

```
except:
```

**Why it matters:** A bare `except:` also catches KeyboardInterrupt and SystemExit and hides real failures.

**Fix:** Catch the specific exception you expect and log or re raise everything else.

### 8. 🟡 Medium · Public function has no test

`app/app.py:56` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def setup_users():
```

**Why it matters:** `setup_users` (complexity 4, 2 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import setup_users

def test_setup_users_happy_path():
    result = setup_users()
    assert result == ...  # expected value

@pytest.mark.parametrize("case", [...])  # one case per branch
def test_setup_users_branches(case):
    ...
```

</details>

### 9. 🟡 Medium · Public function has no test

`app/app.py:116` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def has_no_empty_params(rule):
```

**Why it matters:** `has_no_empty_params` (complexity 3, 2 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import has_no_empty_params

def test_has_no_empty_params_happy_path():
    result = has_no_empty_params(rule=...)
    assert result == ...  # expected value

@pytest.mark.parametrize("case", [...])  # one case per branch
def test_has_no_empty_params_branches(case):
    ...
```

</details>

### 10. 🟡 Medium · Public function has no test

`app/app.py:122` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def sitemap():
```

**Why it matters:** `sitemap` (complexity 7, 2 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import sitemap

def test_sitemap_happy_path():
    result = sitemap()
    assert result == ...  # expected value

@pytest.mark.parametrize("case", [...])  # one case per branch
def test_sitemap_branches(case):
    ...
```

</details>

### 11. 🟡 Medium · Public function has no test

`app/app.py:197` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def fetch_customer():
```

**Why it matters:** `fetch_customer` (complexity 5, 4 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import fetch_customer

def test_fetch_customer_happy_path():
    result = fetch_customer()
    assert result == ...  # expected value

@pytest.mark.parametrize("case", [...])  # one case per branch
def test_fetch_customer_branches(case):
    ...
```

</details>

### 12. 🟡 Medium · Public function has no test

`app/app.py:222` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def get_customer(cust_id):
```

**Why it matters:** `get_customer` (complexity 5, 4 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import get_customer

def test_get_customer_happy_path():
    result = get_customer(cust_id=...)
    assert result == ...  # expected value

@pytest.mark.parametrize("case", [...])  # one case per branch
def test_get_customer_branches(case):
    ...
```

</details>

### 13. 🟡 Medium · Public function has no test

`app/app.py:247` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def search_customer():
```

**Why it matters:** `search_customer` (complexity 6, 3 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import search_customer

def test_search_customer_happy_path():
    result = search_customer()
    assert result == ...  # expected value

@pytest.mark.parametrize("case", [...])  # one case per branch
def test_search_customer_branches(case):
    ...
```

</details>

### 14. 🟡 Medium · Sensitive data written to logs

`app/app.py:87` · Security agent · rule S011 · CWE-532 · source static · confidence 0.70

```
print("JWT Token from API: {0}".format(decoded))
```

**Why it matters:** A secret or personal value appears to be written to logs, where it is retained and widely readable.

**Fix:** Mask or drop the sensitive field before logging.

### 15. 🔵 Low · No test files supplied

`app/app.py:1` · Test coverage agent · rule T003 · source static · confidence 1.00

**Why it matters:** The change contains source code but no tests, so none of its behaviour is protected against regressions.

**Fix:** Add a pytest module next to the code. The findings below list the tests to write first.

### 16. 🔵 Low · Public function has no test

`app/app.py:80` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def get_exp_date():
```

**Why it matters:** `get_exp_date` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import get_exp_date

def test_get_exp_date_happy_path():
    result = get_exp_date()
    assert result == ...  # expected value
```

</details>

### 17. 🔵 Low · Public function has no test

`app/app.py:84` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def verify_jwt(token):
```

**Why it matters:** `verify_jwt` (complexity 3, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import verify_jwt

def test_verify_jwt_happy_path():
    result = verify_jwt(token=...)
    assert result == ...  # expected value
```

</details>

### 18. 🔵 Low · Public function has no test

`app/app.py:96` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def insecure_verify(token):
```

**Why it matters:** `insecure_verify` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import insecure_verify

def test_insecure_verify_happy_path():
    result = insecure_verify(token=...)
    assert result == ...  # expected value
```

</details>

### 19. 🔵 Low · Public function has no test

`app/app.py:102` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def pnf(e):
```

**Why it matters:** `pnf` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import pnf

def test_pnf_happy_path():
    result = pnf(e=...)
    assert result == ...  # expected value
```

</details>

### 20. 🔵 Low · Public function has no test

`app/app.py:135` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def reg_customer():
```

**Why it matters:** `reg_customer` (complexity 3, 1 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import reg_customer

def test_reg_customer_happy_path():
    result = reg_customer()
    assert result == ...  # expected value
```

</details>

### 21. 🔵 Low · Public function has no test

`app/app.py:151` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def reg_user():
```

**Why it matters:** `reg_user` (complexity 3, 1 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import reg_user

def test_reg_user_happy_path():
    result = reg_user()
    assert result == ...  # expected value
```

</details>

### 22. 🔵 Low · Public function has no test

`app/app.py:171` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def login():
```

**Why it matters:** `login` (complexity 3, 1 branches) is never exercised by a test.

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

### 23. 🔵 Low · Public function has no test

`app/app.py:285` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def index():
```

**Why it matters:** `index` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import index

def test_index_happy_path():
    result = index()
    assert result == ...  # expected value
```

</details>

### 24. 🔵 Low · Public function has no test

`app/app.py:291` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def hello():
```

**Why it matters:** `hello` (complexity 3, 1 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import hello

def test_hello_happy_path():
    result = hello()
    assert result == ...  # expected value
```

</details>

### 25. 🔵 Low · Public function has no test

`app/app.py:311` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def yaml_upload():
```

**Why it matters:** `yaml_upload` (complexity 1, 0 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import yaml_upload

def test_yaml_upload_happy_path():
    result = yaml_upload()
    assert result == ...  # expected value
```

</details>

### 26. 🔵 Low · Public function has no test

`app/app.py:316` · Test coverage agent · rule T001 · source static · confidence 0.85

```
def yaml_hammer():
```

**Why it matters:** `yaml_hammer` (complexity 3, 1 branches) is never exercised by a test.

**Fix:** Add a unit test that covers the normal path and each branch.

<details><summary>Suggested test</summary>

```python
import pytest
from app import yaml_hammer

def test_yaml_hammer_happy_path():
    result = yaml_hammer()
    assert result == ...  # expected value
```

</details>

## Agent runs

| Agent | Mode | Model | Status | Tool calls | Cache | Seconds |
|---|---|---|---|---:|---|---:|
| Bug and anti pattern agent | static | none | ok | 0 | miss | 0.18 |
| Security agent | static | none | ok | 0 | miss | 0.19 |
| Test coverage agent | static | none | ok | 0 | miss | 0.2 |

_Generated by CodeSentinel, a LangGraph multi agent code reviewer. Generated in read only automatic mode. No human has reviewed this report yet._