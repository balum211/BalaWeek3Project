"""Evaluation harness.

Part A  Seeded samples with ground truth. Measures recall of seeded issues,
        precision of security and bug findings, and wall clock time.
Part B  Real open source code pulled from GitHub (intentionally vulnerable
        teaching projects). No ground truth, so we report counts and verdicts
        and keep the full reports in sample_outputs/ for human review.

    uv run python evals/run_evals.py            # static or LLM mode, depending on .env
    uv run python evals/run_evals.py --no-github
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from codesentinel.config import get_settings, provider_label  # noqa: E402
from codesentinel.graph import review_once  # noqa: E402
from codesentinel.tools.github_tools import GitHubError, fetch_files  # noqa: E402

OUT = ROOT / "sample_outputs"
REAL_WORLD = [
    "https://github.com/fportantier/vulpy/blob/master/bad/libuser.py",
    "https://github.com/anxolerd/dvpwa/blob/master/sqli/dao/student.py",
    "https://github.com/we45/Vulnerable-Flask-App/blob/master/app/app.py",
]


def load(name: str) -> list[dict]:
    return [{"path": p.name, "content": p.read_text(encoding="utf-8")} for p in sorted((ROOT / "samples" / name).glob("*.py"))]


def matches(finding: dict, issue: dict) -> bool:
    return abs(finding["line"] - issue["line"]) <= 1 and finding["rule_id"] in issue["rules"]


def llm_match(finding: dict, issue: dict) -> bool:
    if "llm" not in finding["source"]:
        return False
    text = f"{finding['title']} {finding['explanation']}".lower()
    return abs(finding["line"] - issue["line"]) <= 3 and any(k in text for k in issue["keywords"])


def eval_seeded(truth: dict) -> list[dict]:
    rows = []
    for name, spec in truth.items():
        started = time.time()
        state = review_once(load(name), source={"kind": "sample", "label": f"Sample: {name}"}, namespace=f"evals/{name}")
        seconds = time.time() - started
        report = state["report"]
        findings = report["findings"]
        hit = [i for i in spec["issues"] if any(matches(f, i) for f in findings)]
        llm_hit = [i for i in spec["llm_only"] if any(llm_match(f, i) for f in findings)]
        scored = [f for f in findings if f["agent"] in {"bugs", "security"}]
        true_pos = [f for f in scored if any(matches(f, i) for i in spec["issues"]) or
                    any(llm_match(f, i) for i in spec["llm_only"])]
        rows.append({
            "sample": name, "seeded": len(spec["issues"]), "found": len(hit),
            "recall": round(len(hit) / len(spec["issues"]), 3),
            "llm_only_total": len(spec["llm_only"]), "llm_only_found": len(llm_hit),
            "precision": round(len(true_pos) / len(scored), 3) if scored else 1.0,
            "findings": len(findings), "verdict": report["verdict"], "score": report["score"],
            "seconds": round(seconds, 2), "missed": [i["what"] for i in spec["issues"] if i not in hit],
            "agent_modes": {r["agent"]: f"{r['mode']}/{r['status']}" for r in report["agent_runs"]},
        })
        (OUT / f"{name}_report.md").write_text(report["markdown"], encoding="utf-8")
    return rows


def eval_real_world() -> list[dict]:
    rows = []
    for url in REAL_WORLD:
        started = time.time()
        try:
            files, meta = fetch_files(url)
        except GitHubError as exc:
            rows.append({"url": url, "error": str(exc)})
            continue
        meta.pop("changed_lines", None)
        label = f"{meta['namespace']}: {meta.get('path', '')}"
        state = review_once([f.model_dump() for f in files], source={**meta, "label": label}, namespace=meta["namespace"])
        report = state["report"]
        stem = (meta["namespace"] + "_" + meta.get("path", "pr")).replace("/", "_").replace(".py", "")
        (OUT / f"realworld_{stem}.md").write_text(report["markdown"], encoding="utf-8")
        rows.append({"url": url, "lines": sum(len(f.content.splitlines()) for f in files), "findings": len(report["findings"]),
                     "counts": report["counts"], "verdict": report["verdict"], "score": report["score"],
                     "seconds": round(time.time() - started, 2), "report": f"sample_outputs/realworld_{stem}.md",
                     "top": [f"{f['severity']}: {f['title']} (line {f['line']})" for f in report["findings"][:5]]})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-github", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    settings = get_settings()
    truth = json.loads((ROOT / "evals" / "ground_truth.json").read_text(encoding="utf-8"))
    seeded = eval_seeded(truth)
    real = [] if args.no_github else eval_real_world()
    results = {"mode": provider_label(settings.provider), "seeded": seeded, "real_world": real}
    (ROOT / "evals" / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")

    total_seeded = sum(r["seeded"] for r in seeded)
    total_found = sum(r["found"] for r in seeded)
    md = [f"# Evaluation results", "", f"Mode: **{results['mode']}**", "",
          "## Part A: seeded samples with ground truth", "",
          "| Sample | Seeded issues found | Recall | Precision (bugs+security) | LLM only issues found | Verdict | Score | Seconds |",
          "|---|---:|---:|---:|---:|---|---:|---:|"]
    for r in seeded:
        md.append(f"| {r['sample']} | {r['found']} / {r['seeded']} | {r['recall']:.0%} | {r['precision']:.0%} | "
                  f"{r['llm_only_found']} / {r['llm_only_total']} | {r['verdict']} | {r['score']} | {r['seconds']} |")
    md += ["", f"**Overall recall on seeded issues: {total_found} / {total_seeded} ({total_found / total_seeded:.0%}).**", "",
           "LLM only issues need semantic reasoning (authorization gaps, float equality, unbounded loops). They are expected to be "
           "found only when an LLM key is configured.", ""]
    if real:
        md += ["## Part B: real open source code from GitHub", "",
               "| Source | Lines | Findings | Critical / High | Verdict | Seconds | Report |", "|---|---:|---:|---:|---|---:|---|"]
        for r in real:
            if "error" in r:
                md.append(f"| {r['url']} | error: {r['error']} | | | | | |")
                continue
            md.append(f"| {r['url'].split('github.com/')[1]} | {r['lines']} | {r['findings']} | {r['counts']['critical']} / "
                      f"{r['counts']['high']} | {r['verdict']} | {r['seconds']} | [{Path(r['report']).name}](../{r['report']}) |")
        md.append("")
        for r in real:
            if "top" in r:
                md += [f"**{r['url'].split('github.com/')[1]}** top findings:"] + [f"- {t}" for t in r["top"]] + [""]
    (ROOT / "evals" / "results.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
