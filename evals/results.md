# Evaluation results

Mode: **Static analysis only (no LLM key found)**

## Part A: seeded samples with ground truth

| Sample | Seeded issues found | Recall | Precision (bugs+security) | LLM only issues found | Verdict | Score | Seconds |
|---|---:|---:|---:|---:|---|---:|---:|
| flask_user_api | 12 / 12 | 100% | 100% | 0 / 3 | block | 5 | 0.27 |
| inventory_pipeline | 12 / 12 | 100% | 100% | 0 / 2 | request_changes | 27 | 0.15 |
| payments_service | 7 / 7 | 100% | 100% | 0 / 3 | block | 22 | 0.12 |

**Overall recall on seeded issues: 31 / 31 (100%).**

LLM only issues need semantic reasoning (authorization gaps, float equality, unbounded loops). They are expected to be found only when an LLM key is configured.

## Part B: real open source code from GitHub

| Source | Lines | Findings | Critical / High | Verdict | Seconds | Report |
|---|---:|---:|---:|---|---:|---|
| fportantier/vulpy/blob/master/bad/libuser.py | 61 | 9 | 3 / 0 | block | 0.87 | [realworld_fportantier_vulpy_bad_libuser.md](../sample_outputs/realworld_fportantier_vulpy_bad_libuser.md) |
| anxolerd/dvpwa/blob/master/sqli/dao/student.py | 47 | 6 | 1 / 0 | block | 0.83 | [realworld_anxolerd_dvpwa_sqli_dao_student.md](../sample_outputs/realworld_anxolerd_dvpwa_sqli_dao_student.md) |
| we45/Vulnerable-Flask-App/blob/master/app/app.py | 339 | 26 | 4 / 2 | block | 1.01 | [realworld_we45_Vulnerable-Flask-App_app_app.md](../sample_outputs/realworld_we45_Vulnerable-Flask-App_app_app.md) |

**fportantier/vulpy/blob/master/bad/libuser.py** top findings:
- critical: SQL built from string formatting (line 12)
- critical: SQL built from string formatting (line 25)
- critical: SQL built from string formatting (line 53)
- low: No test files supplied (line 1)
- low: Public function has no test (line 5)

**anxolerd/dvpwa/blob/master/sqli/dao/student.py** top findings:
- critical: SQL built from string formatting (line 42)
- medium: Public function has no test (line 25)
- low: No test files supplied (line 1)
- low: Public function has no test (line 11)
- low: Public function has no test (line 15)

**we45/Vulnerable-Flask-App/blob/master/app/app.py** top findings:
- critical: Hardcoded secret (line 27)
- critical: Hardcoded secret (line 63)
- critical: JWT signature not verified (line 97)
- critical: SQL built from string formatting (line 261)
- high: Weak hash algorithm (line 141)
