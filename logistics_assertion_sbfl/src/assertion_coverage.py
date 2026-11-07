"""Binary per-assertion touch spectra: precondition checked / effect applied.

No states, condition truth, unmet literals, reference, or gold are used here.
Effects are unconditional STRIPS effects: application is inferred from executed.
"""

from dataclasses import dataclass
from pathlib import Path

from .literal import _atom
from .pddl_assertions import load_domain, parse_sexpression
from .utils import DataError, read_json


@dataclass(frozen=True)
class CoverageTrace:
    trace_id: str
    passed: bool
    covered_assertions: frozenset
    problem_origin: str = ""
    source_file: str = ""


def _boolean(value, field):
    if type(value) is not bool:
        raise DataError(field + " must be a JSON boolean.")
    return value


def action_parameters(text):
    root = parse_sexpression(text)
    parameters = {}
    for node in root[1:]:
        if not isinstance(node, list) or not node or not isinstance(node[0], str) or node[0].casefold() != ":action":
            continue
        fields = {node[index].casefold(): node[index + 1] for index in range(2, len(node), 2)}
        parameters[node[1].casefold()] = tuple(token.casefold() for token in fields[":parameters"]
                                               if token.startswith("?"))
    return parameters


def grounded_key(literal, assignment):
    negative, template = _atom(literal)
    grounded = []
    for token in template:
        if token.startswith("?"):
            if token not in assignment:
                raise DataError("Unbound action parameter: " + token)
            grounded.append(assignment[token].casefold())
        else:
            grounded.append(token)
    return negative, tuple(grounded)


def parse_coverage_trace(raw, case_id, domain, parameters, source_file=""):
    if not isinstance(raw, dict):
        raise DataError("Trace JSON must be an object.")
    trace_id = raw.get("trace_id")
    if not isinstance(trace_id, str) or not trace_id:
        raise DataError("Missing trace_id; no filename inference.")
    if "test_passed" not in raw:
        raise DataError("Missing explicit test_passed label.")
    passed = _boolean(raw["test_passed"], "test_passed")
    if "domain" in raw and (not isinstance(raw["domain"], str) or raw["domain"].casefold() != case_id.casefold()):
        raise DataError("Trace domain mismatch: " + trace_id)
    if not isinstance(raw.get("steps"), list):
        raise DataError("Trace steps must be a list.")
    assertions_by_action = {name.casefold(): [item for item in domain.assertions if item.action == name]
                            for name in domain.action_names}
    covered = set()
    for step in raw["steps"]:
        if not isinstance(step, dict):
            raise DataError("Trace step must be an object.")
        attempted = _boolean(step.get("attempted"), "attempted")
        executed = _boolean(step.get("executed"), "executed")
        if executed and not attempted:
            raise DataError("executed=true contradicts attempted=false.")
        if not attempted:
            continue
        action = step.get("action_name")
        if not isinstance(action, str) or action.casefold() not in assertions_by_action:
            raise DataError("Unknown attempted action: " + str(action))
        action = action.casefold()
        arguments = step.get("arguments")
        if (not isinstance(arguments, list) or len(arguments) != len(parameters[action])
                or any(not isinstance(arg, str) for arg in arguments)):
            raise DataError("Wrong argument list for " + action)
        assignment = dict(zip(parameters[action], arguments))
        checked = step.get("grounded_preconditions")
        if not isinstance(checked, list):
            raise DataError("Missing grounded_preconditions check record; no action-wide fallback.")
        checked_keys = {_atom(literal) for literal in checked}
        expected_keys = {grounded_key(item.literal, assignment) for item in assertions_by_action[action]
                         if item.section == "precondition"}
        if not checked_keys <= expected_keys:
            raise DataError("Checked precondition is not in the parsed action: " + action)
        for assertion in assertions_by_action[action]:
            if assertion.section == "precondition":
                if grounded_key(assertion.literal, assignment) in checked_keys:
                    covered.add(assertion.assertion_id)
            elif executed:
                # Parser accepts only unconditional STRIPS effects. A no-op effect
                # is still applied; no state-difference test is used for coverage.
                covered.add(assertion.assertion_id)
    origin = raw.get("problem_origin", "")
    if not isinstance(origin, str):
        raise DataError("problem_origin must be a string.")
    return CoverageTrace(trace_id, passed, frozenset(covered), origin, source_file)


def load_case_coverage(project, case_id):
    folder = Path(project) / "data" / case_id
    text = (folder / "domain.pddl").read_text(encoding="utf-8-sig")
    domain = load_domain(folder / "domain.pddl")
    parameters = action_parameters(text)
    files = sorted((folder / "traces").glob("*.json"))
    if not files:
        raise FileNotFoundError("no trace files found")
    traces = []
    seen = set()
    for path in files:
        try:
            trace = parse_coverage_trace(read_json(path), case_id, domain, parameters, path.name)
        except (ValueError, KeyError) as error:
            raise DataError(path.name + ": " + str(error)) from error
        if trace.trace_id in seen:
            raise DataError("Duplicate trace_id: " + trace.trace_id)
        seen.add(trace.trace_id)
        traces.append(trace)
    coverage = {item.assertion_id: tuple(int(item.assertion_id in trace.covered_assertions) for trace in traces)
                for item in domain.assertions}
    return domain, tuple(traces), coverage


def count_spectrum(coverage, traces):
    F = sum(not trace.passed for trace in traces)
    counts = {}
    for assertion_id, vector in coverage.items():
        if len(vector) != len(traces) or any(type(value) is not int or value not in (0, 1) for value in vector):
            raise DataError("Coverage must contain one integer 0/1 per trace.")
        counts[assertion_id] = {
            "ef": sum(value for value, trace in zip(vector, traces) if not trace.passed),
            "ep": sum(value for value, trace in zip(vector, traces) if trace.passed),
            "total_failure_traces": F,
        }
    return counts
