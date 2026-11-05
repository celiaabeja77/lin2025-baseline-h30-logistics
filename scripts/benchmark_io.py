"""Independent STRIPS replay and exact-literal evaluation (not repair generation)."""
import json
import re
from pathlib import Path


def parse(text):
    tokens = re.findall(r"\(|\)|[^\s()]+", re.sub(r";[^\n]*", "", text).lower())
    stack = [[]]
    for token in tokens:
        if token == "(":
            node = []
            stack[-1].append(node)
            stack.append(node)
        elif token == ")":
            if len(stack) == 1:
                raise ValueError("Unbalanced PDDL")
            stack.pop()
        else:
            stack[-1].append(token)
    if len(stack) != 1 or len(stack[0]) != 1:
        raise ValueError("Unbalanced PDDL")
    return stack[0][0]


def read_pddl(path):
    return parse(Path(path).read_text(encoding="utf-8"))


def dump(node):
    return "(" + " ".join(dump(x) if isinstance(x, list) else x for x in node) + ")"


def clauses(node):
    if not node:
        return []
    return node[1:] if node[0] == "and" else [node]


def typed_names(tokens):
    names = []
    skip = False
    for token in tokens:
        if skip:
            skip = False
        elif token == "-":
            skip = True
        else:
            names.append(token)
    return names


def actions(tree):
    result = {}
    for node in tree[1:]:
        if isinstance(node, list) and node and node[0] == ":action":
            fields = dict(zip(node[2::2], node[3::2]))
            result[node[1]] = {"parameters": typed_names(fields[":parameters"]), "pre": fields[":precondition"], "eff": fields[":effect"], "node": node}
    return result


def literal_key(node):
    neg = bool(node and node[0] == "not")
    atom = node[1] if neg else node
    if any(not isinstance(x, str) for x in atom):
        raise ValueError(f"Unsupported nested/numeric logical literal: {node}")
    if atom[0] in {"and", "or", "forall", "exists", "when", "imply", "increase", "decrease", "assign"}:
        raise ValueError(f"Unsupported logical literal: {node}")
    return neg, atom[0], tuple(atom[1:])


def assertion_set(tree):
    result = set()
    for name, action in actions(tree).items():
        for component in ("pre", "eff"):
            for node in clauses(action[component]):
                if node[0] == "increase":
                    # Only total-cost bookkeeping is outside Boolean plan validity.
                    if node[1] != ["total-cost"]:
                        raise ValueError("Unsupported numeric fluent")
                    continue
                neg, predicate, args = literal_key(node)
                result.add((name, component, neg, predicate, args))
    return result


def gold_edits(clean, flawed):
    a, b = assertion_set(clean), assertion_set(flawed)
    return {(1,) + x for x in a - b} | {(-1,) + x for x in b - a}


def repair_key(record):
    return (record["operation"], record["action"], record["component"], record["negative"], record["predicate"], tuple(record["arguments"]))


def apply_edits(tree, records):
    tree = json.loads(json.dumps(tree))
    indexed = actions(tree)
    for record in records:
        act = indexed[record["action"]]
        field = ":precondition" if record["component"] == "pre" else ":effect"
        node = act["node"]
        index = node.index(field) + 1
        literals = list(clauses(node[index]))
        atom = [record["predicate"]] + record["arguments"]
        lit = ["not", atom] if record["negative"] else atom
        if record["operation"] == 1:
            if lit not in literals:
                literals.append(lit)
        else:
            if lit not in literals:
                raise ValueError(f"Deleting absent assertion: {record}")
            # Author RepairPrec/RepairEffs remove every matching occurrence.
            # Generated benchmark files can contain duplicate literals.
            literals = [existing for existing in literals if existing != lit]
        node[index] = ["and"] + literals
        act["pre" if field == ":precondition" else "eff"] = node[index]
    return tree


def truth(node, state, mapping):
    if node[0] == "and":
        return all(truth(x, state, mapping) for x in node[1:])
    if node[0] == "not":
        return not truth(node[1], state, mapping)
    if node[0] == "=":
        return mapping.get(node[1], node[1]) == mapping.get(node[2], node[2])
    literal_key(node)  # reject unsupported features explicitly
    atom = tuple(mapping.get(x, x) for x in node)
    return atom in state


def read_plan(path):
    steps = []
    for line in Path(path).read_text().splitlines():
        line = line.split(";", 1)[0].strip().lower()
        if line:
            steps.append(tuple(line.strip("()").split()))
    return steps


def replay(domain, problem, steps, details=False):
    indexed = actions(domain)
    functions = {f[0] for n in domain if isinstance(n, list) and n and n[0] == ":functions" for f in n[1:] if isinstance(f, list)}
    # Reject numeric logic/updates. Static numeric functions used as action-cost
    # expressions do not change Boolean applicability or goal satisfaction.
    for action in indexed.values():
        for literal in clauses(action["pre"]):
            _, predicate, _ = literal_key(literal)
            if predicate in functions:
                raise ValueError("Numeric function used as a logical precondition")
        for literal in clauses(action["eff"]):
            if literal[0] == "increase" and literal[1] == ["total-cost"]:
                continue
            _, predicate, _ = literal_key(literal)
            if predicate in functions:
                raise ValueError("Unsupported numeric fluent update")
    initial = next(n[1:] for n in problem if isinstance(n, list) and n and n[0] == ":init")
    state = set()
    for node in initial:
        if node[0] == "=":
            if not isinstance(node[1], list) or node[1][0] not in functions:
                raise ValueError("Unsupported numeric initial state")
            continue
        if node[0] == "not":
            continue
        state.add(tuple(node))
    goal = next(n[1] for n in problem if isinstance(n, list) and n and n[0] == ":goal")
    trace = []
    for i, step in enumerate(steps):
        action = indexed[step[0]]
        if len(action["parameters"]) != len(step) - 1:
            raise ValueError("Wrong action arity")
        mapping = dict(zip(action["parameters"], step[1:]))
        unmet = [dump(c) for c in clauses(action["pre"]) if not truth(c, state, mapping)]
        if unmet:
            return {"sequence_completed": False, "full_goal_reached": False, "first_failure_index": i, "failed_action": list(step), "unmet_preconditions_lifted": unmet, **({"trace": trace} if details else {})}
        add, delete = set(), set()
        for literal in clauses(action["eff"]):
            if literal[0] == "increase":
                if literal[1] != ["total-cost"]:
                    raise ValueError("Unsupported numeric effect")
                continue
            neg, predicate, args = literal_key(literal)
            atom = (predicate,) + tuple(mapping.get(x, x) for x in args)
            (delete if neg else add).add(atom)
        state = (state - delete) | add
        if details:
            trace.append({"index": i, "action": list(step), "add": sorted(add), "delete": sorted(delete)})
    return {"sequence_completed": True, "full_goal_reached": truth(goal, state, {}), "first_failure_index": None, **({"trace": trace} if details else {})}


def plans(root):
    root = Path(root)
    for task in sorted(p for p in root.iterdir() if p.is_dir()):
        problem = task / (task.name + ".pddl")
        if not problem.exists():
            continue
        for folder, prefix, label in [("white-list", "val-plan", "positive"), ("black-list", "inval-plan", "negative")]:
            for path in sorted((task / folder).glob(prefix + "*")):
                if not re.fullmatch(re.escape(prefix) + r"(?:\.\d+)?", path.name):
                    continue
                idx = int(Path(str(path) + ".idx").read_text().strip()) if label == "negative" else None
                yield {"task": task.name, "problem": problem, "path": path, "label": label, "expected_failure_index": idx}


def evaluate(domain, root):
    records = []
    for plan in plans(root):
        result = replay(domain, read_pddl(plan["problem"]), read_plan(plan["path"]))
        expected = plan["expected_failure_index"]
        passed = (result["sequence_completed"] and result["full_goal_reached"]) if plan["label"] == "positive" else result["first_failure_index"] == expected
        records.append({"task": plan["task"], "plan": plan["path"].name, "label": plan["label"], "expected_failure_index": expected, "constraint_passed": passed, **result})
    summary = {}
    for label in ("positive", "negative"):
        selected = [r for r in records if r["label"] == label]
        summary[label + "_total"] = len(selected)
        summary[label + "_passed"] = sum(r["constraint_passed"] for r in selected)
    summary["total"] = len(records)
    summary["passed"] = sum(r["constraint_passed"] for r in records)
    summary["rate"] = summary["passed"] / summary["total"] if summary["total"] else None
    return summary, records


def paper_metrics(lines, flaws_path):
    # Match the official notebook's predicate-level metric, including its
    # per-line precision numerator and prefix-collapsed recall denominator.
    flaws = {}
    for line in Path(flaws_path).read_text().splitlines():
        if line.strip():
            *parts, op = line.strip().split(",")
            flaws[tuple(parts)] = int(op)
    predicted = {}
    hits = count = 0
    for line in lines:
        if line.strip():
            *parts, op = line.strip().split(",")
            prefix, op = tuple(parts), int(op)
            count += 1
            hits += prefix in flaws and op + flaws[prefix] == 0
            predicted[prefix] = op
    recovered = sum(prefix in predicted and op + predicted[prefix] == 0 for prefix, op in flaws.items())
    # Empty prediction: use precision=0 (official notebook returns None instead).
    precision = hits / count if count else 0.0
    recall = recovered / len(flaws) if flaws else None
    return {"paper_precision": precision, "paper_recall": recall, "paper_f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0, "paper_flaws": len(flaws), "paper_empty_prediction_convention": "precision=0" if not count else None}
