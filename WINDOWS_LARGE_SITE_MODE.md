# Windows Large Site Mode

This build adds a stronger Windows large-site path for 40-60 BMS/PCS projects.

## What changed

- BMS worker snapshots are no longer emitted to Qt UI one-by-one from every worker cycle.
  Workers coalesce the latest snapshot into an in-memory cache, and the Qt main
  thread drains that cache on a timer.
- BMS Modbus connect/read/write operations are limited by a global IO semaphore
  (`max_parallel_bms_io`, default 10). This acts like a lightweight worker pool
  without rewriting the whole runtime.
- Start All BMS uses a larger stagger interval by default, so Windows does not
  try to open dozens of TCP sessions at the same instant.
- Existing UI/curve/log/status throttling remains enabled.

## Recommended Windows settings for 40-60 devices

- Performance Mode: Enabled
- Large Site Mode: Enabled
- Max Parallel BMS IO: 8-12
- Start Stagger: 0.5s
- UI Refresh: 3-5s
- Curve Refresh: 5-10s
- Status Refresh: 5s
- Log Flush: 1000ms

## Notes

This is still the same desktop app architecture. It is much lighter on the Qt
main thread, but for very large sites the long-term architecture should move the
runtime into a background service and let the UI read snapshots only.
