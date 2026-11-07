"""Pure assertion-touch SBFL + Ochiai on the existing Logistics H30 traces.

The nine copied baseline modules are unchanged. This adapter handles the new
directory layout and explicit `success` labels. All blind rankings are written
before evaluation metadata is loaded. No planning or simulation is performed.
"""

import argparse
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path

from baseline_topk import aggregate_metrics, topk_for_case
from src.assertion_coverage import action_parameters, count_spectrum, parse_coverage_trace
from src.evaluation import evaluate_ground_truth, same_action_tie_check
from src.pddl_assertions import load_domain
from src.ranking import rank_assertions
from src.utils import DataError, read_json, write_csv, write_json


POLICY = "precondition_checked_effect_applied"
TRACE_ROOT = Path("traces/official_2success_2failure/by_domain")
KS = (1, 3, 5)
RANK_FIELDS = ("case_id", "assertion_id", "action", "section", "component_type", "literal",
               "ef", "ep", "total_failure_traces", "ochiai", "best_rank", "worst_rank",
               "average_rank", "tie_group_size")
SUMMARY_FIELDS = ("case_id", "status", "coverage_policy", "evaluation_status", "group_id", "group_title",
                  "operation", "num_assertions", "num_traces", "num_success_traces", "num_failure_traces",
                  "ground_truth_in_candidate_set", "ground_truth_assertion", "reference_fault_slot",
                  "original_assertion", "replacement_assertion", "ef", "ep", "total_failure_traces",
                  "ground_truth_score", "best_rank", "worst_rank", "average_rank", "tie_group_size",
                  "strict_top1", "strict_top3", "strict_top5", "tie_aware_top1", "tie_aware_top3", "tie_aware_top5",
                  "same_action_coverage_identical", "same_action_ef_ep_identical", "same_action_score_identical", "notes")
TOPK_FIELDS = ("case_id", "k", "num_candidates", "evaluation_status", "ground_truth_assertion",
               "strict_hit", "tie_aware_hit")
METRIC_FIELDS = ("scope", "k", "num_evaluated_cases", "num_rankable_cases", "num_missing_assertion_cases",
                 "strict_hits", "strict_accuracy", "tie_aware_hits", "tie_aware_accuracy")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fingerprint(root):
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def csv_output(path, fields, rows):
    write_csv(path, fields, ({field: row.get(field, "") for field in fields} for row in rows))


def adapt_trace(raw):
    """Map an explicit label, never an S/F filename or ground truth."""
    for name in ("success", "sequence_completed", "full_goal_reached"):
        if type(raw.get(name)) is not bool:
            raise DataError(name + " must be an explicit JSON boolean")
    if raw["success"] != (raw["sequence_completed"] and raw["full_goal_reached"]):
        raise DataError("success contradicts completion AND full original goal")
    if raw.get("validator_status") not in {"VALID", "INVALID"}:
        raise DataError("Missing supported validator status")
    if raw["success"] != (raw["validator_status"] == "VALID"):
        raise DataError("Simulator label and validator disagree")
    # In-memory schema translation only: original JSON bytes are never edited.
    return {**raw, "test_passed": raw["success"]}


def score_case(project, case_id):
    """Read only the mutant Domain and its four mutant traces."""
    domain_path = project / case_id / "domain.pddl"
    domain = load_domain(domain_path)
    parameters = action_parameters(domain_path.read_text(encoding="utf-8-sig"))
    files = sorted((project / TRACE_ROOT / case_id).glob("*.trace.json"))
    if len(files) != 4:
        raise DataError(case_id + ": expected exactly four selected traces")
    traces = []
    for path in files:
        raw = read_json(path)
        if raw.get("domain_sha256") != sha(domain_path):
            raise DataError(case_id + ": trace/domain hash mismatch")
        traces.append(parse_coverage_trace(adapt_trace(raw), case_id, domain, parameters,
                                         path.relative_to(project).as_posix()))
    if len({t.trace_id for t in traces}) != len(traces):
        raise DataError(case_id + ": duplicate trace IDs")
    if sum(t.passed for t in traces) != 2:
        raise DataError(case_id + ": expected two successes and two failures")
    coverage = {a.assertion_id: tuple(int(a.assertion_id in t.covered_assertions) for t in traces)
                for a in domain.assertions}
    counts = count_spectrum(coverage, traces)
    ranking = rank_assertions(case_id, domain.assertions, counts)
    return {"domain": domain, "traces": tuple(traces), "coverage": coverage, "ranking": ranking}


def evaluate_case(case_id, scored, metadata):
    """Attach gold after scoring. Deleted literals never become candidates."""
    if metadata.get("case_id") != case_id:
        raise DataError("Ground truth case mismatch")
    original, replacement = metadata["original_assertion"], metadata["replacement_assertion"]
    operation = "delete" if replacement is None else "add" if original is None else "replace"
    if original is None and replacement is None:
        raise DataError("Both original and replacement assertions are absent")
    if metadata.get("operation", operation) != operation:
        raise DataError("Inconsistent edit operation")
    slot = f"{metadata['faulty_action']}.{metadata['component'].lstrip(':')}[{metadata['original_slot_1based']}]"
    summary = {"case_id": case_id, "status": "OK", "coverage_policy": POLICY,
               "group_id": metadata.get("group_id", ""), "group_title": metadata.get("group_title", ""),
               "operation": operation, "num_assertions": len(scored["domain"].assertions),
               "num_traces": len(scored["traces"]), "num_success_traces": sum(t.passed for t in scored["traces"]),
               "num_failure_traces": sum(not t.passed for t in scored["traces"]),
               "reference_fault_slot": slot, "original_assertion": original or "",
               "replacement_assertion": replacement or ""}
    if operation == "delete":
        ranking = [{**row, "is_ground_truth": False} for row in scored["ranking"]]
        summary.update(evaluation_status="missing_assertion_not_in_candidate_set",
                       ground_truth_in_candidate_set=False, ground_truth_assertion="",
                       total_failure_traces=summary["num_failure_traces"],
                       notes="Deleted gold literal is absent from existing-assertion candidates; no score or rank is fabricated. Counted as a miss in all-case exact-assertion accuracy.")
        for k in KS:
            summary[f"strict_top{k}"] = summary[f"tie_aware_top{k}"] = False
    else:
        adapted_gold = {"assertion_id": slot, "faulty_action": metadata["faulty_action"],
                        "component_section": metadata["component"],
                        "assertion_index_1based": metadata["original_slot_1based"],
                        "injected_assertion": replacement}
        _, evaluation, ranking = evaluate_ground_truth(adapted_gold, scored["domain"].assertions, scored["ranking"])
        gold = next(r for r in ranking if r["is_ground_truth"])
        summary.update(evaluation, evaluation_status="rankable", ground_truth_in_candidate_set=True,
                       ef=gold["ef"], ep=gold["ep"], total_failure_traces=gold["total_failure_traces"],
                       notes="Binary assertion-touch SBFL + Ochiai; exact-score ties retained. Gold is evaluation only.")
    tie_rows, tie_checks = same_action_tie_check(metadata["faulty_action"], ranking, scored["coverage"])
    summary.update(tie_checks)
    return {**scored, "ranking": ranking, "summary": summary, "tie_checks": tie_checks,
            "tie_rows": tie_rows}


def compute_metrics(topk_summary):
    metrics = []
    for scope, selected in (("all_cases_missing_assertions_count_as_misses", topk_summary),
                            ("rankable_existing_assertion_cases", [r for r in topk_summary if r["evaluation_status"] == "rankable"])):
        for row in aggregate_metrics(selected):
            at_k = [r for r in selected if r["k"] == row["k"]]
            metrics.append({"scope": scope, **row,
                            "num_rankable_cases": sum(r["evaluation_status"] == "rankable" for r in at_k),
                            "num_missing_assertion_cases": sum(r["evaluation_status"] != "rankable" for r in at_k)})
    return metrics


def write_blind(output, case_id, scored):
    folder = output / case_id
    csv_output(folder / "ranking_blind.csv", RANK_FIELDS, scored["ranking"])
    ids = [t.trace_id for t in scored["traces"]]
    csv_output(folder / "coverage_matrix.csv", ("assertion_id", *ids),
               ({"assertion_id": a, **dict(zip(ids, v))} for a, v in scored["coverage"].items()))
    csv_output(folder / "trace_labels.csv", ("trace_id", "result", "problem_origin", "label_field", "source_file"),
               ({"trace_id": t.trace_id, "result": "success" if t.passed else "failure",
                 "problem_origin": t.problem_origin, "label_field": "success", "source_file": t.source_file}
                for t in scored["traces"]))


def write_reports(output, summaries, topk_summary, metrics):
    all_metrics = [m for m in metrics if m["scope"].startswith("all_cases")]
    supported = [m for m in metrics if m["scope"] == "rankable_existing_assertion_cases"]
    missing = [s["case_id"] for s in summaries if not s["ground_truth_in_candidate_set"]]
    lines = ["# Logistics SBFL＋Ochiai", "",
             f"{len(summaries)} 個錯誤版本；{sum(s['num_traces'] for s in summaries)} 條既有軌跡；"
             f"{sum(s['num_success_traces'] for s in summaries)} 成功／{sum(s['num_failure_traces'] for s in summaries)} 失敗。每版獨立計分。", "",
             "Coverage 沿用 Depot baseline：precondition 的 grounded literal 出現在檢查紀錄就算碰到，無論真值；"
             "動作 executed=true 時，其所有無條件 STRIPS effects 都算碰到，包含未改變狀態的效果。每條軌跡每條 assertion 只記 0/1。", "",
             "Ochiai = ef / sqrt(F × (ef + ep))；ef、ep 分別是碰到它的失敗、成功軌跡數；F 是該版全部失敗軌跡數，本資料每版 F=2。分母為零時分數為 0。", "",
             "先完成所有現有 assertions 的盲排名，才載入 evaluation/fault_info。正確 Domain、reference traces、狀態差異、條件真值與首次偏離均不參與計分。", "",
             "Strict Top-K：worst_rank ≤ K；Tie-aware Top-K：best_rank ≤ K。候選清單保留完整同分群組，所以可超過 K 條。", "",
             "## Top-1／3／5（全部案例）", "",
             "缺失 assertion 在此 baseline 沒有候選槽位；全案例 exact-assertion 指標將這類案例計為未命中。", "",
             "| K | 案例數 | Strict Accuracy | Tie-aware Accuracy |", "|---:|---:|---:|---:|"]
    for m in all_metrics:
        lines.append(f"| {m['k']} | {m['num_evaluated_cases']} | {m['strict_accuracy']:.2%} ({m['strict_hits']}/{m['num_evaluated_cases']}) | {m['tie_aware_accuracy']:.2%} ({m['tie_aware_hits']}/{m['num_evaluated_cases']}) |")
    lines.extend(["", "## 真正錯誤仍存在於候選集的案例", "",
                  "這是候選集涵蓋範圍內的補充指標，不能取代全案例結果。", "",
                  "| K | 可排名案例數 | Strict Accuracy | Tie-aware Accuracy |", "|---:|---:|---:|---:|"])
    for m in supported:
        fmt = lambda value: f"{value:.2%}" if isinstance(value, (int, float)) else "N/A"
        lines.append(f"| {m['k']} | {m['num_evaluated_cases']} | {fmt(m['strict_accuracy'])} ({m['strict_hits']}/{m['num_evaluated_cases']}) | {fmt(m['tie_aware_accuracy'])} ({m['tie_aware_hits']}/{m['num_evaluated_cases']}) |")
    lines.extend(["", "## SBFL 排名結果", "",
                  "缺失案例只顯示原版故障槽位，ef、ep、score、rank 留空，不把被刪除的 literal 加回方法輸入。", "",
                  "| Case | 編輯 | 真正錯誤／原版缺失位置 | ef | ep | F | Ochiai | 排名區間 | 並列數 |",
                  "|---|---|---|---:|---:|---:|---:|---|---:|"])
    for s in summaries:
        present = s["ground_truth_in_candidate_set"]
        location = s.get("ground_truth_assertion") or s["reference_fault_slot"] + "（已刪除）"
        score = f"{s['ground_truth_score']:.6f}" if present else "—"
        rank = f"{s['best_rank']}～{s['worst_rank']}" if present else "無對應候選"
        lines.append(f"| {s['case_id']} | {s['operation']} | {location} | {s.get('ef', '—')} | {s.get('ep', '—')} | {s['num_failure_traces']} | {score} | {rank} | {s.get('tie_group_size', '—')} |")
    lines.extend(["", "## Top-K 候選數與命中", "",
                  "| Case | Top-1 候選數 | Top-3 候選數 | Top-5 候選數 | Strict 最小命中 K（1/3/5） | Tie-aware 最小命中 K（1/3/5） |",
                  "|---|---:|---:|---:|---|---|"])
    for s in summaries:
        rows = [r for r in topk_summary if r["case_id"] == s["case_id"]]
        first = lambda key: next((f"Top-{r['k']}" for r in rows if r[key]), "未命中")
        lines.append(f"| {s['case_id']} | {rows[0]['num_candidates']} | {rows[1]['num_candidates']} | {rows[2]['num_candidates']} | {first('strict_hit')} | {first('tie_aware_hit')} |")
    rankable = [s for s in summaries if s["ground_truth_in_candidate_set"]]
    if rankable:
        top_gold = sum(s["best_rank"] == 1 for s in rankable)
        sizes = [s["tie_group_size"] for s in rankable if s["best_rank"] == 1]
        lines.extend(["", "## 本次觀察", "",
                      f"- {len(rankable)} 個可排名案例中，{top_gold} 案真正錯誤位於最高分群組；這是候選群組命中，不能解讀為唯一第一名。"])
        if sizes:
            lines.append(f"- 真正錯誤所在的最高分群組有 {min(sizes)}～{max(sizes)} 條並列。")
        for s in rankable:
            if s["tie_group_size"] == s["num_assertions"]:
                lines.append(f"- {s['case_id']} 的全部 {s['num_assertions']} 條 assertions 都同分，這一案的分數未縮小候選範圍。")
    lines.extend(["", "## 解讀範圍", "",
                  f"- 缺失 assertion 案例：{'、'.join(missing) if missing else '無'}。它們仍有其餘現有 assertions 的完整排名。",
                  "- 本次使用套件內已選定的每版 2 成功＋2 失敗，並非全部 50 題都投入 SBFL，各版本使用的四個 Problem 也可能不同。",
                  "- 成功／失敗平衡與案例保留條件屬資料選樣設計；結果是這個選定子集的定位表現。",
                  "- 同分代表此 coverage 與分數不能排序群組內候選；顯示順序不是額外的名次。",
                  "- 每案 ranking_blind.csv、ranking.csv、coverage_matrix.csv、trace_labels.csv、top1/3/5.csv 可供追查。",
                  "- 本次沒有新建 fault、改寫 Problem／Goal／Plan／Trace、重新規劃、重新模擬、使用模型或進行 repair。", ""])
    (output / "report.md").write_text("\n".join(lines), encoding="utf-8")
    (output / "top_k.md").write_text("\n".join(lines[:lines.index("## SBFL 排名結果")]) + "\n\n逐案候選數與完整排名見 report.md。\n", encoding="utf-8")


def run(project, output, cases=None, emit=print):
    project, output = Path(project).resolve(), Path(output).resolve()
    if output == project or project in output.parents or output in project.parents:
        raise DataError("Output must be separate from, and not an ancestor of, the input package")
    before = fingerprint(project)
    index = read_json(project / "SHA256SUMS.json")
    for relative, expected in index.items():
        if before.get(relative) != expected:
            raise DataError("Source package hash mismatch: " + relative)
    discovered = sorted(p.name for p in project.iterdir() if p.is_dir() and re.fullmatch(r"H\d+", p.name))
    if cases is None:
        cases = discovered
    if not cases or any(c not in discovered for c in cases):
        raise DataError("No cases or an unknown case selected")
    scored_cases, blind_hashes = {}, {}
    # Barrier: every blind ranking is complete before reading any gold metadata.
    for cid in cases:
        scored = score_case(project, cid)
        write_blind(output, cid, scored)
        scored_cases[cid] = scored
        blind_hashes[cid] = sha(output / cid / "ranking_blind.csv")
        emit(f"SCORED {cid}: 4 traces; {len(scored['domain'].assertions)} existing assertions")
    summaries, topk_summary = [], []
    for cid, scored in scored_cases.items():
        metadata = read_json(project / "evaluation" / cid / "fault_info.json")
        if metadata.get("domain_sha256") != before[f"{cid}/domain.pddl"]:
            raise DataError("Gold/domain hash mismatch: " + cid)
        computed = evaluate_case(cid, scored, metadata)
        summary = computed["summary"]
        summaries.append(summary)
        folder = output / cid
        csv_output(folder / "ranking.csv", (*RANK_FIELDS, "is_ground_truth"), computed["ranking"])
        write_json(folder / "summary.json", summary)
        write_json(folder / "same_action_tie_check.json", computed["tie_checks"])
        candidates, rows = topk_for_case(cid, computed["ranking"])
        for row in rows:
            row["evaluation_status"] = summary["evaluation_status"]
            if not summary["ground_truth_in_candidate_set"]:
                row["strict_hit"] = row["tie_aware_hit"] = False
        for k, selected in candidates.items():
            csv_output(folder / f"top{k}.csv", (*RANK_FIELDS, "is_ground_truth"), selected)
        topk_summary.extend(rows)
        if sha(folder / "ranking_blind.csv") != blind_hashes[cid]:
            raise DataError("Blind ranking changed during evaluation")
    metrics = compute_metrics(topk_summary)
    csv_output(output / "summary.csv", SUMMARY_FIELDS, summaries)
    csv_output(output / "top_k_summary.csv", TOPK_FIELDS, topk_summary)
    csv_output(output / "top_k_metrics.csv", METRIC_FIELDS, metrics)
    write_reports(output, summaries, topk_summary, metrics)
    after = fingerprint(project)
    if before != after:
        raise DataError("Source input bytes changed")
    reuse = read_json(Path(__file__).parent / "baseline_reuse.json")
    for entry in reuse:
        if sha(Path(__file__).parent / entry["copy"]) != entry["sha256"]:
            raise DataError("Reused baseline module changed: " + entry["copy"])
    write_json(output / "method.json", {
        "method": "pure assertion-level SBFL", "formula": "Ochiai",
        "formula_expression": "ef / sqrt(F * (ef + ep)); zero denominator -> 0",
        "coverage_policy": POLICY, "binary_per_trace": True, "condition_truth_used_for_scoring": False,
        "state_difference_used_for_scoring": False, "ground_truth_used_for_scoring": False,
        "reference_model_or_traces_used_for_scoring": False, "ml_or_llm_used": False,
        "explicit_label": "success", "label_consistency": "sequence_completed AND full_goal_reached",
        "preconditions": "Grounded literal in attempted step grounded_preconditions check record",
        "effects": "All unconditional effects of executed actions, including no-op effects",
        "ties": "Exact equal score -> shared best/worst/average rank; no arbitrary tie breaking",
        "missing_assertions": "No gold-derived virtual candidates; unrankable, counted as misses in all-case accuracy",
        "strict_topk": "worst_rank <= K", "tie_aware_topk": "best_rank <= K",
        "selected_traces": "Only the four existing mutant traces per case; no reference traces in spectra",
    })
    write_json(output / "run_manifest.json", {
        "created_at_utc": datetime.now(timezone.utc).isoformat(), "input_project": str(project),
        "cases": list(cases), "case_count": len(cases), "mutant_trace_count": sum(s["num_traces"] for s in summaries),
        "rankable_case_count": sum(s["ground_truth_in_candidate_set"] for s in summaries),
        "missing_assertion_cases": [s["case_id"] for s in summaries if not s["ground_truth_in_candidate_set"]],
        "input_files_before_and_after_identical": True, "source_input_file_count": len(before),
        "source_sha256_index_entries_verified": len(index), "input_sha256": before,
        "all_blind_rankings_saved_before_gold_loaded": True, "blind_ranking_sha256": blind_hashes,
        "baseline_modules_reused_byte_identically": reuse, "new_planner_runs": 0,
        "new_simulator_runs": 0, "new_faults_created": 0,
    })
    return summaries, metrics


def main():
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=root.parent / "experiments/logistics_challenge_30_validated")
    parser.add_argument("--output", type=Path, default=root / "results")
    parser.add_argument("--case", help="Optional one H case; default all 30 existing cases")
    args = parser.parse_args()
    summaries, metrics = run(args.project, args.output, [args.case] if args.case else None)
    print(f"DONE: {len(summaries)} cases; summary/report in {args.output.resolve()}")
    for row in metrics:
        if row["scope"].startswith("all_cases"):
            print(f"Top-{row['k']}: Strict {row['strict_hits']}/{row['num_evaluated_cases']}; Tie-aware {row['tie_aware_hits']}/{row['num_evaluated_cases']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
