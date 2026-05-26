# v4.15 State Change / Offline Cooldown / Quiet Control Log Fix

This build is based on `ESS-AIO_v4.15_hb_timer_stop_log_loop_fix.zip` and adds the missing quiet-log/state-change stabilization pass.

## Confirmed/added

- Control Log UI is quiet by default: heartbeat success, queue OK, idle/ready, and per-PCS strategy OK lines are hidden from the QTextEdit view.
- Warning/error/fault/cutoff/timeout/offline/recovered/cooldown/start/stop state lines remain visible.
- Repeated noisy fault lines are normalized and rate-limited before entering the UI.
- Existing FleetDeviceWorker offline cooldown remains active: repeated connect failures enter long cooldown instead of reconnect storms.
- Existing task/status refresh throttling remains active.

## Notes

- This does not change BMS/PCS communication or strategy power dispatch logic.
- Logs still rotate/write asynchronously through the existing operation log path.
