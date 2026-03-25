"""
Metadata Extractor Module - Input & Identification Layer
Extracts ECU type, software ID, VIN, and other metadata from binary files.
"""

import re
from typing import Optional


class MetadataExtractor:
    """Extracts metadata from ECU binary data by analyzing strings and patterns."""

    # Known ECU manufacturer identifiers
    ECU_MANUFACTURERS = {
        b"BOSCH": "Bosch",
        b"Bosch": "Bosch",
        b"EDC15": "Bosch EDC15",
        b"EDC16": "Bosch EDC16",
        b"EDC17": "Bosch EDC17",
        b"MED17": "Bosch MED17",
        b"ME7": "Bosch ME7",
        b"MED9": "Bosch MED9",
        b"DELPHI": "Delphi",
        b"Delphi": "Delphi",
        b"DCM3": "Delphi DCM3",
        b"DCM6": "Delphi DCM6",
        b"SIEMENS": "Siemens",
        b"Siemens": "Siemens",
        b"SID301": "Siemens SID301",
        b"SID803": "Siemens SID803",
        b"SID206": "Siemens SID206",
        b"CONTINENTAL": "Continental",
        b"Continental": "Continental",
        b"SIMOS": "Siemens/Continental SIMOS",
        b"PCR2": "Continental PCR2",
        b"DENSO": "Denso",
        b"Denso": "Denso",
        b"MARELLI": "Magneti Marelli",
        b"Marelli": "Magneti Marelli",
        b"IAW": "Magneti Marelli IAW",
        b"HITACHI": "Hitachi",
    }

    # VIN pattern: 17 alphanumeric characters (excluding I, O, Q)
    VIN_PATTERN = re.compile(rb"[A-HJ-NPR-Z0-9]{17}")

    # Software version patterns
    SW_PATTERNS = [
        re.compile(rb"SW:\s*([A-Za-z0-9._\-]+)"),
        re.compile(rb"SW[_\s]?[Vv]ersion[:\s]*([A-Za-z0-9._\-]+)"),
        re.compile(rb"(\d{3}\.\d{3}\.\d{3})"),  # Common Bosch format
        re.compile(rb"([A-Z]{2}\d{2}\.\d{2}\.\d{2})"),  # Continental format
    ]

    # Hardware number patterns
    HW_PATTERNS = [
        re.compile(rb"HW:\s*([A-Za-z0-9._\-]+)"),
        re.compile(rb"HW[_\s]?[Vv]ersion[:\s]*([A-Za-z0-9._\-]+)"),
        re.compile(rb"(\d{3}\s?\d{3}\s?\d{3}\s?[A-Z]?)"),  # VAG part number
    ]

    def __init__(self, data: bytearray) -> None:
        self.data = data
        self.strings: list[str] = []
        self._extract_strings()

    def _extract_strings(self, min_length: int = 4) -> None:
        """Extract printable ASCII strings from binary data."""
        current: list[int] = []
        for byte in self.data:
            if 32 <= byte < 127:
                current.append(byte)
            else:
                if len(current) >= min_length:
                    self.strings.append(bytes(current).decode("ascii"))
                current = []
        if len(current) >= min_length:
            self.strings.append(bytes(current).decode("ascii"))

    def detect_ecu_type(self) -> str:
        """Detect the ECU manufacturer and type from binary data."""
        detected: list[str] = []

        # Search for known manufacturer identifiers
        for marker, name in self.ECU_MANUFACTURERS.items():
            if marker in self.data:
                if name not in detected:
                    detected.append(name)

        if detected:
            # Return the most specific match (longest name)
            return max(detected, key=len)
        return "Unknown ECU"

    def extract_vin(self) -> Optional[str]:
        """Extract VIN (Vehicle Identification Number) from binary data."""
        matches = self.VIN_PATTERN.findall(self.data)
        for match in matches:
            vin = match.decode("ascii")
            # Basic VIN validation: check digit position and common prefixes
            if self._validate_vin(vin):
                return vin
        return None

    def _validate_vin(self, vin: str) -> bool:
        """Basic VIN validation."""
        if len(vin) != 17:
            return False
        # Check that it's not all same characters (likely padding)
        if len(set(vin)) < 5:
            return False
        # Common VIN prefixes for major manufacturers
        valid_prefixes = [
            "WVW", "WAU", "WBA", "WDB", "WDD", "WF0",  # German
            "1G", "2G", "3G", "1F", "2F", "1H", "1N",   # North American
            "JT", "JN", "JM", "JH",                      # Japanese
            "SAL", "SAJ", "SAR",                          # British
            "ZAR", "ZFA", "ZLA",                          # Italian
            "VF1", "VF3", "VF7",                          # French
            "KMH", "KNA", "KNM",                          # Korean
            "TRU", "TMB",                                  # Czech
        ]
        for prefix in valid_prefixes:
            if vin.startswith(prefix):
                return True
        # If no known prefix, still accept if it looks valid
        return vin[0].isalpha()

    def extract_software_id(self) -> Optional[str]:
        """Extract software version/ID from binary data."""
        for pattern in self.SW_PATTERNS:
            matches = pattern.findall(self.data)
            if matches:
                return matches[0].decode("ascii")
        return None

    def extract_hardware_id(self) -> Optional[str]:
        """Extract hardware version/part number from binary data."""
        for pattern in self.HW_PATTERNS:
            matches = pattern.findall(self.data)
            if matches:
                return matches[0].decode("ascii")
        return None

    def get_file_info(self) -> dict:
        """Get comprehensive file information."""
        return {
            "file_size": len(self.data),
            "ecu_type": self.detect_ecu_type(),
            "vin": self.extract_vin(),
            "software_id": self.extract_software_id(),
            "hardware_id": self.extract_hardware_id(),
            "string_count": len(self.strings),
        }

    def get_strings_containing(self, keyword: str) -> list[str]:
        """Return all extracted strings containing the given keyword."""
        keyword_lower = keyword.lower()
        return [s for s in self.strings if keyword_lower in s.lower()]
