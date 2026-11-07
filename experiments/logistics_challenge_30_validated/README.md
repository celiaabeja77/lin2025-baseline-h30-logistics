# Logistics：30 個具備 2 成功＋2 失敗的 Domain

已從 H55 中剔除 25 個配額不足版本。保留原 H 編號；原資料夾不變。

- Domain：30 個；正式 native UP mutant Trace：120 條（60 成功／60 失敗）。
- 原版完整成功 Trace：10 條；官方 Problem／參考 FD 計畫：50 題／50 條。
- 本次僅匯出子集；規劃器／模擬器新增執行次數均為 0。
- 改動總表：evaluation/CASES_30.md；完整接續記憶：PROGRESS_MEMORY.md；剔除原因：evaluation/subset_selection.json。
- 原始 Domain、Problem、計畫與 Trace 位元組均保留；每版只改一條 Assertion 的證據承接原 H55 稽核。
- 套件含評估真值；盲測方法輸入需另行隔離。尚未執行 SBFL／LLM／Ontology。

保留：H08、H15、H21、H23、H25、H26、H28、H29、H32、H33、H34、H35、H36、H38、H40、H41、H42、H43、H44、H45、H46、H47、H48、H49、H50、H51、H52、H53、H54、H55。

剔除：H01、H02、H03、H04、H05、H06、H07、H09、H10、H11、H12、H13、H14、H16、H17、H18、H19、H20、H22、H24、H27、H30、H31、H37、H39。

可用任何 Python 3 執行 `python -B verify_package.py`，核對 hash、每版 2＋2、完整 Goal，以及保存的 grounded 狀態轉移；不需安裝 UP／FD。

