"""Aggregate Lin-on-H30 runs into tables; joins SBFL localization columns for context only."""
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
SBFL = ROOT / "data" / "sbfl_summary.csv"
CASES = ROOT / "data" / "h30" / "case_manifest.json"
SETTINGS = ["P4", "P40", "P4N"]

rows = json.loads((ROOT / "results" / "all_runs.json").read_text(encoding="utf-8"))
audit = json.loads((ROOT / "results" / "input_audit.json").read_text(encoding="utf-8"))
sbfl = {r["case_id"]: r for r in csv.DictReader(SBFL.open(encoding="utf-8-sig"))}
manifest = {c["case_id"]: c for c in json.loads(CASES.read_text(encoding="utf-8"))}
by = defaultdict(list)
for r in rows:
    by[(r["case"], r["setting"])].append(r)
cases = sorted({r["case"] for r in rows})
neg_cases = [c for c in cases if audit[c]["negatives_dev"] > 0]


def ok(rs):
    return [r for r in rs if r["status"] in ("ok", "validation_failed")]


def frac(rs, key):
    rs = ok(rs)
    return sum(bool(r.get(key)) for r in rs) / len(rs) if rs else 0.0


def avg(rs, key):
    rs = ok(rs)
    return mean(r[key] for r in rs) if rs else 0.0


def agg(setting, subset):
    per = [by[(c, setting)] for c in subset]
    allr = [r for rs in per for r in rs]
    return {
        "runs": len(allr), "ok": sum(r["status"] == "ok" for r in allr),
        "timeout": sum(r["status"] == "timeout" for r in allr),
        "error": sum(r["status"] == "error" for r in allr),
        "dev_violations": sum(r["status"] == "validation_failed" for r in allr),
        "precision": mean(avg(rs, "precision") for rs in per),
        "recall": mean(avg(rs, "recall") for rs in per),
        "f1": mean(avg(rs, "f1") for rs in per),
        "exact_recovery": mean(frac(rs, "exact_recovery") for rs in per),
        "heldout_all_passed": mean(frac(rs, "heldout_all_passed") for rs in per),
        "touches_gold_action": mean(frac(rs, "touches_gold_action") for rs in per),
        "mean_repairs": mean(avg(rs, "repairs") for rs in per),
        "mean_seconds": mean(avg(rs, "wall_seconds") for rs in per),
    }


summary = {"all30": {s: agg(s, cases) for s in SETTINGS},
           "negative_cases": {"cases": neg_cases, **{s: agg(s, neg_cases) for s in SETTINGS}}}
(ROOT / "results" / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

f = lambda x: f"{x:.3f}"
L = ["# Lin et al. (AAAI-25) repairer on H30 Logistics — results", "",
     "Run-level means are averaged within each case first, then across cases. Exact = the repair set equals the gold assertion edits exactly (literal and arguments). Held-out = every held-out constraint passes on test problems 40–49 (10 positive plans, plus any oracle negatives).", ""]
for title, key, subset in [("All 30 cases", "all30", cases), (f"The {len(neg_cases)} cases with negative plans ({', '.join(neg_cases)})", "negative_cases", neg_cases)]:
    L += [f"## {title}", "", "| Setting | ok/runs | Timeout | P | R | F1 | Exact | Held-out pass | Touches gold action | Mean repairs | Seconds |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for s in SETTINGS:
        a = summary[key][s]
        L.append(f"| {s} | {a['ok']}/{a['runs']} | {a['timeout']} | {f(a['precision'])} | {f(a['recall'])} | {f(a['f1'])} | {f(a['exact_recovery'])} | {f(a['heldout_all_passed'])} | {f(a['touches_gold_action'])} | {a['mean_repairs']:.2f} | {a['mean_seconds']:.2f} |")
    L.append("")
L += ["## Per case (Exact and Held-out are counts out of 5 seeds; SBFL columns come from data/sbfl_summary.csv, for context only)", "",
      "| Case | Group | Fault | SBFL gold rank (best–worst) | P4 F1 | P4 exact | P4 held-out | P40 F1 | P40 exact | P40 held-out | Dev negatives | P4N F1 | P4N exact | P4N held-out | P4N repairs (seed 1) |",
      "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for c in cases:
    m, sb = manifest[c], sbfl.get(c, {})
    rank = f"{sb.get('best_rank')}–{sb.get('worst_rank')}" if sb.get("best_rank") else "not in candidates"
    fault = f"{m['faulty_action']} {m['component']}: {m['original_assertion'] or '∅'} → {m['replacement_assertion'] or '∅'}"
    cells = []
    for s in SETTINGS:
        rs = by[(c, s)]
        if s == "P4N":
            cells.append(str(audit[c]["negatives_dev"]))
        cells += [f(avg(rs, "f1")), str(sum(bool(r.get("exact_recovery")) for r in rs)), str(sum(bool(r.get("heldout_all_passed")) for r in rs))]
    first = next((r for r in by[(c, "P4N")] if r["repeat"] == 1), {})
    L.append(f"| {c} | {m['group_id']} | `{fault}` | {rank} | " + " | ".join(cells) + f" | `{'; '.join(first.get('predicted', [])) or '(none)'}` |")
(ROOT / "results" / "results.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L[:30]))
