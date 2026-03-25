"""
Hex Viewer Widget - Shows hex data with before/after comparison.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel,
    QSpinBox, QGroupBox, QPushButton, QScrollBar,
)
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor
from PyQt5.QtCore import Qt


class HexViewer(QWidget):
    """Hex viewer widget with before/after diff highlighting."""

    BYTES_PER_LINE = 16

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.original_data: bytearray = bytearray()
        self.modified_data: bytearray = bytearray()
        self.current_offset = 0
        self.visible_lines = 32
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the hex viewer UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Navigation bar
        nav_layout = QHBoxLayout()

        nav_layout.addWidget(QLabel("Go to address:"))
        self.address_input = QSpinBox()
        self.address_input.setPrefix("0x")
        self.address_input.setDisplayIntegerBase(16)
        self.address_input.setMaximum(0x7FFFFFFF)
        self.address_input.setMinimumWidth(150)
        self.address_input.valueChanged.connect(self._on_address_changed)
        nav_layout.addWidget(self.address_input)

        self.btn_prev = QPushButton("< Prev")
        self.btn_prev.clicked.connect(self._prev_page)
        nav_layout.addWidget(self.btn_prev)

        self.btn_next = QPushButton("Next >")
        self.btn_next.clicked.connect(self._next_page)
        nav_layout.addWidget(self.btn_next)

        self.info_label = QLabel("No file loaded")
        nav_layout.addStretch()
        nav_layout.addWidget(self.info_label)

        layout.addLayout(nav_layout)

        # Hex display area
        hex_layout = QHBoxLayout()

        # Original data (Before)
        before_group = QGroupBox("Before (Original)")
        before_layout = QVBoxLayout(before_group)
        self.before_text = QTextEdit()
        self.before_text.setReadOnly(True)
        self.before_text.setFont(QFont("Courier New", 10))
        self.before_text.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #d4d4d4; }"
        )
        self.before_text.setMinimumWidth(500)
        before_layout.addWidget(self.before_text)
        hex_layout.addWidget(before_group)

        # Modified data (After)
        after_group = QGroupBox("After (Modified)")
        after_layout = QVBoxLayout(after_group)
        self.after_text = QTextEdit()
        self.after_text.setReadOnly(True)
        self.after_text.setFont(QFont("Courier New", 10))
        self.after_text.setStyleSheet(
            "QTextEdit { background-color: #1e1e1e; color: #d4d4d4; }"
        )
        self.after_text.setMinimumWidth(500)
        after_layout.addWidget(self.after_text)
        hex_layout.addWidget(after_group)

        layout.addLayout(hex_layout)

        # Changes summary
        self.changes_label = QLabel("No changes")
        self.changes_label.setStyleSheet("color: #888; padding: 4px;")
        layout.addWidget(self.changes_label)

    def set_data(self, original: bytearray, modified: bytearray) -> None:
        """Set the data to display."""
        self.original_data = original
        self.modified_data = modified
        self.current_offset = 0
        self.address_input.setMaximum(max(0, len(original) - 1))
        self._update_display()
        self._update_changes_summary()

    def _on_address_changed(self, value: int) -> None:
        """Handle address input change."""
        self.current_offset = (value // self.BYTES_PER_LINE) * self.BYTES_PER_LINE
        self._update_display()

    def _prev_page(self) -> None:
        """Navigate to previous page."""
        page_size = self.visible_lines * self.BYTES_PER_LINE
        self.current_offset = max(0, self.current_offset - page_size)
        self.address_input.setValue(self.current_offset)

    def _next_page(self) -> None:
        """Navigate to next page."""
        page_size = self.visible_lines * self.BYTES_PER_LINE
        max_offset = max(0, len(self.original_data) - page_size)
        self.current_offset = min(max_offset, self.current_offset + page_size)
        self.address_input.setValue(self.current_offset)

    def _update_display(self) -> None:
        """Update the hex display with current data."""
        if not self.original_data:
            return

        self._render_hex(self.before_text, self.original_data, is_original=True)
        self._render_hex(self.after_text, self.modified_data, is_original=False)

        total = len(self.original_data)
        self.info_label.setText(
            f"File size: {total:,} bytes (0x{total:X}) | "
            f"Showing offset: 0x{self.current_offset:08X}"
        )

    def _render_hex(self, text_widget: QTextEdit, data: bytearray, is_original: bool) -> None:
        """Render hex data into a QTextEdit with diff highlighting."""
        text_widget.clear()
        cursor = text_widget.textCursor()

        # Define formats
        normal_fmt = QTextCharFormat()
        normal_fmt.setForeground(QColor("#d4d4d4"))

        changed_fmt = QTextCharFormat()
        if is_original:
            changed_fmt.setForeground(QColor("#ff6b6b"))  # Red for original changed bytes
            changed_fmt.setBackground(QColor("#3d1f1f"))
        else:
            changed_fmt.setForeground(QColor("#51cf66"))  # Green for new values
            changed_fmt.setBackground(QColor("#1f3d1f"))

        address_fmt = QTextCharFormat()
        address_fmt.setForeground(QColor("#569cd6"))

        ascii_fmt = QTextCharFormat()
        ascii_fmt.setForeground(QColor("#ce9178"))

        end_offset = min(
            self.current_offset + self.visible_lines * self.BYTES_PER_LINE,
            len(data),
        )

        for line_start in range(self.current_offset, end_offset, self.BYTES_PER_LINE):
            # Address
            cursor.insertText(f"0x{line_start:08X}: ", address_fmt)

            # Hex bytes
            line_end = min(line_start + self.BYTES_PER_LINE, len(data))
            for i in range(line_start, line_end):
                is_changed = (
                    i < len(self.original_data)
                    and i < len(self.modified_data)
                    and self.original_data[i] != self.modified_data[i]
                )
                fmt = changed_fmt if is_changed else normal_fmt
                cursor.insertText(f"{data[i]:02X} ", fmt)

            # Padding for incomplete lines
            remaining = self.BYTES_PER_LINE - (line_end - line_start)
            if remaining > 0:
                cursor.insertText("   " * remaining, normal_fmt)

            # ASCII representation
            cursor.insertText(" ", normal_fmt)
            for i in range(line_start, line_end):
                ch = chr(data[i]) if 32 <= data[i] < 127 else "."
                is_changed = (
                    i < len(self.original_data)
                    and i < len(self.modified_data)
                    and self.original_data[i] != self.modified_data[i]
                )
                fmt = changed_fmt if is_changed else ascii_fmt
                cursor.insertText(ch, fmt)

            cursor.insertText("\n", normal_fmt)

        text_widget.setTextCursor(cursor)

    def _update_changes_summary(self) -> None:
        """Update the changes summary label."""
        if not self.original_data or not self.modified_data:
            self.changes_label.setText("No data loaded")
            return

        change_count = sum(
            1
            for i in range(min(len(self.original_data), len(self.modified_data)))
            if self.original_data[i] != self.modified_data[i]
        )

        if change_count == 0:
            self.changes_label.setText("No changes detected")
            self.changes_label.setStyleSheet("color: #888; padding: 4px;")
        else:
            self.changes_label.setText(
                f"{change_count} byte(s) modified"
            )
            self.changes_label.setStyleSheet("color: #51cf66; padding: 4px; font-weight: bold;")

    def go_to_first_change(self) -> None:
        """Navigate to the first changed byte."""
        for i in range(min(len(self.original_data), len(self.modified_data))):
            if self.original_data[i] != self.modified_data[i]:
                self.current_offset = (i // self.BYTES_PER_LINE) * self.BYTES_PER_LINE
                self.address_input.setValue(self.current_offset)
                return
