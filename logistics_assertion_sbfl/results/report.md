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

## SBFL 排名結果

缺失案例只顯示原版故障槽位，ef、ep、score、rank 留空，不把被刪除的 literal 加回方法輸入。

| Case | 編輯 | 真正錯誤／原版缺失位置 | ef | ep | F | Ochiai | 排名區間 | 並列數 |
|---|---|---|---:|---:|---:|---:|---|---:|
| H08 | replace | DRIVE-TRUCK.precondition[5] | 2 | 0 | 2 | 1.000000 | 1～7 | 7 |
| H15 | replace | LOAD-TRUCK.precondition[5] | 2 | 0 | 2 | 1.000000 | 1～5 | 5 |
| H21 | delete | LOAD-TRUCK.effect[2]（已刪除） | — | — | 2 | — | 無對應候選 | — |
| H23 | delete | DRIVE-TRUCK.effect[2]（已刪除） | — | — | 2 | — | 無對應候選 | — |
| H25 | delete | UNLOAD-TRUCK.effect[2]（已刪除） | — | — | 2 | — | 無對應候選 | — |
| H26 | replace | LOAD-TRUCK.effect[2] | 2 | 0 | 2 | 1.000000 | 1～21 | 21 |
| H28 | replace | UNLOAD-TRUCK.precondition[5] | 2 | 0 | 2 | 1.000000 | 1～21 | 21 |
| H29 | replace | LOAD-TRUCK.effect[1] | 2 | 0 | 2 | 1.000000 | 1～14 | 14 |
| H32 | add | DRIVE-TRUCK.effect[3] | 2 | 0 | 2 | 1.000000 | 1～17 | 17 |
| H33 | add | DRIVE-TRUCK.effect[3] | 2 | 0 | 2 | 1.000000 | 1～17 | 17 |
| H34 | add | FLY-AIRPLANE.effect[3] | 2 | 2 | 2 | 0.707107 | 1～21 | 21 |
| H35 | add | LOAD-TRUCK.effect[3] | 2 | 0 | 2 | 1.000000 | 1～22 | 22 |
| H36 | add | DRIVE-TRUCK.effect[3] | 2 | 0 | 2 | 1.000000 | 1～15 | 15 |
| H38 | replace | DRIVE-TRUCK.effect[2] | 2 | 0 | 2 | 1.000000 | 1～14 | 14 |
| H40 | replace | LOAD-TRUCK.effect[2] | 2 | 0 | 2 | 1.000000 | 1～21 | 21 |
| H41 | replace | LOAD-TRUCK.precondition[3] | 2 | 2 | 2 | 0.707107 | 1～14 | 14 |
| H42 | replace | UNLOAD-TRUCK.precondition[3] | 2 | 0 | 2 | 1.000000 | 1～21 | 21 |
| H43 | replace | DRIVE-TRUCK.precondition[2] | 2 | 2 | 2 | 0.707107 | 1～7 | 7 |
| H44 | replace | LOAD-TRUCK.effect[2] | 2 | 0 | 2 | 1.000000 | 1～21 | 21 |
| H45 | replace | UNLOAD-TRUCK.effect[2] | 2 | 0 | 2 | 1.000000 | 1～23 | 23 |
| H46 | replace | DRIVE-TRUCK.effect[2] | 2 | 0 | 2 | 1.000000 | 1～14 | 14 |
| H47 | add | LOAD-TRUCK.effect[3] | 2 | 0 | 2 | 1.000000 | 1～15 | 15 |
| H48 | add | UNLOAD-TRUCK.effect[3] | 2 | 2 | 2 | 0.707107 | 1～29 | 29 |
| H49 | add | UNLOAD-AIRPLANE.effect[3] | 2 | 2 | 2 | 0.707107 | 1～21 | 21 |
| H50 | add | LOAD-TRUCK.effect[3] | 2 | 0 | 2 | 1.000000 | 1～15 | 15 |
| H51 | add | UNLOAD-TRUCK.effect[3] | 2 | 2 | 2 | 0.707107 | 1～44 | 44 |
| H52 | add | UNLOAD-AIRPLANE.effect[3] | 2 | 2 | 2 | 0.707107 | 1～21 | 21 |
| H53 | add | LOAD-TRUCK.effect[3] | 2 | 2 | 2 | 0.707107 | 1～35 | 35 |
| H54 | add | UNLOAD-TRUCK.effect[3] | 2 | 2 | 2 | 0.707107 | 1～35 | 35 |
| H55 | add | UNLOAD-AIRPLANE.effect[3] | 2 | 2 | 2 | 0.707107 | 1～21 | 21 |

## Top-K 候選數與命中

| Case | Top-1 候選數 | Top-3 候選數 | Top-5 候選數 | Strict 最小命中 K（1/3/5） | Tie-aware 最小命中 K（1/3/5） |
|---|---:|---:|---:|---|---|
| H08 | 7 | 7 | 7 | 未命中 | Top-1 |
| H15 | 5 | 5 | 5 | Top-5 | Top-1 |
| H21 | 20 | 20 | 20 | 未命中 | 未命中 |
| H23 | 13 | 13 | 13 | 未命中 | 未命中 |
| H25 | 22 | 22 | 22 | 未命中 | 未命中 |
| H26 | 21 | 21 | 21 | 未命中 | Top-1 |
| H28 | 21 | 21 | 21 | 未命中 | Top-1 |
| H29 | 14 | 14 | 14 | 未命中 | Top-1 |
| H32 | 17 | 17 | 17 | 未命中 | Top-1 |
| H33 | 17 | 17 | 17 | 未命中 | Top-1 |
| H34 | 21 | 21 | 21 | 未命中 | Top-1 |
| H35 | 22 | 22 | 22 | 未命中 | Top-1 |
| H36 | 15 | 15 | 15 | 未命中 | Top-1 |
| H38 | 14 | 14 | 14 | 未命中 | Top-1 |
| H40 | 21 | 21 | 21 | 未命中 | Top-1 |
| H41 | 14 | 14 | 14 | 未命中 | Top-1 |
| H42 | 21 | 21 | 21 | 未命中 | Top-1 |
| H43 | 7 | 7 | 7 | 未命中 | Top-1 |
| H44 | 21 | 21 | 21 | 未命中 | Top-1 |
| H45 | 23 | 23 | 23 | 未命中 | Top-1 |
| H46 | 14 | 14 | 14 | 未命中 | Top-1 |
| H47 | 15 | 15 | 15 | 未命中 | Top-1 |
| H48 | 29 | 29 | 29 | 未命中 | Top-1 |
| H49 | 21 | 21 | 21 | 未命中 | Top-1 |
| H50 | 15 | 15 | 15 | 未命中 | Top-1 |
| H51 | 44 | 44 | 44 | 未命中 | Top-1 |
| H52 | 21 | 21 | 21 | 未命中 | Top-1 |
| H53 | 35 | 35 | 35 | 未命中 | Top-1 |
| H54 | 35 | 35 | 35 | 未命中 | Top-1 |
| H55 | 21 | 21 | 21 | 未命中 | Top-1 |

## 本次觀察

- 27 個可排名案例中，27 案真正錯誤位於最高分群組；這是候選群組命中，不能解讀為唯一第一名。
- 真正錯誤所在的最高分群組有 5～44 條並列。
- H51 的全部 44 條 assertions 都同分，這一案的分數未縮小候選範圍。

## 解讀範圍

- 缺失 assertion 案例：H21、H23、H25。它們仍有其餘現有 assertions 的完整排名。
- 本次使用套件內已選定的每版 2 成功＋2 失敗，並非全部 50 題都投入 SBFL，各版本使用的四個 Problem 也可能不同。
- 成功／失敗平衡與案例保留條件屬資料選樣設計；結果是這個選定子集的定位表現。
- 同分代表此 coverage 與分數不能排序群組內候選；顯示順序不是額外的名次。
- 每案 ranking_blind.csv、ranking.csv、coverage_matrix.csv、trace_labels.csv、top1/3/5.csv 可供追查。
- 本次沒有新建 fault、改寫 Problem／Goal／Plan／Trace、重新規劃、重新模擬、使用模型或進行 repair。
