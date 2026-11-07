"""Verify an exported subset using only Python's standard library.

This checks copied data and replays saved grounded conditions/effects. The
source PDDL/parser audit is carried forward by byte identity; no planner or UP
simulation is invoked here.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUT = BASE / "traces/official_2success_2failure"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_trace(trace, plan):
    rows = [line.strip() for line in plan.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith(";")]
    assert len(rows) == trace["planned_action_count"]
    state = set(trace["initial_state"])
    rejected = None
    for index, step in enumerate(trace["steps"], 1):
        assert step["step"] == index and step["action"] == rows[index - 1]
        assert state == set(step["state_before"])
        conditions = {p: p in state for p in step["grounded_preconditions"]}
        assert {r["literal"]: r["satisfied"] for r in step["precondition_results"]} == conditions
        unmet = sorted(p for p, ok in conditions.items() if not ok)
        assert sorted(step["unmet_preconditions"]) == unmet
        assert step["attempted"] and step["applicable"] == step["executed"] == (not unmet)
        before = set(state)
        if step["executed"]:
            state = (state - set(step["grounded_effect_delete_list"])) | set(step["grounded_effect_add_list"])
        else:
            rejected = index
            assert index == len(trace["steps"])
        assert state == set(step["state_after"])
        assert sorted(state - before) == step["predicates_added"]
        assert sorted(before - state) == step["predicates_removed"]
    completed = rejected is None and len(trace["steps"]) == len(rows)
    reached = all(g in state for g in trace["problem_goals"])
    assert trace["sequence_completed"] == completed
    assert trace["full_goal_reached"] == reached
    assert trace["success"] == trace["plan_accepted"] == (completed and reached)
    assert trace["success"] == (trace["validator_status"] == "VALID")
    assert trace["executed_action_count"] == sum(s["executed"] for s in trace["steps"])
    assert trace["first_rejected_step"] == rejected
    assert set(trace["final_state"]) == state
    assert trace["unmet_goals"] == [g for g in trace["problem_goals"] if g not in state]
    return len(trace["steps"])


def main():
    index = read(BASE / "SHA256SUMS.json")
    indexed = set(index)
    actual = {p.relative_to(BASE).as_posix() for p in BASE.rglob("*")
              if p.is_file() and "__pycache__" not in p.parts}
    assert actual - indexed <= {"SHA256SUMS.json", "evaluation/package_audit.json"}
    for relative, expected in index.items():
        assert sha(BASE / relative) == expected, relative
    selection = read(BASE / "evaluation/subset_selection.json")
    keep = selection["retained_domain_ids"]
    removed = selection["removed_domain_ids"]
    assert len(keep) == 30 and len(removed) == 25 and not set(keep) & set(removed)
    cases = read(BASE / "evaluation/case_manifest.json")
    assert [c["case_id"] for c in cases] == keep
    assert sorted(p.name for p in BASE.glob("H[0-9][0-9]") if p.is_dir()) == keep
    assert sorted(p.name for p in (OUT / "by_domain").iterdir() if p.is_dir()) == keep
    assert sorted(p.name for p in (OUT / "inputs/domains").iterdir() if p.is_dir()) == keep
    assert sorted(p.name for p in (BASE / "evaluation").glob("H[0-9][0-9]") if p.is_dir()) == keep
    groups = read(BASE / "evaluation/group_manifest.json")
    assert sorted(m[0] for g in groups for m in g["members"]) == keep
    source = read(BASE / "source_manifest.json")
    for entry in source["files"]:
        assert sha(BASE / entry["local_path"]) == entry["sha256"]
    screening = read(OUT / "evaluation/candidate_screening.json")
    assert len(screening["candidates"]) == 1500
    assert Counter(r["domain"] for r in screening["candidates"]) == {cid: 50 for cid in keep}
    counts, failure_kinds = Counter(), Counter()
    references = set()
    summary = read(OUT / "summary.json")
    for case in cases:
        cid = case["case_id"]
        assert sha(BASE / cid / "domain.pddl") == case["domain_sha256"]
        assert sha(OUT / "inputs/domains" / cid / "domain.pddl") == case["domain_sha256"]
        manifest = read(OUT / "by_domain" / cid / "manifest.json")
        assert manifest["selected_successes"] == manifest["selected_failures"] == 2
        assert manifest["missing_successes"] == manifest["missing_failures"] == 0
        assert {p.stem.removesuffix(".trace") for p in (OUT / "by_domain" / cid).glob("*.trace.json")} == {"S1", "S2", "F1", "F2"}
        assert len({r["problem_id"] for r in manifest["traces"]}) == 4
        for pick in manifest["traces"]:
            trace = read(OUT / "by_domain" / cid / (pick["trace_id"] + ".trace.json"))
            plan = OUT / trace["plan_path"]
            assert trace["domain"] == cid and trace["domain_sha256"] == case["domain_sha256"]
            assert sha(plan) == trace["plan_sha256"]
            assert sha(OUT / trace["problem_path"]) == trace["problem_sha256"]
            assert (OUT / "by_domain" / cid / (pick["trace_id"] + ".plan")).read_bytes() == plan.read_bytes()
            assert trace["success"] == pick["expected_success"]
            counts["attempted_steps"] += verify_trace(trace, plan)
            counts["successes" if trace["success"] else "failures"] += 1
            if not trace["success"]:
                failure_kinds[trace["failure_kind"]] += 1
            reference = read(OUT / "evaluation/reference_traces" / (trace["problem_id"] + ".trace.json"))
            assert reference["success"]
            assert reference["plan_sha256"] == trace["plan_sha256"]
            assert reference["problem_sha256"] == trace["problem_sha256"]
            assert reference["problem_goals"] == trace["problem_goals"]
            if trace["problem_id"] not in references:
                verify_trace(reference, plan)
                references.add(trace["problem_id"])
    assert counts["successes"] == summary["success_traces"] == 60
    assert counts["failures"] == summary["failure_traces"] == 60
    assert summary["native_mutant_traces"] == 120
    assert summary["domains"] == summary["domains_with_two_success_two_failure"] == 30
    assert len(references) == summary["native_reference_full_traces"]
    assert dict(failure_kinds) == summary["failure_kinds"]
    report = {"status": "pass", "date": "2026-10-22", "retained_domains": 30, "removed_domains": 25,
              "native_mutant_traces_reused_byte_identically": 120, "successes": 60, "failures": 60,
              "each_domain_has_two_success_two_failure": True, "reference_full_traces": len(references),
              "saved_grounded_attempted_steps_rechecked": counts["attempted_steps"],
              "removed_domains_absent_from_active_Domains_inputs_traces_and_case_manifests": True,
              "plan_Problem_Goal_and_source_bytes_preserved": True, "no_replanning_or_new_simulation": True,
              "verification_scope": "File SHA-256 and replay of saved grounded preconditions/effects; source PDDL/parser audit retained by byte identity"}
    (BASE / "evaluation/package_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
