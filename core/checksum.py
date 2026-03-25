"""
Checksum Calculator - Integrity Layer
Computes and verifies checksums for ECU binary files.
"""

import struct
from typing import Optional


class ChecksumCalculator:
    """
    Handles checksum calculation and correction for ECU binary files.
    Supports multiple checksum algorithms used by different ECU manufacturers.
    """

    def __init__(self, data: bytearray) -> None:
        self.data = data

    def crc32(self, start: int, length: int) -> int:
        """Calculate CRC32 checksum for a data region."""
        crc = 0xFFFFFFFF
        poly = 0xEDB88320

        for i in range(start, min(start + length, len(self.data))):
            crc ^= self.data[i]
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ poly
                else:
                    crc >>= 1

        return crc ^ 0xFFFFFFFF

    def crc16(self, start: int, length: int) -> int:
        """Calculate CRC16-CCITT checksum for a data region."""
        crc = 0xFFFF
        poly = 0x1021

        for i in range(start, min(start + length, len(self.data))):
            crc ^= self.data[i] << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = ((crc << 1) ^ poly) & 0xFFFF
                else:
                    crc = (crc << 1) & 0xFFFF

        return crc

    def simple_sum(self, start: int, length: int, width: int = 8) -> int:
        """
        Calculate simple additive checksum.
        width: 8 for byte sum, 16 for word sum, 32 for dword sum.
        """
        total = 0
        end = min(start + length, len(self.data))

        if width == 8:
            for i in range(start, end):
                total += self.data[i]
        elif width == 16:
            for i in range(start, end - 1, 2):
                total += (self.data[i] << 8) | self.data[i + 1]
        elif width == 32:
            for i in range(start, end - 3, 4):
                total += struct.unpack_from(">I", self.data, i)[0]

        return total & (2**width - 1)

    def xor_checksum(self, start: int, length: int) -> int:
        """Calculate XOR checksum for a data region."""
        result = 0
        for i in range(start, min(start + length, len(self.data))):
            result ^= self.data[i]
        return result

    def complement_checksum(self, start: int, length: int) -> int:
        """Calculate two's complement checksum."""
        total = self.simple_sum(start, length, 32)
        return (~total + 1) & 0xFFFFFFFF

    def verify_block_checksum(
        self,
        block_start: int,
        block_length: int,
        checksum_address: int,
        algorithm: str = "crc32",
    ) -> dict:
        """
        Verify a block checksum.
        Returns dict with 'valid', 'expected', 'calculated' fields.
        """
        if algorithm == "crc32":
            calculated = self.crc32(block_start, block_length)
        elif algorithm == "crc16":
            calculated = self.crc16(block_start, block_length)
        elif algorithm == "sum8":
            calculated = self.simple_sum(block_start, block_length, 8)
        elif algorithm == "sum16":
            calculated = self.simple_sum(block_start, block_length, 16)
        elif algorithm == "sum32":
            calculated = self.simple_sum(block_start, block_length, 32)
        elif algorithm == "xor":
            calculated = self.xor_checksum(block_start, block_length)
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        # Read stored checksum
        if algorithm in ("crc32", "sum32"):
            stored = struct.unpack_from("<I", self.data, checksum_address)[0]
        elif algorithm in ("crc16", "sum16"):
            stored = struct.unpack_from("<H", self.data, checksum_address)[0]
        else:
            stored = self.data[checksum_address]

        return {
            "valid": calculated == stored,
            "calculated": calculated,
            "stored": stored,
            "block_start": block_start,
            "block_length": block_length,
            "checksum_address": checksum_address,
            "algorithm": algorithm,
        }

    def correct_block_checksum(
        self,
        block_start: int,
        block_length: int,
        checksum_address: int,
        algorithm: str = "crc32",
    ) -> Optional[int]:
        """
        Recalculate and write the correct checksum for a block.
        Returns the new checksum value.
        """
        if algorithm == "crc32":
            new_checksum = self.crc32(block_start, block_length)
            struct.pack_into("<I", self.data, checksum_address, new_checksum)
        elif algorithm == "crc16":
            new_checksum = self.crc16(block_start, block_length)
            struct.pack_into("<H", self.data, checksum_address, new_checksum)
        elif algorithm == "sum8":
            new_checksum = self.simple_sum(block_start, block_length, 8)
            self.data[checksum_address] = new_checksum & 0xFF
        elif algorithm == "sum16":
            new_checksum = self.simple_sum(block_start, block_length, 16)
            struct.pack_into("<H", self.data, checksum_address, new_checksum)
        elif algorithm == "sum32":
            new_checksum = self.simple_sum(block_start, block_length, 32)
            struct.pack_into("<I", self.data, checksum_address, new_checksum)
        elif algorithm == "xor":
            new_checksum = self.xor_checksum(block_start, block_length)
            self.data[checksum_address] = new_checksum & 0xFF
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

        return new_checksum


class ValidationEngine:
    """Validates that modifications stay within safe limits."""

    # Safety limits for common tuning parameters
    SAFETY_LIMITS: dict[str, dict[str, float]] = {
        "boost_pressure": {
            "min": 500.0,    # mbar
            "max": 3500.0,   # mbar
            "unit": "mbar",
        },
        "injection_quantity": {
            "min": 0.0,      # mg/stroke
            "max": 120.0,    # mg/stroke
            "unit": "mg/str",
        },
        "rail_pressure": {
            "min": 200.0,    # bar
            "max": 2200.0,   # bar
            "unit": "bar",
        },
        "injection_timing": {
            "min": -30.0,    # degrees BTDC
            "max": 15.0,     # degrees BTDC
            "unit": "deg",
        },
        "torque_limit": {
            "min": 0.0,      # Nm
            "max": 800.0,    # Nm
            "unit": "Nm",
        },
        "rpm_limit": {
            "min": 800.0,    # RPM
            "max": 8000.0,   # RPM
            "unit": "RPM",
        },
    }

    def __init__(self) -> None:
        self.warnings: list[str] = []
        self.errors: list[str] = []

    def validate_value(self, param_name: str, value: float) -> bool:
        """Check if a value is within safe limits for the given parameter."""
        if param_name not in self.SAFETY_LIMITS:
            self.warnings.append(f"No safety limits defined for '{param_name}'")
            return True

        limits = self.SAFETY_LIMITS[param_name]
        if value < limits["min"]:
            self.errors.append(
                f"{param_name}: value {value} below minimum {limits['min']} {limits['unit']}"
            )
            return False
        if value > limits["max"]:
            self.errors.append(
                f"{param_name}: value {value} above maximum {limits['max']} {limits['unit']}"
            )
            return False
        return True

    def validate_percentage_change(
        self, original: float, modified: float, max_change_pct: float = 30.0
    ) -> bool:
        """Validate that a value hasn't changed by more than the allowed percentage."""
        if original == 0:
            return True
        change_pct = abs((modified - original) / original) * 100
        if change_pct > max_change_pct:
            self.warnings.append(
                f"Value changed by {change_pct:.1f}% (max allowed: {max_change_pct}%)"
            )
            return False
        return True

    def validate_file_size(self, original_size: int, modified_size: int) -> bool:
        """Ensure file size hasn't changed (critical for ECU files)."""
        if original_size != modified_size:
            self.errors.append(
                f"File size changed from {original_size} to {modified_size} bytes!"
            )
            return False
        return True

    def get_report(self) -> dict:
        """Get validation report."""
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors.copy(),
            "warnings": self.warnings.copy(),
        }

    def clear(self) -> None:
        """Clear all warnings and errors."""
        self.warnings.clear()
        self.errors.clear()
