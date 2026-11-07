# Logistics：剔除缺額版本後的 30 個 Domain

整理日期：2026-10-22（Asia/Taipei）。來源：H55 既有資料；新資料夾 `experiments/logistics_challenge_30_validated`。

## 本次變更

從 H01–H55 中排除沒有取得 2 條完整成功＋2 條失敗 Trace 的 25 個版本，形成 30 個版本的新子集。原 H55、H40 與原始證據均未修改或刪除。保留原 H 編號，不重新編成 H01–H30。

## 保留與剔除

保留 30 個：H08、H15、H21、H23、H25、H26、H28、H29、H32、H33、H34、H35、H36、H38、H40、H41、H42、H43、H44、H45、H46、H47、H48、H49、H50、H51、H52、H53、H54、H55。

剔除 25 個：H01、H02、H03、H04、H05、H06、H07、H09、H10、H11、H12、H13、H14、H16、H17、H18、H19、H20、H22、H24、H27、H30、H31、H37、H39。

剔除是針對這批固定官方參考計畫的成功／失敗配額，不代表每一版在所有替代計畫下都無法失敗或成功。原因明列於 `evaluation/subset_selection.json`。

## Trace 與驗證定義

官方 50 個 Problem 與原版 Domain 不變。計畫均已先由 Fast Downward 在原版解出並通過驗證，再以完全相同的計畫重播到錯誤 Domain。

成功必須同時滿足：(1) 全部動作執行完畢；(2) 原 Problem 的全部 Goal 達成。任一步被拒絕，或全部動作執行後仍缺 Goal，都算失敗。原版已失敗的非法計畫不作為參考計畫。

本包共 30 個 Domain、120 條既有 native UP mutant Trace，60 成功＋60 失敗，每版 2＋2。另保留 10 條原版完整成功 Trace，與 mutant 分開計數。

只複製既有結果並核對位元組／SHA-256，沒有重新注入、規劃、模擬或修改 Problem／Goal。候選資料保留 30×50＝1500 組既有符號篩選；不可誤稱 1500 次 native UP 模擬。

## 來源與工具

Repository：tomsilver/pddlgym；commit `ab268e40ac7b2de8d060ec0c48c27003d1a62d62`；Domain `pddlgym/pddl/manylogistics.pddl`（logistics-strips）。

官方 Problems：train/problem0–39、test/problem40–49。原版 SHA-256 `1e53d7715105db947a91bdaf55c0027bccc3d037f3771cf9b5422b1fd6c58715`。

既有執行工具：Unified Planning 1.3.0 的 SequentialSimulator＋sequential_plan_validator；Fast Downward 計畫由 up-fast-downward 0.5.2 取得。未執行 PDDLGym Gym runtime。

30 版各只改一條 Assertion，對應原 H55 的 AST 與官方／UP Parser 檢查；本次以原樣副本與 SHA-256 承接該證據，未重跑 Parser。H38、H40 的既有 Add／Delete overlap 仍在，UP 的 add-after-delete 行為保留，其他規劃器相容性未另測。

## 保留案例的實際改動

| H 編號 | 類別 | 動作 | 部位 | 原 Assertion → 新 Assertion | Trace |
|---|---|---|---|---|---|
| H08 | G2 行程端點關係錯綁或漏綁 | DRIVE-TRUCK | :precondition[5] | `(at ?truck ?loc-from)` → `(at ?truck ?loc-to)` | 2 成功＋2 失敗 |
| H15 | G3 貨物來源與承載身分混淆 | LOAD-TRUCK | :precondition[5] | `(at ?obj ?loc)` → `(in ?obj ?truck)` | 2 成功＋2 失敗 |
| H21 | G5 新狀態漏建立，後段才受阻 | LOAD-TRUCK | :effect[2] | `(in ?obj ?truck)` → 刪除 | 2 成功＋2 失敗 |
| H23 | G5 新狀態漏建立，後段才受阻 | DRIVE-TRUCK | :effect[2] | `(at ?truck ?loc-to)` → 刪除 | 2 成功＋2 失敗 |
| H25 | G5 新狀態漏建立，後段才受阻 | UNLOAD-TRUCK | :effect[2] | `(at ?obj ?loc)` → 刪除 | 2 成功＋2 失敗 |
| H26 | G6 關係方向寫反 | LOAD-TRUCK | :effect[2] | `(in ?obj ?truck)` → `(in ?truck ?obj)` | 2 成功＋2 失敗 |
| H28 | G6 關係方向寫反 | UNLOAD-TRUCK | :precondition[5] | `(in ?obj ?truck)` → `(in ?truck ?obj)` | 2 成功＋2 失敗 |
| H29 | G7 Effect 改到錯誤對象 | LOAD-TRUCK | :effect[1] | `(not (at ?obj ?loc))` → `(not (at ?truck ?loc))` | 2 成功＋2 失敗 |
| H32 | G8 動作破壞共享地圖 | DRIVE-TRUCK | :effect[3] | 新增 → `(not (in-city ?loc-from ?city))` | 2 成功＋2 失敗 |
| H33 | G8 動作破壞共享地圖 | DRIVE-TRUCK | :effect[3] | 新增 → `(not (in-city ?loc-to ?city))` | 2 成功＋2 失敗 |
| H34 | G8 動作破壞共享地圖 | FLY-AIRPLANE | :effect[3] | 新增 → `(not (AIRPORT ?loc-to))` | 2 成功＋2 失敗 |
| H35 | G9 動作破壞物件身分 | LOAD-TRUCK | :effect[3] | 新增 → `(not (OBJ ?obj))` | 2 成功＋2 失敗 |
| H36 | G9 動作破壞物件身分 | DRIVE-TRUCK | :effect[3] | 新增 → `(not (TRUCK ?truck))` | 2 成功＋2 失敗 |
| H38 | G10 新狀態錯寫回原處 | DRIVE-TRUCK | :effect[2] | `(at ?truck ?loc-to)` → `(at ?truck ?loc-from)` | 2 成功＋2 失敗 |
| H40 | G10 新狀態錯寫回原處 | LOAD-TRUCK | :effect[2] | `(in ?obj ?truck)` → `(at ?obj ?loc)` | 2 成功＋2 失敗 |
| H41 | G11 一般地點被錯限縮為機場 | LOAD-TRUCK | :precondition[3] | `(LOCATION ?loc)` → `(AIRPORT ?loc)` | 2 成功＋2 失敗 |
| H42 | G11 一般地點被錯限縮為機場 | UNLOAD-TRUCK | :precondition[3] | `(LOCATION ?loc)` → `(AIRPORT ?loc)` | 2 成功＋2 失敗 |
| H43 | G11 一般地點被錯限縮為機場 | DRIVE-TRUCK | :precondition[2] | `(LOCATION ?loc-from)` → `(AIRPORT ?loc-from)` | 2 成功＋2 失敗 |
| H44 | G12 地面位置與承載關係寫錯 | LOAD-TRUCK | :effect[2] | `(in ?obj ?truck)` → `(at ?obj ?truck)` | 2 成功＋2 失敗 |
| H45 | G12 地面位置與承載關係寫錯 | UNLOAD-TRUCK | :effect[2] | `(at ?obj ?loc)` → `(in ?obj ?loc)` | 2 成功＋2 失敗 |
| H46 | G12 地面位置與承載關係寫錯 | DRIVE-TRUCK | :effect[2] | `(at ?truck ?loc-to)` → `(in ?truck ?loc-to)` | 2 成功＋2 失敗 |
| H47 | G13 裝卸誤刪參與者身分 | LOAD-TRUCK | :effect[3] | 新增 → `(not (TRUCK ?truck))` | 2 成功＋2 失敗 |
| H48 | G13 裝卸誤刪參與者身分 | UNLOAD-TRUCK | :effect[3] | 新增 → `(not (OBJ ?obj))` | 2 成功＋2 失敗 |
| H49 | G13 裝卸誤刪參與者身分 | UNLOAD-AIRPLANE | :effect[3] | 新增 → `(not (AIRPLANE ?airplane))` | 2 成功＋2 失敗 |
| H50 | G14 裝卸誤刪運具所在位置 | LOAD-TRUCK | :effect[3] | 新增 → `(not (at ?truck ?loc))` | 2 成功＋2 失敗 |
| H51 | G14 裝卸誤刪運具所在位置 | UNLOAD-TRUCK | :effect[3] | 新增 → `(not (at ?truck ?loc))` | 2 成功＋2 失敗 |
| H52 | G14 裝卸誤刪運具所在位置 | UNLOAD-AIRPLANE | :effect[3] | 新增 → `(not (at ?airplane ?loc))` | 2 成功＋2 失敗 |
| H53 | G15 裝卸破壞共用機場資格 | LOAD-TRUCK | :effect[3] | 新增 → `(not (AIRPORT ?loc))` | 2 成功＋2 失敗 |
| H54 | G15 裝卸破壞共用機場資格 | UNLOAD-TRUCK | :effect[3] | 新增 → `(not (AIRPORT ?loc))` | 2 成功＋2 失敗 |
| H55 | G15 裝卸破壞共用機場資格 | UNLOAD-AIRPLANE | :effect[3] | 新增 → `(not (AIRPORT ?loc))` | 2 成功＋2 失敗 |

## 檔案與後續邊界

- `Hxx/domain.pddl`：僅包含上述 30 個版本。
- `traces/official_2success_2failure/by_domain/Hxx/`：每版 S1、S2、F1、F2 與相同計畫；共 120 條 Trace。
- `reference/`、`traces/.../inputs/`、`plans/`、`planner/`：官方來源與完整 50 題參考計畫保留。
- `evaluation/case_manifest.json`、`group_manifest.json`、`CASES_30.md`：只列保留的 30 版。原分組編號保留，過濾後各組數量可不同。
- `evaluation/subset_selection.json`：25 個剔除原因；`copied_source_files.json`：來源與副本 hash。
- `evaluation/single_assertion_recheck.json`：保留 30 版的先前單一 Assertion 檢查證據。
- `SHA256SUMS.json`、`verify_package.py`、`evaluation/package_audit.json`：套件完整性與保存的 grounded Trace 重播核對；不重新呼叫規劃器或模擬器。

每步仍含 Domain／Problem、動作與參數、前後狀態、grounded Precondition 真假、未滿足條件、Add／Delete Effects、實際狀態差與 attempted／executed；另記錄最終全部 Goal。

本包含故障真值與原版比較，屬建置／評估資料，不能整包作為待測 LLM 的盲測輸入。SBFL、LLM、Ontology 及修復實驗均未執行，困難度與 Ontology 增益未測量。

