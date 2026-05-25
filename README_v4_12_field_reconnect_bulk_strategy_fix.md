# ESS-AIO v4.12 field reconnect / bulk BMS / strategy cutoff fix

This package focuses on field stability for Windows EXE operation.

Key changes:
- BMS polling reconnect is capped. After repeated connect failures, the worker marks the device offline and stops instead of reconnecting forever.
- Fleet command-only workers no longer connect while idle. They connect only when a real command, periodic command, or heartbeat is due.
- Fleet reconnect failures enter a long cooldown after repeated failures to avoid reconnect storms.
- Single BMS heartbeat no longer opens a separate reconnecting connection. It requires BMS monitoring/polling to be running and queues heartbeat writes on the polling worker.
- Added one-click commands for online BMS only:
  - Clear Fault All Online
  - Power On All Online
  - Stay All Online
- Single Clear Fault and EMS cmd prefer the BMS polling worker command queue when available.
- Cluster Strategy: when charge/discharge cutoff voltage is reached, PCS power is set to 0 and the strategy stops instead of continuing to run at 0.
- Updated `.github/workflows/build-windows.yml` to the latest light Windows build workflow.
- Fixed the previous `cmd_value is not defined` issue in `handle_start_heartbeat`.

Operational notes:
- Start BMS monitoring before enabling BMS heartbeat or 0x038B cycle.
- Bulk BMS commands intentionally only target online/running BMS polling workers and do not create new connections to offline devices.
- If a disconnected device should be retried, restart monitoring for that device manually.
