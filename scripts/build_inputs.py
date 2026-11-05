"""Convert the H30 Logistics fault package into Lin et al. (AAAI-25) repairer inputs.

Settings (repairer inputs; the clean domain and gold edits never enter these trees):
  P4   positive-only, the same 4 reference plans (S1,S2,F1,F2) that the SBFL baseline used.
  P40  positive-only, all 40 train reference plans (more positive evidence than SBFL).
  P4N  P4 + negative plans with first-inapplicable index, derived OFFLINE with the clean
       domain as oracle (extra information, as in the paper's "both" setting).

Held-out evaluation set (never shown to the repairer):
  10 test reference plans (positive) + negatives derived the same way from test problems.

Negative plan = prefix of a reference plan (executable in clean AND faulty) + one action that
is applicable in the faulty domain but inapplicable in the clean domain. Its .idx is the
0-based index of that last action, matching author NegativePlan.execute().
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_io import actions, clauses, gold_edits, read_pddl, read_plan, replay, truth  # noqa: E402

H30 = ROOT / "data" / "h30"
TR = H30 / "traces"
PROBLEMS = H30 / "reference" / "problems"
CLEAN = H30 / "reference" / "domain.pddl"
TRAIN = [f"train_problem{i}" for i in range(40)]
TEST = [f"test_problem{i}" for i in range(40, 50)]


def problem_path(pid):
    split, name = pid.split("_", 1)
    return PROBLEMS / split / f"{name}.pddl"


def plan_path(pid):
    return TR / "plans" / f"{pid}.plan"


def init_state(problem):
    init = next(n[1:] for n in problem if isinstance(n, list) and n and n[0] == ":init")
    return {tuple(a) for a in init if a[0] not in ("=", "not")}


def objects(problem):
    node = next(n[1:] for n in problem if isinstance(n, list) and n and n[0] == ":objects")
    out, skip = [], False
    for tok in node:
        if skip:
            skip = False
        elif tok == "-":
            skip = True
        else:
            out.append(tok)
    return out


def apply(action, mapping, state):
    add, delete = set(), set()
    for lit in clauses(action["eff"]):
        neg = lit[0] == "not"
        atom = lit[1] if neg else lit
        g = tuple([atom[0]] + [mapping.get(x, x) for x in atom[1:]])
        (delete if neg else add).add(g)
    return (state - delete) | add


def groundings(action, state, objs):
    """All parameter bindings that make `action` applicable in `state` (join over positive pre)."""
    params = action["parameters"]
    pos = [c for c in clauses(action["pre"]) if c[0] not in ("not", "=")]
    by_pred = {}
    for atom in state:
        by_pred.setdefault(atom[0], []).append(atom)
    results = []

    def pick(remaining, binding):
        # Most-constrained literal first: most already-bound variables, then fewest atoms.
        return min(remaining, key=lambda c: (-sum(1 for v in c[1:] if v in binding),
                                             len(by_pred.get(c[0], []))))

    def rec(remaining, binding):
        if not remaining:
            free = [p for p in params if p not in binding]
            stack = [dict(binding)]
            for p in free:
                stack = [{**b, p: o} for b in stack for o in objs]
            for b in stack:
                if truth(["and"] + clauses(action["pre"]), state, b):
                    results.append(tuple(b[p] for p in params))
            return
        lit = pick(remaining, binding)
        rest = [c for c in remaining if c is not lit]
        for atom in by_pred.get(lit[0], []):
            if len(atom) != len(lit):
                continue
            b, ok = dict(binding), True
            for var, val in zip(lit[1:], atom[1:]):
                if var.startswith("?"):
                    if b.setdefault(var, val) != val:
                        ok = False
                        break
                elif var != val:
                    ok = False
                    break
            if ok:
                rec(rest, b)

    rec(pos, {})
    return sorted(set(results))


def negatives(clean, faulty, problem, steps, cap):
    """Reference-plan prefixes extended by one faulty-only-applicable action."""
    ca, fa = actions(clean), actions(faulty)
    objs = objects(problem)
    cs = fs = init_state(problem)
    found = []
    for k in range(len(steps) + 1):
        for name in sorted(fa):
            for args in groundings(fa[name], fs, objs):
                m = dict(zip(ca[name]["parameters"], args))
                if not truth(["and"] + clauses(ca[name]["pre"]), cs, m):
                    found.append((k, (name,) + args))
        if k == len(steps):
            break
        name, args = steps[k][0], steps[k][1:]
        cm, fm = dict(zip(ca[name]["parameters"], args)), dict(zip(fa[name]["parameters"], args))
        if not truth(["and"] + clauses(fa[name]["pre"]), fs, fm):
            break  # prefix no longer executable in the faulty domain
        assert truth(["and"] + clauses(ca[name]["pre"]), cs, cm), "reference plan must be clean-valid"
        cs, fs = apply(ca[name], cm, cs), apply(fa[name], fm, fs)
    # Deterministic, diversity-first choice: earliest candidate of each action schema, then earliest.
    chosen, seen = [], set()
    for k, act in found:
        if act[0] not in seen and len(chosen) < cap:
            chosen.append((k, act)); seen.add(act[0])
    for k, act in found:
        if len(chosen) >= cap:
            break
        if (k, act) not in chosen:
            chosen.append((k, act))
    return [(list(steps[:k]) + [act], k) for k, act in chosen], len(found)


def write_plan(path, steps):
    path.write_text("".join("(" + " ".join(s) + ")\n" for s in steps), encoding="utf-8")


def build_tree(target, faulty_path, positives, negs):
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copy2(faulty_path, target / "domain-modified.pddl")
    tasks = sorted({p for p in positives} | {p for p, _, _ in negs})
    for pid in tasks:
        d = target / pid
        (d / "white-list").mkdir(parents=True)
        (d / "black-list").mkdir()
        shutil.copy2(problem_path(pid), d / f"{pid}.pddl")
        if pid in positives:
            shutil.copy2(plan_path(pid), d / "white-list" / "val-plan")
    counter = {}
    for pid, steps, idx in negs:
        counter[pid] = counter.get(pid, 0) + 1
        p = target / pid / "black-list" / f"inval-plan.{counter[pid]}"
        write_plan(p, steps)
        Path(str(p) + ".idx").write_text(f"{idx}\n", encoding="utf-8")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--neg-per-problem", type=int, default=2)
    ap.add_argument("--case", action="append")
    args = ap.parse_args()
    clean = read_pddl(CLEAN)
    cases = sorted(p.name for p in H30.iterdir() if p.is_dir() and p.name.startswith("H"))
    audit = {}
    for case in cases:
        if args.case and case not in args.case:
            continue
        faulty_path = H30 / case / "domain.pddl"
        faulty = read_pddl(faulty_path)
        manifest = json.loads((TR / "by_domain" / case / "manifest.json").read_text(encoding="utf-8"))
        p4 = [t["problem_id"] for t in manifest["traces"]]
        for pid in p4:  # the SBFL plans must be the official reference plans
            assert (TR / "by_domain" / case / f"{[t['trace_id'] for t in manifest['traces'] if t['problem_id']==pid][0]}.plan").read_bytes().replace(b"\r", b"") == plan_path(pid).read_bytes().replace(b"\r", b"")

        def negs_for(pids):
            out, pool = [], {}
            for pid in pids:
                prob = read_pddl(problem_path(pid))
                lst, n = negatives(clean, faulty, prob, read_plan(plan_path(pid)), args.neg_per_problem)
                pool[pid] = n
                out += [(pid, s, i) for s, i in lst]
            return out, pool

        neg_dev, pool_dev = negs_for(p4)
        neg_test, pool_test = negs_for(TEST)
        settings = {"P4": (p4, []), "P40": (TRAIN, []), "P4N": (p4, neg_dev)}
        for name, (pos, negs) in settings.items():
            build_tree(ROOT / "inputs" / name / case, faulty_path, pos, negs)
        build_tree(ROOT / "heldout" / case, faulty_path, TEST, neg_test)
        # Label audit on the clean domain (oracle check of the constructed contract).
        label_check = []
        for tree in [ROOT / "inputs" / s / case for s in settings] + [ROOT / "heldout" / case]:
            for t in sorted(p for p in tree.iterdir() if p.is_dir()):
                prob = read_pddl(t / f"{t.name}.pddl")
                for p in sorted((t / "white-list").glob("val-plan")):
                    r = replay(clean, prob, read_plan(p))
                    label_check.append(r["sequence_completed"] and r["full_goal_reached"])
                for p in sorted((t / "black-list").glob("inval-plan.[0-9]*")):
                    if p.name.endswith(".idx"):
                        continue
                    idx = int(Path(str(p) + ".idx").read_text())
                    r = replay(clean, prob, read_plan(p))
                    rf = replay(faulty, prob, read_plan(p))
                    label_check.append(r["first_failure_index"] == idx and rf["first_failure_index"] is None)
        assert all(label_check), f"label contract broken in {case}"
        audit[case] = {
            "p4_problems": p4,
            "negatives_dev": len(neg_dev), "negative_candidates_dev": pool_dev,
            "negatives_heldout": len(neg_test), "negative_candidates_heldout": sum(pool_test.values()),
            "gold_edits": [list(map(str, g)) for g in sorted(gold_edits(clean, faulty))],
            "faulty_sha256": sha(faulty_path), "labels_checked": len(label_check),
        }
        print(f"{case}: dev negatives {len(neg_dev)} (pool {sum(pool_dev.values())}), held-out negatives {len(neg_test)}", flush=True)
    (ROOT / "results").mkdir(exist_ok=True)
    (ROOT / "results" / "input_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
