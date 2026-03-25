"""
Processing Engine - The core logic for ECU tuning operations.
Handles search & replace, DTC removal, and Stage tuning.
"""

from typing import Optional


class ProcessingEngine:
    """
    Main processing engine for ECU binary modifications.
    Implements search & replace, DTC removal, and tuning operations.
    """

    def __init__(self, data: bytearray) -> None:
        self.data = data
        self.operations_log: list[dict] = []

    def search_and_replace(
        self,
        search_pattern: bytes,
        replace_pattern: bytes,
        max_replacements: int = 0,
    ) -> int:
        """
        Search for a byte pattern and replace with new bytes.
        max_replacements=0 means replace all occurrences.
        Returns number of replacements made.
        """
        if len(search_pattern) != len(replace_pattern):
            raise ValueError(
                "Search and replace patterns must be the same length "
                "to maintain file size integrity"
            )

        count = 0
        pos = 0
        while True:
            idx = self.data.find(search_pattern, pos)
            if idx == -1:
                break

            # Log the operation
            self.operations_log.append({
                "type": "search_replace",
                "address": idx,
                "original": bytes(self.data[idx:idx + len(search_pattern)]),
                "modified": replace_pattern,
            })

            self.data[idx:idx + len(search_pattern)] = replace_pattern
            count += 1
            pos = idx + len(replace_pattern)

            if max_replacements > 0 and count >= max_replacements:
                break

        return count

    def remove_dtc(self, dtc_code: str, dtc_table_entries: list[dict]) -> bool:
        """
        Remove a DTC (Diagnostic Trouble Code) from the binary.

        dtc_code: e.g. "P0401"
        dtc_table_entries: list of dicts with 'address', 'enable_byte', 'enable_value', 'disable_value'
        """
        for entry in dtc_table_entries:
            if entry.get("dtc_code") == dtc_code:
                address = entry["address"]
                disable_value = entry.get("disable_value", 0x00)

                if address < len(self.data):
                    original = self.data[address]
                    self.data[address] = disable_value

                    self.operations_log.append({
                        "type": "dtc_remove",
                        "dtc_code": dtc_code,
                        "address": address,
                        "original": original,
                        "modified": disable_value,
                    })
                    return True

        return False

    def remove_dtc_by_pattern(
        self,
        dtc_hex: bytes,
        dtc_table_start: int = -1,
        dtc_table_end: int = -1,
    ) -> int:
        """
        Remove DTC by searching for its hex pattern in the DTC table.
        Sets the enable flag byte (typically following the DTC ID) to 0x00.
        Returns number of DTCs disabled.

        SAFETY: If dtc_table_start/dtc_table_end are provided, only searches
        within that region. Otherwise searches the full file but limits
        modifications and logs warnings.
        """
        if len(dtc_hex) < 2:
            raise ValueError("DTC hex pattern must be at least 2 bytes")

        count = 0
        search_start = dtc_table_start if dtc_table_start >= 0 else 0
        search_end = dtc_table_end if dtc_table_end >= 0 else len(self.data)

        # Safety: track how many matches we find to warn about excessive matches
        max_safe_modifications = 50
        pos = search_start

        while pos < search_end:
            idx = self.data.find(dtc_hex, pos, search_end)
            if idx == -1:
                break

            # The enable/disable byte is typically right after the DTC code
            flag_offset = idx + len(dtc_hex)
            if flag_offset < len(self.data):
                original = self.data[flag_offset]
                if original != 0x00:  # Only modify if not already disabled
                    self.data[flag_offset] = 0x00
                    self.operations_log.append({
                        "type": "dtc_pattern_remove",
                        "address": idx,
                        "flag_address": flag_offset,
                        "original_flag": original,
                        "modified_flag": 0x00,
                    })
                    count += 1

                    # Safety limit to prevent mass corruption
                    if count >= max_safe_modifications:
                        self.operations_log.append({
                            "type": "warning",
                            "message": f"DTC removal stopped at {count} matches (safety limit). "
                                       f"Pattern may be too common.",
                        })
                        break

            pos = idx + len(dtc_hex)

        return count

    def disable_system_by_pattern(
        self,
        system_name: str,
        search_pattern: bytes,
        disable_pattern: bytes,
    ) -> bool:
        """
        Disable an ECU system (EGR, DPF, etc.) by pattern matching.
        """
        idx = self.data.find(search_pattern)
        if idx == -1:
            return False

        if len(search_pattern) != len(disable_pattern):
            raise ValueError("Patterns must be same length")

        original = bytes(self.data[idx:idx + len(search_pattern)])
        self.data[idx:idx + len(search_pattern)] = disable_pattern

        self.operations_log.append({
            "type": "system_disable",
            "system": system_name,
            "address": idx,
            "original": original,
            "modified": disable_pattern,
        })
        return True

    def apply_map_multiplier(
        self,
        map_start: int,
        map_length: int,
        multiplier: float,
        value_size: int = 2,
        max_value: Optional[int] = None,
    ) -> int:
        """
        Apply a percentage multiplier to a map/table.
        Used for Stage 1 tuning (e.g., boost map +10%).

        value_size: 1 for byte values, 2 for word values
        max_value: maximum allowed value (safety limit)
        Returns number of values modified.
        """
        if value_size not in (1, 2):
            raise ValueError(f"value_size must be 1 or 2, got {value_size}")
        if multiplier <= 0:
            raise ValueError(f"multiplier must be positive, got {multiplier}")
        if max_value is None:
            max_value = (2 ** (value_size * 8)) - 1

        # Calculate safe end boundary aligned to value_size
        data_end = min(map_start + map_length, len(self.data))
        # Ensure we don't read past the data boundary
        safe_end = data_end - (value_size - 1)

        count = 0
        for offset in range(map_start, safe_end, value_size):
            if value_size == 1:
                original = self.data[offset]
                new_val = int(original * multiplier)
                new_val = max(0, min(new_val, max_value))
                self.data[offset] = new_val
            elif value_size == 2:
                original = (self.data[offset] << 8) | self.data[offset + 1]
                new_val = int(original * multiplier)
                new_val = max(0, min(new_val, max_value))
                self.data[offset] = (new_val >> 8) & 0xFF
                self.data[offset + 1] = new_val & 0xFF
            count += 1

        self.operations_log.append({
            "type": "map_multiplier",
            "map_start": map_start,
            "map_length": map_length,
            "multiplier": multiplier,
            "values_modified": count,
        })
        return count

    def apply_map_offset(
        self,
        map_start: int,
        map_length: int,
        offset_value: int,
        value_size: int = 2,
        max_value: Optional[int] = None,
    ) -> int:
        """
        Apply an additive offset to a map/table.
        Used for injection timing adjustments, etc.
        """
        if value_size not in (1, 2):
            raise ValueError(f"value_size must be 1 or 2, got {value_size}")
        if max_value is None:
            max_value = (2 ** (value_size * 8)) - 1

        # Calculate safe end boundary aligned to value_size
        data_end = min(map_start + map_length, len(self.data))
        safe_end = data_end - (value_size - 1)

        count = 0
        for offset in range(map_start, safe_end, value_size):
            if value_size == 1:
                original = self.data[offset]
                new_val = original + offset_value
                new_val = max(0, min(new_val, max_value))
                self.data[offset] = new_val
            elif value_size == 2:
                original = (self.data[offset] << 8) | self.data[offset + 1]
                new_val = original + offset_value
                new_val = max(0, min(new_val, max_value))
                self.data[offset] = (new_val >> 8) & 0xFF
                self.data[offset + 1] = new_val & 0xFF
            count += 1

        self.operations_log.append({
            "type": "map_offset",
            "map_start": map_start,
            "map_length": map_length,
            "offset": offset_value,
            "values_modified": count,
        })
        return count

    def zero_fill(self, start: int, length: int) -> None:
        """Fill a region with zeros (used for DPF/EGR map blanking)."""
        end = min(start + length, len(self.data))
        original = bytes(self.data[start:end])
        for i in range(start, end):
            self.data[i] = 0x00

        self.operations_log.append({
            "type": "zero_fill",
            "address": start,
            "length": end - start,
            "original_sample": original[:16],
        })

    def fill_value(self, start: int, length: int, value: int) -> None:
        """Fill a region with a specific byte value."""
        end = min(start + length, len(self.data))
        for i in range(start, end):
            self.data[i] = value & 0xFF

        self.operations_log.append({
            "type": "fill_value",
            "address": start,
            "length": end - start,
            "value": value,
        })

    def get_operations_log(self) -> list[dict]:
        """Return the log of all operations performed."""
        return self.operations_log.copy()

    def clear_log(self) -> None:
        """Clear the operations log."""
        self.operations_log.clear()
