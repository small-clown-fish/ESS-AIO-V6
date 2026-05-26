# Windows deep performance optimization

This build keeps the existing communication and strategy behavior, and adds two lower-risk performance optimizations:

1. CSV/alarm recorder batching
   - Async recorder drains queued CSV writes in bounded batches.
   - This reduces Python thread wakeups and Windows disk/Defender pressure when many devices write at the same sampling tick.

2. Visible-page-only heavy UI refresh
   - Live data still updates `latest_snapshots` on every sample for Strategy.
   - Heavy repaint work for Curves, Details, Driver Points and Alarms is skipped when those pages are not visible.
   - Device table refresh is throttled more aggressively when the Devices page is not visible.

This should reduce Windows “Not Responding” symptoms without changing power dispatch, BMS polling, PCS profile logic, or Cluster Strategy calculations.
