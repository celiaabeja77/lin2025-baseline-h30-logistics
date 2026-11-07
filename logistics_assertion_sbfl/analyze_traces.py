"""Explain existing SBFL results using saved mutant/reference execution traces.

This is post-hoc analysis with evaluation gold, not a new localization method.
Scores, input traces, and prior result files are read-only throughout.
"""

import argparse
import csv
import re
from collections import Counter, defaultdict
from pathlib import Path

from run_all import fingerprint, sha
from src.assertion_coverage import action_parameters, grounded_key
from src.literal import _atom
from src.pddl_assertions import load_domain
from src.utils import read_json, write_json


ORDER = ("S1", "S2", "F1", "F2")
FOCUS = ("H51", "H41", "H26", "H34", "H21")


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def literal_keys(literals):
    return {_atom(x) for x in literals}


def target_text(key):
    negative, atom = key
    text = "(" + " ".join(atom) + ")"
    return "(not " + text + ")" if negative else text


def ground_text(text, assignment):
    return target_text(grounded_key(text, assignment))


def explain_trace(raw, reference, metadata, parameters):
    """Describe observations and gold-guided dependency matches, not SBFL output."""
    assert raw["success"] == (raw["sequence_completed"] and raw["full_goal_reached"])
    assert reference["success"] and raw["problem_goals"] == reference["problem_goals"]
    assert raw["plan_sha256"] == reference["plan_sha256"]
    actions = defaultdict(lambda: {"attempted": 0, "executed": 0})
    events, divergence = [], None
    for step, correct in zip(raw["steps"], reference["steps"]):
        assert step["step"] == correct["step"] and step["action"] == correct["action"]
        actions[step["action_name"].upper()]["attempted"] += int(step["attempted"])
        actions[step["action_name"].upper()]["executed"] += int(step["executed"])
        if divergence is None and literal_keys(step["state_after"]) != literal_keys(correct["state_after"]):
            divergence = step["step"]
        if step["action_name"].casefold() != metadata["faulty_action"].casefold():
            continue
        assignment = dict(zip(parameters[step["action_name"].casefold()], step["arguments"]))
        original = ground_text(metadata["original_assertion"], assignment) if metadata["original_assertion"] else None
        replacement = ground_text(metadata["replacement_assertion"], assignment) if metadata["replacement_assertion"] else None
        observed = next((p["satisfied"] for p in step["precondition_results"]
                         if replacement and _atom(p["literal"]) == _atom(replacement)), None)
        events.append({"step": step["step"], "action": step["action"], "executed": step["executed"],
                       "original_grounded_literal": original, "replacement_grounded_literal": replacement,
                       "checked_precondition_truth": observed,
                       "actual_predicates_added": step["predicates_added"],
                       "actual_predicates_removed": step["predicates_removed"]})
    rejected = next((s for s in raw["steps"] if not s["executed"]), None)
    missing = rejected["unmet_preconditions"] if rejected else raw["unmet_goals"]
    links = []
    for unmet in missing:
        candidates = []
        for event in events:
            step = raw["steps"][event["step"] - 1]
            original, replacement = event["original_grounded_literal"], event["replacement_grounded_literal"]
            if metadata["component"] == ":precondition":
                if rejected and step["step"] == rejected["step"] and replacement and _atom(replacement) == _atom(unmet):
                    candidates.append({"type": "changed_precondition_rejected", "source_step": step["step"],
                                       "source_action": step["action"], "required_literal": unmet,
                                       "failure_step": rejected["step"], "failure_action": rejected["action"]})
                continue
            if not event["executed"] or (rejected and event["step"] >= rejected["step"]):
                continue
            unmet_key = _atom(unmet)
            reason = None
            if replacement and _atom(replacement)[0]:
                removed = (False, _atom(replacement)[1])
                if removed == unmet_key and removed in literal_keys(step["predicates_removed"]):
                    reason = "wrong_effect_actually_removed_later_required_fact"
            if original and not _atom(original)[0] and _atom(original) == unmet_key:
                if unmet_key not in literal_keys(step["state_after"]):
                    reason = "changed_or_deleted_effect_did_not_establish_required_fact"
            if reason:
                end = rejected["step"] - 1 if rejected else len(raw["steps"])
                persistent = all(unmet_key not in literal_keys(s["state_after"])
                                 for s in raw["steps"][event["step"] - 1:end])
                if persistent:
                    candidates.append({"type": reason, "source_step": event["step"], "source_action": event["action"],
                                       "required_literal": unmet, "failure_step": rejected["step"] if rejected else None,
                                       "failure_action": rejected["action"] if rejected else "final_goal_check",
                                       "fact_absent_continuously_until_failure": True})
        if candidates:
            links.append(candidates[-1])
    return {"trace_id": raw["trace_id"], "problem_id": raw["problem_id"], "success": raw["success"],
            "goals": raw["problem_goals"], "planned_steps": raw["planned_action_count"],
            "attempted_steps": len(raw["steps"]), "executed_steps": raw["executed_action_count"],
            "first_rejected_step": raw["first_rejected_step"], "first_rejected_action": raw["first_rejected_action"],
            "unmet_preconditions_at_rejection": rejected["unmet_preconditions"] if rejected else [],
            "unmet_goals": raw["unmet_goals"], "failure_kind": raw["failure_kind"],
            "first_state_difference_from_reference": divergence, "fault_action_events": events,
            "gold_guided_dependency_matches": links, "action_counts": dict(actions),
            "execution_sequence": [{"step": s["step"], "action": s["action"], "executed": s["executed"],
                                    "unmet_preconditions": s["unmet_preconditions"]} for s in raw["steps"]]}


def md_table(headers, rows):
    return ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers),
            *["| " + " | ".join(str(x).replace("|", "\\|") for x in row) + " |" for row in rows]]


def report_text(cases, overview, problem_summary):
    lines = ["# Logistics：SBFL 難定位案例與跨 Problem Trace／Coverage 分析", "",
             "這批資料的主要困難是最高分候選大量並列。27 個仍存在於候選集的真正錯誤都位於最高分群組；沒有觀察到 gold 落在較低分群組的排名偏移。另 3 案的 gold 已被刪除，屬候選集缺口。", "",
             "資料是 30 個錯誤版本、120 條選定的官方 Problem 重播，每版 2 成功＋2 失敗，實際涵蓋 10 個不同 Problem。不同版本的 S1/S2/F1/F2 不一定對應相同 Problem；50 題官方題庫不全數投入這次 SBFL。", "",
             "下列所有向量固定依 S1、S2、F1、F2 排列，1 表示該條軌跡碰到該 assertion，0 表示沒有。每條 trace 只記一次；檢查過的 precondition 不分真值，只有實際執行的動作才覆蓋 effects。", "",
             "## 案例概覽", ""]
    labels = {"H51": "所有 coverage 飽和，物件再利用差異消失", "H41": "有檢查相同，條件真值不同",
              "H26": "不同動作共同出現在失敗路線", "H34": "機場位置參數與再利用順序被壓縮",
              "H21": "缺失 assertion 候選缺口；與 H26 可同症狀"}
    lines += md_table(["Case", "觀察到的困難", "gold ef/ep", "gold 分數", "gold 排名", "coverage 群組數"],
                      [(cid, labels[cid], f"{cases[cid]['summary']['ef']}/{cases[cid]['summary']['ep']}" if cases[cid]['summary']['ground_truth_in_candidate_set'] == 'true' else "無候選",
                        cases[cid]['summary']['ground_truth_score'] or "無候選",
                        f"{cases[cid]['summary']['best_rank']}～{cases[cid]['summary']['worst_rank']}" if cases[cid]['summary']['best_rank'] else "無候選",
                        len(cases[cid]["coverage_groups"])) for cid in FOCUS])
    lines += ["", "## H51：做過一樣的動作，後續是否再用同一輛車卻不同", "",
              "UNLOAD-TRUCK 多了一條錯誤效果 `(not (at ?truck ?loc))`：卸貨後順便抹掉卡車位置。", ""]
    lines += md_table(["Trace", "官方 Problem", "觀察到的執行差異", "結果"], [
        ("S1", "train_problem2", "第 6 步卸貨刪除 (at t1 l11)，計畫於此結束", "成功：完整貨物目標已達成"),
        ("S2", "train_problem16", "第 11 步卸貨刪除 (at t2 l21)，之後第 12、13 步只操作飛機", "成功：沒有再使用 t2"),
        ("F1", "train_problem5", "第 9 步卸貨刪除 (at t0 l00)，第 13 步再次用 t0 裝貨", "失敗：缺 (at t0 l00)"),
        ("F2", "train_problem7", "第 20 步卸貨刪除 (at t3 l32)，第 21 步同車再次卸貨", "失敗：缺 (at t3 l32)")])
    lines += ["", "四條 trace 都至少實際執行過六種動作，因此全部 44 條 assertions 的 coverage 都是 `[1,1,1,1]`，ef=2、ep=2、F=2、Ochiai=0.707107，並列第 1～44 名。", "",
              "成功 trace 也真的刪錯卡車位置；完整貨物目標仍可達成，並不證明所有狀態都正確。失敗與否取決於後續是否還需要該車的位置，而不是 UNLOAD-TRUCK 是否曾出現。", "",
              "F1 最早的狀態差異是第 5 步（另一輛 t1），但與第 13 步直接對應的缺失事實來自第 9 步 t0。F2 最早差異也是第 5 步，但與第 21 步缺 (at t3 l32) 對應的是第 20 步。不可把第一次偏離自動當成這次受阻的直接來源。", "",
              "以下是實際執行次數（不是新的 coverage 或新的可疑度計分）：", ""]
    h51 = cases["H51"]
    lines += md_table(["動作", *ORDER], [(action, *[h51["traces"][tid]["action_counts"].get(action, {}).get("executed", 0) for tid in ORDER])
                                         for action in ("LOAD-TRUCK", "UNLOAD-TRUCK", "DRIVE-TRUCK", "LOAD-AIRPLANE", "UNLOAD-AIRPLANE", "FLY-AIRPLANE")])
    lines += ["", "雖然次數與順序不同，binary assertion coverage 仍全部為 1；僅改用次數也尚未經實驗驗證能定位。", "",
              "## H41：同一條件都檢查過，但機場與一般地點的真值不同", "",
              "LOAD-TRUCK.precondition[3] 把 `(LOCATION ?loc)` 寫成 `(AIRPORT ?loc)`，因此一般地點不能裝貨。", ""]
    truth_rows = []
    for tid in ORDER:
        t = cases["H41"]["traces"][tid]
        event = t["fault_action_events"][0]
        truth_rows.append((tid, t["problem_id"], event["step"], event["replacement_grounded_literal"],
                           "成立" if event["checked_precondition_truth"] else "不成立", 1, "成功" if t["success"] else "失敗"))
    lines += md_table(["Trace", "Problem", "檢查步驟", "代入物件的錯誤條件", "當下真值", "binary coverage", "結果"], truth_rows)
    lines += ["", "四次 LOAD-TRUCK 檢查中，其餘四條 preconditions 都成立；只有錯寫的機場條件在失敗 trace 不成立。這個差異保存在原始 precondition_results，未進入目前的 SBFL 分數。", ""]
    lines += md_table(["候選／群組", "S1", "S2", "F1", "F2", "ef", "ep", "Ochiai"], [
        ("錯誤的 LOAD-TRUCK.precondition[3]", 1, 1, 1, 1, 2, 2, "0.707107"),
        ("其餘正確的 LOAD-TRUCK preconditions", 1, 1, 1, 1, 2, 2, "0.707107"),
        ("正確的 DRIVE-TRUCK 全部 assertions", 1, 1, 1, 1, 2, 2, "0.707107"),
        ("LOAD-TRUCK effects", 1, 1, 0, 0, 0, 2, "0")])
    lines += ["", "因此 5 條 LOAD-TRUCK preconditions 加上 9 條 DRIVE-TRUCK assertions 共 14 條同分第一。失敗時裝貨 effects 未執行，所以 effects 與 preconditions 的 coverage 可以不同，不能說『嘗試一個 action 就把全部 assertion 一起加一』。", "",
              "## H26：成功只走空運，卡車路線的正確與錯誤 assertions 一起得高分", "",
              "LOAD-TRUCK.effect[2] 將 `(in ?obj ?truck)` 寫反為 `(in ?truck ?obj)`。", ""]
    lines += md_table(["Trace", "Problem", "執行觀察", "結果"], [
        ("S1", "train_problem0", "7 步，只有飛機裝貨、飛行、卸貨", "成功"),
        ("S2", "train_problem1", "14 步，只有飛機裝貨、飛行、卸貨", "成功"),
        ("F1", "train_problem2", "第 4 步裝貨建立 (in t1 p0)，第 6 步卸貨要求 (in p0 t1)", "第 6 步受阻"),
        ("F2", "train_problem5", "第 2 步裝 p2 建立 (in t1 p2)，第 5 步卸 p2 要求 (in p2 t1)", "第 5 步受阻")])
    lines += [""]
    lines += md_table(["候選群組", "S1", "S2", "F1", "F2", "數量", "ef/ep", "Ochiai"], [
        ("LOAD-TRUCK 全部 preconditions/effects", 0, 0, 1, 1, 7, "2/0", 1),
        ("UNLOAD-TRUCK 被檢查的 preconditions", 0, 0, 1, 1, 5, "2/0", 1),
        ("DRIVE-TRUCK 全部 assertions", 0, 0, 1, 1, 9, "2/0", 1),
        ("UNLOAD-TRUCK 沒執行的 effects", 0, 0, 0, 0, 2, "0/0", 0)])
    lines += ["", "因此真正錯誤與其他正常 assertions 共 21 條並列第 1～21 名。這裡同時有同一 action 內的共同覆蓋，以及不同 action 在失敗路線中共同出現；兩者需分開說明。", "",
              "新增能拆開卡車動作組合的合理 Problem，可能改善跨 action 的共同覆蓋；若同一個 action 的 assertions 仍每次一起被檢查或套用，增加 trace 數量本身不保證分開。這是方法設計上的推論，尚未以新增 Problem 驗證。", "",
              "## H34：成功與失敗都飛行，但是否再次使用被破壞的機場不同", "",
              "FLY-AIRPLANE 多了 `(not (AIRPORT ?loc-to))`，到達後移除目的地的機場資格。", ""]
    lines += md_table(["Trace", "Problem", "關鍵過程", "結果"], [
        ("S1", "train_problem2", "第 2 步移除 (airport l10)，後續卸貨、改走卡車", "成功"),
        ("S2", "train_problem3", "第 2 步刪 l10、第 5 步刪 l20 的機場資格；後續不再飛行", "成功"),
        ("F1", "train_problem0", "第 4 步 a4 到 l10 並刪機場資格，第 6 步 a4 要從 l10 再起飛", "缺 (airport l10) 而受阻"),
        ("F2", "train_problem1", "第 2 步 a5 到 l10 並刪機場資格，第 6 步 a5 要從 l10 再起飛", "缺 (airport l10) 而受阻")])
    lines += ["", "三種空運動作的 21 條 assertions 都是 `[1,1,1,1]`，分數 0.707107，共享第 1～21 名。完整 trace 能顯示機場參數與再次使用的先後順序；binary coverage 只留下是否曾碰過。", "",
              "案例描述文字提到『另一架飛機無法降落』，但這兩條已保存失敗 trace 實際呈現的是同一架飛機從剛到達的地點再起飛受阻；本分析以實際紀錄為準。", "",
              "## H21：與 H26 的失敗症狀、現有 coverage 相同，但真正缺失的 literal 沒有候選", "",
              "H21 刪掉 `(in ?obj ?truck)`；H26 則保留一條內容寫反的 effect。兩版使用相同的四個 Problem、相同計畫與相同成功／失敗結果：F1 都在第 6 步卸貨，F2 都在第 5 步卸貨時缺少正向的 in 關係。", "",
              "兩版共有的 42 條候選（依相同 assertion ID 對照，僅比 coverage）都有相同向量。H26 額外存在內容寫反的 LOAD-TRUCK.effect[2]，H21 完全沒有那個 effect 槽位。H21 最高分仍有 20 條，但真正缺少的效果不能直接排入名次。這是候選集設計限制，應與同分問題分開報告。", "",
              "## 同一個 Problem，換錯誤版本後的失敗位置不同", ""]
    lines += md_table(["Problem", "H26", "H41", "H51"], [
        ("train_problem2", "第 6 步 UNLOAD-TRUCK：缺 (in p0 t1)", "成功", "成功，但最後卸貨抹掉卡車位置"),
        ("train_problem5", "第 5 步 UNLOAD-TRUCK：缺 (in p2 t1)", "第 2 步 LOAD-TRUCK：缺 (airport l11)", "第 13 步 LOAD-TRUCK：缺 (at t0 l00)")])
    lines += ["", "這也說明不能把 S1/F1 當作固定 Problem 名稱，或把實際受阻的 action 當作真正錯誤 action。這張對照保持 Problem 與參考計畫不變，只比較現有不同 mutant 的紀錄。", "",
              "## 全 30 案的 coverage 多樣性", ""]
    distribution = Counter(r["num_distinct_coverage_vectors"] for r in overview)
    lines += md_table(["每案不同 coverage 向量數", "案例數"], sorted(distribution.items()))
    lines += ["", "每版有 42～44 條 assertions，但在目前四條選定 trace 上，實際只形成 1～4 種不同向量。這是本資料中可直接量化的證據不足現象，不等於已證明所有可能 Problem 都無法分開。", "",
              "## 選定 Problem 的使用情況", "",
              "以下次數只計入本次選定子集，不是各 Problem 在完整題庫或所有 mutant 上的自然成功率。", ""]
    lines += md_table(["官方 Problem", "參考計畫步數", "目標數", "本子集重播次數", "成功", "失敗"],
                      [(r["problem_id"], r["reference_plan_steps"], len(r["goals"]), r["selected_replays"], r["successes"], r["failures"]) for r in problem_summary])
    lines += ["", "## 全 120 條 trace 概覽", "",
              "『覆蓋數』是本次既有 coverage_matrix.csv 中為 1 的現有 assertions 數；參考計畫步數是完整計畫長度，實際重播可能提早受阻。", ""]
    lines += md_table(["Case", "Trace", "Problem", "完整計畫步數", "實際執行步數", "覆蓋數", "結果／受阻位置"],
                      [(cid, tid, cases[cid]["traces"][tid]["problem_id"], cases[cid]["traces"][tid]["planned_steps"],
                        cases[cid]["traces"][tid]["executed_steps"], cases[cid]["traces"][tid]["num_covered_assertions"],
                        "成功" if cases[cid]["traces"][tid]["success"] else
                        f"第 {cases[cid]['traces'][tid]['first_rejected_step']} 步 {cases[cid]['traces'][tid]['first_rejected_action']}" if cases[cid]["traces"][tid]["first_rejected_step"] else "完整執行後 Goal 未達成")
                       for cid in cases for tid in ORDER])
    lines += ["", "## 證據與方法邊界", "",
              "- 這是讀取既有 gold、reference trace 與狀態資訊的事後分析；不是聲稱 SBFL 已自行找出以上因果關係。",
              "- 失敗依賴配對核對 grounded literal、實際增刪、後續持續缺失及受阻條件；沒有另外做反事實修復實驗。",
              "- 每案完整執行順序、grounded fault 事件、coverage 群組與 assertion IDs 在 cases/Hxx.json。",
              "- 不重新算分、不重播、不改 Domain、Problem、Plan、Trace 或原有 results。來源雜湊與保存檢查在 audit.json。", ""]
    return "\n".join(lines)


def analyze(project, results, output):
    project, results, output = project.resolve(), results.resolve(), output.resolve()
    if any(output == root or root in output.parents or output in root.parents for root in (project, results)):
        raise ValueError("Analysis output must be separate from original input and ranking folders")
    source_before, results_before = fingerprint(project), fingerprint(results)
    manifest = read_json(results / "run_manifest.json")
    assert source_before == manifest["input_sha256"]
    summaries = read_csv(results / "summary.csv")
    cases, problem_rows, overview = {}, {}, []
    failures, executed_steps = Counter(), 0
    for summary in summaries:
        cid = summary["case_id"]
        domain_path = project / cid / "domain.pddl"
        domain = load_domain(domain_path)
        parameters = action_parameters(domain_path.read_text(encoding="utf-8-sig"))
        metadata = read_json(project / "evaluation" / cid / "fault_info.json")
        ranking = read_csv(results / cid / "ranking.csv")
        matrix = read_csv(results / cid / "coverage_matrix.csv")
        groups = defaultdict(list)
        for row in matrix:
            groups[tuple(int(row[tid]) for tid in ORDER)].append(row["assertion_id"])
        score_map = {r["assertion_id"]: float(r["ochiai"]) for r in ranking}
        assert {r["assertion_id"] for r in matrix} == {a.assertion_id for a in domain.assertions}
        data = {"summary": summary, "gold_metadata_evaluation_only": metadata, "trace_order": ORDER,
                "coverage_groups": [{"vector": vector, "num_assertions": len(ids), "assertion_ids": ids,
                                     "scores": sorted({score_map[aid] for aid in ids})} for vector, ids in groups.items()],
                "traces": {}}
        for tid in ORDER:
            relative = Path("traces/official_2success_2failure/by_domain") / cid / (tid + ".trace.json")
            raw = read_json(project / relative)
            assert raw["trace_id"] == tid and raw["domain"] == cid
            assert re.fullmatch(r"train_problem\d+", raw["problem_id"])
            reference_path = project / "traces/official_2success_2failure/evaluation/reference_traces" / (raw["problem_id"] + ".trace.json")
            reference = read_json(reference_path)
            trace = explain_trace(raw, reference, metadata, parameters)
            trace["source_trace"] = relative.as_posix()
            trace["num_covered_assertions"] = sum(int(r[tid]) for r in matrix)
            trace["covered_assertion_ids"] = [r["assertion_id"] for r in matrix if r[tid] == "1"]
            data["traces"][tid] = trace
            if not raw["success"]:
                failures[raw["failure_kind"]] += 1
            executed_steps += trace["executed_steps"]
            p = problem_rows.setdefault(raw["problem_id"], {"problem_id": raw["problem_id"], "goals": raw["problem_goals"],
                                                           "reference_plan_steps": raw["planned_action_count"], "selected_replays": 0,
                                                           "successes": 0, "failures": 0, "occurrences": []})
            assert p["goals"] == raw["problem_goals"] and p["reference_plan_steps"] == raw["planned_action_count"]
            p["selected_replays"] += 1
            p["successes" if raw["success"] else "failures"] += 1
            p["occurrences"].append({"case_id": cid, "trace_id": tid, "success": raw["success"]})
        cases[cid] = data
        overview.append({"case_id": cid, "num_assertions": len(matrix), "num_distinct_coverage_vectors": len(groups),
                         "num_distinct_scores": len(set(score_map.values())),
                         "top_score_group_size": sum(r["best_rank"] == "1" for r in ranking),
                         "gold_rank_interval": [summary["best_rank"], summary["worst_rank"]] if summary["best_rank"] else None})
        write_json(output / "cases" / (cid + ".json"), data)
    # Check the key statements used in the written examples directly.
    assert len(cases["H51"]["coverage_groups"]) == 1
    assert list(cases["H51"]["coverage_groups"][0]["vector"]) == [1, 1, 1, 1]
    assert cases["H51"]["coverage_groups"][0]["num_assertions"] == 44
    assert [cases["H41"]["traces"][tid]["fault_action_events"][0]["checked_precondition_truth"] for tid in ORDER] == [True, True, False, False]
    for cid, expected in (("H51", {"F1": (9, 13), "F2": (20, 21)}),
                          ("H26", {"F1": (4, 6), "F2": (2, 5)}),
                          ("H34", {"F1": (4, 6), "F2": (2, 6)}),
                          ("H21", {"F1": (4, 6), "F2": (2, 5)})):
        for tid, pair in expected.items():
            links = cases[cid]["traces"][tid]["gold_guided_dependency_matches"]
            assert len(links) == 1 and (links[0]["source_step"], links[0]["failure_step"]) == pair
    h26 = {aid: tuple(int(r[t]) for t in ORDER) for r in read_csv(results / "H26/coverage_matrix.csv") for aid in [r["assertion_id"]]}
    h21 = {r["assertion_id"]: tuple(int(r[t]) for t in ORDER) for r in read_csv(results / "H21/coverage_matrix.csv")}
    assert len(h21) == 42 and all(h26[aid] == vector for aid, vector in h21.items())
    problem_summary = sorted(problem_rows.values(), key=lambda x: int(x["problem_id"].removeprefix("train_problem")))
    assert len(cases) == 30 and sum(p["selected_replays"] for p in problem_summary) == 120
    write_json(output / "coverage_overview.json", overview)
    write_json(output / "problem_summary.json", problem_summary)
    (output / "report.md").write_text(report_text(cases, overview, problem_summary), encoding="utf-8")
    assert fingerprint(project) == source_before
    assert fingerprint(results) == results_before
    audit = {"status": "pass", "analysis_type": "posthoc_gold_and_reference_trace_analysis_only",
             "source_project": str(project), "existing_sbfl_results": str(results),
             "cases": len(cases), "selected_mutant_traces": 120, "unique_selected_official_problems": len(problem_summary),
             "successes": sum(p["successes"] for p in problem_summary), "failures": sum(p["failures"] for p in problem_summary),
             "failure_kinds": dict(failures), "total_executed_steps": executed_steps,
             "coverage_group_count_distribution": dict(sorted(Counter(r["num_distinct_coverage_vectors"] for r in overview).items())),
             "raw_input_file_count": len(source_before), "original_sbfl_result_file_count": len(results_before),
             "raw_inputs_byte_identical_before_and_after": True, "sbfl_results_byte_identical_before_and_after": True,
             "example_dependency_matches_grounded_and_persistent": True, "H21_H26_common_candidate_coverage_identical": True,
             "new_planner_runs": 0, "new_simulator_runs": 0, "scores_recomputed_or_changed": False,
             "source_run_manifest_sha256": sha(results / "run_manifest.json")}
    write_json(output / "audit.json", audit)
    print(audit)
    return audit


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=root.parent / "experiments/logistics_challenge_30_validated")
    parser.add_argument("--results", type=Path, default=root / "results")
    parser.add_argument("--output", type=Path, default=root / "trace_analysis")
    args = parser.parse_args()
    analyze(args.project, args.results, args.output)
