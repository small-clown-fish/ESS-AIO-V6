# ESS-AIO v4.17 UI performance follow-up

This build adds additional Windows UI load reduction on top of the previous Qt deleted-widget guard build.

## Added

- Overview model emits smaller changed ranges instead of repainting the whole table.
- Main navigation page changes trigger one catch-up refresh for the newly visible heavy page only.
- Details and Alarms pages do not repaint while hidden.
- Alarms table updates are diff-based and wrapped with `setUpdatesEnabled(False/True)`.
- Driver Points page is hidden-page guarded, signature-deduplicated, and capped to 300 rows by default in Performance Mode unless the operator filters/searches.
- PCS Live Registers auto refresh is hidden-page guarded and re-entry protected.
- Global status no longer forces Overview refresh every timer tick; it respects the status refresh interval.

## Notes

Communication, strategy, power dispatch, and PCS/BMS command paths are unchanged.
