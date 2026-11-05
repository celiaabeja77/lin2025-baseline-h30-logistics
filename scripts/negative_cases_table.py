"""Detailed P4 vs P4N table for the cases that have negative plans (H08, H29, H38, H40)."""
import json
import sys
from collections import Counter
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_io import assertion_set, gold_edits, read_pddl  # noqa: E402

H30 = ROOT / "data" / "h30"
clean_tree = read_pddl(H30 / "reference" / "domain.pddl")
clean = assertion_set(clean_tree)
audit = json.loads((ROOT / "results" / "input_audit.json").read_text(encoding="utf-8"))
manifest = {c["case_id"]: c for c in json.loads((H30 / "case_manifest.json").read_text(encoding="utf-8"))}
CASES = [c for c in sorted(audit) if audit[c]["negatives_dev"] > 0]


def fmt(k):
    op, action, comp, neg, pred, args = k
    lit = f"({pred} {' '.join(args)})"
    lit = f"(not {lit})" if neg else lit
    return f"{'－' if op == -1 else '＋'} {action.upper()} {comp} {lit}"


def edits(keys):
    return "<br>".join(fmt(k) for k in sorted(keys, key=lambda k: (k[1], k[2], -k[0]))) or "（無）"


L = ["# 4 個有反例的案例：P4 vs P4N 詳細結果", "",
     "＋＝新增、－＝刪除。「修回正確 Domain」直接比對修好的 Domain 和正確 Domain 的全部 Assertion。保留集＝test problem 40–49：10 條正例＋該案的保留反例。每個設定跑 5 次。", ""]
L += ["## 案例背景", "", "| 案例 | 錯在哪 | 原本 → 錯誤寫法 | 為什麼變寬鬆 | 正確修法 | 給 Lin 的反例數 | 保留集反例數 |", "|---|---|---|---|---|---|---|"]
why = {"H08": "卡車不在出發地也能開走", "H29": "貨物裝車後還在地上，可重複裝貨",
       "H38": "開車後卡車留在原地，可在原地繼續動作", "H40": "貨物裝車後還在地上，可重複裝貨"}
for c in CASES:
    m = manifest[c]
    gold = gold_edits(clean_tree, read_pddl(H30 / c / "domain.pddl"))
    L.append(f"| {c} | {m['faulty_action']} {m['component']} | `{m['original_assertion']}` → `{m['replacement_assertion']}` | {why.get(c, '')} | {edits(gold)} | {audit[c]['negatives_dev']} | {audit[c]['negatives_heldout']} |")
L += ["", "## 結果", "",
      "| 案例 | 設定 | Lin 的修改（5 次中幾次） | 修回正確 Domain | 保留集正例通過 | 保留集反例通過 | 保留集全過 | 平均修改數 | F1 | 平均秒數 |",
      "|---|---|---|---|---|---|---|---|---|---|"]
tot = {s: Counter() for s in ("P4", "P4N")}
for c in CASES:
    for s in ("P4", "P4N"):
        runs = sorted((ROOT / "results" / "runs" / s / c).glob("run_*"))
        outs, ms, same = Counter(), [], 0
        for r in runs:
            recs = json.loads((r / "repairs_full.json").read_text())
            outs[frozenset((x["operation"], x["action"], x["component"], x["negative"], x["predicate"], tuple(x["arguments"])) for x in recs)] += 1
            ms.append(json.loads((r / "metrics.json").read_text(encoding="utf-8")))
            same += assertion_set(read_pddl(r / "domain-repaired.pddl")) == clean
        n = len(runs)
        pos = f"{sum(m['heldout_pos_passed'] for m in ms)}/{sum(m['heldout_pos_total'] for m in ms)}"
        neg = f"{sum(m['heldout_neg_passed'] for m in ms)}/{sum(m['heldout_neg_total'] for m in ms)}"
        allp = sum(m["heldout_all_passed"] for m in ms)
        tot[s].update({"same": same, "all": allp, "n": n})
        rep = "<br><br>".join(f"{edits(k)}（{v}/5）" for k, v in outs.most_common())
        L.append(f"| {c} | {s} | {rep} | {same}/{n} | {pos} | {neg} | {allp}/{n} | {mean(m['repairs'] for m in ms):.1f} | {mean(m['f1'] for m in ms):.2f} | {mean(m['wall_seconds'] for m in ms):.2f} |")
L += ["", "## 合計（4 案 × 5 次 = 20 次）", "", "| 設定 | 修回正確 Domain | 保留集全過 |", "|---|---|---|"]
for s in ("P4", "P4N"):
    L.append(f"| {s} | {tot[s]['same']}/{tot[s]['n']} | {tot[s]['all']}/{tot[s]['n']} |")
L += ["", "保留集正例／反例欄是 5 次加總（例如 50 條正例＝10 條 × 5 次）。"]
(ROOT / "results" / "negative_cases.md").write_text("\n".join(L) + "\n", encoding="utf-8")
print("\n".join(L))
