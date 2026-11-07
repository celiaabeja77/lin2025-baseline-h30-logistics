# Logistics SBFL＋Ochiai

30 個錯誤版本；120 條既有軌跡；60 成功／60 失敗。每版獨立計分。

Coverage 沿用 Depot baseline：precondition 的 grounded literal 出現在檢查紀錄就算碰到，無論真值；動作 executed=true 時，其所有無條件 STRIPS effects 都算碰到，包含未改變狀態的效果。每條軌跡每條 assertion 只記 0/1。

Ochiai = ef / sqrt(F × (ef + ep))；ef、ep 分別是碰到它的失敗、成功軌跡數；F 是該版全部失敗軌跡數，本資料每版 F=2。分母為零時分數為 0。

先完成所有現有 assertions 的盲排名，才載入 evaluation/fault_info。正確 Domain、reference traces、狀態差異、條件真值與首次偏離均不參與計分。

Strict Top-K：worst_rank ≤ K；Tie-aware Top-K：best_rank ≤ K。候選清單保留完整同分群組，所以可超過 K 條。

## Top-1／3／5（全部案例）

缺失 assertion 在此 baseline 沒有候選槽位；全案例 exact-assertion 指標將這類案例計為未命中。

| K | 案例數 | Strict Accuracy | Tie-aware Accuracy |
|---:|---:|---:|---:|
| 1 | 30 | 0.00% (0/30) | 90.00% (27/30) |
| 3 | 30 | 0.00% (0/30) | 90.00% (27/30) |
| 5 | 30 | 3.33% (1/30) | 90.00% (27/30) |

## 真正錯誤仍存在於候選集的案例

這是候選集涵蓋範圍內的補充指標，不能取代全案例結果。

| K | 可排名案例數 | Strict Accuracy | Tie-aware Accuracy |
|---:|---:|---:|---:|
| 1 | 27 | 0.00% (0/27) | 100.00% (27/27) |
| 3 | 27 | 0.00% (0/27) | 100.00% (27/27) |
| 5 | 27 | 3.70% (1/27) | 100.00% (27/27) |


逐案候選數與完整排名見 report.md。
