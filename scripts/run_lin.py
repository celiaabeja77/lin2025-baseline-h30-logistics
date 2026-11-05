"""Run the unchanged Lin et al. repairer (via the 2026-10-30 reproduction worker) on H30 inputs.

Scoring happens in this parent process only; gold (clean domain) never enters worker inputs.
"""
import argparse
import concurrent.futures
import csv
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPRO = Path(__file__).resolve().parent
sys.path.insert(0, str(REPRO))
from benchmark_io import actions, evaluate, gold_edits, read_pddl, repair_key  # noqa: E402

REPO = ROOT / "third_party" / "classical-domain-repairer"
PY = Path(sys.executable)
H30 = ROOT / "data" / "h30"
CLEAN = H30 / "reference" / "domain.pddl"
SETTINGS = ["P4", "P40", "P4N"]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def run_one(case, setting, repeat, timeout, resume):
    inputs = ROOT / "inputs" / setting / case
    out = ROOT / "results" / "runs" / setting / case / f"run_{repeat}"
    out.mkdir(parents=True, exist_ok=True)
    mf = out / "metrics.json"
    if resume and mf.exists():
        return json.loads(mf.read_text(encoding="utf-8"))
    # P4N uses negatives; P4/P40 have empty black-lists, so "both" mode is identical to positive-only there.
    mode = "both"
    cmd = [str(PY), "-B", str(REPRO / "run_worker.py"), str(REPO), str(inputs), str(out), mode]
    env = {**os.environ, "PYTHONHASHSEED": str(repeat), "PYTHONIOENCODING": "utf-8"}
    row = {"case": case, "setting": setting, "repeat": repeat}
    t0 = time.perf_counter()
    try:
        with (out / "stdout.txt").open("w", encoding="utf-8") as so, (out / "stderr.txt").open("w", encoding="utf-8") as se:
            p = subprocess.run(cmd, cwd=out, env=env, stdout=so, stderr=se, timeout=timeout)
        row["status"] = "ok" if p.returncode == 0 else "error"
    except subprocess.TimeoutExpired:
        row["status"] = "timeout"
    row["wall_seconds"] = round(time.perf_counter() - t0, 3)
    if row["status"] == "ok":
        clean, faulty = read_pddl(CLEAN), read_pddl(H30 / case / "domain.pddl")
        gold = gold_edits(clean, faulty)
        pred_records = json.loads((out / "repairs_full.json").read_text())
        pred = {repair_key(r) for r in pred_records}
        tp = len(pred & gold)
        P = tp / len(pred) if pred else 0.0
        R = tp / len(gold)
        gold_actions = {g[1] for g in gold}
        row.update({
            "repairs": len(pred), "gold_edits": len(gold), "tp": tp,
            "precision": P, "recall": R, "f1": 2 * P * R / (P + R) if P + R else 0.0,
            "exact_recovery": pred == gold,
            "touches_gold_action": bool({r[1] for r in pred} & gold_actions),
            "only_gold_action": bool(pred) and {r[1] for r in pred} <= gold_actions,
            "predicted": sorted(r["author_line"] for r in pred_records),
        })
        row.update(json.loads((out / "worker_stats.json").read_text()))
        repaired = read_pddl(out / "domain-repaired.pddl")
        dev, dev_rec = evaluate(repaired, inputs)
        row["dev_passed"], row["dev_total"] = dev["passed"], dev["total"]
        row["dev_all_passed"] = dev["passed"] == dev["total"]
        ho, ho_rec = evaluate(repaired, ROOT / "heldout" / case)
        row.update({"heldout_pos_passed": ho["positive_passed"], "heldout_pos_total": ho["positive_total"],
                    "heldout_neg_passed": ho["negative_passed"], "heldout_neg_total": ho["negative_total"]})
        # Behavioural equivalence on held-out set == every held-out constraint passes.
        row["heldout_all_passed"] = ho["passed"] == ho["total"]
        save(out / "validation.json", {"dev": dev, "dev_records": dev_rec, "heldout": ho, "heldout_records": ho_rec})
        if not row["dev_all_passed"]:
            row["status"] = "validation_failed"
    save(mf, row)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--resume", action="store_true")
    ap.add_argument("--case", action="append")
    ap.add_argument("--setting", action="append")
    a = ap.parse_args()
    cases = sorted(p.name for p in (ROOT / "inputs" / "P4").iterdir())
    jobs = [(c, s, r) for c in cases if not a.case or c in a.case
            for s in SETTINGS if not a.setting or s in a.setting
            for r in range(1, a.repeats + 1)]
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    save(ROOT / "results" / "environment.json", {"python": str(PY), "repairer_commit": commit, "repeats": a.repeats,
                                                  "timeout_seconds": a.timeout, "seed_note": "PYTHONHASHSEED=repeat"})
    rows = []
    with concurrent.futures.ThreadPoolExecutor(a.workers) as pool:
        futs = [pool.submit(run_one, *j, a.timeout, a.resume) for j in jobs]
        for i, f in enumerate(concurrent.futures.as_completed(futs), 1):
            r = f.result(); rows.append(r)
            print(f"[{i}/{len(jobs)}] {r['case']} {r['setting']} #{r['repeat']} {r['status']} {r['wall_seconds']}s "
                  f"F1={r.get('f1')} exact={r.get('exact_recovery')} heldout={r.get('heldout_all_passed')}", flush=True)
    allrows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "results" / "runs").glob("*/*/run_*/metrics.json"))]
    save(ROOT / "results" / "all_runs.json", allrows)
    fields = sorted({k for r in allrows for k in r})
    with (ROOT / "results" / "all_runs.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(allrows)


if __name__ == "__main__":
    main()
