# Logistics assertion-level SBFL＋Ochiai

對 `experiments/logistics_challenge_30_validated` 的 30 個錯誤版本、120 條已保存軌跡執行原本的純 SBFL baseline。每版獨立使用 2 成功＋2 失敗；不混入正確版本的 reference traces。

```bash
python -B run_all.py --project ../experiments/logistics_challenge_30_validated
python -B verify_results.py --project ../experiments/logistics_challenge_30_validated
python -B -m unittest discover -s tests -v
```

只需要 Python 3 標準函式庫，不需要 UP、Fast Downward 或模型。Windows 可用 `python -B -X utf8`；Linux 可用 `python3 -B`。本資料夾可獨立搬移，使用 `--project` 指向原始資料；`--output` 指定另一個輸出資料夾。`--case H08` 可只算一案。

## Coverage 與分數

- Precondition：在 attempted step 的 `grounded_preconditions` 中有對應 literal，記為碰到；不使用條件真值。
- Effect：動作 `executed=true`，其無條件 STRIPS effects 都記為碰到，包含合法 no-op。拒絕執行的動作不覆蓋 effects。
- 每條軌跡每條 assertion 只記 0/1；重複碰到不累加。
- 直接使用 JSON `success`，先檢查它等於 `sequence_completed AND full_goal_reached` 且與 validator 一致。不依 S/F 檔名推定結果。
- `Ochiai = ef / sqrt(F × (ef + ep))`；分母為零時分數為 0。`F` 是該案所有失敗軌跡數，本資料每案為 2。
- 同分保留整組；`best_rank`／`worst_rank` 是共享排名區間。Strict 命中採 `worst_rank <= K`，Tie-aware 採 `best_rank <= K`。

`src/` 的 8 個模組及 `baseline_topk.py` 均逐位元複製自既有 `depot_assertion_sbfl`；雜湊見 `baseline_reuse.json`。新程式只調整資料夾結構、label schema 與不同 fault operation 的評估。舊版 Depot 程式與結果均保留。

## 三個缺失 assertion 案例

H21、H23、H25 的 gold literal 已從 Domain 刪除。現有 assertion 候選集中沒有那條 literal，因此不捏造 coverage、分數或排名，也不從正確 Domain 補回候選。

- 全部 30 案的 exact-assertion accuracy：這 3 案計為未命中。
- 另外列出可排名 27 案的條件性結果，清楚標示分母。
- 這 3 案仍輸出其餘現有 assertions 的完整 ranking 與 Top-K 清單；`ground_truth_in_candidate_set=false`，gold score/rank 留空。
- 原版故障槽位僅保存在評估欄位 `reference_fault_slot`，不參與候選建立或計分。

## 輸出

`results/report.md` 是中文完整報告，包含 30 案 gold 結果、兩種分母的 Strict／Tie-aware Top-1／3／5、逐案候選數與限制。

`results/summary.csv`、`top_k_summary.csv`、`top_k_metrics.csv` 可匯入表格工具。每案另外有 `coverage_matrix.csv`、`trace_labels.csv`、`ranking_blind.csv`、帶 gold 註記的 `ranking.csv`、`summary.json`、`same_action_tie_check.json`、`top1.csv`、`top3.csv`、`top5.csv`。

所有 blind ranking 都先保存，才載入 gold 做評估；`ranking_blind.csv` 不含 gold 標記。原始套件所有檔案執行前後做 SHA-256 比對，記錄於 `results/run_manifest.json`。

`verify_results.py` 獨立重建所有 coverage bits、ef/ep/F、Ochiai、並列區間與 Top-K，再核對保存的 grounded 狀態轉移及 30 個單條修改。它只在結果資料夾寫入 `verification.json`；不呼叫資料套件中會寫檔的驗證 main()，也不重新執行規劃器或模擬器。

本次只有使用套件內已選定的 120 條 mutant traces；官方 50 題不全數投入，四條測試也可能隨錯誤版本不同。結果應解讀為這個 2＋2 選定子集上的表現。

## 事後 Trace／Coverage 分析

`python -B analyze_traces.py` 讀取已有排名、原始 mutant traces、reference traces 與評估真值，輸出 `trace_analysis/report.md`。此報告分析 H51、H41、H26、H34、H21 的具體困難，並列出全 30 案的 coverage 多樣性、10 個選定官方 Problem 的使用情況與全部 120 條 trace 概覽。

每案 grounded 事件、動作順序、執行次數與 coverage 群組保存於 `trace_analysis/cases/Hxx.json`；`audit.json` 記錄原始資料和既有 SBFL 結果均保持位元組不變。這是使用 gold 的事後解釋，不是新的定位分數；也沒有執行新 Problem、規劃、模擬或修復。先前交付的 ZIP 保留當時的計分程式與結果；此新增分析請使用目前資料夾中的檔案。
