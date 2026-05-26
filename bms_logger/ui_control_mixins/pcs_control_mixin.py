from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

from ..pcs_client import PcsClient


class PcsControlMixin:
    def _execute_pcs_command(
        self,
        action_name: str,
        pcs_method_name: str,
        confirm: bool = True,
    ) -> None:
        device_name = self._get_selected_control_device()
        if not device_name:
            return

        if confirm:
            reply = QMessageBox.question(
                self,
                f"Confirm {action_name}",
                f"Execute PCS action '{action_name}' for current selected device context ({device_name})?",
            )
            if reply != QMessageBox.Yes:
                return

        self.control_state_label.setText("Executing")
        self.last_control_result_label.setText(f"PCS {action_name}")
        self.control_log(f"[CONTROL] {device_name}: PCS {action_name} started")

        if hasattr(self, "app_facade"):
            result = self.app_facade.execute_pcs_command_for_device(
                device_name=device_name,
                method_name=pcs_method_name,
                action_name=action_name,
                precheck=False,
            )
            if result.ok:
                self.control_state_label.setText("Done")
                self.last_control_result_label.setText(f"PCS {action_name} success")
                self.control_log(f"[CONTROL] {device_name}: {result.message}")
                QMessageBox.information(self, "Success", f"PCS {action_name} success")
            else:
                self.control_state_label.setText("Failed")
                self.last_control_result_label.setText(result.message)
                self.control_log(f"[CONTROL] {device_name}: PCS {action_name} failed - {result.message}")
                QMessageBox.warning(self, "Failed", result.message)
            return

        # Fallback path for tests/older app wiring: still use the same FleetDeviceWorker queue.
        pcs_name = self._get_selected_pcs_name()
        if not pcs_name:
            self.control_state_label.setText("Failed")
            self.last_control_result_label.setText("No PCS selected")
            QMessageBox.warning(self, "Failed", "No PCS selected")
            return
        def pcs_factory(name: str):
            return self.create_pcs_client_for_pcs_name(name)
        self.fleet_manager.start_pcs_command_workers([pcs_name], pcs_factory, interval_s=float(getattr(self, "heartbeat_interval", 1.0)))
        count = self.fleet_manager.enqueue_pcs_command([pcs_name], pcs_method_name, label=action_name)
        if count == 1:
            self.control_state_label.setText("Queued")
            self.last_control_result_label.setText(f"PCS {action_name} queued")
            self.control_log(f"[CONTROL] PCS {action_name} queued on FleetDeviceWorker: {pcs_name}")
        else:
            self.control_state_label.setText("Failed")
            self.last_control_result_label.setText("PCS command not queued")
            QMessageBox.warning(self, "Failed", f"PCS {action_name} not queued for {pcs_name}")
        return

    def handle_pcs_start(self) -> None:
        self._execute_pcs_command("Start", "start", confirm=True)

    def handle_pcs_stop(self) -> None:
        self._execute_pcs_command("Stop", "stop", confirm=True)

    def handle_pcs_reset_fault(self) -> None:
        self._execute_pcs_command("Reset Fault", "reset_fault", confirm=True)

    def handle_pcs_hv_on(self) -> None:
        self._execute_pcs_command("HV On", "hv_on", confirm=True)

    def handle_pcs_hv_off(self) -> None:
        self._execute_pcs_command("HV Off", "hv_off", confirm=True)

    def handle_pcs_close_dc_breaker(self) -> None:
        self._execute_pcs_command("Close DC Breaker", "close_dc_breaker", confirm=True)

    def handle_pcs_open_dc_breaker(self) -> None:
        self._execute_pcs_command("Open DC Breaker", "open_dc_breaker", confirm=True)

    def _format_pcs_breaker_state(self, pcs_client: PcsClient) -> str:
        try:
            if pcs_client.is_dc_breaker_open():
                return "Open"
            if pcs_client.is_dc_breaker_closed():
                return "Closed"
            return "Unknown"
        except Exception as exc:
            return f"Error: {exc}"

    def handle_refresh_pcs_status(self) -> None:
        device_name = self._get_selected_control_device()
        if not device_name:
            return

        if hasattr(self, "app_facade"):
            result = self.app_facade.read_pcs_status_for_device(device_name)
            if not result.ok:
                self.control_log(f"[CONTROL] {device_name}: {result.message}")
                QMessageBox.critical(self, "Error", result.message)
                return

            for key, value in dict(result.value or {}).items():
                if key in self.pcs_status_labels:
                    self.pcs_status_labels[key].setText(str(value))
            self.control_log(f"[CONTROL] {device_name}: PCS status refreshed")
            return

        pcs_client = self.create_pcs_client()
        try:
            if not pcs_client.connect():
                self.control_log(f"[CONTROL] {device_name}: PCS status refresh failed - connect failed")
                QMessageBox.critical(self, "Error", "PCS connect failed")
                return

            values = {}
            for key, func in [
                ("online", lambda: "Online" if pcs_client.is_online() else "Offline"),
                ("run_status", lambda: str(pcs_client.get_run_status())),
                ("fault_status", lambda: str(pcs_client.get_fault_status())),
                ("alarm_status", lambda: str(pcs_client.get_alarm_status())),
                ("dc_breaker", lambda: self._format_pcs_breaker_state(pcs_client)),
                ("active_power", lambda: str(pcs_client.get_active_power())),
                ("mode", lambda: str(pcs_client.get_mode())),
                ("remote_local", lambda: str(pcs_client.get_remote_local_status())),
            ]:
                try:
                    values[key] = func()
                except Exception as exc:
                    values[key] = f"Error: {exc}"

            for key, value in values.items():
                self.pcs_status_labels[key].setText(value)

            self.control_log(f"[CONTROL] {device_name}: PCS status refreshed")

        except Exception as exc:
            self.control_log(f"[CONTROL] {device_name}: PCS status refresh exception - {exc}")
            QMessageBox.critical(self, "Error", f"PCS status refresh exception:\n{exc}")

        finally:
            try:
                pcs_client.close()
            except Exception:
                pass


    def _pcs_live_point_names(self, pcs_client: PcsClient) -> list[str]:
        preferred = [
            "heartbeat",
            "set_active_power",
            "run_status",
            "remote_local_status",
            "ac_breaker_status",
            "dc_breaker_status",
            "active_power",
            "discharge_active_power",
            "reactive_power",
            "dc_voltage",
            "dc_current",
            "ac_voltage",
            "ac_current",
            "frequency",
            "power_factor",
            "fault_status",
            "alarm_status",
            "mode",
            "online_status",
        ]
        points = getattr(pcs_client, "points", {}) or {}
        names = [name for name in preferred if name in points]
        # Add remaining commonly useful non-command measurements without flooding the UI.
        for name in sorted(points.keys()):
            if name in names:
                continue
            cfg = points.get(name, {}) or {}
            access = str(cfg.get("access", "")).upper()
            if name.endswith("_cmd") or access in {"WO", "RW"}:
                continue
            if len(names) >= 40:
                break
            names.append(name)
        return names

    def _format_pcs_point_meaning(self, cfg: dict, raw: object) -> str:
        enum = cfg.get("enum") or cfg.get("values") or {}
        key = str(int(raw)) if isinstance(raw, (int, float)) and float(raw).is_integer() else str(raw)
        if isinstance(enum, dict) and key in enum:
            return str(enum[key])
        remark = cfg.get("remark") or cfg.get("description") or ""
        return str(remark)

    def handle_refresh_pcs_live_status(self) -> None:
        device_name = self._get_selected_control_device()
        if not device_name:
            return
        pcs_name = self._get_selected_pcs_name()
        pcs_client = self.create_pcs_client_for_pcs_name(pcs_name)
        rows = []
        try:
            if not pcs_client.connect():
                raise RuntimeError("PCS connect failed")
            for point_name in self._pcs_live_point_names(pcs_client):
                cfg = (pcs_client.points or {}).get(point_name, {}) or {}
                address = cfg.get("address", "")
                unit = cfg.get("unit", "")
                title = cfg.get("name_cn") or cfg.get("name_en") or cfg.get("description") or point_name
                try:
                    raw = pcs_client.read_raw(point_name)
                    try:
                        value = pcs_client.read_value(point_name)
                    except Exception:
                        value = raw
                    meaning = self._format_pcs_point_meaning(cfg, raw)
                    rows.append([point_name, address, title, raw, value, unit, meaning])
                except Exception as exc:
                    rows.append([point_name, address, title, "-", "-", unit, f"ERROR: {exc}"])
        except Exception as exc:
            self.control_log(f"[PCS] Live status refresh failed: {exc}")
            if hasattr(self, "pcs_live_table"):
                self.pcs_live_table.setRowCount(1)
                for col, value in enumerate(["ERROR", "-", "PCS live refresh", "-", "-", "", str(exc)]):
                    self.pcs_live_table.setItem(0, col, QTableWidgetItem(str(value)))
            return
        finally:
            try:
                pcs_client.close()
            except Exception:
                pass

        if not hasattr(self, "pcs_live_table"):
            return
        self.pcs_live_table.setRowCount(len(rows))
        for row_idx, row in enumerate(rows):
            for col, value in enumerate(row):
                text = self._pcs_fmt_cell_value(value) if hasattr(self, "_pcs_fmt_cell_value") else str(value)
                item = QTableWidgetItem(text)
                self.pcs_live_table.setItem(row_idx, col, item)
        self.control_log(f"[PCS] Live registers refreshed: pcs={pcs_name}, rows={len(rows)}")

    def handle_toggle_pcs_live_auto_refresh(self, checked: bool) -> None:
        if not hasattr(self, "pcs_live_timer"):
            return
        if checked:
            interval_ms = int(float(self.pcs_live_interval_spin.value()) * 1000) if hasattr(self, "pcs_live_interval_spin") else 2000
            self.pcs_live_timer.start(max(500, interval_ms))
            self.handle_refresh_pcs_live_status()
            self.control_log("[PCS] Live register auto refresh started")
        else:
            self.pcs_live_timer.stop()
            self.control_log("[PCS] Live register auto refresh stopped")

    def handle_start_pcs_heartbeat(self) -> None:
        # PCS heartbeat is kept behind the FleetDeviceWorker queue. It no longer
        # opens a direct connect/write/close loop from the UI timer.
        pcs_name = self._get_selected_pcs_name()
        if not pcs_name:
            QMessageBox.information(self, "PCS Heartbeat", "No PCS selected.")
            return

        def pcs_factory(name: str):
            return self.create_pcs_client_for_pcs_name(name)

        self.fleet_manager.start_pcs_heartbeats(
            [pcs_name],
            pcs_factory,
            interval_s=float(getattr(self, "heartbeat_interval", 1.0)),
            heartbeat_enabled=True,
        )
        if hasattr(self, "pcs_hb_state_label"):
            self.pcs_hb_state_label.setText(f"PCS HB queued: {pcs_name}")
        self.control_log(f"[PCS] Heartbeat worker started for {pcs_name} through FleetDeviceWorker queue")

    def handle_stop_pcs_heartbeat(self) -> None:
        pcs_name = self._get_selected_pcs_name()
        stopped = 0
        if pcs_name and hasattr(self.fleet_manager, "stop_named"):
            stopped = self.fleet_manager.stop_named("PCS", [pcs_name])
        elif hasattr(self, "pcs_heartbeat_timer"):
            self.pcs_heartbeat_timer.stop()
        if hasattr(self, "pcs_hb_state_label"):
            self.pcs_hb_state_label.setText("PCS HB: stopped")
        self.control_log(f"[PCS] Heartbeat stopped for {pcs_name or 'selected PCS'}; workers stopped={stopped}")

    def handle_pcs_heartbeat_tick(self) -> None:
        # Kept for old QTimer signal compatibility. Direct PCS heartbeat writes
        # are intentionally disabled; heartbeat is handled by FleetDeviceWorker.
        return


    def _set_selected_pcs_power_value(self, *, method_name: str, value: float, unit: str, label: str) -> None:
        device_name = self._get_selected_control_device()
        if not device_name:
            return
        pcs_name = self._get_selected_pcs_name()
        self.control_state_label.setText("Executing")
        self.last_control_result_label.setText(label)
        self.control_log(f"[CONTROL] {device_name}: {label} started for PCS={pcs_name}, value={value}{unit}")

        try:
            if hasattr(self, "app_facade"):
                if method_name == "set_active_power":
                    result = self.app_facade.set_pcs_power(pcs_name, value, precheck=False)
                elif method_name == "set_reactive_power" and hasattr(self.app_facade, "set_pcs_reactive_power"):
                    result = self.app_facade.set_pcs_reactive_power(pcs_name, value, precheck=False)
                else:
                    raise RuntimeError(f"Unsupported power method: {method_name}")
                if result.ok:
                    self.control_state_label.setText("Done")
                    self.last_control_result_label.setText(f"{label} success")
                    self.control_log(f"[CONTROL] {device_name}: {result.message}")
                    QMessageBox.information(self, "Success", f"{label} success")
                else:
                    self.control_state_label.setText("Failed")
                    self.last_control_result_label.setText(result.message)
                    self.control_log(f"[CONTROL] {device_name}: {label} failed - {result.message}")
                    QMessageBox.warning(self, "Failed", result.message)
                return

            def pcs_factory(name: str):
                return self.create_pcs_client_for_pcs_name(name)
            self.fleet_manager.start_pcs_command_workers([pcs_name], pcs_factory, interval_s=float(getattr(self, "heartbeat_interval", 1.0)))
            count = self.fleet_manager.enqueue_pcs_command([pcs_name], method_name, float(value), label=f"{label}={value}{unit}")
            if count != 1:
                raise RuntimeError(f"PCS command not queued for {pcs_name}")
            self.control_state_label.setText("Queued")
            self.last_control_result_label.setText(f"{label} queued")
            self.control_log(f"[CONTROL] {label} queued on FleetDeviceWorker, PCS={pcs_name}, value={value}{unit}")
            return
        except Exception as exc:
            self.control_state_label.setText("Failed")
            self.last_control_result_label.setText(str(exc))
            self.control_log(f"[CONTROL] {device_name}: {label} exception - {exc}")
            QMessageBox.critical(self, "Error", f"{label} exception:\n{exc}")

    def handle_set_pcs_active_power(self) -> None:
        value = float(self.pcs_active_power_spin.value()) if hasattr(self, "pcs_active_power_spin") else 0.0
        self._set_selected_pcs_power_value(method_name="set_active_power", value=value, unit="kW", label="Set Active Power")

    def handle_set_pcs_reactive_power(self) -> None:
        value = float(self.pcs_reactive_power_spin.value()) if hasattr(self, "pcs_reactive_power_spin") else 0.0
        self._set_selected_pcs_power_value(method_name="set_reactive_power", value=value, unit="kvar", label="Set Reactive Power")

    def apply_runtime_params(self) -> None:
        self.fake_mode = self.fake_mode_combo.currentText() == "Fake"
        if hasattr(self, "pcs_control_ui_combo"):
            self.pcs_control_ui_enabled = self.pcs_control_ui_combo.currentText() == "Enabled"
        self.heartbeat_interval = float(self.heartbeat_interval_spin.value())
        self.hv_step_timeout = float(self.hv_timeout_spin.value())
        self.hv_poll_interval = float(self.hv_poll_interval_spin.value())
        self.pcs_zero_power_threshold = float(self.pcs_zero_power_spin.value())
        self.charge_cutoff_max_cell_voltage = float(self.charge_cutoff_voltage_spin.value())
        self.discharge_cutoff_min_cell_voltage = float(self.discharge_cutoff_voltage_spin.value())
        self.cutoff_mode = self.cutoff_mode_combo.currentText()
        self.cutoff_trigger_confirm_count = int(self.cutoff_trigger_confirm_spin.value())
        self.cutoff_recover_confirm_count = int(self.cutoff_recover_confirm_spin.value())
        self.alarm_history_window_before_minutes = int(self.alarm_window_before_spin.value())
        self.alarm_history_window_after_minutes = int(self.alarm_window_after_spin.value())
        self.power_derating_enabled = self.derating_enabled_combo.currentText() == "Enabled"
        self.derating_margin_mv = float(self.derating_margin_spin.value())
        self.derating_power_kw = float(self.derating_power_spin.value())
        self.power_tracking_enabled = self.power_tracking_enabled_combo.currentText() == "Enabled"
        self.power_tracking_tolerance_kw = float(self.power_tracking_tolerance_spin.value())
        self.power_tracking_confirm_count = int(self.power_tracking_confirm_spin.value())
        self.power_tracking_auto_retry = self.power_retry_enabled_combo.currentText() == "Enabled"
        self.power_tracking_retry_interval = int(self.power_retry_interval_spin.value())
        self.power_tracking_max_retry = int(self.power_retry_max_spin.value())
        self.pcs_fault_protection_mode = self.pcs_fault_protection_combo.currentText()
        self.pcs_fault_protection_enabled = self.pcs_fault_protection_mode != "Disabled"
        self.pcs_fault_confirm_count = int(self.pcs_fault_confirm_spin.value())
        if hasattr(self, "worker_stagger_spin"):
            self.worker_start_stagger_seconds = float(self.worker_stagger_spin.value())
        if hasattr(self, "performance_mode_combo"):
            self.performance_mode_enabled = self.performance_mode_combo.currentText() == "Enabled"
        if hasattr(self, "ui_refresh_interval_spin"):
            self.ui_refresh_interval = float(self.ui_refresh_interval_spin.value())
        if hasattr(self, "curve_refresh_interval_spin"):
            self.curve_refresh_interval = float(self.curve_refresh_interval_spin.value())
        if hasattr(self, "status_refresh_interval_spin"):
            self.status_refresh_interval = float(self.status_refresh_interval_spin.value())
        if hasattr(self, "log_flush_interval_spin"):
            self.log_flush_interval_ms = int(self.log_flush_interval_spin.value())
            timer = getattr(self, "_log_flush_timer", None)
            if timer is not None:
                try:
                    timer.setInterval(int(self.log_flush_interval_ms))
                except Exception:
                    pass
        if hasattr(self, "fleet_status_timer"):
            try:
                self.fleet_status_timer.setInterval(int(max(1000, float(getattr(self, "status_refresh_interval", 5.0)) * 1000)))
            except Exception:
                pass

        self.control_log(
            "[PARAM] Runtime parameters applied: "
            f"mode={'Fake' if self.fake_mode else 'Real'}, "
            f"pcs_control_ui={'Enabled' if self.pcs_control_ui_enabled else 'Disabled'}, "
            f"heartbeat={self.heartbeat_interval}s, "
            f"hv_timeout={self.hv_step_timeout}s, "
            f"hv_poll={self.hv_poll_interval}s, "
            f"pcs_zero_power={self.pcs_zero_power_threshold}kW, "
            f"charge_cutoff={self.charge_cutoff_max_cell_voltage}mV, "
            f"discharge_cutoff={self.discharge_cutoff_min_cell_voltage}mV"
            f"cutoff_mode={self.cutoff_mode}, "
            f"cutoff_trigger_confirm={self.cutoff_trigger_confirm_count}, "
            f"cutoff_recover_confirm={self.cutoff_recover_confirm_count}, "
            f"alarm_window_before={self.alarm_history_window_before_minutes}min, "
            f"alarm_window_after={self.alarm_history_window_after_minutes}min, "
            f"worker_stagger={self.worker_start_stagger_seconds}s, "
            f"performance_mode={'Enabled' if getattr(self, 'performance_mode_enabled', True) else 'Disabled'}, "
            f"ui_refresh={self.ui_refresh_interval}s, "
            f"curve_refresh={getattr(self, 'curve_refresh_interval', 5.0)}s, "
            f"status_refresh={getattr(self, 'status_refresh_interval', 5.0)}s, "
        )
        self.save_runtime_config()

    # ------------------------------------------------------------------
    # Fleet-scale controls: 24 BMS + 48 PCS heartbeat and broadcast PCS commands
    # ------------------------------------------------------------------
    def _fleet_bms_names(self) -> list[str]:
        return [str(d.get("name", "")).strip() for d in getattr(self, "devices", []) if str(d.get("name", "")).strip()]

    def _fleet_pcs_names(self) -> list[str]:
        names: list[str] = []
        for name, cfg in getattr(self, "pcs_configs", {}).items():
            if not str(name).strip():
                continue
            if not isinstance(cfg, dict):
                continue
            if not bool(cfg.get("enabled", False)):
                continue
            if not str(cfg.get("host", "")).strip():
                continue
            points = cfg.get("points", {}) or {}
            if "heartbeat" not in points:
                continue
            names.append(str(name).strip())
        return names

    def handle_start_fleet_heartbeats(self) -> None:
        # Safer fleet heartbeat behavior: do not create separate BMS/PCS
        # reconnecting heartbeat workers. BMS heartbeat is queued only on
        # already-running BMS polling workers. PCS heartbeat remains disabled
        # by default because this site is currently using strategy/command
        # control without PCS heartbeat.
        bms_names = self._online_bms_worker_names() if hasattr(self, "_online_bms_worker_names") else []
        if not bms_names:
            QMessageBox.information(self, "Fleet Heartbeat", "No running BMS polling workers. Start BMS monitoring first.")
            return
        started = 0
        for name in bms_names:
            if self._start_bms_queue_heartbeat(name):
                started += 1
        if hasattr(self, "pcs_hb_state_label"):
            self.pcs_hb_state_label.setText(f"BMS HB queued: {started}")
        self.last_heartbeat_status = f"BMS HB queued: {started}"
        self.refresh_global_status_bar()
        self.control_log(f"[FLEET] Queued BMS heartbeat on existing polling workers: {started}/{len(bms_names)}. PCS heartbeat not started.")

    def handle_stop_fleet_heartbeats(self) -> None:
        stopped = 0
        if hasattr(self, "bms_queue_heartbeat_timers"):
            for name in list(self.bms_queue_heartbeat_timers.keys()):
                if self._stop_bms_queue_heartbeat(name):
                    stopped += 1
        if hasattr(self, "pcs_hb_state_label"):
            self.pcs_hb_state_label.setText("BMS HB: stopped")
        self.last_heartbeat_status = "Stopped"
        self.refresh_global_status_bar()
        self.control_log(f"[FLEET] BMS queued heartbeats stopped: {stopped}. Command workers were left running.")

    def _ensure_pcs_fleet_running(self) -> list[str]:
        pcs_names = self._fleet_pcs_names()
        if not pcs_names:
            return []
        def pcs_factory(name: str):
            return self.create_pcs_client_for_pcs_name(name)
        self.fleet_manager.start_pcs_heartbeats(pcs_names, pcs_factory, interval_s=float(getattr(self, "heartbeat_interval", 1.0)))
        return pcs_names

    def handle_fleet_pcs_start(self) -> None:
        pcs_names = self._ensure_pcs_fleet_running()
        count = self.fleet_manager.enqueue_pcs_command(pcs_names, "start", label="PCS start")
        self.control_log(f"[FLEET] Queued PCS start for {count}/{len(pcs_names)} PCS")

    def handle_fleet_pcs_stop(self) -> None:
        pcs_names = self._ensure_pcs_fleet_running()
        # Stop should be fast and broadcast through existing persistent clients.
        count = self.fleet_manager.enqueue_pcs_command(pcs_names, "stop", label="PCS stop")
        self.control_log(f"[FLEET] Queued PCS stop for {count}/{len(pcs_names)} PCS")

    def handle_fleet_set_active_power(self) -> None:
        pcs_names = self._ensure_pcs_fleet_running()
        value = float(self.pcs_active_power_spin.value()) if hasattr(self, "pcs_active_power_spin") else 0.0
        count = self.fleet_manager.enqueue_pcs_command(pcs_names, "set_active_power", value, label=f"set_active_power={value:.1f}kW")
        self.control_log(f"[FLEET] Queued set active power {value:.1f} kW for {count}/{len(pcs_names)} PCS")

    def handle_fleet_set_reactive_power(self) -> None:
        pcs_names = self._ensure_pcs_fleet_running()
        value = float(self.pcs_reactive_power_spin.value()) if hasattr(self, "pcs_reactive_power_spin") else 0.0
        count = self.fleet_manager.enqueue_pcs_command(pcs_names, "set_reactive_power", value, label=f"set_reactive_power={value:.1f}kvar")
        self.control_log(f"[FLEET] Queued set reactive power {value:.1f} kvar for {count}/{len(pcs_names)} PCS")

    def handle_fleet_status_summary(self) -> None:
        snapshots = self.fleet_manager.snapshots()
        total = len(snapshots)
        online = sum(1 for s in snapshots.values() if s.get("online"))
        errors = sum(1 for s in snapshots.values() if s.get("last_error"))
        bms = sum(1 for k in snapshots if k.startswith("BMS:"))
        pcs = sum(1 for k in snapshots if k.startswith("PCS:"))
        msg = f"Fleet workers={total}, online={online}, errors={errors}, BMS={bms}, PCS={pcs}"
        self.control_log(f"[FLEET] {msg}")
        if hasattr(self, "pcs_hb_state_label"):
            self.pcs_hb_state_label.setText(f"Fleet: {online}/{total} online")
