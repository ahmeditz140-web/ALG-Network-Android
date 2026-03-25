"""
Dashboard Widget - Main tuning controls and quick actions.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton,
    QLabel, QComboBox, QProgressBar, QFrame, QGridLayout,
    QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit,
)
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtCore import Qt, pyqtSignal


class TuningButton(QPushButton):
    """Custom styled button for tuning operations."""

    def __init__(self, text: str, color: str = "#2196F3", parent: QWidget = None) -> None:
        super().__init__(text, parent)
        self.setMinimumHeight(50)
        self.setMinimumWidth(140)
        self.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
            }}
            QPushButton:hover {{
                background-color: {self._lighten(color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken(color)};
            }}
            QPushButton:disabled {{
                background-color: #555;
                color: #999;
            }}
        """)

    def _lighten(self, hex_color: str) -> str:
        """Make a hex color lighter."""
        r = min(255, int(hex_color[1:3], 16) + 30)
        g = min(255, int(hex_color[3:5], 16) + 30)
        b = min(255, int(hex_color[5:7], 16) + 30)
        return f"#{r:02X}{g:02X}{b:02X}"

    def _darken(self, hex_color: str) -> str:
        """Make a hex color darker."""
        r = max(0, int(hex_color[1:3], 16) - 30)
        g = max(0, int(hex_color[3:5], 16) - 30)
        b = max(0, int(hex_color[5:7], 16) - 30)
        return f"#{r:02X}{g:02X}{b:02X}"


class Dashboard(QWidget):
    """Main dashboard with tuning controls."""

    # Signals
    stage1_requested = pyqtSignal()
    dpf_off_requested = pyqtSignal()
    egr_off_requested = pyqtSignal()
    dtc_remove_requested = pyqtSignal(str)  # DTC code
    lambda_off_requested = pyqtSignal()
    adblue_off_requested = pyqtSignal()
    flaps_off_requested = pyqtSignal()
    cat_off_requested = pyqtSignal()
    speed_limit_off_requested = pyqtSignal()
    start_stop_off_requested = pyqtSignal()
    hot_start_fix_requested = pyqtSignal()
    torque_limit_off_requested = pyqtSignal()
    custom_dtc_requested = pyqtSignal(str)  # Custom DTC pattern

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dashboard UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)

        # ── File Info Section ──
        info_group = QGroupBox("File Information")
        info_group.setStyleSheet(self._group_style())
        info_layout = QGridLayout(info_group)

        self.lbl_file_name = QLabel("No file loaded")
        self.lbl_file_name.setFont(QFont("Segoe UI", 10, QFont.Bold))
        info_layout.addWidget(QLabel("File:"), 0, 0)
        info_layout.addWidget(self.lbl_file_name, 0, 1)

        self.lbl_ecu_type = QLabel("-")
        info_layout.addWidget(QLabel("ECU Type:"), 1, 0)
        info_layout.addWidget(self.lbl_ecu_type, 1, 1)

        self.lbl_vehicle = QLabel("-")
        info_layout.addWidget(QLabel("Vehicle:"), 1, 2)
        info_layout.addWidget(self.lbl_vehicle, 1, 3)

        self.lbl_sw_version = QLabel("-")
        info_layout.addWidget(QLabel("Software:"), 2, 0)
        info_layout.addWidget(self.lbl_sw_version, 2, 1)

        self.lbl_vin = QLabel("-")
        info_layout.addWidget(QLabel("VIN:"), 2, 2)
        info_layout.addWidget(self.lbl_vin, 2, 3)

        self.lbl_file_size = QLabel("-")
        info_layout.addWidget(QLabel("Size:"), 3, 0)
        info_layout.addWidget(self.lbl_file_size, 3, 1)

        self.lbl_file_hash = QLabel("-")
        info_layout.addWidget(QLabel("Hash:"), 3, 2)
        info_layout.addWidget(self.lbl_file_hash, 3, 3)

        main_layout.addWidget(info_group)

        # ── Quick Tuning Actions ──
        tuning_group = QGroupBox("Quick Tuning Actions")
        tuning_group.setStyleSheet(self._group_style())
        tuning_layout = QGridLayout(tuning_group)
        tuning_layout.setSpacing(10)

        # Row 1 - Performance
        self.btn_stage1 = TuningButton("Stage 1", "#E91E63")
        self.btn_stage1.setToolTip("Apply Stage 1 performance tune (boost, fueling, torque)")
        self.btn_stage1.clicked.connect(self.stage1_requested.emit)
        tuning_layout.addWidget(self.btn_stage1, 0, 0)

        self.btn_dpf_off = TuningButton("DPF Off", "#FF5722")
        self.btn_dpf_off.setToolTip("Remove Diesel Particulate Filter")
        self.btn_dpf_off.clicked.connect(self.dpf_off_requested.emit)
        tuning_layout.addWidget(self.btn_dpf_off, 0, 1)

        self.btn_egr_off = TuningButton("EGR Off", "#FF9800")
        self.btn_egr_off.setToolTip("Disable Exhaust Gas Recirculation")
        self.btn_egr_off.clicked.connect(self.egr_off_requested.emit)
        tuning_layout.addWidget(self.btn_egr_off, 0, 2)

        self.btn_lambda_off = TuningButton("Lambda Off", "#FFC107")
        self.btn_lambda_off.setToolTip("Disable Lambda/O2 sensor monitoring")
        self.btn_lambda_off.clicked.connect(self.lambda_off_requested.emit)
        tuning_layout.addWidget(self.btn_lambda_off, 0, 3)

        # Row 2 - Systems
        self.btn_adblue_off = TuningButton("AdBlue Off", "#9C27B0")
        self.btn_adblue_off.setToolTip("Disable AdBlue/SCR system")
        self.btn_adblue_off.clicked.connect(self.adblue_off_requested.emit)
        tuning_layout.addWidget(self.btn_adblue_off, 1, 0)

        self.btn_flaps_off = TuningButton("Flaps Off", "#673AB7")
        self.btn_flaps_off.setToolTip("Disable intake flaps/swirl flaps")
        self.btn_flaps_off.clicked.connect(self.flaps_off_requested.emit)
        tuning_layout.addWidget(self.btn_flaps_off, 1, 1)

        self.btn_cat_off = TuningButton("CAT Off", "#3F51B5")
        self.btn_cat_off.setToolTip("Disable catalyst monitoring")
        self.btn_cat_off.clicked.connect(self.cat_off_requested.emit)
        tuning_layout.addWidget(self.btn_cat_off, 1, 2)

        self.btn_speed_limit = TuningButton("Speed Limit Off", "#2196F3")
        self.btn_speed_limit.setToolTip("Remove speed limiter")
        self.btn_speed_limit.clicked.connect(self.speed_limit_off_requested.emit)
        tuning_layout.addWidget(self.btn_speed_limit, 1, 3)

        # Row 3 - Additional
        self.btn_start_stop = TuningButton("Start/Stop Off", "#00BCD4")
        self.btn_start_stop.setToolTip("Disable Start/Stop system")
        self.btn_start_stop.clicked.connect(self.start_stop_off_requested.emit)
        tuning_layout.addWidget(self.btn_start_stop, 2, 0)

        self.btn_hot_start = TuningButton("Hot Start Fix", "#009688")
        self.btn_hot_start.setToolTip("Apply hot start fix")
        self.btn_hot_start.clicked.connect(self.hot_start_fix_requested.emit)
        tuning_layout.addWidget(self.btn_hot_start, 2, 1)

        self.btn_torque_limit = TuningButton("Torque Limit Off", "#4CAF50")
        self.btn_torque_limit.setToolTip("Remove torque limiters")
        self.btn_torque_limit.clicked.connect(self.torque_limit_off_requested.emit)
        tuning_layout.addWidget(self.btn_torque_limit, 2, 2)

        main_layout.addWidget(tuning_group)

        # ── DTC Removal Section ──
        dtc_group = QGroupBox("DTC Code Removal")
        dtc_group.setStyleSheet(self._group_style())
        dtc_layout = QHBoxLayout(dtc_group)

        dtc_layout.addWidget(QLabel("Select DTC:"))
        self.dtc_combo = QComboBox()
        self.dtc_combo.setMinimumWidth(300)
        self.dtc_combo.setEditable(True)
        self.dtc_combo.setPlaceholderText("Type or select DTC code (e.g. P0401)")
        dtc_layout.addWidget(self.dtc_combo)

        self.btn_remove_dtc = TuningButton("Remove DTC", "#f44336")
        self.btn_remove_dtc.setMinimumHeight(40)
        self.btn_remove_dtc.clicked.connect(self._on_remove_dtc)
        dtc_layout.addWidget(self.btn_remove_dtc)

        self.btn_remove_all_dtc = TuningButton("Remove All DTCs", "#d32f2f")
        self.btn_remove_all_dtc.setMinimumHeight(40)
        dtc_layout.addWidget(self.btn_remove_all_dtc)

        main_layout.addWidget(dtc_group)

        # ── Stage 1 Settings ──
        stage_group = QGroupBox("Stage 1 Settings")
        stage_group.setStyleSheet(self._group_style())
        stage_layout = QGridLayout(stage_group)

        stage_layout.addWidget(QLabel("Boost Increase (%):"), 0, 0)
        self.boost_pct = QSpinBox()
        self.boost_pct.setRange(0, 50)
        self.boost_pct.setValue(10)
        self.boost_pct.setSuffix("%")
        stage_layout.addWidget(self.boost_pct, 0, 1)

        stage_layout.addWidget(QLabel("Fuel Increase (%):"), 0, 2)
        self.fuel_pct = QSpinBox()
        self.fuel_pct.setRange(0, 30)
        self.fuel_pct.setValue(8)
        self.fuel_pct.setSuffix("%")
        stage_layout.addWidget(self.fuel_pct, 0, 3)

        stage_layout.addWidget(QLabel("Torque Increase (%):"), 1, 0)
        self.torque_pct = QSpinBox()
        self.torque_pct.setRange(0, 40)
        self.torque_pct.setValue(15)
        self.torque_pct.setSuffix("%")
        stage_layout.addWidget(self.torque_pct, 1, 1)

        stage_layout.addWidget(QLabel("Rail Pressure (%):"), 1, 2)
        self.rail_pct = QSpinBox()
        self.rail_pct.setRange(0, 20)
        self.rail_pct.setValue(5)
        self.rail_pct.setSuffix("%")
        stage_layout.addWidget(self.rail_pct, 1, 3)

        self.chk_remove_egr = QCheckBox("Include EGR Off")
        self.chk_remove_egr.setChecked(True)
        stage_layout.addWidget(self.chk_remove_egr, 2, 0)

        self.chk_remove_dpf = QCheckBox("Include DPF Off")
        self.chk_remove_dpf.setChecked(False)
        stage_layout.addWidget(self.chk_remove_dpf, 2, 1)

        main_layout.addWidget(stage_group)

        # ── Operations Log ──
        log_group = QGroupBox("Operations Log")
        log_group.setStyleSheet(self._group_style())
        log_layout = QVBoxLayout(log_group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(120)
        self.log_text.setFont(QFont("Courier New", 9))
        self.log_text.setStyleSheet(
            "QTextEdit { background-color: #1a1a2e; color: #e0e0e0; }"
        )
        log_layout.addWidget(self.log_text)

        main_layout.addWidget(log_group)
        main_layout.addStretch()

    def _group_style(self) -> str:
        """Return the group box stylesheet."""
        return """
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QLabel {
                color: #ccc;
            }
            QComboBox, QSpinBox, QDoubleSpinBox {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 4px;
            }
            QCheckBox {
                color: #ccc;
            }
        """

    def _on_remove_dtc(self) -> None:
        """Handle DTC removal button click."""
        dtc_code = self.dtc_combo.currentText().strip().upper()
        if dtc_code:
            self.dtc_remove_requested.emit(dtc_code)

    def update_file_info(self, info: dict) -> None:
        """Update the file information display."""
        self.lbl_file_name.setText(info.get("file_name", "-"))
        self.lbl_ecu_type.setText(info.get("ecu_type", "-"))
        self.lbl_vehicle.setText(info.get("vehicle", "-"))
        self.lbl_sw_version.setText(info.get("software_id", "-") or "-")
        self.lbl_vin.setText(info.get("vin", "-") or "-")

        size = info.get("file_size", 0)
        self.lbl_file_size.setText(f"{size:,} bytes ({size / 1024:.1f} KB)")
        self.lbl_file_hash.setText(info.get("file_hash", "-")[:16] + "...")

    def populate_dtc_list(self, dtc_list: list[dict]) -> None:
        """Populate the DTC combo box with available codes."""
        self.dtc_combo.clear()
        for dtc in dtc_list:
            display = f"{dtc['dtc_code']} - {dtc['description']}"
            self.dtc_combo.addItem(display, dtc['dtc_code'])

    def log_operation(self, message: str) -> None:
        """Add a message to the operations log."""
        self.log_text.append(message)

    def set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable all tuning buttons."""
        for btn in [
            self.btn_stage1, self.btn_dpf_off, self.btn_egr_off,
            self.btn_lambda_off, self.btn_adblue_off, self.btn_flaps_off,
            self.btn_cat_off, self.btn_speed_limit, self.btn_start_stop,
            self.btn_hot_start, self.btn_torque_limit,
            self.btn_remove_dtc, self.btn_remove_all_dtc,
        ]:
            btn.setEnabled(enabled)
