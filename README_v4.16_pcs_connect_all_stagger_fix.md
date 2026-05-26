# v4.16 PCS Connect All Stagger Fix

This build reduces Windows UI freezes when connecting many PCS devices.

Changes:
- `Connect all PCS` now starts PCS polling workers in a staggered sequence.
- PCS Modbus connect/read/write operations are protected by a global PCS IO semaphore.
- PCS all-connect uses the existing `Start Stagger` setting, defaulting to 0.5s.
- PCS all-connect refreshes the PCS table once after queueing instead of repainting heavily per device.
- Existing BMS Large Site Mode / Performance Mode behavior is unchanged.

Recommended settings for 40-60 device sites:
- Performance Mode: Enabled
- Large Site Mode: Enabled
- Start Stagger: 0.5s
- Max Parallel BMS IO: 8-12
