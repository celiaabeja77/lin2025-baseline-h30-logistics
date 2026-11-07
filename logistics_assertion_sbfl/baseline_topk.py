"""Export Top-1/3/5 from existing ranking CSVs, preserving complete ties.

No domains/traces are loaded and no suspiciousness scores are recomputed.
Candidate lists use best_rank<=K; strict hits use worst_rank<=K.
"""

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path


CASES = ("D1", "D2a", "D2b", "D3")
KS = (1, 3, 5)
SUMMARY_FIELDS = ("case_id", "k", "num_candidates", "ground_truth_assertion", "strict_hit", "tie_aware_hit")
METRIC_FIELDS = ("k", "num_evaluated_cases", "strict_hits", "strict_accuracy", "tie_aware_hits", "tie_aware_accuracy")


def normalize_ranking(rows):
    normalized = []
    for source in rows:
        row = dict(source)
        for name in ("best_rank", "worst_rank", "tie_group_size"):
            row[name] = int(row[name])
        row["ochiai"] = float(row["ochiai"])
        if not math.isfinite(row["ochiai"]) or not 0 <= row["ochiai"] <= 1:
            raise ValueError("Invalid Ochiai score.")
        if row["best_rank"] < 1 or row["worst_rank"] < row["best_rank"]:
            raise ValueError("Invalid rank interval.")
        if row["tie_group_size"] != row["worst_rank"] - row["best_rank"] + 1:
            raise ValueError("Tie size differs from rank interval.")
        marker = row.get("is_ground_truth", False)
        if isinstance(marker, str):
            if marker.casefold() not in ("true", "false", ""):
                raise ValueError("Invalid ground truth annotation.")
            marker = marker.casefold() == "true"
        if type(marker) is not bool:
            raise ValueError("Invalid ground truth annotation.")
        row["is_ground_truth"] = marker
        normalized.append(row)
    if not normalized or len({row["assertion_id"] for row in normalized}) != len(normalized):
        raise ValueError("Ranking is empty or has duplicate assertion IDs.")
    if sum(row["is_ground_truth"] for row in normalized) > 1:
        raise ValueError("Expected at most one ground truth assertion per case.")
    groups = defaultdict(list)
    for row in normalized:
        groups[(row["best_rank"], row["worst_rank"])].append(row)
    expected_start, previous_score = 1, math.inf
    for (best, worst), group in sorted(groups.items()):
        scores = {row["ochiai"] for row in group}
        if best != expected_start or len(group) != worst - best + 1 or len(scores) != 1:
            raise ValueError("Incomplete or inconsistent tie group in ranking.csv.")
        score = next(iter(scores))
        if score >= previous_score:
            raise ValueError("Equal scores must share a group and scores must descend.")
        expected_start, previous_score = worst + 1, score
    return sorted(normalized, key=lambda row: row["best_rank"])


def topk_for_case(case_id, rows):
    ranking = normalize_ranking(rows)
    gold = next((row for row in ranking if row["is_ground_truth"]), None)
    outputs, summary = {}, []
    for k in KS:
        candidates = [row for row in ranking if row["best_rank"] <= k]
        outputs[k] = candidates
        summary.append({"case_id": case_id, "k": k, "num_candidates": len(candidates),
                        "ground_truth_assertion": gold["assertion_id"] if gold else "",
                        "strict_hit": gold["worst_rank"] <= k if gold else "",
                        "tie_aware_hit": gold["best_rank"] <= k if gold else ""})
    return outputs, summary


def aggregate_metrics(summary):
    rows = []
    for k in KS:
        evaluated = [row for row in summary if row["k"] == k and type(row["strict_hit"]) is bool]
        count = len(evaluated)
        strict = sum(row["strict_hit"] for row in evaluated)
        aware = sum(row["tie_aware_hit"] for row in evaluated)
        rows.append({"k": k, "num_evaluated_cases": count, "strict_hits": strict,
                     "strict_accuracy": strict / count if count else "",
                     "tie_aware_hits": aware, "tie_aware_accuracy": aware / count if count else ""})
    return rows


def write_csv(path, fields, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: str(value).lower() if type(value) is bool else value
                             for key, value in row.items()})


def export_results(results_dir, cases=None, emit=print):
    root = Path(results_dir)
    if cases is None:
        summary_path = root / "summary.csv"
        if summary_path.is_file():
            with summary_path.open(encoding="utf-8-sig", newline="") as handle:
                cases = [row["case_id"] for row in csv.DictReader(handle)
                         if row.get("status") == "OK" and row.get("case_id") in CASES]
        else:
            cases = list(CASES)
    summary = []
    for case_id in cases:
        if case_id not in CASES:
            raise ValueError("Unknown case ID: " + case_id)
        ranking_path = root / case_id / "ranking.csv"
        if not ranking_path.is_file():
            emit(f"SKIPPED {case_id}: ranking.csv not found")
            continue
        with ranking_path.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            fields = list(reader.fieldnames or [])
            candidates, rows = topk_for_case(case_id, list(reader))
        for k, selected in candidates.items():
            # Keep existing columns; do not change source ranking or scores.
            write_csv(root / case_id / f"top{k}.csv", fields,
                      ({key: row.get(key, "") for key in fields} for row in selected))
        summary.extend(rows)
        for row in rows:
            emit(f"{case_id} Top-{row['k']}: {row['num_candidates']} candidates (complete ties)")
    if not summary:
        return []
    metrics = aggregate_metrics(summary)
    write_csv(root / "top_k_summary.csv", SUMMARY_FIELDS, summary)
    write_csv(root / "top_k_metrics.csv", METRIC_FIELDS, metrics)
    markdown = ["# Top-1 / Top-3 / Top-5", "",
                "候選清單保留同分整組，採 best_rank <= K；因此清單可能超過 K 條。", "",
                "Strict 命中採 ground truth worst_rank <= K；tie-aware 命中採 best_rank <= K。", "",
                "| K | 評估案例數 | Strict 命中率 | Tie-aware 命中率 |", "|---:|---:|---:|---:|"]
    for row in metrics:
        if row["num_evaluated_cases"]:
            markdown.append(f"| {row['k']} | {row['num_evaluated_cases']} | {row['strict_accuracy']:.0%} | "
                            f"{row['tie_aware_accuracy']:.0%} |")
        else:
            markdown.append(f"| {row['k']} | 0 | 未提供 ground truth | 未提供 ground truth |")
    markdown.extend(["", "| Case | K | 候選數量 | Strict 命中 | Tie-aware 命中 |",
                     "|---|---:|---:|---|---|"])
    for row in summary:
        display = lambda value: "true" if value is True else "false" if value is False else "未提供"
        markdown.append(f"| {row['case_id']} | {row['k']} | {row['num_candidates']} | "
                        f"{display(row['strict_hit'])} | {display(row['tie_aware_hit'])} |")
    markdown.extend(["", "候選 assertions 在各案 top1.csv、top3.csv、top5.csv。此工具只讀已有 ranking.csv，未重新計分。"])
    (root / "top_k.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=Path(__file__).resolve().parent / "results")
    parser.add_argument("--case", choices=CASES)
    args = parser.parse_args()
    summary = export_results(args.results, (args.case,) if args.case else None)
    if not summary:
        print("No current ranking files were exported. Check --results and summary status.")
        return 1
    print("Top-K report: " + str(args.results / "top_k.md"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
