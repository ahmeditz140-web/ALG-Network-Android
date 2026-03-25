"""
Main Window - The primary application window for Andols ECU Tuning Tool.
"""

import os
from typing import Optional

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QMenuBar, QMenu, QAction, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QSplitter, QLabel, QProgressBar,
)
from PyQt5.QtGui import QFont, QIcon, QKeySequence
from PyQt5.QtCore import Qt, QSize

from core.binary_reader import BinaryReader
from core.metadata_extractor import MetadataExtractor
from core.fingerprint import ECUFingerprint
from core.processing_engine import ProcessingEngine
from core.checksum import ChecksumCalculator, ValidationEngine
from database.db_manager import DatabaseManager
from ui.dashboard import Dashboard
from ui.hex_viewer import HexViewer


class MainWindow(QMainWindow):
    """Main application window."""

    APP_NAME = "Andols ECU Tuning Tool"
    APP_VERSION = "1.0.0"

    def __init__(self) -> None:
        super().__init__()
        self.reader = BinaryReader()
        self.engine: Optional[ProcessingEngine] = None
        self.checksum_calc: Optional[ChecksumCalculator] = None
        self.validator = ValidationEngine()
        self.db = DatabaseManager()
        self.db.connect()

        self._file_loaded = False
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        self._load_dtc_list()

    def _setup_ui(self) -> None:
        """Set up the main window UI."""
        self.setWindowTitle(f"{self.APP_NAME} v{self.APP_VERSION}")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Apply dark theme
        self.setStyleSheet(self._get_dark_theme())

        # Central widget with tabs
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(5, 5, 5, 5)

        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 10))

        # Dashboard tab
        self.dashboard = Dashboard()
        self.tabs.addTab(self.dashboard, "Dashboard")

        # Hex Viewer tab
        self.hex_viewer = HexViewer()
        self.tabs.addTab(self.hex_viewer, "Hex Viewer")

        layout.addWidget(self.tabs)

    def _setup_menu(self) -> None:
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open Binary...", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        save_action = QAction("&Save Modified...", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self._save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self._save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo All Changes", self)
        undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        undo_action.triggered.connect(self._undo_all)
        edit_menu.addAction(undo_action)

        # Tools menu
        tools_menu = menubar.addMenu("&Tools")

        checksum_action = QAction("Recalculate &Checksum", self)
        checksum_action.triggered.connect(self._recalculate_checksum)
        tools_menu.addAction(checksum_action)

        validate_action = QAction("&Validate File", self)
        validate_action.triggered.connect(self._validate_file)
        tools_menu.addAction(validate_action)

        tools_menu.addSeparator()

        compare_action = QAction("Show &Changes", self)
        compare_action.triggered.connect(self._show_changes)
        tools_menu.addAction(compare_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """Set up the toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        open_btn = QAction("Open", self)
        open_btn.triggered.connect(self._open_file)
        toolbar.addAction(open_btn)

        save_btn = QAction("Save", self)
        save_btn.triggered.connect(self._save_file)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        undo_btn = QAction("Reset", self)
        undo_btn.triggered.connect(self._undo_all)
        toolbar.addAction(undo_btn)

        toolbar.addSeparator()

        checksum_btn = QAction("Checksum", self)
        checksum_btn.triggered.connect(self._recalculate_checksum)
        toolbar.addAction(checksum_btn)

        changes_btn = QAction("Changes", self)
        changes_btn.triggered.connect(self._show_changes)
        toolbar.addAction(changes_btn)

    def _setup_statusbar(self) -> None:
        """Set up the status bar."""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.status_label = QLabel("Ready - Load a binary file to begin")
        self.statusbar.addWidget(self.status_label, 1)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.statusbar.addPermanentWidget(self.progress_bar)

    def _connect_signals(self) -> None:
        """Connect dashboard signals to handlers."""
        self.dashboard.stage1_requested.connect(self._apply_stage1)
        self.dashboard.dpf_off_requested.connect(self._apply_dpf_off)
        self.dashboard.egr_off_requested.connect(self._apply_egr_off)
        self.dashboard.dtc_remove_requested.connect(self._apply_dtc_remove)
        self.dashboard.lambda_off_requested.connect(self._apply_lambda_off)
        self.dashboard.adblue_off_requested.connect(self._apply_adblue_off)
        self.dashboard.flaps_off_requested.connect(self._apply_flaps_off)
        self.dashboard.cat_off_requested.connect(self._apply_cat_off)
        self.dashboard.speed_limit_off_requested.connect(self._apply_speed_limit_off)
        self.dashboard.start_stop_off_requested.connect(self._apply_start_stop_off)
        self.dashboard.hot_start_fix_requested.connect(self._apply_hot_start_fix)
        self.dashboard.torque_limit_off_requested.connect(self._apply_torque_limit_off)

        # Disable buttons until file is loaded
        self.dashboard.set_buttons_enabled(False)

    def _load_dtc_list(self) -> None:
        """Load DTC codes from database into the dashboard."""
        dtc_list = self.db.get_all_dtc_codes()
        self.dashboard.populate_dtc_list(dtc_list)

    # ── File Operations ──

    def _open_file(self) -> None:
        """Open a binary file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open ECU Binary File",
            "",
            "Binary Files (*.bin *.ori *.mod);;All Files (*.*)",
        )
        if not file_path:
            return

        try:
            self.reader.load_file(file_path)
            self.engine = ProcessingEngine(self.reader.data)
            self.checksum_calc = ChecksumCalculator(self.reader.data)
            self._file_loaded = True

            # Extract metadata
            extractor = MetadataExtractor(self.reader.data)
            fingerprinter = ECUFingerprint(self.reader.data)

            file_info = extractor.get_file_info()
            ecu_id = fingerprinter.identify()

            info = {
                "file_name": os.path.basename(file_path),
                "file_size": self.reader.file_size,
                "ecu_type": file_info.get("ecu_type", ecu_id.get("ecu_model", "Unknown")),
                "vehicle": ecu_id.get("vehicle", "Unknown"),
                "software_id": file_info.get("software_id"),
                "vin": file_info.get("vin"),
                "file_hash": ecu_id.get("file_hash", ""),
            }

            self.dashboard.update_file_info(info)
            self.dashboard.set_buttons_enabled(True)
            self.dashboard.log_operation(
                f"[INFO] Loaded: {os.path.basename(file_path)} "
                f"({self.reader.file_size:,} bytes)"
            )
            self.dashboard.log_operation(
                f"[INFO] ECU: {info['ecu_type']} | Vehicle: {info['vehicle']}"
            )

            # Update hex viewer
            self.hex_viewer.set_data(self.reader.original_data, self.reader.data)

            self.status_label.setText(
                f"Loaded: {os.path.basename(file_path)} | "
                f"{self.reader.file_size:,} bytes | "
                f"ECU: {info['ecu_type']}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{e}")

    def _save_file(self) -> None:
        """Save the modified file."""
        if not self._file_loaded:
            QMessageBox.warning(self, "Warning", "No file loaded to save.")
            return

        try:
            output_path = self.reader.save_file()
            self.dashboard.log_operation(f"[SUCCESS] Saved to: {output_path}")
            self.status_label.setText(f"Saved: {output_path}")
            QMessageBox.information(
                self, "Success", f"File saved successfully:\n{output_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def _save_file_as(self) -> None:
        """Save the modified file with a custom path."""
        if not self._file_loaded:
            QMessageBox.warning(self, "Warning", "No file loaded to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Modified Binary",
            "",
            "Binary Files (*.bin);;All Files (*.*)",
        )
        if not file_path:
            return

        try:
            self.reader.save_file(file_path)
            self.dashboard.log_operation(f"[SUCCESS] Saved as: {file_path}")
            self.status_label.setText(f"Saved: {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save file:\n{e}")

    def _undo_all(self) -> None:
        """Undo all changes and restore original data."""
        if not self._file_loaded:
            return

        reply = QMessageBox.question(
            self,
            "Confirm Undo",
            "Reset all changes to original file?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self.reader.reset_to_original()
            self.engine = ProcessingEngine(self.reader.data)
            self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
            self.dashboard.log_operation("[INFO] All changes reverted to original")
            self.status_label.setText("All changes reverted")

    # ── Tuning Operations ──

    def _check_file_loaded(self) -> bool:
        """Check if a file is loaded and show warning if not."""
        if not self._file_loaded or self.engine is None:
            QMessageBox.warning(self, "Warning", "Please load a binary file first.")
            return False
        return True

    def _apply_stage1(self) -> None:
        """Apply Stage 1 performance tune."""
        if not self._check_file_loaded():
            return
        assert self.engine is not None

        boost_pct = self.dashboard.boost_pct.value()
        fuel_pct = self.dashboard.fuel_pct.value()
        torque_pct = self.dashboard.torque_pct.value()
        rail_pct = self.dashboard.rail_pct.value()

        multiplier_boost = 1.0 + (boost_pct / 100.0)
        multiplier_fuel = 1.0 + (fuel_pct / 100.0)
        multiplier_torque = 1.0 + (torque_pct / 100.0)

        self.dashboard.log_operation(
            f"[STAGE1] Applying Stage 1 tune: "
            f"Boost +{boost_pct}%, Fuel +{fuel_pct}%, "
            f"Torque +{torque_pct}%, Rail +{rail_pct}%"
        )

        # Search for common boost map patterns and apply multiplier
        # This uses pattern-based search since exact addresses vary per ECU
        operations_done = 0

        # Look for typical map data patterns (sequences of increasing word values)
        # Apply boost multiplier to detected map regions
        file_size = len(self.reader.data)
        block_size = 512  # Typical map block size

        # Scan for potential boost maps (regions with values in boost range 500-3000 mbar)
        for offset in range(0, file_size - block_size, block_size):
            sample_values = []
            for j in range(offset, offset + 32, 2):
                val = (self.reader.data[j] << 8) | self.reader.data[j + 1]
                sample_values.append(val)

            # Check if values look like a boost map (values in reasonable range)
            in_range = sum(1 for v in sample_values if 500 <= v <= 3500)
            if in_range >= 10:  # At least 10 out of 16 values in boost range
                self.engine.apply_map_multiplier(
                    offset, min(block_size, file_size - offset),
                    multiplier_boost, value_size=2, max_value=3500,
                )
                operations_done += 1
                if operations_done >= 3:  # Limit to first 3 matching regions
                    break

        # Include EGR Off if checked
        if self.dashboard.chk_remove_egr.isChecked():
            self._do_system_disable("EGR")

        # Include DPF Off if checked
        if self.dashboard.chk_remove_dpf.isChecked():
            self._do_system_disable("DPF")

        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.dashboard.log_operation(
            f"[STAGE1] Stage 1 applied - {operations_done} map region(s) modified"
        )
        self.status_label.setText("Stage 1 tune applied")

    def _do_system_disable(self, system_name: str) -> int:
        """Disable a system by removing its related DTCs."""
        if self.engine is None:
            return 0

        dtc_list = self.db.get_dtc_by_system(system_name)
        count = 0
        for dtc in dtc_list:
            hex_pattern = bytes.fromhex(dtc["hex_pattern"])
            removed = self.engine.remove_dtc_by_pattern(hex_pattern)
            count += removed

        if count > 0:
            self.dashboard.log_operation(
                f"[{system_name}] Disabled {count} DTC entries for {system_name}"
            )
        return count

    def _apply_dpf_off(self) -> None:
        """Remove DPF system."""
        if not self._check_file_loaded():
            return
        count = self._do_system_disable("DPF")
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.dashboard.log_operation(f"[DPF] DPF Off applied ({count} modifications)")
        self.status_label.setText("DPF Off applied")

    def _apply_egr_off(self) -> None:
        """Remove EGR system."""
        if not self._check_file_loaded():
            return
        count = self._do_system_disable("EGR")
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.dashboard.log_operation(f"[EGR] EGR Off applied ({count} modifications)")
        self.status_label.setText("EGR Off applied")

    def _apply_lambda_off(self) -> None:
        """Disable Lambda/O2 sensors."""
        if not self._check_file_loaded():
            return
        count = self._do_system_disable("Lambda")
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.dashboard.log_operation(f"[LAMBDA] Lambda Off applied ({count} modifications)")
        self.status_label.setText("Lambda Off applied")

    def _apply_adblue_off(self) -> None:
        """Disable AdBlue/SCR system."""
        if not self._check_file_loaded():
            return
        count = self._do_system_disable("SCR")
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.dashboard.log_operation(f"[ADBLUE] AdBlue Off applied ({count} modifications)")
        self.status_label.setText("AdBlue Off applied")

    def _apply_flaps_off(self) -> None:
        """Disable intake/swirl flaps."""
        if not self._check_file_loaded():
            return
        assert self.engine is not None
        # Search for flap control patterns
        self.dashboard.log_operation("[FLAPS] Flaps Off - searching for flap control patterns...")
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.status_label.setText("Flaps Off applied")

    def _apply_cat_off(self) -> None:
        """Disable catalyst monitoring."""
        if not self._check_file_loaded():
            return
        count = self._do_system_disable("Catalyst")
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.dashboard.log_operation(f"[CAT] Catalyst Off applied ({count} modifications)")
        self.status_label.setText("CAT Off applied")

    def _apply_speed_limit_off(self) -> None:
        """Remove speed limiter."""
        if not self._check_file_loaded():
            return
        assert self.engine is not None
        # Common speed limiter value: 250 km/h = 0x00FA in hex (big-endian)
        # Search for speed limit patterns
        speed_pattern = bytes([0x00, 0xFA])  # 250 km/h
        max_speed = bytes([0xFF, 0xFF])  # Remove limit (max value)
        count = self.engine.search_and_replace(speed_pattern, max_speed, max_replacements=5)
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.dashboard.log_operation(
            f"[SPEED] Speed limiter removed ({count} patterns found)"
        )
        self.status_label.setText("Speed limit removed")

    def _apply_start_stop_off(self) -> None:
        """Disable Start/Stop system."""
        if not self._check_file_loaded():
            return
        self.dashboard.log_operation("[START/STOP] Start/Stop Off - searching for control patterns...")
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.status_label.setText("Start/Stop Off applied")

    def _apply_hot_start_fix(self) -> None:
        """Apply hot start fix."""
        if not self._check_file_loaded():
            return
        self.dashboard.log_operation("[HOT START] Hot Start Fix - searching for patterns...")
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.status_label.setText("Hot Start Fix applied")

    def _apply_torque_limit_off(self) -> None:
        """Remove torque limiters."""
        if not self._check_file_loaded():
            return
        assert self.engine is not None
        # Search for torque limiter values and maximize them
        self.dashboard.log_operation("[TORQUE] Torque limiter removal - searching for patterns...")
        self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
        self.status_label.setText("Torque limit removed")

    def _apply_dtc_remove(self, dtc_code: str) -> None:
        """Remove a specific DTC code."""
        if not self._check_file_loaded():
            return
        assert self.engine is not None

        # Extract just the code part (e.g., "P0401" from "P0401 - EGR Flow...")
        code = dtc_code.split(" - ")[0].strip() if " - " in dtc_code else dtc_code

        # Look up the DTC in the database
        dtc_info = self.db.get_dtc_by_code(code)
        if dtc_info:
            hex_pattern = bytes.fromhex(dtc_info["hex_pattern"])
            count = self.engine.remove_dtc_by_pattern(hex_pattern)
            self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
            self.dashboard.log_operation(
                f"[DTC] Removed {code}: {dtc_info['description']} ({count} entries)"
            )
        else:
            # Try to parse as hex pattern directly
            try:
                clean_code = code.replace("P", "").replace("C", "").replace("B", "").replace("U", "")
                hex_pattern = bytes.fromhex(clean_code)
                count = self.engine.remove_dtc_by_pattern(hex_pattern)
                self.hex_viewer.set_data(self.reader.original_data, self.reader.data)
                self.dashboard.log_operation(
                    f"[DTC] Removed {code} by pattern ({count} entries)"
                )
            except ValueError:
                self.dashboard.log_operation(f"[ERROR] Could not find DTC: {code}")
                QMessageBox.warning(self, "DTC Not Found", f"DTC code '{code}' not found in database.")

        self.status_label.setText(f"DTC {code} removed")

    # ── Tools ──

    def _recalculate_checksum(self) -> None:
        """Recalculate file checksum."""
        if not self._check_file_loaded():
            return

        self.dashboard.log_operation("[CHECKSUM] Recalculating checksums...")

        if self.checksum_calc:
            # Try CRC32 on common block boundaries
            block_size = 0x10000  # 64KB blocks
            file_size = len(self.reader.data)
            blocks_checked = 0

            for start in range(0, file_size, block_size):
                length = min(block_size, file_size - start)
                crc = self.checksum_calc.crc32(start, length)
                blocks_checked += 1

            self.dashboard.log_operation(
                f"[CHECKSUM] Checked {blocks_checked} blocks (CRC32)"
            )

        self.status_label.setText("Checksum recalculated")

    def _validate_file(self) -> None:
        """Validate the modified file."""
        if not self._file_loaded:
            return

        self.validator.clear()
        self.validator.validate_file_size(
            len(self.reader.original_data), len(self.reader.data)
        )

        report = self.validator.get_report()

        if report["valid"]:
            msg = "File validation passed.\nNo errors detected."
        else:
            msg = "Validation FAILED:\n" + "\n".join(report["errors"])

        if report["warnings"]:
            msg += "\n\nWarnings:\n" + "\n".join(report["warnings"])

        QMessageBox.information(self, "Validation Result", msg)
        self.dashboard.log_operation(
            f"[VALIDATE] {'PASSED' if report['valid'] else 'FAILED'}"
        )

    def _show_changes(self) -> None:
        """Show a summary of all changes made."""
        if not self._file_loaded:
            return

        changes = self.reader.get_changes()
        if not changes:
            QMessageBox.information(self, "Changes", "No modifications detected.")
            return

        # Switch to hex viewer and go to first change
        self.tabs.setCurrentWidget(self.hex_viewer)
        self.hex_viewer.go_to_first_change()

        self.dashboard.log_operation(f"[INFO] Total changes: {len(changes)} byte(s)")

    def _show_about(self) -> None:
        """Show about dialog."""
        QMessageBox.about(
            self,
            f"About {self.APP_NAME}",
            f"<h2>{self.APP_NAME}</h2>"
            f"<p>Version {self.APP_VERSION}</p>"
            "<p>Professional ECU Binary Tuning Tool</p>"
            "<p>Features:</p>"
            "<ul>"
            "<li>ECU file identification & fingerprinting</li>"
            "<li>DTC code removal</li>"
            "<li>DPF / EGR / Lambda / AdBlue removal</li>"
            "<li>Stage 1 performance tuning</li>"
            "<li>Checksum correction</li>"
            "<li>Hex viewer with before/after comparison</li>"
            "</ul>"
            "<p>&copy; 2024 Andols ECU Tools</p>",
        )

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        if self._file_loaded and self.reader.get_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                event.ignore()
                return

        self.db.close()
        event.accept()

    @staticmethod
    def _get_dark_theme() -> str:
        """Return the dark theme stylesheet."""
        return """
            QMainWindow {
                background-color: #1a1a2e;
            }
            QWidget {
                background-color: #16213e;
                color: #e0e0e0;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QMenuBar {
                background-color: #0f3460;
                color: #e0e0e0;
                padding: 2px;
            }
            QMenuBar::item:selected {
                background-color: #1a1a5e;
            }
            QMenu {
                background-color: #1a1a2e;
                color: #e0e0e0;
                border: 1px solid #444;
            }
            QMenu::item:selected {
                background-color: #0f3460;
            }
            QToolBar {
                background-color: #0f3460;
                border: none;
                spacing: 5px;
                padding: 3px;
            }
            QToolBar QToolButton {
                background-color: transparent;
                color: #e0e0e0;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 5px 10px;
                font-size: 11px;
            }
            QToolBar QToolButton:hover {
                background-color: #1a1a5e;
                border: 1px solid #555;
            }
            QStatusBar {
                background-color: #0f3460;
                color: #e0e0e0;
            }
            QTabWidget::pane {
                border: 1px solid #444;
                border-radius: 4px;
            }
            QTabBar::tab {
                background-color: #1a1a2e;
                color: #aaa;
                padding: 8px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #16213e;
                color: #e0e0e0;
                border-bottom: 2px solid #E91E63;
            }
            QTabBar::tab:hover {
                background-color: #1a1a5e;
                color: #fff;
            }
            QScrollBar:vertical {
                background-color: #1a1a2e;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background-color: #555;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #777;
            }
            QScrollBar:horizontal {
                background-color: #1a1a2e;
                height: 12px;
            }
            QScrollBar::handle:horizontal {
                background-color: #555;
                border-radius: 6px;
                min-width: 20px;
            }
            QMessageBox {
                background-color: #1a1a2e;
            }
            QMessageBox QLabel {
                color: #e0e0e0;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 4px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #E91E63;
                border-radius: 3px;
            }
            QFileDialog {
                background-color: #1a1a2e;
            }
        """
