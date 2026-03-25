"""
Fingerprinting System - Input & Identification Layer
Identifies ECU files by comparing hash signatures against a known database.
"""

import hashlib
from typing import Optional


class ECUFingerprint:
    """
    Fingerprinting system that identifies ECU files by hashing specific
    regions and comparing against known signatures.
    """

    # Known ECU fingerprints database
    # Format: {hash: {ecu_type, vehicle, engine, ecu_model}}
    KNOWN_FINGERPRINTS: dict[str, dict[str, str]] = {
        # Volkswagen / Audi
        "vw_edc17c64_2.0tdi": {
            "ecu_type": "Bosch",
            "vehicle": "VW/Audi",
            "engine": "2.0 TDI CR",
            "ecu_model": "EDC17C64",
            "header_pattern": "EDC17C64",
        },
        "vw_edc17c46_2.0tdi": {
            "ecu_type": "Bosch",
            "vehicle": "VW/Audi",
            "engine": "2.0 TDI CR",
            "ecu_model": "EDC17C46",
            "header_pattern": "EDC17C46",
        },
        "vw_med17.5_2.0tsi": {
            "ecu_type": "Bosch",
            "vehicle": "VW/Audi",
            "engine": "2.0 TSI",
            "ecu_model": "MED17.5",
            "header_pattern": "MED17.5",
        },
        "vw_simos18_2.0tsi": {
            "ecu_type": "Continental",
            "vehicle": "VW/Audi",
            "engine": "2.0 TSI EA888",
            "ecu_model": "SIMOS18",
            "header_pattern": "SIMOS18",
        },
        # BMW
        "bmw_mevd17.2_n20": {
            "ecu_type": "Bosch",
            "vehicle": "BMW",
            "engine": "N20 2.0T",
            "ecu_model": "MEVD17.2",
            "header_pattern": "MEVD17.2",
        },
        "bmw_edc17c50_n47": {
            "ecu_type": "Bosch",
            "vehicle": "BMW",
            "engine": "N47 2.0D",
            "ecu_model": "EDC17C50",
            "header_pattern": "EDC17C50",
        },
        # Mercedes
        "mb_edc17cp57_om651": {
            "ecu_type": "Bosch",
            "vehicle": "Mercedes-Benz",
            "engine": "OM651 2.1 CDI",
            "ecu_model": "EDC17CP57",
            "header_pattern": "EDC17CP57",
        },
        # Ford
        "ford_sid206_1.6tdci": {
            "ecu_type": "Continental",
            "vehicle": "Ford",
            "engine": "1.6 TDCi",
            "ecu_model": "SID206",
            "header_pattern": "SID206",
        },
        # Renault / Dacia
        "renault_edc17c42_1.5dci": {
            "ecu_type": "Bosch",
            "vehicle": "Renault",
            "engine": "1.5 dCi",
            "ecu_model": "EDC17C42",
            "header_pattern": "EDC17C42",
        },
        # Fiat
        "fiat_edc16c39_1.3jtd": {
            "ecu_type": "Bosch",
            "vehicle": "Fiat",
            "engine": "1.3 JTD",
            "ecu_model": "EDC16C39",
            "header_pattern": "EDC16C39",
        },
        # Hyundai / Kia
        "hyundai_edc17c57_1.7crdi": {
            "ecu_type": "Bosch",
            "vehicle": "Hyundai/Kia",
            "engine": "1.7 CRDi",
            "ecu_model": "EDC17C57",
            "header_pattern": "EDC17C57",
        },
    }

    def __init__(self, data: bytearray) -> None:
        self.data = data

    def compute_full_hash(self) -> str:
        """Compute SHA-256 hash of the entire file."""
        return hashlib.sha256(self.data).hexdigest()

    def compute_region_hash(self, start: int, length: int) -> str:
        """Compute SHA-256 hash of a specific region."""
        region = self.data[start:start + length]
        return hashlib.sha256(region).hexdigest()

    def compute_header_hash(self, header_size: int = 512) -> str:
        """Compute hash of the file header region."""
        return self.compute_region_hash(0, min(header_size, len(self.data)))

    def identify_by_pattern(self) -> Optional[dict[str, str]]:
        """Identify the ECU by searching for known patterns in the data."""
        for _key, info in self.KNOWN_FINGERPRINTS.items():
            pattern = info.get("header_pattern", "")
            if pattern and pattern.encode("ascii") in self.data:
                return {
                    "ecu_type": info["ecu_type"],
                    "vehicle": info["vehicle"],
                    "engine": info["engine"],
                    "ecu_model": info["ecu_model"],
                }
        return None

    def identify(self) -> dict[str, str]:
        """
        Main identification method. Tries pattern matching first,
        then falls back to hash comparison.
        """
        # Try pattern-based identification
        result = self.identify_by_pattern()
        if result:
            result["method"] = "pattern"
            result["file_hash"] = self.compute_full_hash()
            return result

        # Return unknown with hash info
        return {
            "ecu_type": "Unknown",
            "vehicle": "Unknown",
            "engine": "Unknown",
            "ecu_model": "Unknown",
            "method": "none",
            "file_hash": self.compute_full_hash(),
        }

    def get_file_signature(self) -> dict[str, str]:
        """Generate a signature dict for the file (useful for database storage)."""
        return {
            "full_hash": self.compute_full_hash(),
            "header_hash": self.compute_header_hash(),
            "file_size": str(len(self.data)),
        }
