"""Parse STRIPS conjunctions into occurrence IDs without a PDDL dependency.

This parser extracts syntax; it never executes actions or reasons about states.
Unsupported PDDL constructs fail explicitly rather than losing assertions.
"""

from dataclasses import dataclass
from pathlib import Path

from .utils import DataError


@dataclass(frozen=True)
class Assertion:
    assertion_id: str
    action: str
    section: str
    index: int
    component_type: str
    literal: str


@dataclass(frozen=True)
class DomainAssertions:
    action_names: tuple
    assertions: tuple


def tokenize(text):
    """Parentheses and atoms, with semicolon comments removed by a lexer."""
    tokens, atom = [], []
    comment = False
    for char in text:
        if comment:
            if char in "\r\n":
                comment = False
            continue
        if char == ";":
            if atom:
                tokens.append("".join(atom))
                atom = []
            comment = True
        elif char in "()" or char.isspace():
            if atom:
                tokens.append("".join(atom))
                atom = []
            if char in "()":
                tokens.append(char)
        else:
            atom.append(char)
    if atom:
        tokens.append("".join(atom))
    return tokens


def parse_sexpression(text):
    roots, stack = [], []
    for token in tokenize(text):
        if token == "(":
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ")":
            if not stack:
                raise DataError("Unexpected closing parenthesis in PDDL.")
            stack.pop()
        else:
            if not stack:
                raise DataError("PDDL atom outside parentheses.")
            stack[-1].append(token)
    if stack:
        raise DataError("Unclosed parenthesis in PDDL.")
    if (len(roots) != 1 or not roots[0] or not isinstance(roots[0][0], str)
            or roots[0][0].lower() != "define"):
        raise DataError("Expected one (define ...) PDDL expression.")
    return roots[0]


def format_sexpression(node):
    return "(" + " ".join(format_sexpression(item) if isinstance(item, list) else item
                           for item in node) + ")"


def _literals(expression, predicates):
    if not isinstance(expression, list):
        raise DataError("Expected a parenthesized assertion expression.")
    if not expression:
        return []
    head = expression[0]
    if not isinstance(head, str):
        raise DataError("Invalid assertion head.")
    if head.lower() == "and":
        return [literal for child in expression[1:] for literal in _literals(child, predicates)]
    negative = head.lower() == "not"
    if negative:
        if len(expression) != 2 or not isinstance(expression[1], list):
            raise DataError("Expected (not (predicate ...)).")
        atom = expression[1]
    else:
        atom = expression
    if (not atom or not isinstance(atom[0], str) or atom[0].lower() not in predicates
            or any(not isinstance(item, str) for item in atom)):
        raise DataError("Unsupported PDDL construct or undeclared predicate: "
                        + format_sexpression(expression))
    return [(expression, negative)]


def extract_assertions(text):
    root = parse_sexpression(text)
    # PDDL keywords are case-insensitive; preserve action/predicate source spelling.
    declarations = [node for node in root[1:] if isinstance(node, list) and node
                    and isinstance(node[0], str) and node[0].lower() == ":predicates"]
    if len(declarations) != 1:
        raise DataError("Expected one :predicates declaration.")
    predicates = set()
    for declaration in declarations[0][1:]:
        if not isinstance(declaration, list) or not declaration or not isinstance(declaration[0], str):
            raise DataError("Invalid predicate declaration.")
        predicates.add(declaration[0].lower())
    actions, assertions = [], []
    for node in root[1:]:
        if not isinstance(node, list) or not node or not isinstance(node[0], str):
            continue
        if node[0].lower() == ":durative-action":
            raise DataError("Durative actions are unsupported by this STRIPS assertion parser.")
        if node[0].lower() != ":action":
            continue
        if len(node) < 2 or not isinstance(node[1], str):
            raise DataError("Missing action name.")
        action = node[1]
        if action.lower() in {name.lower() for name in actions}:
            raise DataError("Duplicate action name: " + action)
        actions.append(action)
        properties = {}
        if (len(node) - 2) % 2:
            raise DataError("Malformed action properties: " + action)
        for offset in range(2, len(node), 2):
            key = node[offset]
            if not isinstance(key, str) or not key.startswith(":"):
                raise DataError("Invalid action property: " + action)
            key = key.lower()
            if key in properties or key not in {":parameters", ":precondition", ":effect"}:
                raise DataError("Duplicate or unsupported action property: " + key)
            properties[key] = node[offset + 1]
        for section in ("precondition", "effect"):
            if ":" + section not in properties:
                raise DataError("Missing :" + section + " in " + action)
            for index, (literal, negative) in enumerate(
                    _literals(properties[":" + section], predicates), start=1):
                component = ("precondition_negative" if negative else "precondition_positive") \
                    if section == "precondition" else ("delete_effect" if negative else "add_effect")
                assertions.append(Assertion(f"{action}.{section}[{index}]", action, section,
                                            index, component, format_sexpression(literal)))
    if not actions:
        raise DataError("No :action definitions found.")
    return DomainAssertions(tuple(actions), tuple(assertions))


def load_domain(path):
    return extract_assertions(Path(path).read_text(encoding="utf-8-sig"))
