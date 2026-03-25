"""
Binary Reader Module - Input & Identification Layer
Reads .bin files and converts them to ByteArray for processing.
"""

import os
from typing import Optional


class BinaryReader:
    """Handles reading and basic operations on ECU binary files."""

    def __init__(self) -> None:
        self.file_path: str = ""
        self.data: bytearray = bytearray()
        self.original_data: bytearray = bytearray()
        self.file_size: int = 0

    def load_file(self, file_path: str) -> bool:
        """Load a binary file into memory."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")

        with open(file_path, "rb") as f:
            raw = f.read()

        self.file_path = file_path
        self.data = bytearray(raw)
        self.original_data = bytearray(raw)
        self.file_size = len(self.data)
        return True

    def save_file(self, output_path: Optional[str] = None) -> str:
        """Save the modified binary data to a file."""
        if not self.data:
            raise ValueError("No data loaded to save.")

        # CRITICAL SAFETY CHECK: file size must not change
        if len(self.data) != len(self.original_data):
            raise RuntimeError(
                f"SAFETY ERROR: File size changed from {len(self.original_data)} "
                f"to {len(self.data)} bytes. This would brick the ECU. "
                f"Save aborted."
            )

        if output_path is None:
            base, ext = os.path.splitext(self.file_path)
            output_path = f"{base}_modified{ext}"

        with open(output_path, "wb") as f:
            f.write(self.data)

        # Verify written file size matches
        written_size = os.path.getsize(output_path)
        if written_size != len(self.original_data):
            raise RuntimeError(
                f"SAFETY ERROR: Written file size ({written_size}) does not match "
                f"original ({len(self.original_data)}). File may be corrupted."
            )

        return output_path

    def get_byte(self, address: int) -> int:
        """Get a single byte at the given address."""
        if address < 0 or address >= self.file_size:
            raise IndexError(f"Address 0x{address:X} out of range (file size: 0x{self.file_size:X})")
        return self.data[address]

    def set_byte(self, address: int, value: int) -> None:
        """Set a single byte at the given address."""
        if address < 0 or address >= self.file_size:
            raise IndexError(f"Address 0x{address:X} out of range")
        if value < 0 or value > 0xFF:
            raise ValueError(f"Byte value must be 0x00-0xFF, got 0x{value:X}")
        self.data[address] = value

    def get_bytes(self, start: int, length: int) -> bytearray:
        """Get a range of bytes starting at the given address."""
        if start < 0 or start + length > self.file_size:
            raise IndexError(f"Range 0x{start:X}-0x{start + length:X} out of bounds")
        return self.data[start:start + length]

    def set_bytes(self, start: int, values: bytes) -> None:
        """Set a range of bytes starting at the given address."""
        end = start + len(values)
        if start < 0 or end > self.file_size:
            raise IndexError(f"Range 0x{start:X}-0x{end:X} out of bounds")
        self.data[start:end] = values

    def find_pattern(self, pattern: bytes, start: int = 0) -> list[int]:
        """Find all occurrences of a byte pattern in the data."""
        results: list[int] = []
        search_start = start
        while True:
            pos = self.data.find(pattern, search_start)
            if pos == -1:
                break
            results.append(pos)
            search_start = pos + 1
        return results

    def find_pattern_with_mask(self, pattern: bytes, mask: bytes, start: int = 0) -> list[int]:
        """
        Find pattern with wildcard mask.
        Mask byte 0xFF = must match, 0x00 = wildcard (any byte).
        """
        if len(pattern) != len(mask):
            raise ValueError("Pattern and mask must be the same length")

        results: list[int] = []
        pat_len = len(pattern)

        for i in range(start, self.file_size - pat_len + 1):
            match = True
            for j in range(pat_len):
                if mask[j] == 0xFF and self.data[i + j] != pattern[j]:
                    match = False
                    break
            if match:
                results.append(i)

        return results

    def get_word_le(self, address: int) -> int:
        """Get a 16-bit little-endian word at the given address."""
        data = self.get_bytes(address, 2)
        return data[0] | (data[1] << 8)

    def get_word_be(self, address: int) -> int:
        """Get a 16-bit big-endian word at the given address."""
        data = self.get_bytes(address, 2)
        return (data[0] << 8) | data[1]

    def get_dword_le(self, address: int) -> int:
        """Get a 32-bit little-endian double word at the given address."""
        data = self.get_bytes(address, 4)
        return data[0] | (data[1] << 8) | (data[2] << 16) | (data[3] << 24)

    def get_dword_be(self, address: int) -> int:
        """Get a 32-bit big-endian double word at the given address."""
        data = self.get_bytes(address, 4)
        return (data[0] << 24) | (data[1] << 16) | (data[2] << 8) | data[3]

    def get_changes(self) -> list[dict]:
        """Compare current data with original and return list of changes."""
        changes: list[dict] = []
        for i in range(self.file_size):
            if self.data[i] != self.original_data[i]:
                changes.append({
                    "address": i,
                    "original": self.original_data[i],
                    "modified": self.data[i],
                })
        return changes

    def reset_to_original(self) -> None:
        """Reset data back to the original loaded state."""
        self.data = bytearray(self.original_data)

    def get_hex_dump(self, start: int, length: int, bytes_per_line: int = 16) -> str:
        """Generate a formatted hex dump of a region."""
        lines: list[str] = []
        end = min(start + length, self.file_size)

        for offset in range(start, end, bytes_per_line):
            chunk = self.data[offset:min(offset + bytes_per_line, end)]
            hex_part = " ".join(f"{b:02X}" for b in chunk)
            ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
            lines.append(f"0x{offset:08X}: {hex_part:<{bytes_per_line * 3}}  {ascii_part}")

        return "\n".join(lines)
