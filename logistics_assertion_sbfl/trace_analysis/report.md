# Logistics：SBFL 難定位案例與跨 Problem Trace／Coverage 分析

這批資料的主要困難是最高分候選大量並列。27 個仍存在於候選集的真正錯誤都位於最高分群組；沒有觀察到 gold 落在較低分群組的排名偏移。另 3 案的 gold 已被刪除，屬候選集缺口。

資料是 30 個錯誤版本、120 條選定的官方 Problem 重播，每版 2 成功＋2 失敗，實際涵蓋 10 個不同 Problem。不同版本的 S1/S2/F1/F2 不一定對應相同 Problem；50 題官方題庫不全數投入這次 SBFL。

下列所有向量固定依 S1、S2、F1、F2 排列，1 表示該條軌跡碰到該 assertion，0 表示沒有。每條 trace 只記一次；檢查過的 precondition 不分真值，只有實際執行的動作才覆蓋 effects。

## 案例概覽

| Case | 觀察到的困難 | gold ef/ep | gold 分數 | gold 排名 | coverage 群組數 |
|---|---|---|---|---|---|
| H51 | 所有 coverage 飽和，物件再利用差異消失 | 2/2 | 0.7071067811865475 | 1～44 | 1 |
| H41 | 有檢查相同，條件真值不同 | 2/2 | 0.7071067811865475 | 1～14 | 2 |
| H26 | 不同動作共同出現在失敗路線 | 2/0 | 1.0 | 1～21 | 3 |
| H34 | 機場位置參數與再利用順序被壓縮 | 2/2 | 0.7071067811865475 | 1～21 | 2 |
| H21 | 缺失 assertion 候選缺口；與 H26 可同症狀 | 無候選 | 無候選 | 無候選 | 3 |

## H51：做過一樣的動作，後續是否再用同一輛車卻不同

UNLOAD-TRUCK 多了一條錯誤效果 `(not (at ?truck ?loc))`：卸貨後順便抹掉卡車位置。

| Trace | 官方 Problem | 觀察到的執行差異 | 結果 |
|---|---|---|---|
| S1 | train_problem2 | 第 6 步卸貨刪除 (at t1 l11)，計畫於此結束 | 成功：完整貨物目標已達成 |
| S2 | train_problem16 | 第 11 步卸貨刪除 (at t2 l21)，之後第 12、13 步只操作飛機 | 成功：沒有再使用 t2 |
| F1 | train_problem5 | 第 9 步卸貨刪除 (at t0 l00)，第 13 步再次用 t0 裝貨 | 失敗：缺 (at t0 l00) |
| F2 | train_problem7 | 第 20 步卸貨刪除 (at t3 l32)，第 21 步同車再次卸貨 | 失敗：缺 (at t3 l32) |

四條 trace 都至少實際執行過六種動作，因此全部 44 條 assertions 的 coverage 都是 `[1,1,1,1]`，ef=2、ep=2、F=2、Ochiai=0.707107，並列第 1～44 名。

成功 trace 也真的刪錯卡車位置；完整貨物目標仍可達成，並不證明所有狀態都正確。失敗與否取決於後續是否還需要該車的位置，而不是 UNLOAD-TRUCK 是否曾出現。

F1 最早的狀態差異是第 5 步（另一輛 t1），但與第 13 步直接對應的缺失事實來自第 9 步 t0。F2 最早差異也是第 5 步，但與第 21 步缺 (at t3 l32) 對應的是第 20 步。不可把第一次偏離自動當成這次受阻的直接來源。

以下是實際執行次數（不是新的 coverage 或新的可疑度計分）：

| 動作 | S1 | S2 | F1 | F2 |
|---|---|---|---|---|
| LOAD-TRUCK | 1 | 1 | 3 | 4 |
| UNLOAD-TRUCK | 1 | 1 | 2 | 3 |
| DRIVE-TRUCK | 1 | 1 | 4 | 7 |
| LOAD-AIRPLANE | 1 | 3 | 1 | 2 |
| UNLOAD-AIRPLANE | 1 | 3 | 1 | 2 |
| FLY-AIRPLANE | 1 | 4 | 1 | 2 |

雖然次數與順序不同，binary assertion coverage 仍全部為 1；僅改用次數也尚未經實驗驗證能定位。

## H41：同一條件都檢查過，但機場與一般地點的真值不同

LOAD-TRUCK.precondition[3] 把 `(LOCATION ?loc)` 寫成 `(AIRPORT ?loc)`，因此一般地點不能裝貨。

| Trace | Problem | 檢查步驟 | 代入物件的錯誤條件 | 當下真值 | binary coverage | 結果 |
|---|---|---|---|---|---|---|
| S1 | train_problem2 | 4 | (airport l10) | 成立 | 1 | 成功 |
| S2 | train_problem16 | 9 | (airport l20) | 成立 | 1 | 成功 |
| F1 | train_problem5 | 2 | (airport l11) | 不成立 | 1 | 失敗 |
| F2 | train_problem7 | 3 | (airport l21) | 不成立 | 1 | 失敗 |

四次 LOAD-TRUCK 檢查中，其餘四條 preconditions 都成立；只有錯寫的機場條件在失敗 trace 不成立。這個差異保存在原始 precondition_results，未進入目前的 SBFL 分數。

| 候選／群組 | S1 | S2 | F1 | F2 | ef | ep | Ochiai |
|---|---|---|---|---|---|---|---|
| 錯誤的 LOAD-TRUCK.precondition[3] | 1 | 1 | 1 | 1 | 2 | 2 | 0.707107 |
| 其餘正確的 LOAD-TRUCK preconditions | 1 | 1 | 1 | 1 | 2 | 2 | 0.707107 |
| 正確的 DRIVE-TRUCK 全部 assertions | 1 | 1 | 1 | 1 | 2 | 2 | 0.707107 |
| LOAD-TRUCK effects | 1 | 1 | 0 | 0 | 0 | 2 | 0 |

因此 5 條 LOAD-TRUCK preconditions 加上 9 條 DRIVE-TRUCK assertions 共 14 條同分第一。失敗時裝貨 effects 未執行，所以 effects 與 preconditions 的 coverage 可以不同，不能說『嘗試一個 action 就把全部 assertion 一起加一』。

## H26：成功只走空運，卡車路線的正確與錯誤 assertions 一起得高分

LOAD-TRUCK.effect[2] 將 `(in ?obj ?truck)` 寫反為 `(in ?truck ?obj)`。

| Trace | Problem | 執行觀察 | 結果 |
|---|---|---|---|
| S1 | train_problem0 | 7 步，只有飛機裝貨、飛行、卸貨 | 成功 |
| S2 | train_problem1 | 14 步，只有飛機裝貨、飛行、卸貨 | 成功 |
| F1 | train_problem2 | 第 4 步裝貨建立 (in t1 p0)，第 6 步卸貨要求 (in p0 t1) | 第 6 步受阻 |
| F2 | train_problem5 | 第 2 步裝 p2 建立 (in t1 p2)，第 5 步卸 p2 要求 (in p2 t1) | 第 5 步受阻 |

| 候選群組 | S1 | S2 | F1 | F2 | 數量 | ef/ep | Ochiai |
|---|---|---|---|---|---|---|---|
| LOAD-TRUCK 全部 preconditions/effects | 0 | 0 | 1 | 1 | 7 | 2/0 | 1 |
| UNLOAD-TRUCK 被檢查的 preconditions | 0 | 0 | 1 | 1 | 5 | 2/0 | 1 |
| DRIVE-TRUCK 全部 assertions | 0 | 0 | 1 | 1 | 9 | 2/0 | 1 |
| UNLOAD-TRUCK 沒執行的 effects | 0 | 0 | 0 | 0 | 2 | 0/0 | 0 |

因此真正錯誤與其他正常 assertions 共 21 條並列第 1～21 名。這裡同時有同一 action 內的共同覆蓋，以及不同 action 在失敗路線中共同出現；兩者需分開說明。

新增能拆開卡車動作組合的合理 Problem，可能改善跨 action 的共同覆蓋；若同一個 action 的 assertions 仍每次一起被檢查或套用，增加 trace 數量本身不保證分開。這是方法設計上的推論，尚未以新增 Problem 驗證。

## H34：成功與失敗都飛行，但是否再次使用被破壞的機場不同

FLY-AIRPLANE 多了 `(not (AIRPORT ?loc-to))`，到達後移除目的地的機場資格。

| Trace | Problem | 關鍵過程 | 結果 |
|---|---|---|---|
| S1 | train_problem2 | 第 2 步移除 (airport l10)，後續卸貨、改走卡車 | 成功 |
| S2 | train_problem3 | 第 2 步刪 l10、第 5 步刪 l20 的機場資格；後續不再飛行 | 成功 |
| F1 | train_problem0 | 第 4 步 a4 到 l10 並刪機場資格，第 6 步 a4 要從 l10 再起飛 | 缺 (airport l10) 而受阻 |
| F2 | train_problem1 | 第 2 步 a5 到 l10 並刪機場資格，第 6 步 a5 要從 l10 再起飛 | 缺 (airport l10) 而受阻 |

三種空運動作的 21 條 assertions 都是 `[1,1,1,1]`，分數 0.707107，共享第 1～21 名。完整 trace 能顯示機場參數與再次使用的先後順序；binary coverage 只留下是否曾碰過。

案例描述文字提到『另一架飛機無法降落』，但這兩條已保存失敗 trace 實際呈現的是同一架飛機從剛到達的地點再起飛受阻；本分析以實際紀錄為準。

## H21：與 H26 的失敗症狀、現有 coverage 相同，但真正缺失的 literal 沒有候選

H21 刪掉 `(in ?obj ?truck)`；H26 則保留一條內容寫反的 effect。兩版使用相同的四個 Problem、相同計畫與相同成功／失敗結果：F1 都在第 6 步卸貨，F2 都在第 5 步卸貨時缺少正向的 in 關係。

兩版共有的 42 條候選（依相同 assertion ID 對照，僅比 coverage）都有相同向量。H26 額外存在內容寫反的 LOAD-TRUCK.effect[2]，H21 完全沒有那個 effect 槽位。H21 最高分仍有 20 條，但真正缺少的效果不能直接排入名次。這是候選集設計限制，應與同分問題分開報告。

## 同一個 Problem，換錯誤版本後的失敗位置不同

| Problem | H26 | H41 | H51 |
|---|---|---|---|
| train_problem2 | 第 6 步 UNLOAD-TRUCK：缺 (in p0 t1) | 成功 | 成功，但最後卸貨抹掉卡車位置 |
| train_problem5 | 第 5 步 UNLOAD-TRUCK：缺 (in p2 t1) | 第 2 步 LOAD-TRUCK：缺 (airport l11) | 第 13 步 LOAD-TRUCK：缺 (at t0 l00) |

這也說明不能把 S1/F1 當作固定 Problem 名稱，或把實際受阻的 action 當作真正錯誤 action。這張對照保持 Problem 與參考計畫不變，只比較現有不同 mutant 的紀錄。

## 全 30 案的 coverage 多樣性

| 每案不同 coverage 向量數 | 案例數 |
|---|---|
| 1 | 1 |
| 2 | 10 |
| 3 | 10 |
| 4 | 9 |

每版有 42～44 條 assertions，但在目前四條選定 trace 上，實際只形成 1～4 種不同向量。這是本資料中可直接量化的證據不足現象，不等於已證明所有可能 Problem 都無法分開。

## 選定 Problem 的使用情況

以下次數只計入本次選定子集，不是各 Problem 在完整題庫或所有 mutant 上的自然成功率。

| 官方 Problem | 參考計畫步數 | 目標數 | 本子集重播次數 | 成功 | 失敗 |
|---|---|---|---|---|---|
| train_problem0 | 7 | 2 | 24 | 23 | 1 |
| train_problem1 | 14 | 5 | 24 | 20 | 4 |
| train_problem2 | 6 | 2 | 28 | 10 | 18 |
| train_problem3 | 6 | 3 | 1 | 1 | 0 |
| train_problem4 | 9 | 4 | 3 | 0 | 3 |
| train_problem5 | 25 | 6 | 26 | 0 | 26 |
| train_problem7 | 30 | 4 | 8 | 0 | 8 |
| train_problem9 | 14 | 5 | 1 | 1 | 0 |
| train_problem15 | 16 | 3 | 1 | 1 | 0 |
| train_problem16 | 13 | 4 | 4 | 4 | 0 |

## 全 120 條 trace 概覽

『覆蓋數』是本次既有 coverage_matrix.csv 中為 1 的現有 assertions 數；參考計畫步數是完整計畫長度，實際重播可能提早受阻。

| Case | Trace | Problem | 完整計畫步數 | 實際執行步數 | 覆蓋數 | 結果／受阻位置 |
|---|---|---|---|---|---|---|
| H08 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H08 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H08 | F1 | train_problem2 | 6 | 4 | 34 | 第 5 步 (drive-truck t1 l10 l11 c1) |
| H08 | F2 | train_problem5 | 25 | 0 | 7 | 第 1 步 (drive-truck t1 l10 l11 c1) |
| H15 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H15 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H15 | F1 | train_problem2 | 6 | 3 | 25 | 第 4 步 (load-truck p0 t1 l10) |
| H15 | F2 | train_problem5 | 25 | 1 | 14 | 第 2 步 (load-truck p2 t1 l11) |
| H21 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H21 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H21 | F1 | train_problem2 | 6 | 5 | 40 | 第 6 步 (unload-truck p0 t1 l11) |
| H21 | F2 | train_problem5 | 25 | 4 | 20 | 第 5 步 (unload-truck p2 t1 l10) |
| H23 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H23 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H23 | F1 | train_problem2 | 6 | 5 | 40 | 第 6 步 (unload-truck p0 t1 l11) |
| H23 | F2 | train_problem5 | 25 | 1 | 13 | 第 2 步 (load-truck p2 t1 l11) |
| H25 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H25 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H25 | F1 | train_problem2 | 6 | 6 | 42 | 完整執行後 Goal 未達成 |
| H25 | F2 | train_problem5 | 25 | 18 | 42 | 第 19 步 (load-airplane p1 a5 l00) |
| H26 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H26 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H26 | F1 | train_problem2 | 6 | 5 | 41 | 第 6 步 (unload-truck p0 t1 l11) |
| H26 | F2 | train_problem5 | 25 | 4 | 21 | 第 5 步 (unload-truck p2 t1 l10) |
| H28 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H28 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H28 | F1 | train_problem2 | 6 | 5 | 41 | 第 6 步 (unload-truck p0 t1 l11) |
| H28 | F2 | train_problem5 | 25 | 4 | 21 | 第 5 步 (unload-truck p2 t1 l10) |
| H29 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H29 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H29 | F1 | train_problem2 | 6 | 4 | 34 | 第 5 步 (drive-truck t1 l10 l11 c1) |
| H29 | F2 | train_problem5 | 25 | 2 | 16 | 第 3 步 (drive-truck t1 l11 l10 c1) |
| H32 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H32 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H32 | F1 | train_problem5 | 25 | 2 | 17 | 第 3 步 (drive-truck t1 l11 l10 c1) |
| H32 | F2 | train_problem7 | 30 | 18 | 44 | 第 19 步 (drive-truck t3 l30 l32 c3) |
| H33 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H33 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H33 | F1 | train_problem5 | 25 | 2 | 17 | 第 3 步 (drive-truck t1 l11 l10 c1) |
| H33 | F2 | train_problem7 | 30 | 3 | 17 | 第 4 步 (drive-truck t2 l21 l20 c2) |
| H34 | S1 | train_problem2 | 6 | 6 | 44 | 成功 |
| H34 | S2 | train_problem3 | 6 | 6 | 21 | 成功 |
| H34 | F1 | train_problem0 | 7 | 5 | 21 | 第 6 步 (fly-airplane a4 l10 l20) |
| H34 | F2 | train_problem1 | 14 | 5 | 21 | 第 6 步 (fly-airplane a5 l10 l50) |
| H35 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H35 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H35 | F1 | train_problem2 | 6 | 5 | 42 | 第 6 步 (unload-truck p0 t1 l11) |
| H35 | F2 | train_problem5 | 25 | 4 | 22 | 第 5 步 (unload-truck p2 t1 l10) |
| H36 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H36 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H36 | F1 | train_problem2 | 6 | 5 | 42 | 第 6 步 (unload-truck p0 t1 l11) |
| H36 | F2 | train_problem5 | 25 | 1 | 15 | 第 2 步 (load-truck p2 t1 l11) |
| H38 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H38 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H38 | F1 | train_problem2 | 6 | 5 | 41 | 第 6 步 (unload-truck p0 t1 l11) |
| H38 | F2 | train_problem5 | 25 | 1 | 14 | 第 2 步 (load-truck p2 t1 l11) |
| H40 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H40 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H40 | F1 | train_problem2 | 6 | 5 | 41 | 第 6 步 (unload-truck p0 t1 l11) |
| H40 | F2 | train_problem5 | 25 | 4 | 21 | 第 5 步 (unload-truck p2 t1 l10) |
| H41 | S1 | train_problem2 | 6 | 6 | 43 | 成功 |
| H41 | S2 | train_problem16 | 13 | 13 | 43 | 成功 |
| H41 | F1 | train_problem5 | 25 | 1 | 14 | 第 2 步 (load-truck p2 t1 l11) |
| H41 | F2 | train_problem7 | 30 | 2 | 14 | 第 3 步 (load-truck p1 t2 l21) |
| H42 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H42 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H42 | F1 | train_problem2 | 6 | 5 | 41 | 第 6 步 (unload-truck p0 t1 l11) |
| H42 | F2 | train_problem5 | 25 | 15 | 43 | 第 16 步 (unload-truck p0 t0 l02) |
| H43 | S1 | train_problem2 | 6 | 6 | 43 | 成功 |
| H43 | S2 | train_problem16 | 13 | 13 | 43 | 成功 |
| H43 | F1 | train_problem5 | 25 | 2 | 16 | 第 3 步 (drive-truck t1 l11 l10 c1) |
| H43 | F2 | train_problem7 | 30 | 0 | 7 | 第 1 步 (drive-truck t3 l32 l30 c3) |
| H44 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H44 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H44 | F1 | train_problem2 | 6 | 5 | 41 | 第 6 步 (unload-truck p0 t1 l11) |
| H44 | F2 | train_problem5 | 25 | 4 | 21 | 第 5 步 (unload-truck p2 t1 l10) |
| H45 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H45 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H45 | F1 | train_problem2 | 6 | 6 | 43 | 完整執行後 Goal 未達成 |
| H45 | F2 | train_problem5 | 25 | 18 | 43 | 第 19 步 (load-airplane p1 a5 l00) |
| H46 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H46 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H46 | F1 | train_problem2 | 6 | 5 | 41 | 第 6 步 (unload-truck p0 t1 l11) |
| H46 | F2 | train_problem5 | 25 | 1 | 14 | 第 2 步 (load-truck p2 t1 l11) |
| H47 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H47 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H47 | F1 | train_problem2 | 6 | 4 | 35 | 第 5 步 (drive-truck t1 l10 l11 c1) |
| H47 | F2 | train_problem5 | 25 | 2 | 17 | 第 3 步 (drive-truck t1 l11 l10 c1) |
| H48 | S1 | train_problem2 | 6 | 6 | 44 | 成功 |
| H48 | S2 | train_problem9 | 14 | 14 | 44 | 成功 |
| H48 | F1 | train_problem5 | 25 | 18 | 44 | 第 19 步 (load-airplane p1 a5 l00) |
| H48 | F2 | train_problem7 | 30 | 10 | 29 | 第 11 步 (load-airplane p1 a8 l20) |
| H49 | S1 | train_problem0 | 7 | 7 | 21 | 成功 |
| H49 | S2 | train_problem2 | 6 | 6 | 44 | 成功 |
| H49 | F1 | train_problem1 | 14 | 3 | 21 | 第 4 步 (load-airplane p2 a5 l10) |
| H49 | F2 | train_problem4 | 9 | 4 | 21 | 第 5 步 (fly-airplane a4 l30 l20) |
| H50 | S1 | train_problem0 | 7 | 7 | 20 | 成功 |
| H50 | S2 | train_problem1 | 14 | 14 | 20 | 成功 |
| H50 | F1 | train_problem2 | 6 | 4 | 35 | 第 5 步 (drive-truck t1 l10 l11 c1) |
| H50 | F2 | train_problem5 | 25 | 2 | 17 | 第 3 步 (drive-truck t1 l11 l10 c1) |
| H51 | S1 | train_problem2 | 6 | 6 | 44 | 成功 |
| H51 | S2 | train_problem16 | 13 | 13 | 44 | 成功 |
| H51 | F1 | train_problem5 | 25 | 12 | 44 | 第 13 步 (load-truck p0 t0 l00) |
| H51 | F2 | train_problem7 | 30 | 20 | 44 | 第 21 步 (unload-truck p1 t3 l32) |
| H52 | S1 | train_problem0 | 7 | 7 | 21 | 成功 |
| H52 | S2 | train_problem2 | 6 | 6 | 44 | 成功 |
| H52 | F1 | train_problem1 | 14 | 3 | 21 | 第 4 步 (load-airplane p2 a5 l10) |
| H52 | F2 | train_problem4 | 9 | 4 | 21 | 第 5 步 (fly-airplane a4 l30 l20) |
| H53 | S1 | train_problem2 | 6 | 6 | 44 | 成功 |
| H53 | S2 | train_problem15 | 16 | 16 | 44 | 成功 |
| H53 | F1 | train_problem5 | 25 | 10 | 35 | 第 11 步 (fly-airplane a5 l10 l00) |
| H53 | F2 | train_problem7 | 30 | 15 | 44 | 第 16 步 (fly-airplane a7 l10 l30) |
| H54 | S1 | train_problem2 | 6 | 6 | 44 | 成功 |
| H54 | S2 | train_problem16 | 13 | 13 | 44 | 成功 |
| H54 | F1 | train_problem5 | 25 | 10 | 35 | 第 11 步 (fly-airplane a5 l10 l00) |
| H54 | F2 | train_problem7 | 30 | 11 | 35 | 第 12 步 (fly-airplane a8 l20 l30) |
| H55 | S1 | train_problem0 | 7 | 7 | 21 | 成功 |
| H55 | S2 | train_problem2 | 6 | 6 | 44 | 成功 |
| H55 | F1 | train_problem1 | 14 | 5 | 21 | 第 6 步 (fly-airplane a5 l10 l50) |
| H55 | F2 | train_problem4 | 9 | 4 | 21 | 第 5 步 (fly-airplane a4 l30 l20) |

## 證據與方法邊界

- 這是讀取既有 gold、reference trace 與狀態資訊的事後分析；不是聲稱 SBFL 已自行找出以上因果關係。
- 失敗依賴配對核對 grounded literal、實際增刪、後續持續缺失及受阻條件；沒有另外做反事實修復實驗。
- 每案完整執行順序、grounded fault 事件、coverage 群組與 assertion IDs 在 cases/Hxx.json。
- 不重新算分、不重播、不改 Domain、Problem、Plan、Trace 或原有 results。來源雜湊與保存檢查在 audit.json。
