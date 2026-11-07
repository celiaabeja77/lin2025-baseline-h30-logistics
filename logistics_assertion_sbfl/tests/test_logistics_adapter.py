"""Regression checks for schema adaptation and missing-assertion evaluation."""

import copy
import unittest

from run_all import adapt_trace, compute_metrics, evaluate_case
from src.assertion_coverage import CoverageTrace, count_spectrum
from src.pddl_assertions import extract_assertions
from src.ranking import rank_assertions
from src.utils import DataError


DOMAIN = """(define (domain tiny) (:requirements :strips)
(:predicates (p ?x) (q ?x))
(:action A :parameters (?x) :precondition (p ?x) :effect (q ?x)))"""


def fixture():
    domain = extract_assertions(DOMAIN)
    traces = (CoverageTrace("F", False, frozenset(a.assertion_id for a in domain.assertions)),
              CoverageTrace("S", True, frozenset()))
    coverage = {a.assertion_id: (1, 0) for a in domain.assertions}
    return {"domain": domain, "traces": traces, "coverage": coverage,
            "ranking": rank_assertions("H00", domain.assertions, count_spectrum(coverage, traces))}


class LogisticsAdapterTests(unittest.TestCase):
    def test_label_is_explicit_not_filename(self):
        raw = {"trace_id": "F1", "success": True, "sequence_completed": True,
               "full_goal_reached": True, "validator_status": "VALID"}
        original = copy.deepcopy(raw)
        self.assertTrue(adapt_trace(raw)["test_passed"])
        self.assertEqual(raw, original)

    def test_completed_but_goal_not_reached_remains_failure(self):
        raw = {"success": False, "sequence_completed": True, "full_goal_reached": False,
               "validator_status": "INVALID"}
        self.assertFalse(adapt_trace(raw)["test_passed"])

    def test_incomplete_or_goal_false_cannot_be_success(self):
        for completed, goal in ((False, True), (True, False), (False, False)):
            with self.subTest(completed=completed, goal=goal), self.assertRaises(DataError):
                adapt_trace({"success": True, "sequence_completed": completed,
                             "full_goal_reached": goal, "validator_status": "VALID"})

    def test_string_label_and_missing_label_rejected(self):
        for label in ("true", 1, None):
            with self.subTest(label=label), self.assertRaises(DataError):
                adapt_trace({"success": label, "sequence_completed": True,
                             "full_goal_reached": True, "validator_status": "VALID"})

    def test_validator_disagreement_rejected(self):
        with self.assertRaises(DataError):
            adapt_trace({"success": True, "sequence_completed": True,
                         "full_goal_reached": True, "validator_status": "INVALID"})

    def test_deleted_assertion_never_becomes_virtual_candidate(self):
        scored = fixture()
        original = copy.deepcopy(scored["ranking"])
        gold = {"case_id": "H00", "faulty_action": "A", "component": ":effect",
                "original_slot_1based": 2, "original_assertion": "(p ?x)", "replacement_assertion": None}
        result = evaluate_case("H00", scored, gold)
        self.assertEqual(scored["ranking"], original)
        self.assertEqual(len(result["ranking"]), 2)
        self.assertFalse(any(r["is_ground_truth"] for r in result["ranking"]))
        self.assertFalse(result["summary"]["ground_truth_in_candidate_set"])
        self.assertNotIn("ground_truth_score", result["summary"])
        self.assertFalse(result["summary"]["tie_aware_top5"])

    def test_added_literal_uses_existing_mutant_slot(self):
        scored = fixture()
        gold = {"case_id": "H00", "faulty_action": "A", "component": ":effect",
                "original_slot_1based": 1, "original_assertion": None, "replacement_assertion": "(q ?x)", "operation": "add"}
        result = evaluate_case("H00", scored, gold)
        self.assertEqual(result["summary"]["ground_truth_assertion"], "A.effect[1]")
        self.assertTrue(result["summary"]["ground_truth_in_candidate_set"])

    def test_changing_gold_changes_only_annotation_and_evaluation(self):
        scored = fixture()
        variants = []
        for component, literal in ((":precondition", "(p ?x)"), (":effect", "(q ?x)")):
            gold = {"case_id": "H00", "faulty_action": "A", "component": component,
                    "original_slot_1based": 1, "original_assertion": "(p ?x)", "replacement_assertion": literal}
            result = evaluate_case("H00", scored, gold)
            variants.append([{k: v for k, v in row.items() if k != "is_ground_truth"} for row in result["ranking"]])
        self.assertEqual(variants[0], variants[1])
        self.assertEqual(variants[0], scored["ranking"])

    def test_absent_cases_are_misses_in_all_case_denominator(self):
        records = []
        for k in (1, 3, 5):
            records.extend([{"case_id": "H00", "k": k, "strict_hit": True, "tie_aware_hit": True, "evaluation_status": "rankable"},
                            {"case_id": "H01", "k": k, "strict_hit": False, "tie_aware_hit": False,
                             "evaluation_status": "missing_assertion_not_in_candidate_set"}])
        metrics = compute_metrics(records)
        self.assertEqual([r["strict_accuracy"] for r in metrics[:3]], [0.5] * 3)
        self.assertEqual([r["num_evaluated_cases"] for r in metrics[:3]], [2] * 3)
        self.assertEqual([r["strict_accuracy"] for r in metrics[3:]], [1.0] * 3)
        self.assertEqual([r["num_evaluated_cases"] for r in metrics[3:]], [1] * 3)


if __name__ == "__main__":
    unittest.main()
