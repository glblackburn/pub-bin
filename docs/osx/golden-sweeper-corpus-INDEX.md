# Golden sweeper capture corpus (local)

Raw PNGs, sidecar JSONL, and legacy ``*-annotated.png`` live under [`screenshots/golden-sweeper-captures/`](screenshots/golden-sweeper-captures/) (directory is **gitignored** — present only on machines that ran the sweeper).

**Labeling:** None of these frames were operator-flagged as “golden visible.” Legacy sidecars often contained **dozens** of lines from gold-tinted UI (scroll strips, buff rows). **Detector v2** keeps compact, blob-shaped HSV regions and caps output (see ``detect_magic_cookie_hits`` in ``osx/cookie_clicker_golden_sweeper.py``). The **assessment** column is a **heuristic** for triage, not ground truth. For **human-labeled** ground truth and session triage notes (building-column false positives, **`max_hits`** saturation, JSON **`bbox`** vs **`x`/`y`** coordinate spaces), see **[plan-018 — Field observations](plans/plan-018-magic-cookie-detection-remediation.md)** (section *Field observations*) and **`tools/eval_magic_cookie_labels.py`**.

Regenerate this file and ``*-v2-annotated.png`` after new captures:

```bash
./osx/.venv/bin/python3 tools/build_golden_sweeper_corpus_index.py
```

| # | stem | legacy JSON lines | v2 hits | assessment | raw | json |
|---|------|-------------------|---------|------------|-----|------|
| 1 | `golden-sweeper-20260503-001148-298003-f00000` | 93 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001148-298003-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001148-298003-f00000.json) |
| 2 | `golden-sweeper-20260503-001150-001222-f00001` | 81 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001150-001222-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001150-001222-f00001.json) |
| 3 | `golden-sweeper-20260503-001246-574019-f00000` | 79 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001246-574019-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001246-574019-f00000.json) |
| 4 | `golden-sweeper-20260503-001248-248976-f00001` | 79 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001248-248976-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001248-248976-f00001.json) |
| 5 | `golden-sweeper-20260503-001517-423128-f00000` | 118 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001517-423128-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001517-423128-f00000.json) |
| 6 | `golden-sweeper-20260503-001519-181198-f00001` | 117 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001519-181198-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001519-181198-f00001.json) |
| 7 | `golden-sweeper-20260503-001549-062528-f00000` | 111 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001549-062528-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001549-062528-f00000.json) |
| 8 | `golden-sweeper-20260503-001550-837397-f00001` | 103 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001550-837397-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001550-837397-f00001.json) |
| 9 | `golden-sweeper-20260503-001620-935280-f00000` | 108 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001620-935280-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001620-935280-f00000.json) |
| 10 | `golden-sweeper-20260503-001622-724493-f00001` | 99 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001622-724493-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001622-724493-f00001.json) |
| 11 | `golden-sweeper-20260503-001652-679842-f00000` | 120 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001652-679842-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001652-679842-f00000.json) |
| 12 | `golden-sweeper-20260503-001654-481331-f00001` | 116 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001654-481331-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001654-481331-f00001.json) |
| 13 | `golden-sweeper-20260503-001725-226958-f00000` | 83 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001725-226958-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001725-226958-f00000.json) |
| 14 | `golden-sweeper-20260503-001726-982723-f00001` | 80 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001726-982723-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-001726-982723-f00001.json) |
| 15 | `golden-sweeper-20260503-002148-556651-f00000` | 98 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002148-556651-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002148-556651-f00000.json) |
| 16 | `golden-sweeper-20260503-002150-402204-f00001` | 96 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002150-402204-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002150-402204-f00001.json) |
| 17 | `golden-sweeper-20260503-002220-303770-f00000` | 94 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002220-303770-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002220-303770-f00000.json) |
| 18 | `golden-sweeper-20260503-002221-987189-f00001` | 96 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002221-987189-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002221-987189-f00001.json) |
| 19 | `golden-sweeper-20260503-002251-835187-f00000` | 95 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002251-835187-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002251-835187-f00000.json) |
| 20 | `golden-sweeper-20260503-002253-589971-f00001` | 98 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002253-589971-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002253-589971-f00001.json) |
| 21 | `golden-sweeper-20260503-002323-365201-f00000` | 93 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002323-365201-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002323-365201-f00000.json) |
| 22 | `golden-sweeper-20260503-002325-096293-f00001` | 97 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002325-096293-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002325-096293-f00001.json) |
| 23 | `golden-sweeper-20260503-002354-723431-f00000` | 94 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002354-723431-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002354-723431-f00000.json) |
| 24 | `golden-sweeper-20260503-002356-488661-f00001` | 92 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002356-488661-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002356-488661-f00001.json) |
| 25 | `golden-sweeper-20260503-002427-056134-f00000` | 103 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002427-056134-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002427-056134-f00000.json) |
| 26 | `golden-sweeper-20260503-002428-806355-f00001` | 94 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002428-806355-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002428-806355-f00001.json) |
| 27 | `golden-sweeper-20260503-002458-892834-f00000` | 99 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002458-892834-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002458-892834-f00000.json) |
| 28 | `golden-sweeper-20260503-002500-705588-f00001` | 92 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002500-705588-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002500-705588-f00001.json) |
| 29 | `golden-sweeper-20260503-002531-910891-f00000` | 96 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002531-910891-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002531-910891-f00000.json) |
| 30 | `golden-sweeper-20260503-002533-692636-f00001` | 95 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002533-692636-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002533-692636-f00001.json) |
| 31 | `golden-sweeper-20260503-002604-777976-f00000` | 98 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002604-777976-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002604-777976-f00000.json) |
| 32 | `golden-sweeper-20260503-002706-119795-f00000` | 101 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002706-119795-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002706-119795-f00000.json) |
| 33 | `golden-sweeper-20260503-002739-319685-f00000` | 105 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002739-319685-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002739-319685-f00000.json) |
| 34 | `golden-sweeper-20260503-002812-145002-f00000` | 104 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002812-145002-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002812-145002-f00000.json) |
| 35 | `golden-sweeper-20260503-002814-036355-f00001` | 90 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002814-036355-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002814-036355-f00001.json) |
| 36 | `golden-sweeper-20260503-002843-832303-f00000` | 98 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002843-832303-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002843-832303-f00000.json) |
| 37 | `golden-sweeper-20260503-002845-536292-f00001` | 94 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002845-536292-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002845-536292-f00001.json) |
| 38 | `golden-sweeper-20260503-002915-500216-f00000` | 99 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002915-500216-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002915-500216-f00000.json) |
| 39 | `golden-sweeper-20260503-002917-266259-f00001` | 98 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002917-266259-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002917-266259-f00001.json) |
| 40 | `golden-sweeper-20260503-002947-512735-f00000` | 93 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002947-512735-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002947-512735-f00000.json) |
| 41 | `golden-sweeper-20260503-002949-259596-f00001` | 95 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002949-259596-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-002949-259596-f00001.json) |
| 42 | `golden-sweeper-20260503-003019-284808-f00000` | 90 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003019-284808-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003019-284808-f00000.json) |
| 43 | `golden-sweeper-20260503-003021-150635-f00001` | 92 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003021-150635-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003021-150635-f00001.json) |
| 44 | `golden-sweeper-20260503-003052-209891-f00000` | 112 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003052-209891-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003052-209891-f00000.json) |
| 45 | `golden-sweeper-20260503-003054-116739-f00001` | 97 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003054-116739-f00001.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003054-116739-f00001.json) |
| 46 | `golden-sweeper-20260503-003513-813593-f00000` | 99 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003513-813593-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003513-813593-f00000.json) |
| 47 | `golden-sweeper-20260503-003545-817510-f00000` | 102 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003545-817510-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003545-817510-f00000.json) |
| 48 | `golden-sweeper-20260503-003617-900783-f00000` | 98 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003617-900783-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003617-900783-f00000.json) |
| 49 | `golden-sweeper-20260503-003649-711125-f00000` | 98 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003649-711125-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003649-711125-f00000.json) |
| 50 | `golden-sweeper-20260503-003721-952068-f00000` | 98 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003721-952068-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003721-952068-f00000.json) |
| 51 | `golden-sweeper-20260503-003754-383689-f00000` | 101 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003754-383689-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003754-383689-f00000.json) |
| 52 | `golden-sweeper-20260503-003826-483686-f00000` | 96 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003826-483686-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-003826-483686-f00000.json) |
| 53 | `golden-sweeper-20260503-004253-990457-f00000` | 100 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-004253-990457-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-004253-990457-f00000.json) |
| 54 | `golden-sweeper-20260503-004744-807611-f00000` | 101 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-004744-807611-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-004744-807611-f00000.json) |
| 55 | `golden-sweeper-20260503-005220-055024-f00000` | 94 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-005220-055024-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-005220-055024-f00000.json) |
| 56 | `golden-sweeper-20260503-010451-420243-f00000` | 101 | 6 | No verified golden; legacy run was UI-heavy false positives. | [raw](screenshots/golden-sweeper-captures/golden-sweeper-20260503-010451-420243-f00000.png) | [json](screenshots/golden-sweeper-captures/golden-sweeper-20260503-010451-420243-f00000.json) |

## v2 annotated previews

### `golden-sweeper-20260503-001148-298003-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001148-298003-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001148-298003-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-001150-001222-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001150-001222-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001150-001222-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-001246-574019-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001246-574019-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001246-574019-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-001248-248976-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001248-248976-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001248-248976-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-001517-423128-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001517-423128-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001517-423128-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-001519-181198-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001519-181198-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001519-181198-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-001549-062528-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001549-062528-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001549-062528-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-001550-837397-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001550-837397-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001550-837397-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-001620-935280-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001620-935280-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001620-935280-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-001622-724493-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001622-724493-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001622-724493-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-001652-679842-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001652-679842-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001652-679842-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-001654-481331-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001654-481331-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001654-481331-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-001725-226958-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001725-226958-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001725-226958-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-001726-982723-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-001726-982723-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-001726-982723-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002148-556651-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002148-556651-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002148-556651-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002150-402204-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002150-402204-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002150-402204-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002220-303770-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002220-303770-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002220-303770-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002221-987189-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002221-987189-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002221-987189-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002251-835187-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002251-835187-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002251-835187-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002253-589971-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002253-589971-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002253-589971-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002323-365201-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002323-365201-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002323-365201-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002325-096293-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002325-096293-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002325-096293-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002354-723431-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002354-723431-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002354-723431-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002356-488661-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002356-488661-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002356-488661-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002427-056134-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002427-056134-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002427-056134-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002428-806355-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002428-806355-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002428-806355-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002458-892834-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002458-892834-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002458-892834-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002500-705588-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002500-705588-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002500-705588-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002531-910891-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002531-910891-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002531-910891-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002533-692636-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002533-692636-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002533-692636-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002604-777976-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002604-777976-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002604-777976-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002706-119795-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002706-119795-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002706-119795-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002739-319685-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002739-319685-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002739-319685-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002812-145002-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002812-145002-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002812-145002-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002814-036355-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002814-036355-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002814-036355-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002843-832303-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002843-832303-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002843-832303-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002845-536292-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002845-536292-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002845-536292-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002915-500216-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002915-500216-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002915-500216-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002917-266259-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002917-266259-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002917-266259-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-002947-512735-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002947-512735-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002947-512735-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-002949-259596-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-002949-259596-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-002949-259596-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-003019-284808-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003019-284808-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003019-284808-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-003021-150635-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003021-150635-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003021-150635-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-003052-209891-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003052-209891-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003052-209891-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-003054-116739-f00001`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003054-116739-f00001-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003054-116739-f00001 v2 annotated" /></p>

### `golden-sweeper-20260503-003513-813593-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003513-813593-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003513-813593-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-003545-817510-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003545-817510-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003545-817510-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-003617-900783-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003617-900783-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003617-900783-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-003649-711125-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003649-711125-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003649-711125-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-003721-952068-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003721-952068-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003721-952068-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-003754-383689-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003754-383689-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003754-383689-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-003826-483686-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-003826-483686-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-003826-483686-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-004253-990457-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-004253-990457-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-004253-990457-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-004744-807611-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-004744-807611-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-004744-807611-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-005220-055024-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-005220-055024-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-005220-055024-f00000 v2 annotated" /></p>

### `golden-sweeper-20260503-010451-420243-f00000`

<p><img src="screenshots/golden-sweeper-captures/golden-sweeper-20260503-010451-420243-f00000-v2-annotated.png" width="560" alt="golden-sweeper-20260503-010451-420243-f00000 v2 annotated" /></p>

