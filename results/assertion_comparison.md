# 每案：錯誤 Assertion vs Lin 的修改（P4、P4N，各 5 個 seed）

判定：✅ 完全修回（修改＝正確答案）；🟡 部分命中（有改到正確答案的一部分）；❌ 沒命中。括號內是 5 次中出現幾次。

| 案例 | 正確修法（gold） | P4 修改 | P4N 修改 |
|---|---|---|---|
| H08 | 新增 DRIVE-TRUCK pre (at ?truck ?loc-from)；刪除 DRIVE-TRUCK pre (at ?truck ?loc-to) | 🟡 刪除 DRIVE-TRUCK pre (at ?truck ?loc-to)（5/5） | ✅ 新增 DRIVE-TRUCK pre (at ?truck ?loc-from)；刪除 DRIVE-TRUCK pre (at ?truck ?loc-to)（5/5） |
| H15 | 新增 LOAD-TRUCK pre (at ?obj ?loc)；刪除 LOAD-TRUCK pre (in ?obj ?truck) | 🟡 刪除 LOAD-TRUCK pre (in ?obj ?truck)（5/5） | 🟡 刪除 LOAD-TRUCK pre (in ?obj ?truck)（5/5） |
| H21 | 新增 LOAD-TRUCK eff (in ?obj ?truck) | ❌ 刪除 UNLOAD-TRUCK pre (in ?obj ?truck)（3/5）<br>✅ 新增 LOAD-TRUCK eff (in ?obj ?truck)（2/5） | ❌ 刪除 UNLOAD-TRUCK pre (in ?obj ?truck)（3/5）<br>✅ 新增 LOAD-TRUCK eff (in ?obj ?truck)（2/5） |
| H23 | 新增 DRIVE-TRUCK eff (at ?truck ?loc-to) | ✅ 新增 DRIVE-TRUCK eff (at ?truck ?loc-to)（5/5） | ✅ 新增 DRIVE-TRUCK eff (at ?truck ?loc-to)（5/5） |
| H25 | 新增 UNLOAD-TRUCK eff (at ?obj ?loc) | ✅ 新增 UNLOAD-TRUCK eff (at ?obj ?loc)（5/5） | ✅ 新增 UNLOAD-TRUCK eff (at ?obj ?loc)（5/5） |
| H26 | 新增 LOAD-TRUCK eff (in ?obj ?truck)；刪除 LOAD-TRUCK eff (in ?truck ?obj) | 🟡 新增 LOAD-TRUCK eff (in ?obj ?truck)（5/5） | ❌ 刪除 UNLOAD-TRUCK pre (in ?obj ?truck)（4/5）<br>🟡 新增 LOAD-TRUCK eff (in ?obj ?truck)（1/5） |
| H28 | 新增 UNLOAD-TRUCK pre (in ?obj ?truck)；刪除 UNLOAD-TRUCK pre (in ?truck ?obj) | 🟡 刪除 UNLOAD-TRUCK pre (in ?truck ?obj)（4/5）<br>❌ 新增 LOAD-TRUCK eff (in ?truck ?obj)（1/5） | 🟡 刪除 UNLOAD-TRUCK pre (in ?truck ?obj)（4/5）<br>❌ 新增 LOAD-TRUCK eff (in ?truck ?obj)（1/5） |
| H29 | 新增 LOAD-TRUCK eff (not (at ?obj ?loc))；刪除 LOAD-TRUCK eff (not (at ?truck ?loc)) | 🟡 刪除 LOAD-TRUCK eff (not (at ?truck ?loc))（4/5）<br>❌ 新增 LOAD-TRUCK eff (at ?truck ?loc)（1/5） | 🟡 新增 LOAD-TRUCK eff (not (at ?obj ?loc))；新增 LOAD-TRUCK eff (at ?truck ?loc)（3/5）<br>✅ 新增 LOAD-TRUCK eff (not (at ?obj ?loc))；刪除 LOAD-TRUCK eff (not (at ?truck ?loc))（2/5） |
| H32 | 刪除 DRIVE-TRUCK eff (not (in-city ?loc-from ?city)) | ❌ 新增 DRIVE-TRUCK eff (in-city ?loc-from ?city)（3/5）<br>✅ 刪除 DRIVE-TRUCK eff (not (in-city ?loc-from ?city))（2/5） | ✅ 刪除 DRIVE-TRUCK eff (not (in-city ?loc-from ?city))（3/5）<br>❌ 新增 DRIVE-TRUCK eff (in-city ?loc-from ?city)（2/5） |
| H33 | 刪除 DRIVE-TRUCK eff (not (in-city ?loc-to ?city)) | ✅ 刪除 DRIVE-TRUCK eff (not (in-city ?loc-to ?city))（4/5）<br>❌ 新增 DRIVE-TRUCK eff (in-city ?loc-to ?city)（1/5） | ✅ 刪除 DRIVE-TRUCK eff (not (in-city ?loc-to ?city))（4/5）<br>❌ 新增 DRIVE-TRUCK eff (in-city ?loc-to ?city)（1/5） |
| H34 | 刪除 FLY-AIRPLANE eff (not (airport ?loc-to)) | ❌ 新增 FLY-AIRPLANE eff (airport ?loc-to)（3/5）<br>✅ 刪除 FLY-AIRPLANE eff (not (airport ?loc-to))（2/5） | ✅ 刪除 FLY-AIRPLANE eff (not (airport ?loc-to))（3/5）<br>❌ 新增 FLY-AIRPLANE eff (airport ?loc-to)（2/5） |
| H35 | 刪除 LOAD-TRUCK eff (not (obj ?obj)) | ❌ 新增 LOAD-TRUCK eff (obj ?obj)（4/5）<br>✅ 刪除 LOAD-TRUCK eff (not (obj ?obj))（1/5） | ✅ 刪除 LOAD-TRUCK eff (not (obj ?obj))（4/5）<br>❌ 新增 LOAD-TRUCK eff (obj ?obj)（1/5） |
| H36 | 刪除 DRIVE-TRUCK eff (not (truck ?truck)) | ❌ 新增 DRIVE-TRUCK eff (truck ?truck)（4/5）<br>✅ 刪除 DRIVE-TRUCK eff (not (truck ?truck))（1/5） | ❌ 新增 DRIVE-TRUCK eff (truck ?truck)（4/5）<br>✅ 刪除 DRIVE-TRUCK eff (not (truck ?truck))（1/5） |
| H38 | 新增 DRIVE-TRUCK eff (at ?truck ?loc-to)；刪除 DRIVE-TRUCK eff (at ?truck ?loc-from) | 🟡 新增 DRIVE-TRUCK eff (at ?truck ?loc-to)（5/5） | 🟡 新增 DRIVE-TRUCK eff (not (at ?truck ?loc-from))；新增 DRIVE-TRUCK eff (at ?truck ?loc-to)；刪除 DRIVE-TRUCK eff (at ?truck ?loc-from)（5/5） |
| H40 | 新增 LOAD-TRUCK eff (in ?obj ?truck)；刪除 LOAD-TRUCK eff (at ?obj ?loc) | 🟡 新增 LOAD-TRUCK eff (in ?obj ?truck)（5/5） | 🟡 新增 LOAD-TRUCK eff (not (at ?obj ?loc))；刪除 LOAD-TRUCK eff (at ?obj ?loc)；刪除 UNLOAD-TRUCK pre (in ?obj ?truck)（4/5）<br>🟡 新增 LOAD-TRUCK eff (in ?obj ?truck)；新增 LOAD-TRUCK eff (not (at ?obj ?loc))；刪除 LOAD-TRUCK eff (at ?obj ?loc)（1/5） |
| H41 | 新增 LOAD-TRUCK pre (location ?loc)；刪除 LOAD-TRUCK pre (airport ?loc) | ❌ 新增 DRIVE-TRUCK eff (airport ?loc-to)（3/5）<br>🟡 刪除 LOAD-TRUCK pre (airport ?loc)（2/5） | ❌ 新增 DRIVE-TRUCK eff (airport ?loc-to)（3/5）<br>🟡 刪除 LOAD-TRUCK pre (airport ?loc)（2/5） |
| H42 | 新增 UNLOAD-TRUCK pre (location ?loc)；刪除 UNLOAD-TRUCK pre (airport ?loc) | ❌ 新增 DRIVE-TRUCK eff (airport ?loc-to)（3/5）<br>🟡 刪除 UNLOAD-TRUCK pre (airport ?loc)（2/5） | ❌ 新增 DRIVE-TRUCK eff (airport ?loc-to)（4/5）<br>🟡 刪除 UNLOAD-TRUCK pre (airport ?loc)（1/5） |
| H43 | 新增 DRIVE-TRUCK pre (location ?loc-from)；刪除 DRIVE-TRUCK pre (airport ?loc-from) | 🟡 刪除 DRIVE-TRUCK pre (airport ?loc-from)（5/5） | 🟡 刪除 DRIVE-TRUCK pre (airport ?loc-from)（5/5） |
| H44 | 新增 LOAD-TRUCK eff (in ?obj ?truck)；刪除 LOAD-TRUCK eff (at ?obj ?truck) | ❌ 刪除 UNLOAD-TRUCK pre (in ?obj ?truck)（4/5）<br>🟡 新增 LOAD-TRUCK eff (in ?obj ?truck)（1/5） | 🟡 新增 LOAD-TRUCK eff (in ?obj ?truck)（3/5）<br>❌ 刪除 UNLOAD-TRUCK pre (in ?obj ?truck)（2/5） |
| H45 | 新增 UNLOAD-TRUCK eff (at ?obj ?loc)；刪除 UNLOAD-TRUCK eff (in ?obj ?loc) | 🟡 新增 UNLOAD-TRUCK eff (at ?obj ?loc)（5/5） | 🟡 新增 UNLOAD-TRUCK eff (at ?obj ?loc)（5/5） |
| H46 | 新增 DRIVE-TRUCK eff (at ?truck ?loc-to)；刪除 DRIVE-TRUCK eff (in ?truck ?loc-to) | 🟡 新增 DRIVE-TRUCK eff (at ?truck ?loc-to)（5/5） | 🟡 新增 DRIVE-TRUCK eff (at ?truck ?loc-to)（5/5） |
| H47 | 刪除 LOAD-TRUCK eff (not (truck ?truck)) | ❌ 新增 LOAD-TRUCK eff (truck ?truck)（3/5）<br>✅ 刪除 LOAD-TRUCK eff (not (truck ?truck))（2/5） | ❌ 新增 LOAD-TRUCK eff (truck ?truck)（3/5）<br>✅ 刪除 LOAD-TRUCK eff (not (truck ?truck))（2/5） |
| H48 | 刪除 UNLOAD-TRUCK eff (not (obj ?obj)) | ❌ 新增 UNLOAD-TRUCK eff (obj ?obj)（5/5） | ✅ 刪除 UNLOAD-TRUCK eff (not (obj ?obj))（3/5）<br>❌ 新增 UNLOAD-TRUCK eff (obj ?obj)（2/5） |
| H49 | 刪除 UNLOAD-AIRPLANE eff (not (airplane ?airplane)) | ❌ 新增 UNLOAD-AIRPLANE eff (airplane ?airplane)（4/5）<br>✅ 刪除 UNLOAD-AIRPLANE eff (not (airplane ?airplane))（1/5） | ❌ 新增 UNLOAD-AIRPLANE eff (airplane ?airplane)（3/5）<br>✅ 刪除 UNLOAD-AIRPLANE eff (not (airplane ?airplane))（2/5） |
| H50 | 刪除 LOAD-TRUCK eff (not (at ?truck ?loc)) | ❌ 新增 LOAD-TRUCK eff (at ?truck ?loc)（3/5）<br>✅ 刪除 LOAD-TRUCK eff (not (at ?truck ?loc))（2/5） | ✅ 刪除 LOAD-TRUCK eff (not (at ?truck ?loc))（3/5）<br>❌ 新增 LOAD-TRUCK eff (at ?truck ?loc)（2/5） |
| H51 | 刪除 UNLOAD-TRUCK eff (not (at ?truck ?loc)) | ✅ 刪除 UNLOAD-TRUCK eff (not (at ?truck ?loc))（4/5）<br>❌ 新增 UNLOAD-TRUCK eff (at ?truck ?loc)（1/5） | ✅ 刪除 UNLOAD-TRUCK eff (not (at ?truck ?loc))（3/5）<br>❌ 新增 UNLOAD-TRUCK eff (at ?truck ?loc)（2/5） |
| H52 | 刪除 UNLOAD-AIRPLANE eff (not (at ?airplane ?loc)) | ✅ 刪除 UNLOAD-AIRPLANE eff (not (at ?airplane ?loc))（4/5）<br>❌ 新增 UNLOAD-AIRPLANE eff (at ?airplane ?loc)（1/5） | ✅ 刪除 UNLOAD-AIRPLANE eff (not (at ?airplane ?loc))（3/5）<br>❌ 新增 UNLOAD-AIRPLANE eff (at ?airplane ?loc)（2/5） |
| H53 | 刪除 LOAD-TRUCK eff (not (airport ?loc)) | ❌ 新增 LOAD-TRUCK eff (airport ?loc)（4/5）<br>✅ 刪除 LOAD-TRUCK eff (not (airport ?loc))（1/5） | ❌ 新增 LOAD-TRUCK eff (airport ?loc)（3/5）<br>✅ 刪除 LOAD-TRUCK eff (not (airport ?loc))（2/5） |
| H54 | 刪除 UNLOAD-TRUCK eff (not (airport ?loc)) | ✅ 刪除 UNLOAD-TRUCK eff (not (airport ?loc))（3/5）<br>❌ 新增 UNLOAD-TRUCK eff (airport ?loc)（2/5） | ❌ 新增 UNLOAD-TRUCK eff (airport ?loc)（3/5）<br>✅ 刪除 UNLOAD-TRUCK eff (not (airport ?loc))（2/5） |
| H55 | 刪除 UNLOAD-AIRPLANE eff (not (airport ?loc)) | ❌ 新增 UNLOAD-AIRPLANE eff (airport ?loc)（3/5）<br>✅ 刪除 UNLOAD-AIRPLANE eff (not (airport ?loc))（2/5） | ❌ 新增 UNLOAD-AIRPLANE eff (airport ?loc)（3/5）<br>✅ 刪除 UNLOAD-AIRPLANE eff (not (airport ?loc))（2/5） |

## 合計（30 案 × 5 次 = 150 次）

| 設定 | ✅ 完全修回 | 🟡 部分命中 | ❌ 沒命中 |
|---|---|---|---|
| P4 | 41 | 53 | 56 |
| P4N | 56 | 44 | 50 |
