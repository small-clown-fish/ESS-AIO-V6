# Windows Deep Performance Optimization 2

This build adds another low-risk performance pass on top of the visible-page/CSV optimization build.

## Changes

- Throttled repeated FleetDeviceWorker status emissions so idle command workers do not repaint task/status tables every 200 ms.
- Scheduler/Tasks table now repaints only when visible and at the configured status refresh interval.
- Task status table rebuild uses `setUpdatesEnabled(False)` during batch updates.
- Dynamic driver-point buffers are downsampled for hidden devices in Performance Mode, while the currently visible curve/driver page keeps full resolution.
- UI log queues are capped before flush, preventing memory growth during log storms.
- Cluster strategy per-PCS success spam is suppressed from the UI Control Log; state changes/errors remain visible.

Communication, strategy calculation, profile mapping, and power dispatch logic are unchanged.
