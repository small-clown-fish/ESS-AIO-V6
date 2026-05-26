# ESS-AIO v4.17 Real UI Model/Snapshot Diff Fix

This package is based on `ESS-AIO_v4.16_runtime_settings_apply_pcs_link_fix.zip`.

Implemented and verified changes:

- Added `bms_logger/ui_table_models.py` with `SnapshotTableModel`.
- Changed Overview device/cluster tables from `QTableWidget` rebuilds to `QTableView + QAbstractTableModel`.
- Overview refresh now uses snapshot diff (`set_rows`) instead of `clear/rebuild` every refresh.
- Overview refresh is skipped while the Overview page is hidden.
- Device table live updates are wrapped in `setUpdatesEnabled(False/True)` and still update only changed cells.
- Global status labels now update only when text changes.
- Full Python compile check passed with `python3 -m compileall -q bms_logger`.

Notes:

- Main BMS Devices table remains `QTableWidget` for compatibility with existing row selection/start/stop logic.
- This is a real low-risk Model/View conversion for high-frequency overview tables, not a full UI rewrite.
