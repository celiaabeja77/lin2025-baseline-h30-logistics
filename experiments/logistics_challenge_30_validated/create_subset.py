"""Export only the existing 2-success/2-failure cases; preserve H55 in place."""
from collections import Counter
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
BASE = Path(__file__).resolve().parent
SOURCE = BASE.parent / "logistics_challenge_55"
REL = Path("traces/official_2success_2failure")
SOURCE_TRACE = SOURCE / REL
OUT = BASE / REL


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write(path, lines):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


COPIED = []


def retain(source, destination):
    raw = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        assert destination.read_bytes() == raw, (destination, "existing copy differs")
    else:
        destination.write_bytes(raw)
    assert destination.read_bytes() == raw
    COPIED.append({"source": source.relative_to(SOURCE).as_posix(),
                   "exported": destination.relative_to(BASE).as_posix(), "sha256": sha(source)})


def main():
    source_hashes = {p.relative_to(SOURCE).as_posix(): sha(p) for p in SOURCE.rglob("*") if p.is_file()}
    old = read(SOURCE_TRACE / "summary.json")
    assert read(SOURCE / "evaluation/package_audit.json")["status"] == "pass"
    selected = [d for d in old["per_domain"] if d["selected_successes"] == d["selected_failures"] == 2
                and not d["missing_successes"] and not d["missing_failures"]]
    rejected = [d for d in old["per_domain"] if d not in selected]
    keep = [d["domain"] for d in selected]
    removed = [d["domain"] for d in rejected]
    assert len(keep) == 30 and len(removed) == 25
    assert {p.name for p in BASE.glob("H[0-9][0-9]") if p.is_dir()} <= set(keep)
    source_cases = {c["case_id"]: c for c in read(SOURCE / "evaluation/case_manifest.json")}
    # Canonical subset manifest omits the legacy authored-test count fields.
    fields = {"case_id", "group_id", "group_title", "description_zh_tw", "faulty_action", "component",
              "original_slot_1based", "original_line_1based", "original_assertion", "replacement_assertion",
              "operation", "domain_sha256", "source_legacy_case"}
    cases = [{k: v for k, v in source_cases[cid].items() if k in fields} for cid in keep]
    retain(SOURCE / "source_manifest.json", BASE / "source_manifest.json")
    for entry in read(SOURCE / "source_manifest.json")["files"]:
        retain(SOURCE / entry["local_path"], BASE / entry["local_path"])
    reference_ids = set()
    counts, failure_kinds = Counter(), Counter()
    for cid in keep:
        retain(SOURCE / cid / "domain.pddl", BASE / cid / "domain.pddl")
        for name in ("fault_info.json", "change.diff"):
            retain(SOURCE / "evaluation" / cid / name, BASE / "evaluation" / cid / name)
        retain(SOURCE_TRACE / "inputs/domains" / cid / "domain.pddl", OUT / "inputs/domains" / cid / "domain.pddl")
        for p in (SOURCE_TRACE / "by_domain" / cid).iterdir():
            if p.is_file():
                retain(p, OUT / "by_domain" / cid / p.name)
        for pick in next(d for d in selected if d["domain"] == cid)["traces"]:
            name = pick["trace_id"]
            retain(SOURCE_TRACE / "evaluation/comparisons" / cid / (name + ".json"), OUT / "evaluation/comparisons" / cid / (name + ".json"))
            trace = read(OUT / "by_domain" / cid / (name + ".trace.json"))
            assert trace["success"] == (trace["sequence_completed"] and trace["full_goal_reached"])
            counts["successes" if trace["success"] else "failures"] += 1
            if not trace["success"]:
                failure_kinds[trace["failure_kind"]] += 1
            reference_ids.add(trace["problem_id"])
    for name in ("inputs/reference", "inputs/problems", "plans", "planner"):
        for p in (SOURCE_TRACE / name).rglob("*"):
            if p.is_file():
                retain(p, OUT / p.relative_to(SOURCE_TRACE))
    for pid in sorted(reference_ids):
        retain(SOURCE_TRACE / "evaluation/reference_traces" / (pid + ".trace.json"), OUT / "evaluation/reference_traces" / (pid + ".trace.json"))
    retain(SOURCE_TRACE / "evaluation/official_problem_profiles.json", OUT / "evaluation/official_problem_profiles.json")
    selection = {"date": "2026-10-22", "source_dataset": "logistics_challenge_55",
                 "rule": "Retain domains with selected_successes=2, selected_failures=2 and both shortfalls zero",
                 "retained_domain_ids": keep, "removed_domain_ids": removed,
                 "retained_count": 30, "removed_count": 25, "original_H_ids_preserved": True,
                 "source_dataset_modified": False,
                 "removed_details": [{"domain": d["domain"], "missing_successes": d["missing_successes"],
                                      "missing_failures": d["missing_failures"], "reason": d["shortfall_explanation"]} for d in rejected]}
    save(BASE / "evaluation/subset_selection.json", selection)
    save(BASE / "evaluation/case_manifest.json", cases)
    groups = []
    for original in read(SOURCE / "evaluation/group_manifest.json"):
        members = [m for m in original["members"] if m[0] in keep]
        if members:
            group = copy.deepcopy(original)
            group["source_range"] = group.pop("range", None)
            group["members"] = members
            group["member_count"] = len(members)
            group["retained_ids"] = [m[0] for m in members]
            groups.append(group)
    save(BASE / "evaluation/group_manifest.json", groups)
    structure = read(SOURCE / "evaluation/single_assertion_recheck.json")
    edit_rows = [r for r in structure["cases"] if r["case_id"] in keep]
    save(BASE / "evaluation/single_assertion_recheck.json", {
        "status": "pass", "checked_cases": 30, "verification_origin": "Subset of earlier fresh H55 dual-parser and PDDL AST audit, copied domains SHA-256 identical",
        "source_audit_sha256": sha(SOURCE / "evaluation/single_assertion_recheck.json"),
        "new_parser_runs_in_this_export": 0, "each_exactly_one_atomic_assertion_edit": True,
        "operations": dict(Counter(r["operation"] for r in edit_rows)), "cases": edit_rows})
    screening = read(SOURCE_TRACE / "evaluation/candidate_screening.json")
    screening["candidates"] = [r for r in screening["candidates"] if r["domain"] in keep]
    screening["candidate_count"] = len(screening["candidates"])
    screening["export_note"] = "Existing symbolic screens retained for 30 domains; no new replay"
    save(OUT / "evaluation/candidate_screening.json", screening)
    trace_selection = read(SOURCE_TRACE / "selection.json")
    trace_selection["domains"] = [r for r in trace_selection["domains"] if r["domain"] in keep]
    save(OUT / "selection.json", trace_selection)
    summary = {"status": "complete", "official_only": True, "authored_Problems_used": 0,
               "domains": 30, "source_dataset_domain_count": 55, "excluded_shortfall_domains": 25,
               "official_Problems_available": 50, "FD_reference_plans_solved_and_validated": 50,
               "native_reference_full_traces": len(reference_ids), "native_mutant_traces": 120,
               "success_traces": counts["successes"], "failure_traces": counts["failures"],
               "domains_with_two_success_two_failure": 30, "missing_success_traces": 0, "missing_failure_traces": 0,
               "failure_kinds": dict(failure_kinds), "all_native_simulator_validator_results_agree": True,
               "all_reference_traces_complete_and_full_Goal_reached": True, "plan_Problem_Goal_bytes_not_modified": True,
               "versions": old["versions"], "reference_trace_ids": sorted(reference_ids),
               "new_planner_runs": 0, "new_native_simulator_runs": 0, "traces_reused_byte_identically": True,
               "SBFL_runs": 0, "LLM_runs": 0, "ontology_runs": 0, "Gym_runtime_runs": 0,
               "success_definition": "sequence_completed AND full_goal_reached",
               "plan_pool_limit": old["plan_pool_limit"], "per_domain": selected}
    assert counts == {"successes": 60, "failures": 60}
    save(OUT / "summary.json", summary)
    source_manifest = read(SOURCE / "source_manifest.json")
    save(OUT / "run_manifest.json", {
        "date": "2026-10-22", "operation": "filter_existing_H55_data_only", "official_source_commit": source_manifest["commit"],
        "versions": old["versions"], "retained_domain_ids": keep,
        "domain_hashes": {c["case_id"]: c["domain_sha256"] for c in cases},
        "source_hashes": {e["local_path"]: e["sha256"] for e in source_manifest["files"]},
        "source_formal_audit_sha256": sha(SOURCE_TRACE / "evaluation/final_audit.json"),
        "success_definition": "All planned actions execute AND every original official Problem goal is satisfied",
        "new_planner_runs": 0, "new_simulator_runs": 0,
        "method_input_boundary": "Gold edits, correct Domain/reference traces and first divergence comparisons are evaluation only"})
    save(BASE / "evaluation/copied_source_files.json", COPIED)
    rows = ["| H 編號 | 類別 | 動作 | 部位 | 原 Assertion → 新 Assertion | Trace |",
            "|---|---|---|---|---|---|"]
    for c in cases:
        old_literal = "`" + c["original_assertion"] + "`" if c["original_assertion"] else "新增"
        new_literal = "`" + c["replacement_assertion"] + "`" if c["replacement_assertion"] else "刪除"
        rows.append(f"| {c['case_id']} | {c['group_id']} {c['group_title']} | {c['faulty_action']} | {c['component']}[{c['original_slot_1based']}] | {old_literal} → {new_literal} | 2 成功＋2 失敗 |")
    write(BASE / "evaluation/CASES_30.md", ["# 合格 30 個 Domain：Assertion 改動表", "", *rows, ""])
    memory = ["# Logistics：剔除缺額版本後的 30 個 Domain", "",
              "整理日期：2026-10-22（Asia/Taipei）。來源：H55 既有資料；新資料夾 `experiments/logistics_challenge_30_validated`。", "",
              "## 本次變更", "",
              "從 H01–H55 中排除沒有取得 2 條完整成功＋2 條失敗 Trace 的 25 個版本，形成 30 個版本的新子集。原 H55、H40 與原始證據均未修改或刪除。保留原 H 編號，不重新編成 H01–H30。", "",
              "## 保留與剔除", "",
              "保留 30 個：" + "、".join(keep) + "。", "",
              "剔除 25 個：" + "、".join(removed) + "。", "",
              "剔除是針對這批固定官方參考計畫的成功／失敗配額，不代表每一版在所有替代計畫下都無法失敗或成功。原因明列於 `evaluation/subset_selection.json`。", "",
              "## Trace 與驗證定義", "",
              "官方 50 個 Problem 與原版 Domain 不變。計畫均已先由 Fast Downward 在原版解出並通過驗證，再以完全相同的計畫重播到錯誤 Domain。", "",
              "成功必須同時滿足：(1) 全部動作執行完畢；(2) 原 Problem 的全部 Goal 達成。任一步被拒絕，或全部動作執行後仍缺 Goal，都算失敗。原版已失敗的非法計畫不作為參考計畫。", "",
              f"本包共 30 個 Domain、120 條既有 native UP mutant Trace，60 成功＋60 失敗，每版 2＋2。另保留 {len(reference_ids)} 條原版完整成功 Trace，與 mutant 分開計數。", "",
              "只複製既有結果並核對位元組／SHA-256，沒有重新注入、規劃、模擬或修改 Problem／Goal。候選資料保留 30×50＝1500 組既有符號篩選；不可誤稱 1500 次 native UP 模擬。", "",
              "## 來源與工具", "",
              "Repository：tomsilver/pddlgym；commit `ab268e40ac7b2de8d060ec0c48c27003d1a62d62`；Domain `pddlgym/pddl/manylogistics.pddl`（logistics-strips）。", "",
              "官方 Problems：train/problem0–39、test/problem40–49。原版 SHA-256 `1e53d7715105db947a91bdaf55c0027bccc3d037f3771cf9b5422b1fd6c58715`。", "",
              "既有執行工具：Unified Planning 1.3.0 的 SequentialSimulator＋sequential_plan_validator；Fast Downward 計畫由 up-fast-downward 0.5.2 取得。未執行 PDDLGym Gym runtime。", "",
              "30 版各只改一條 Assertion，對應原 H55 的 AST 與官方／UP Parser 檢查；本次以原樣副本與 SHA-256 承接該證據，未重跑 Parser。H38、H40 的既有 Add／Delete overlap 仍在，UP 的 add-after-delete 行為保留，其他規劃器相容性未另測。", "",
              "## 保留案例的實際改動", "", *rows, "",
              "## 檔案與後續邊界", "",
              "- `Hxx/domain.pddl`：僅包含上述 30 個版本。",
              "- `traces/official_2success_2failure/by_domain/Hxx/`：每版 S1、S2、F1、F2 與相同計畫；共 120 條 Trace。",
              "- `reference/`、`traces/.../inputs/`、`plans/`、`planner/`：官方來源與完整 50 題參考計畫保留。",
              "- `evaluation/case_manifest.json`、`group_manifest.json`、`CASES_30.md`：只列保留的 30 版。原分組編號保留，過濾後各組數量可不同。",
              "- `evaluation/subset_selection.json`：25 個剔除原因；`copied_source_files.json`：來源與副本 hash。",
              "- `evaluation/single_assertion_recheck.json`：保留 30 版的先前單一 Assertion 檢查證據。",
              "- `SHA256SUMS.json`、`verify_package.py`、`evaluation/package_audit.json`：套件完整性與保存的 grounded Trace 重播核對；不重新呼叫規劃器或模擬器。", "",
              "每步仍含 Domain／Problem、動作與參數、前後狀態、grounded Precondition 真假、未滿足條件、Add／Delete Effects、實際狀態差與 attempted／executed；另記錄最終全部 Goal。", "",
              "本包含故障真值與原版比較，屬建置／評估資料，不能整包作為待測 LLM 的盲測輸入。SBFL、LLM、Ontology 及修復實驗均未執行，困難度與 Ontology 增益未測量。", ""]
    write(BASE / "PROGRESS_MEMORY.md", memory)
    write(BASE.parents[1] / "H30_Validated_Progress_Memory_2026-10-22.md", memory)
    write(BASE / "README.md", ["# Logistics：30 個具備 2 成功＋2 失敗的 Domain", "",
          "已從 H55 中剔除 25 個配額不足版本。保留原 H 編號；原資料夾不變。", "",
          "- Domain：30 個；正式 native UP mutant Trace：120 條（60 成功／60 失敗）。",
          f"- 原版完整成功 Trace：{len(reference_ids)} 條；官方 Problem／參考 FD 計畫：50 題／50 條。",
          "- 本次僅匯出子集；規劃器／模擬器新增執行次數均為 0。",
          "- 改動總表：evaluation/CASES_30.md；完整接續記憶：PROGRESS_MEMORY.md；剔除原因：evaluation/subset_selection.json。",
          "- 原始 Domain、Problem、計畫與 Trace 位元組均保留；每版只改一條 Assertion 的證據承接原 H55 稽核。",
          "- 套件含評估真值；盲測方法輸入需另行隔離。尚未執行 SBFL／LLM／Ontology。", "",
          "保留：" + "、".join(keep) + "。", "", "剔除：" + "、".join(removed) + "。", "",
          "可用任何 Python 3 執行 `python -B verify_package.py`，核對 hash、每版 2＋2、完整 Goal，以及保存的 grounded 狀態轉移；不需安裝 UP／FD。", ""])
    write(OUT / "README.md", ["# 已篩選的 30 個 Domain Trace", "",
          "每版 S1、S2、F1、F2，共 120 條：60 成功、60 失敗。所有計畫先在原版完整成功，再原封不動重播。success = sequence_completed AND full_goal_reached。", "",
          "由既有 H55 native UP 證據逐位元複製，本次沒有新規劃或模擬。evaluation/reference_traces/ 與 comparisons/ 屬評估資訊。", ""])
    after_hashes = {p.relative_to(SOURCE).as_posix(): sha(p) for p in SOURCE.rglob("*") if p.is_file()}
    assert source_hashes == after_hashes, "Source H55 changed during export"
    save(BASE / "evaluation/source_preservation.json", {"status": "pass", "source_H55_files_verified_unchanged": len(source_hashes),
         "all_copied_raw_files_byte_identical": True, "copied_raw_file_count": len(COPIED), "original_H_ids_preserved": True})
    inventory = {p.relative_to(BASE).as_posix(): sha(p) for p in BASE.rglob("*")
                 if p.is_file() and "__pycache__" not in p.parts
                 and p.relative_to(BASE).as_posix() not in {"SHA256SUMS.json", "evaluation/package_audit.json"}}
    save(BASE / "SHA256SUMS.json", inventory)
    spec = importlib.util.spec_from_file_location("verify_filtered_package", BASE / "verify_package.py")
    verification = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verification)
    verification.main()
    package_path = BASE.with_suffix(".zip")
    files = [p for p in BASE.rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    with zipfile.ZipFile(package_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(BASE).as_posix())
    with zipfile.ZipFile(package_path) as archive:
        assert archive.testzip() is None
        assert set(archive.namelist()) == {p.relative_to(BASE).as_posix() for p in files}
        for path in files:
            assert archive.read(path.relative_to(BASE).as_posix()) == path.read_bytes()
        assert len([n for n in archive.namelist() if len(Path(n).parts) == 2 and Path(n).parts[0] in keep and n.endswith("/domain.pddl")]) == 30
        assert not any(any(part in removed for part in Path(name).parts) for name in archive.namelist())
    package_path.with_suffix(".zip.sha256").write_text(sha(package_path) + "  " + package_path.name + "\n", encoding="utf-8")
    print(json.dumps({"archive": str(package_path), "files": len(files), "sha256": sha(package_path),
                      "retained": keep, "removed": removed, "source_unchanged": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
