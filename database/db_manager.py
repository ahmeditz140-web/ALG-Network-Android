"""
Database Manager - Knowledge Base Layer
SQLite database for storing ECU definitions, DTC codes, switches, and patterns.
"""

import os
import sqlite3
from typing import Optional


class DatabaseManager:
    """Manages the SQLite knowledge base for ECU tuning data."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "andols.db")
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Connect to the database and initialize tables."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._populate_defaults()

    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        if self.conn is None:
            raise RuntimeError("Database not connected")

        cursor = self.conn.cursor()

        # ECU Definitions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ecu_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manufacturer TEXT NOT NULL,
                ecu_model TEXT NOT NULL,
                vehicle TEXT,
                engine TEXT,
                file_size INTEGER,
                header_pattern TEXT,
                description TEXT
            )
        """)

        # DTC Codes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dtc_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dtc_code TEXT NOT NULL,
                description TEXT,
                system TEXT,
                hex_pattern TEXT,
                category TEXT
            )
        """)

        # DTC Addresses per ECU
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dtc_addresses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ecu_id INTEGER,
                dtc_id INTEGER,
                address INTEGER,
                enable_value INTEGER DEFAULT 1,
                disable_value INTEGER DEFAULT 0,
                FOREIGN KEY (ecu_id) REFERENCES ecu_definitions(id),
                FOREIGN KEY (dtc_id) REFERENCES dtc_codes(id)
            )
        """)

        # System Switches table (EGR, DPF, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_switches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ecu_id INTEGER,
                system_name TEXT NOT NULL,
                search_pattern TEXT NOT NULL,
                replace_pattern TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (ecu_id) REFERENCES ecu_definitions(id)
            )
        """)

        # Search Patterns table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ecu_id INTEGER,
                pattern_name TEXT NOT NULL,
                search_hex TEXT NOT NULL,
                replace_hex TEXT NOT NULL,
                category TEXT,
                description TEXT,
                FOREIGN KEY (ecu_id) REFERENCES ecu_definitions(id)
            )
        """)

        # Tuning Maps table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tuning_maps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ecu_id INTEGER,
                map_name TEXT NOT NULL,
                map_start_address INTEGER,
                map_length INTEGER,
                value_size INTEGER DEFAULT 2,
                axis_x_label TEXT,
                axis_y_label TEXT,
                value_unit TEXT,
                description TEXT,
                FOREIGN KEY (ecu_id) REFERENCES ecu_definitions(id)
            )
        """)

        # Stage Profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stage_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ecu_id INTEGER,
                stage_name TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (ecu_id) REFERENCES ecu_definitions(id)
            )
        """)

        # Stage Operations table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stage_operations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stage_id INTEGER,
                map_id INTEGER,
                operation_type TEXT NOT NULL,
                value REAL NOT NULL,
                description TEXT,
                FOREIGN KEY (stage_id) REFERENCES stage_profiles(id),
                FOREIGN KEY (map_id) REFERENCES tuning_maps(id)
            )
        """)

        # Checksum Definitions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS checksum_definitions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ecu_id INTEGER,
                block_name TEXT,
                block_start INTEGER NOT NULL,
                block_length INTEGER NOT NULL,
                checksum_address INTEGER NOT NULL,
                algorithm TEXT NOT NULL DEFAULT 'crc32',
                FOREIGN KEY (ecu_id) REFERENCES ecu_definitions(id)
            )
        """)

        self.conn.commit()

    def _populate_defaults(self) -> None:
        """Populate default data if tables are empty."""
        if self.conn is None:
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dtc_codes")
        count = cursor.fetchone()[0]

        if count > 0:
            return

        # Default DTC codes
        dtc_defaults = [
            ("P0401", "EGR Flow Insufficient", "EGR", "0401", "Emissions"),
            ("P0402", "EGR Flow Excessive", "EGR", "0402", "Emissions"),
            ("P0403", "EGR Control Circuit", "EGR", "0403", "Emissions"),
            ("P0404", "EGR Control Circuit Range/Performance", "EGR", "0404", "Emissions"),
            ("P0420", "Catalyst Efficiency Below Threshold Bank 1", "Catalyst", "0420", "Emissions"),
            ("P0421", "Warm Up Catalyst Efficiency Below Threshold Bank 1", "Catalyst", "0421", "Emissions"),
            ("P0430", "Catalyst Efficiency Below Threshold Bank 2", "Catalyst", "0430", "Emissions"),
            ("P2002", "DPF Efficiency Below Threshold", "DPF", "2002", "Emissions"),
            ("P2463", "DPF Soot Accumulation", "DPF", "2463", "Emissions"),
            ("P244A", "DPF Differential Pressure Too Low", "DPF", "244A", "Emissions"),
            ("P244B", "DPF Differential Pressure Too High", "DPF", "244B", "Emissions"),
            ("P2BAE", "NOx Catalyst Efficiency Below Threshold", "SCR", "2BAE", "Emissions"),
            ("P0234", "Turbocharger Overboost Condition", "Turbo", "0234", "Performance"),
            ("P0235", "Turbocharger Boost Sensor A Circuit", "Turbo", "0235", "Performance"),
            ("P0299", "Turbocharger Underboost Condition", "Turbo", "0299", "Performance"),
            ("P0546", "Exhaust Gas Temperature Sensor High Bank 1", "EGT", "0546", "Emissions"),
            ("P0545", "Exhaust Gas Temperature Sensor Low Bank 1", "EGT", "0545", "Emissions"),
            ("P1250", "Fuel Pressure Regulator Control Circuit", "Fuel", "1250", "Fuel"),
            ("P0087", "Fuel Rail Pressure Too Low", "Fuel", "0087", "Fuel"),
            ("P0088", "Fuel Rail Pressure Too High", "Fuel", "0088", "Fuel"),
            ("P0100", "MAF Circuit Malfunction", "MAF", "0100", "Sensor"),
            ("P0101", "MAF Circuit Range/Performance", "MAF", "0101", "Sensor"),
            ("P0110", "IAT Sensor Circuit Malfunction", "IAT", "0110", "Sensor"),
            ("P0115", "ECT Sensor Circuit Malfunction", "ECT", "0115", "Sensor"),
            ("P0170", "Fuel Trim Malfunction Bank 1", "Lambda", "0170", "Fuel"),
            ("P0171", "System Too Lean Bank 1", "Lambda", "0171", "Fuel"),
            ("P0172", "System Too Rich Bank 1", "Lambda", "0172", "Fuel"),
            ("P0130", "O2 Sensor Circuit Bank 1 Sensor 1", "Lambda", "0130", "Sensor"),
            ("P0135", "O2 Sensor Heater Circuit Bank 1 Sensor 1", "Lambda", "0135", "Sensor"),
            ("P0480", "Fan 1 Control Circuit", "Cooling", "0480", "Cooling"),
            ("P0500", "Vehicle Speed Sensor", "VSS", "0500", "Sensor"),
            ("P0600", "Serial Communication Link", "CAN", "0600", "Communication"),
            ("P0650", "MIL Control Circuit", "MIL", "0650", "General"),
        ]

        cursor.executemany(
            "INSERT INTO dtc_codes (dtc_code, description, system, hex_pattern, category) "
            "VALUES (?, ?, ?, ?, ?)",
            dtc_defaults,
        )

        # Default ECU definitions
        ecu_defaults = [
            ("Bosch", "EDC17C64", "VW/Audi", "2.0 TDI CR", 2097152, "EDC17C64", "Common Rail Diesel ECU"),
            ("Bosch", "EDC17C46", "VW/Audi", "2.0 TDI CR", 2097152, "EDC17C46", "Common Rail Diesel ECU"),
            ("Bosch", "EDC17CP14", "BMW", "2.0d N47", 2097152, "EDC17CP14", "BMW Diesel ECU"),
            ("Bosch", "EDC17C50", "BMW", "2.0d N47", 2097152, "EDC17C50", "BMW Diesel ECU"),
            ("Bosch", "MED17.5", "VW/Audi", "2.0 TSI", 2097152, "MED17.5", "Direct Injection Gasoline ECU"),
            ("Bosch", "ME7.5", "VW/Audi", "1.8T", 1048576, "ME7.5", "Gasoline ECU"),
            ("Bosch", "EDC16C39", "Fiat", "1.3 JTD", 1048576, "EDC16C39", "Diesel ECU"),
            ("Bosch", "EDC17C42", "Renault", "1.5 dCi", 2097152, "EDC17C42", "Diesel ECU"),
            ("Bosch", "EDC17CP57", "Mercedes", "2.1 CDI", 2097152, "EDC17CP57", "Diesel ECU"),
            ("Continental", "SID206", "Ford", "1.6 TDCi", 1048576, "SID206", "Diesel ECU"),
            ("Continental", "SIMOS18", "VW/Audi", "2.0 TSI EA888", 4194304, "SIMOS18", "Gasoline ECU"),
            ("Delphi", "DCM3.5", "Renault", "1.5 dCi", 1048576, "DCM3.5", "Diesel ECU"),
            ("Denso", "SH7058", "Subaru", "2.5T", 1048576, "SH7058", "Gasoline ECU"),
        ]

        cursor.executemany(
            "INSERT INTO ecu_definitions "
            "(manufacturer, ecu_model, vehicle, engine, file_size, header_pattern, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            ecu_defaults,
        )

        self.conn.commit()

    # ── Query Methods ──

    def get_all_dtc_codes(self) -> list[dict]:
        """Get all DTC codes from the database."""
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM dtc_codes ORDER BY dtc_code")
        return [dict(row) for row in cursor.fetchall()]

    def get_dtc_by_code(self, dtc_code: str) -> Optional[dict]:
        """Get a specific DTC by its code."""
        if self.conn is None:
            return None
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM dtc_codes WHERE dtc_code = ?", (dtc_code,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_dtc_by_system(self, system: str) -> list[dict]:
        """Get all DTCs for a specific system (EGR, DPF, etc.)."""
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM dtc_codes WHERE system = ? ORDER BY dtc_code", (system,))
        return [dict(row) for row in cursor.fetchall()]

    def get_dtc_by_category(self, category: str) -> list[dict]:
        """Get all DTCs for a specific category."""
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM dtc_codes WHERE category = ? ORDER BY dtc_code",
            (category,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_all_ecu_definitions(self) -> list[dict]:
        """Get all ECU definitions."""
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM ecu_definitions ORDER BY manufacturer, ecu_model")
        return [dict(row) for row in cursor.fetchall()]

    def get_ecu_by_model(self, ecu_model: str) -> Optional[dict]:
        """Get ECU definition by model name."""
        if self.conn is None:
            return None
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM ecu_definitions WHERE ecu_model = ?", (ecu_model,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_switches_for_ecu(self, ecu_id: int) -> list[dict]:
        """Get all system switches for an ECU."""
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM system_switches WHERE ecu_id = ? ORDER BY system_name",
            (ecu_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_patterns_for_ecu(self, ecu_id: int) -> list[dict]:
        """Get all search patterns for an ECU."""
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM search_patterns WHERE ecu_id = ? ORDER BY pattern_name",
            (ecu_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_tuning_maps_for_ecu(self, ecu_id: int) -> list[dict]:
        """Get all tuning maps for an ECU."""
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM tuning_maps WHERE ecu_id = ? ORDER BY map_name",
            (ecu_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_checksum_defs_for_ecu(self, ecu_id: int) -> list[dict]:
        """Get checksum definitions for an ECU."""
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM checksum_definitions WHERE ecu_id = ? ORDER BY block_name",
            (ecu_id,),
        )
        return [dict(row) for row in cursor.fetchall()]

    def search_dtc(self, query: str) -> list[dict]:
        """Search DTC codes by code or description."""
        if self.conn is None:
            return []
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM dtc_codes WHERE dtc_code LIKE ? OR description LIKE ? ORDER BY dtc_code",
            (f"%{query}%", f"%{query}%"),
        )
        return [dict(row) for row in cursor.fetchall()]

    # ── Insert Methods ──

    def add_dtc_code(
        self, dtc_code: str, description: str, system: str, hex_pattern: str, category: str
    ) -> int:
        """Add a new DTC code. Returns the new row ID."""
        if self.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO dtc_codes (dtc_code, description, system, hex_pattern, category) "
            "VALUES (?, ?, ?, ?, ?)",
            (dtc_code, description, system, hex_pattern, category),
        )
        self.conn.commit()
        return cursor.lastrowid or 0

    def add_ecu_definition(
        self,
        manufacturer: str,
        ecu_model: str,
        vehicle: str,
        engine: str,
        file_size: int,
        header_pattern: str,
        description: str,
    ) -> int:
        """Add a new ECU definition. Returns the new row ID."""
        if self.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO ecu_definitions "
            "(manufacturer, ecu_model, vehicle, engine, file_size, header_pattern, description) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (manufacturer, ecu_model, vehicle, engine, file_size, header_pattern, description),
        )
        self.conn.commit()
        return cursor.lastrowid or 0

    def add_switch(
        self,
        ecu_id: int,
        system_name: str,
        search_pattern: str,
        replace_pattern: str,
        description: str = "",
    ) -> int:
        """Add a system switch entry."""
        if self.conn is None:
            raise RuntimeError("Database not connected")
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO system_switches "
            "(ecu_id, system_name, search_pattern, replace_pattern, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (ecu_id, system_name, search_pattern, replace_pattern, description),
        )
        self.conn.commit()
        return cursor.lastrowid or 0
