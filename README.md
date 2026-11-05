# Lin et al.（AAAI-25）修復 Baseline：H30 Logistics

把 Lin, Grastien, Shome & Bercher, *Told You That Will Not Work: Optimal Corrections to Planning Domains Using Counter-Example Plans*（AAAI-25）的作者原版修復器，接到 30 個 Logistics 錯誤 Domain（H30）上，作為 PDDL Domain 修復的 baseline。

- 作者程式：<https://github.com/Songtuan-Lin/classical-domain-repairer>，固定 commit `080e33b22d3adc2bbc60b50d888d2b74bd9d8494`，**未修改**。
- 作者 repo 沒有授權條款，所以本 repo 不附它的程式碼，改由 `scripts/setup_repairer.py` 下載。
- 已執行結果全部附在 `results/`，不重跑也能直接看。

## 快速開始

需要 Python 3.10 和 git。

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # Linux/macOS: .venv/bin/python
.venv/Scripts/python scripts/setup_repairer.py             # 下載作者程式到 third_party/
.venv/Scripts/python -B scripts/build_inputs.py            # 產生 inputs/、heldout/，約 10 分鐘
.venv/Scripts/python -B scripts/run_lin.py --repeats 5 --workers 4   # 450 次，約 2 分鐘
PYTHONIOENCODING=utf-8 .venv/Scripts/python -B scripts/summarize.py
PYTHONIOENCODING=utf-8 .venv/Scripts/python -B scripts/assertion_table.py
PYTHONIOENCODING=utf-8 .venv/Scripts/python -B scripts/negative_cases_table.py
```

`--case H08` 可以只跑單一案例。

## 資料

`data/h30/` 是 30 個錯誤 Domain，每個只改了一條 Assertion：

- 原始 Domain：PDDLGym `manylogistics.pddl`（logistics-strips），commit `ab268e40`。
- 官方 50 個 Problem：train 0–39、test 40–49。
- 每題一條參考計畫：用 Fast Downward 在正確 Domain 上解出，並驗證過。
- 每個案例的錯誤內容列在 `data/h30/case_manifest.json`。
- `data/sbfl_summary.csv` 是同一批資料上的 SBFL（Ochiai）定位結果，只拿來並列參考。

正確 Domain（`data/h30/reference/domain.pddl`）只用在兩個地方：建立反例時判斷標籤，以及最後計分。修復器的輸入資料夾裡沒有正確 Domain，也沒有答案。

## 三種設定

| 設定 | 給修復器的正例 | 給修復器的反例 | 說明 |
|---|---|---|---|
| **P4** | SBFL 用的同 4 條參考計畫 | 無 | **主要 baseline**，和 SBFL 拿到的資訊相同 |
| P40 | train 0–39 全部 40 條參考計畫 | 無 | 正例較多 |
| P4N | 同 P4 | 從同樣 4 題造出的反例＋首次失敗位置 | 對應論文的「正例＋反例」設定；建立反例需要正確 Domain，屬於額外資訊 |

**保留集**是 Lin 看不到、只在修完後用來檢查的資料，包含 test 40–49 的 10 條參考計畫（正例），以及從這 10 題造出的反例。

**反例怎麼造**：取一條參考計畫的前段，這段在正確和錯誤 Domain 都能執行，然後接一個「錯誤 Domain 允許、正確 Domain 不允許」的動作，`.idx` 檔記錄這個動作的位置（從 0 起算）。每題最多造 2 條。

只有 4 個案例造得出反例：H08、H29、H38、H40。其餘 26 個錯誤都讓 Domain 變得更嚴格，不存在「錯誤 Domain 允許、正確 Domain 不允許」的計畫，所以這 26 案的 P4N 輸入和 P4 完全相同。

## 結果

每個案例跑 5 次，先在案例內平均，再跨案例平均。

| 設定 | F1 | 完全修對 | 保留集全部通過 | 改到正確的 Action |
|---|---|---|---|---|
| P4 | 0.509 | 41/150 | 0.847 | 0.907 |
| P40 | 0.487 | 41/150 | 0.867 | 0.880 |
| P4N | 0.564 | 56/150 | 0.980 | 0.887 |

只看有反例的 4 案（共 20 次）：

| 設定 | 修好的 Domain 和正確 Domain 完全相同 | 保留集全部通過 |
|---|---|---|
| P4 | 0/20 | 0/20 |
| P4N | 13/20 | 20/20 |

詳細結果：

- `results/results.md`：各設定的統計，以及逐案和 SBFL 排名的並列。
- `results/assertion_comparison.md`：每案的錯誤 Assertion 對照 Lin 的修改。
- `results/negative_cases.md`：4 個有反例案例的詳細表。
- `results/all_runs.csv`：每一次執行的紀錄。
- `results/runs/<設定>/<案例>/run_k/`：每次執行修好的 Domain、修改清單，以及驗證結果。

F1 的計算方式：每條 Assertion 要 Action、precondition／effect、正負號、Predicate、參數全部相同才算吻合，和正確 Domain 與錯誤 Domain 的實際差異比對。

## 使用時要注意

1. **作者程式不穩定。** 即使輸入相同、`PYTHONHASHSEED` 相同，每次結果仍可能不同。原因是 `fd/pddl/conditions.py` 的 `hash((self.__class__, self.parts))` 用到類別的記憶體位址，有多個修改數同樣最少的解時，選到哪一個就不固定。在 26 個 P4 與 P4N 輸入相同的案例中，130 組配對有 51 組結果不同。所以每個設定至少要跑 5 次，報告平均值。
2. **F1 會低估修對的程度。** 修復器有時會提出「新增一條已經存在的條件」，這條修改實際上沒有作用，卻會被算成多餘的修改。例如 H38 在 P4N 下修好的 Domain 5 次都和正確 Domain 相同，F1 卻只有 0.80。所以要同時看「修好的 Domain 是否和正確 Domain 相同」。
3. **能通過所有計畫，不代表修回原本的規則。** 常見情況是不刪掉多出來的 delete effect，而是再加一條相反的 add effect 把它抵消，例如 H32、H35、H48。
4. **反例只從參考計畫的前段造，** 沒有做更廣泛的搜尋。

## 檔案

```
data/h30/                 錯誤 Domain、正確 Domain、Problems、參考計畫、SBFL 用的 4 條計畫
data/sbfl_summary.csv     SBFL 定位結果（僅參考）
scripts/setup_repairer.py 下載作者程式並切到固定 commit
scripts/build_inputs.py   轉成作者格式、造反例、用正確 Domain 檢查標籤
scripts/run_worker.py     呼叫未修改的作者 main.py，擷取完整修改內容
scripts/benchmark_io.py   獨立重播、套用修改、計算與正確 Domain 的差異
scripts/run_lin.py        執行、計分、保留集驗證
scripts/summarize.py, assertion_table.py, negative_cases_table.py   產生報告
results/                  已執行的結果
```
