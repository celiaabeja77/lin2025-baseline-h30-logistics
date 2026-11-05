# 4 個有反例的案例：P4 vs P4N 詳細結果

＋＝新增、－＝刪除。「修回正確 Domain」直接比對修好的 Domain 和正確 Domain 的全部 Assertion。保留集＝test problem 40–49：10 條正例＋該案的保留反例。每個設定跑 5 次。

## 案例背景

| 案例 | 錯在哪 | 原本 → 錯誤寫法 | 為什麼變寬鬆 | 正確修法 | 給 Lin 的反例數 | 保留集反例數 |
|---|---|---|---|---|---|---|
| H08 | DRIVE-TRUCK :precondition | `(at ?truck ?loc-from)` → `(at ?truck ?loc-to)` | 卡車不在出發地也能開走 | ＋ DRIVE-TRUCK pre (at ?truck ?loc-from)<br>－ DRIVE-TRUCK pre (at ?truck ?loc-to) | 4 | 14 |
| H29 | LOAD-TRUCK :effect | `(not (at ?obj ?loc))` → `(not (at ?truck ?loc))` | 貨物裝車後還在地上，可重複裝貨 | ＋ LOAD-TRUCK eff (not (at ?obj ?loc))<br>－ LOAD-TRUCK eff (not (at ?truck ?loc)) | 2 | 2 |
| H38 | DRIVE-TRUCK :effect | `(at ?truck ?loc-to)` → `(at ?truck ?loc-from)` | 開車後卡車留在原地，可在原地繼續動作 | ＋ DRIVE-TRUCK eff (at ?truck ?loc-to)<br>－ DRIVE-TRUCK eff (at ?truck ?loc-from) | 4 | 14 |
| H40 | LOAD-TRUCK :effect | `(in ?obj ?truck)` → `(at ?obj ?loc)` | 貨物裝車後還在地上，可重複裝貨 | ＋ LOAD-TRUCK eff (in ?obj ?truck)<br>－ LOAD-TRUCK eff (at ?obj ?loc) | 4 | 9 |

## 結果

| 案例 | 設定 | Lin 的修改（5 次中幾次） | 修回正確 Domain | 保留集正例通過 | 保留集反例通過 | 保留集全過 | 平均修改數 | F1 | 平均秒數 |
|---|---|---|---|---|---|---|---|---|---|
| H08 | P4 | － DRIVE-TRUCK pre (at ?truck ?loc-to)（5/5） | 0/5 | 50/50 | 0/70 | 0/5 | 1.0 | 0.67 | 0.41 |
| H08 | P4N | ＋ DRIVE-TRUCK pre (at ?truck ?loc-from)<br>－ DRIVE-TRUCK pre (at ?truck ?loc-to)（5/5） | 5/5 | 50/50 | 70/70 | 5/5 | 2.0 | 1.00 | 1.47 |
| H29 | P4 | － LOAD-TRUCK eff (not (at ?truck ?loc))（4/5）<br><br>＋ LOAD-TRUCK eff (at ?truck ?loc)（1/5） | 0/5 | 50/50 | 0/10 | 0/5 | 1.0 | 0.53 | 0.45 |
| H29 | P4N | ＋ LOAD-TRUCK eff (at ?truck ?loc)<br>＋ LOAD-TRUCK eff (not (at ?obj ?loc))（3/5）<br><br>＋ LOAD-TRUCK eff (not (at ?obj ?loc))<br>－ LOAD-TRUCK eff (not (at ?truck ?loc))（2/5） | 2/5 | 50/50 | 10/10 | 5/5 | 2.0 | 0.70 | 1.04 |
| H38 | P4 | ＋ DRIVE-TRUCK eff (at ?truck ?loc-to)（5/5） | 0/5 | 50/50 | 0/70 | 0/5 | 1.0 | 0.67 | 0.44 |
| H38 | P4N | ＋ DRIVE-TRUCK eff (not (at ?truck ?loc-from))<br>＋ DRIVE-TRUCK eff (at ?truck ?loc-to)<br>－ DRIVE-TRUCK eff (at ?truck ?loc-from)（5/5） | 5/5 | 50/50 | 70/70 | 5/5 | 3.0 | 0.80 | 0.56 |
| H40 | P4 | ＋ LOAD-TRUCK eff (in ?obj ?truck)（5/5） | 0/5 | 50/50 | 0/45 | 0/5 | 1.0 | 0.67 | 0.44 |
| H40 | P4N | ＋ LOAD-TRUCK eff (not (at ?obj ?loc))<br>－ LOAD-TRUCK eff (at ?obj ?loc)<br>－ UNLOAD-TRUCK pre (in ?obj ?truck)（4/5）<br><br>＋ LOAD-TRUCK eff (in ?obj ?truck)<br>＋ LOAD-TRUCK eff (not (at ?obj ?loc))<br>－ LOAD-TRUCK eff (at ?obj ?loc)（1/5） | 1/5 | 50/50 | 45/45 | 5/5 | 3.0 | 0.48 | 0.52 |

## 合計（4 案 × 5 次 = 20 次）

| 設定 | 修回正確 Domain | 保留集全過 |
|---|---|---|
| P4 | 0/20 | 0/20 |
| P4N | 13/20 | 20/20 |

保留集正例／反例欄是 5 次加總（例如 50 條正例＝10 條 × 5 次）。
