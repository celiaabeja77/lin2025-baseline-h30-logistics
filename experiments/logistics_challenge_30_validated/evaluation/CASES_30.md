# 合格 30 個 Domain：Assertion 改動表

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

