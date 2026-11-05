"""Per case: gold assertion edit vs Lin's repairs (P4, P4N), grouped over 5 seeds."""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_io import gold_edits, read_pddl  # noqa: E402

H30 = ROOT / "data" / "h30"
clean = read_pddl(H30 / "reference" / "domain.pddl")


def fmt(op, action, comp, neg, pred, args):
    lit = f"({pred} {' '.join(args)})"
    if neg:
        lit = f"(not {lit})"
    return f"{'刪除' if op == -1 else '新增'} {action.upper()} {'pre' if comp == 'pre' else 'eff'} {lit}"


def edits_text(keys):
    return "；".join(fmt(*k) for k in sorted(keys, key=lambda k: (k[1], k[2], -k[0]))) or "（無）"


lines = ["# 每案：錯誤 Assertion vs Lin 的修改（P4、P4N，各 5 個 seed）", "",
         "判定：✅ 完全修回（修改＝正確答案）；🟡 部分命中（有改到正確答案的一部分）；❌ 沒命中。括號內是 5 次中出現幾次。", "",
         "| 案例 | 正確修法（gold） | P4 修改 | P4N 修改 |", "|---|---|---|---|"]
stats = {"P4": Counter(), "P4N": Counter()}
for case in sorted(p.name for p in (ROOT / "inputs" / "P4").iterdir()):
    gold = gold_edits(clean, read_pddl(H30 / case / "domain.pddl"))
    cells = []
    for s in ("P4", "P4N"):
        outs = Counter()
        for run in sorted((ROOT / "results" / "runs" / s / case).glob("run_*")):
            recs = json.loads((run / "repairs_full.json").read_text())
            outs[frozenset((r["operation"], r["action"], r["component"], r["negative"], r["predicate"], tuple(r["arguments"])) for r in recs)] += 1
        parts = []
        for keys, n in outs.most_common():
            mark = "✅" if keys == gold else ("🟡" if keys & gold else "❌")
            stats[s][mark] += n
            parts.append(f"{mark} {edits_text(keys)}（{n}/5）")
        cells.append("<br>".join(parts))
    lines.append(f"| {case} | {edits_text(gold)} | {cells[0]} | {cells[1]} |")
lines += ["", "## 合計（30 案 × 5 次 = 150 次）", "", "| 設定 | ✅ 完全修回 | 🟡 部分命中 | ❌ 沒命中 |", "|---|---|---|---|"]
for s in ("P4", "P4N"):
    lines.append(f"| {s} | {stats[s]['✅']} | {stats[s]['🟡']} | {stats[s]['❌']} |")
(ROOT / "results" / "assertion_comparison.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines))
