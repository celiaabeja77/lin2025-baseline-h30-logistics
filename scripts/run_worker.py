"""Run unchanged author main.py; capture full repair literals at its output hook."""
import json
import os
import runpy
import sys
import time
from pathlib import Path

from benchmark_io import apply_edits, assertion_set, dump, read_pddl


def main():
    if os.environ.get("LIN_REPRO_TRACE_AFTER"):
        import faulthandler
        faulthandler.dump_traceback_later(int(os.environ["LIN_REPRO_TRACE_AFTER"]), repeat=True)
    repo, inputs, output, mode = map(Path, sys.argv[1:5])
    mode = str(mode)
    sys.path.insert(0, str(repo))
    import repairer
    from hitter.maxsat import MaxSATHitter
    if os.environ.get("LIN_REPRO_CARDINALITY_ENCODING"):
        from functools import partial
        import hitter.maxsat
        # Supplemental diagnostic only. Stock benchmark leaves this unset.
        hitter.maxsat.FM = partial(hitter.maxsat.FM, enc=int(os.environ["LIN_REPRO_CARDINALITY_ENCODING"]))

    counts = {"solver_calls": 0, "hard_conflicts": 0, "candidate_variables": 0}
    original_top, original_add = MaxSATHitter.top, MaxSATHitter.add_conflict

    def top(self):
        counts["solver_calls"] += 1
        return original_top(self)

    def add(self, conflict, weight=None):
        counts["hard_conflicts" if weight is None else "candidate_variables"] += 1
        return original_add(self, conflict, weight)

    MaxSATHitter.top, MaxSATHitter.add_conflict = top, add
    original_write = repairer.Repairer.write
    captured = []

    def write(self, outfile):
        original_write(self, outfile)
        for repair in self._repairs:
            captured.append({"action": repair.target,
                             "component": "pre" if repair.__class__.__name__ == "RepairPrec" else "eff",
                             "negative": repair.atom.negated,
                             "predicate": repair.atom.predicate,
                             "arguments": list(repair.atom.args),
                             "operation": repair.operation,
                             "author_line": str(repair)})

    repairer.Repairer.write = write
    sys.argv = [str(repo / "main.py"), str(inputs), "--domain_file", "domain-modified.pddl", "--outfile", str(output / "repairs.txt"), "--log", os.environ.get("LIN_REPRO_LOG_LEVEL", "INFO")]
    if mode == "positive_only":
        sys.argv.append("--ignore_black_list")
    started = time.perf_counter()
    runpy.run_path(str(repo / "main.py"), run_name="__main__")
    algorithm_seconds = time.perf_counter() - started
    captured.sort(key=lambda r: (r["action"], r["component"], r["negative"], r["predicate"], r["arguments"], r["operation"]))
    (output / "repairs_full.json").write_text(json.dumps(captured, indent=2), encoding="utf-8")
    repaired = apply_edits(read_pddl(inputs / "domain-modified.pddl"), captured)
    repaired_path = output / "domain-repaired.pddl"
    repaired_path.write_text("; Applied exact in-memory repairs captured from unchanged author algorithm.\n" + dump(repaired) + "\n", encoding="utf-8")
    # Parse exported PDDL again so validation is performed on the saved artifact.
    assert assertion_set(read_pddl(repaired_path)) == assertion_set(repaired)
    (output / "worker_stats.json").write_text(json.dumps({**counts, "algorithm_seconds": algorithm_seconds, "cardinality_encoding_override": os.environ.get("LIN_REPRO_CARDINALITY_ENCODING")}, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
