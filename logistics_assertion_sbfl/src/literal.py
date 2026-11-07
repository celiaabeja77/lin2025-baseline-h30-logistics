"""S-expression literal syntax only; no state evaluation."""

from .pddl_assertions import tokenize


def _atom(text):
    if not isinstance(text, str):
        raise ValueError("Literal must be a string.")
    roots, stack = [], []
    for token in tokenize(text):
        if token == "(":
            node = []
            (stack[-1] if stack else roots).append(node)
            stack.append(node)
        elif token == ")":
            if not stack:
                raise ValueError("Unbalanced literal: " + text)
            stack.pop()
        elif stack:
            stack[-1].append(token)
        else:
            raise ValueError("Atom outside literal parentheses: " + text)
    if stack or len(roots) != 1 or not roots[0]:
        raise ValueError("Expected one balanced literal: " + text)
    parts = roots[0]
    negative = isinstance(parts[0], str) and parts[0].casefold() == "not"
    if negative:
        if len(parts) != 2 or not isinstance(parts[1], list):
            raise ValueError("Expected (not (predicate ...)).")
        parts = parts[1]
    if (not parts or any(not isinstance(token, str) for token in parts)
            or parts[0].casefold() in {"and", "or", "not", "when", "forall", "exists", "="}):
        raise ValueError("Expected an atomic literal: " + text)
    return negative, tuple(token.casefold() for token in parts)
