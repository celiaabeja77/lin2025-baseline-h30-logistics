"""Ground truth is used only after scoring, or for input-consistency validation."""

from .pddl_assertions import tokenize
from .utils import DataError


def match_ground_truth(metadata, assertions):
    assertion_id = metadata.get("assertion_id")
    matches = [assertion for assertion in assertions if assertion.assertion_id == assertion_id]
    if len(matches) != 1:
        raise DataError("Ground truth assertion ID not found in parsed domain.")
    assertion = matches[0]
    expected_fields = {"faulty_action": assertion.action,
                       "component_section": ":" + assertion.section,
                       "assertion_index_1based": assertion.index}
    for field, expected in expected_fields.items():
        if field in metadata and metadata[field] != expected:
            raise DataError("Ground truth metadata contradicts assertion ID: " + field)
    if "injected_assertion" in metadata:
        if not isinstance(metadata["injected_assertion"], str) or \
                [token.casefold() for token in tokenize(metadata["injected_assertion"])] != \
                [token.casefold() for token in tokenize(assertion.literal)]:
            raise DataError("Ground truth injected literal differs from parsed assertion.")
    return assertion


def evaluate_ground_truth(metadata, assertions, ranking):
    ground_truth = match_ground_truth(metadata, assertions)
    row = next(row for row in ranking if row["assertion_id"] == ground_truth.assertion_id)
    evaluation = {"ground_truth_assertion": ground_truth.assertion_id,
                  "ground_truth_score": row["ochiai"],
                  **{field: row[field] for field in
                     ("best_rank", "worst_rank", "average_rank", "tie_group_size")}}
    for k in (1, 3, 5):
        evaluation[f"strict_top{k}"] = row["worst_rank"] <= k
        evaluation[f"tie_aware_top{k}"] = row["best_rank"] <= k
    annotated = [{**item, "is_ground_truth": item["assertion_id"] == ground_truth.assertion_id}
                 for item in ranking]
    return ground_truth, evaluation, annotated


def same_action_tie_check(faulty_action, ranking, coverage):
    rows = [dict(row) for row in ranking if row["action"] == faulty_action]
    if not rows:
        raise DataError("No assertions found in ground truth action.")
    checks = {
        "same_action_coverage_identical": len({coverage[row["assertion_id"]] for row in rows}) == 1,
        "same_action_ef_ep_identical": len({(row["ef"], row["ep"]) for row in rows}) == 1,
        "same_action_score_identical": len({row["ochiai"] for row in rows}) == 1,
    }
    return rows, checks
