# Windows Performance Mode

This build adds a lightweight Windows Performance Mode for long-running site tests.

What changes when enabled:

- BMS/PCS Modbus sampling/control logic is unchanged.
- UI table repaint is throttled.
- Curves refresh independently and more slowly than communication polling.
- Control Log and normal Log are flushed in batches instead of one QTextEdit append per line.
- Log panels keep fewer visible lines in performance mode while file logging remains active.
- Fleet/status refresh interval is configurable and defaults to a slower Windows-friendly value.
- Dynamic curve point option lists are not rebuilt on every curve refresh.

Settings are available in Settings -> Scheduler / Performance:

- Performance Mode
- UI Refresh
- Curve Refresh
- Status Refresh
- Log Flush

Recommended Windows field values:

- Performance Mode: Enabled
- UI Refresh: 3 s
- Curve Refresh: 5 s
- Status Refresh: 5 s
- Log Flush: 1000 ms

These settings reduce UI workload only. Strategy timeout decisions still use live BMS snapshots and are not delayed by UI throttling.
