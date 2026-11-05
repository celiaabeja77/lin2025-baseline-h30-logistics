# Lin et al. (AAAI-25) repairer on H30 Logistics — results

Run-level means are averaged within each case first, then across cases. Exact = the repair set equals the gold assertion edits exactly (literal and arguments). Held-out = every held-out constraint passes on test problems 40–49 (10 positive plans, plus any oracle negatives).

## All 30 cases

| Setting | ok/runs | Timeout | P | R | F1 | Exact | Held-out pass | Touches gold action | Mean repairs | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| P4 | 150/150 | 0 | 0.627 | 0.450 | 0.509 | 0.273 | 0.847 | 0.907 | 1.00 | 0.43 |
| P40 | 150/150 | 0 | 0.593 | 0.433 | 0.487 | 0.273 | 0.867 | 0.880 | 1.00 | 0.50 |
| P4N | 150/150 | 0 | 0.626 | 0.540 | 0.564 | 0.373 | 0.980 | 0.887 | 1.20 | 0.49 |

## The 4 cases with negative plans (H08, H29, H38, H40)

| Setting | ok/runs | Timeout | P | R | F1 | Exact | Held-out pass | Touches gold action | Mean repairs | Seconds |
|---|---|---|---|---|---|---|---|---|---|---|
| P4 | 20/20 | 0 | 0.950 | 0.475 | 0.633 | 0.000 | 0.000 | 1.000 | 1.00 | 0.43 |
| P40 | 20/20 | 0 | 0.700 | 0.350 | 0.467 | 0.000 | 0.000 | 0.850 | 1.00 | 0.50 |
| P4N | 20/20 | 0 | 0.692 | 0.825 | 0.745 | 0.350 | 1.000 | 1.000 | 2.50 | 0.90 |

## Per case (Exact and Held-out are counts out of 5 seeds; SBFL columns come from logistics_assertion_sbfl, for context only)

| Case | Group | Fault | SBFL gold rank (best–worst) | P4 F1 | P4 exact | P4 held-out | P40 F1 | P40 exact | P40 held-out | Dev negatives | P4N F1 | P4N exact | P4N held-out | P4N repairs (seed 1) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| H08 | G2 | `DRIVE-TRUCK :precondition: (at ?truck ?loc-from) → (at ?truck ?loc-to)` | 1–7 | 0.667 | 0 | 0 | 0.667 | 0 | 0 | 4 | 1.000 | 5 | 5 | `drive-truck,at,precPos,-1; drive-truck,at,precPos,1` |
| H15 | G3 | `LOAD-TRUCK :precondition: (at ?obj ?loc) → (in ?obj ?truck)` | 1–5 | 0.667 | 0 | 5 | 0.667 | 0 | 5 | 0 | 0.667 | 0 | 5 | `load-truck,in,precPos,-1` |
| H21 | G5 | `LOAD-TRUCK :effect: (in ?obj ?truck) → ∅` | not in candidates | 0.400 | 2 | 5 | 0.200 | 1 | 5 | 0 | 0.400 | 2 | 5 | `unload-truck,in,precPos,-1` |
| H23 | G5 | `DRIVE-TRUCK :effect: (at ?truck ?loc-to) → ∅` | not in candidates | 1.000 | 5 | 5 | 1.000 | 5 | 5 | 0 | 1.000 | 5 | 5 | `drive-truck,at,effPos,1` |
| H25 | G5 | `UNLOAD-TRUCK :effect: (at ?obj ?loc) → ∅` | not in candidates | 1.000 | 5 | 5 | 1.000 | 5 | 5 | 0 | 1.000 | 5 | 5 | `unload-truck,at,effPos,1` |
| H26 | G6 | `LOAD-TRUCK :effect: (in ?obj ?truck) → (in ?truck ?obj)` | 1–21 | 0.667 | 0 | 5 | 0.133 | 0 | 5 | 0 | 0.133 | 0 | 5 | `unload-truck,in,precPos,-1` |
| H28 | G6 | `UNLOAD-TRUCK :precondition: (in ?obj ?truck) → (in ?truck ?obj)` | 1–21 | 0.533 | 0 | 5 | 0.533 | 0 | 5 | 0 | 0.533 | 0 | 5 | `load-truck,in,effPos,1` |
| H29 | G7 | `LOAD-TRUCK :effect: (not (at ?obj ?loc)) → (not (at ?truck ?loc))` | 1–14 | 0.533 | 0 | 0 | 0.267 | 0 | 0 | 2 | 0.700 | 2 | 5 | `load-truck,at,effNeg,1; load-truck,at,effPos,1` |
| H32 | G8 | `DRIVE-TRUCK :effect: ∅ → (not (in-city ?loc-from ?city))` | 1–17 | 0.400 | 2 | 5 | 0.200 | 1 | 5 | 0 | 0.600 | 3 | 5 | `drive-truck,in-city,effPos,1` |
| H33 | G8 | `DRIVE-TRUCK :effect: ∅ → (not (in-city ?loc-to ?city))` | 1–17 | 0.800 | 4 | 5 | 0.400 | 2 | 5 | 0 | 0.800 | 4 | 5 | `drive-truck,in-city,effNeg,-1` |
| H34 | G8 | `FLY-AIRPLANE :effect: ∅ → (not (AIRPORT ?loc-to))` | 1–21 | 0.400 | 2 | 5 | 0.400 | 2 | 5 | 0 | 0.600 | 3 | 5 | `fly-airplane,airport,effNeg,-1` |
| H35 | G9 | `LOAD-TRUCK :effect: ∅ → (not (OBJ ?obj))` | 1–22 | 0.200 | 1 | 5 | 0.600 | 3 | 5 | 0 | 0.800 | 4 | 5 | `load-truck,obj,effNeg,-1` |
| H36 | G9 | `DRIVE-TRUCK :effect: ∅ → (not (TRUCK ?truck))` | 1–15 | 0.200 | 1 | 5 | 0.600 | 3 | 5 | 0 | 0.200 | 1 | 5 | `drive-truck,truck,effPos,1` |
| H38 | G10 | `DRIVE-TRUCK :effect: (at ?truck ?loc-to) → (at ?truck ?loc-from)` | 1–14 | 0.667 | 0 | 0 | 0.667 | 0 | 0 | 4 | 0.800 | 0 | 5 | `drive-truck,at,effNeg,1; drive-truck,at,effPos,-1; drive-truck,at,effPos,1` |
| H40 | G10 | `LOAD-TRUCK :effect: (in ?obj ?truck) → (at ?obj ?loc)` | 1–21 | 0.667 | 0 | 0 | 0.267 | 0 | 0 | 4 | 0.480 | 0 | 5 | `load-truck,at,effNeg,1; load-truck,at,effPos,-1; unload-truck,in,precPos,-1` |
| H41 | G11 | `LOAD-TRUCK :precondition: (LOCATION ?loc) → (AIRPORT ?loc)` | 1–14 | 0.267 | 0 | 2 | 0.667 | 0 | 5 | 0 | 0.267 | 0 | 2 | `drive-truck,airport,effPos,1` |
| H42 | G11 | `UNLOAD-TRUCK :precondition: (LOCATION ?loc) → (AIRPORT ?loc)` | 1–21 | 0.267 | 0 | 5 | 0.400 | 0 | 5 | 0 | 0.133 | 0 | 5 | `drive-truck,airport,effPos,1` |
| H43 | G11 | `DRIVE-TRUCK :precondition: (LOCATION ?loc-from) → (AIRPORT ?loc-from)` | 1–7 | 0.667 | 0 | 5 | 0.667 | 0 | 5 | 0 | 0.667 | 0 | 5 | `drive-truck,airport,precPos,-1` |
| H44 | G12 | `LOAD-TRUCK :effect: (in ?obj ?truck) → (at ?obj ?truck)` | 1–21 | 0.133 | 0 | 5 | 0.133 | 0 | 5 | 0 | 0.400 | 0 | 5 | `load-truck,in,effPos,1` |
| H45 | G12 | `UNLOAD-TRUCK :effect: (at ?obj ?loc) → (in ?obj ?loc)` | 1–23 | 0.667 | 0 | 5 | 0.667 | 0 | 5 | 0 | 0.667 | 0 | 5 | `unload-truck,at,effPos,1` |
| H46 | G12 | `DRIVE-TRUCK :effect: (at ?truck ?loc-to) → (in ?truck ?loc-to)` | 1–14 | 0.667 | 0 | 5 | 0.667 | 0 | 5 | 0 | 0.667 | 0 | 5 | `drive-truck,at,effPos,1` |
| H47 | G13 | `LOAD-TRUCK :effect: ∅ → (not (TRUCK ?truck))` | 1–15 | 0.400 | 2 | 5 | 0.600 | 3 | 5 | 0 | 0.400 | 2 | 5 | `load-truck,truck,effNeg,-1` |
| H48 | G13 | `UNLOAD-TRUCK :effect: ∅ → (not (OBJ ?obj))` | 1–29 | 0.000 | 0 | 5 | 0.800 | 4 | 5 | 0 | 0.600 | 3 | 5 | `unload-truck,obj,effNeg,-1` |
| H49 | G13 | `UNLOAD-AIRPLANE :effect: ∅ → (not (AIRPLANE ?airplane))` | 1–21 | 0.200 | 1 | 5 | 0.600 | 3 | 5 | 0 | 0.400 | 2 | 5 | `unload-airplane,airplane,effPos,1` |
| H50 | G14 | `LOAD-TRUCK :effect: ∅ → (not (at ?truck ?loc))` | 1–15 | 0.400 | 2 | 5 | 0.400 | 2 | 5 | 0 | 0.600 | 3 | 5 | `load-truck,at,effNeg,-1` |
| H51 | G14 | `UNLOAD-TRUCK :effect: ∅ → (not (at ?truck ?loc))` | 1–44 | 0.800 | 4 | 5 | 0.200 | 1 | 5 | 0 | 0.600 | 3 | 5 | `unload-truck,at,effPos,1` |
| H52 | G14 | `UNLOAD-AIRPLANE :effect: ∅ → (not (at ?airplane ?loc))` | 1–21 | 0.800 | 4 | 5 | 0.600 | 3 | 5 | 0 | 0.600 | 3 | 5 | `unload-airplane,at,effNeg,-1` |
| H53 | G15 | `LOAD-TRUCK :effect: ∅ → (not (AIRPORT ?loc))` | 1–35 | 0.200 | 1 | 5 | 0.600 | 3 | 5 | 0 | 0.400 | 2 | 5 | `load-truck,airport,effPos,1` |
| H54 | G15 | `UNLOAD-TRUCK :effect: ∅ → (not (AIRPORT ?loc))` | 1–35 | 0.600 | 3 | 5 | 0.000 | 0 | 5 | 0 | 0.400 | 2 | 5 | `unload-truck,airport,effPos,1` |
| H55 | G15 | `UNLOAD-AIRPLANE :effect: ∅ → (not (AIRPORT ?loc))` | 1–21 | 0.400 | 2 | 5 | 0.000 | 0 | 5 | 0 | 0.400 | 2 | 5 | `unload-airplane,airport,effPos,1` |
