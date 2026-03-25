# Andols ECU Tuning Tool

Professional ECU binary tuning desktop application built with Python and PyQt5.

## Features

### 1. Input & Identification Layer
- **Binary Reader**: Load and parse `.bin` ECU files
- **Metadata Extractor**: Auto-detect ECU type (Bosch, Delphi, Siemens, Continental, Denso), software ID, VIN
- **Fingerprinting System**: Identify ECU by pattern matching and hash comparison

### 2. Knowledge Base
- **DTC Database**: 30+ pre-loaded diagnostic trouble codes (P0401, P2002, P0420, etc.)
- **ECU Definitions**: 13+ ECU models (EDC17, MED17, SID206, SIMOS18, etc.)
- **System Switches**: Configurable patterns for EGR, DPF, Lambda, AdBlue, and more
- **Search Patterns**: Hex pattern matching that works across firmware versions

### 3. Processing Engine
- **Search & Replace**: Pattern-based byte replacement with file size integrity
- **DTC Remover**: Remove individual or all DTCs by code or hex pattern
- **Stage 1 Tuning**: Configurable boost, fuel, torque, and rail pressure adjustments
- **System Disable**: One-click DPF Off, EGR Off, Lambda Off, AdBlue Off, CAT Off, Speed Limit Off

### 4. Integrity Layer
- **Checksum Calculator**: CRC32, CRC16, additive sum, XOR, and complement algorithms
- **Validation Engine**: Safety limits for boost pressure, injection, rail pressure, RPM, torque
- **File Size Protection**: Ensures modifications don't change file size

### 5. User Interface
- **Dashboard**: Color-coded buttons for quick tuning actions
- **Hex Viewer**: Side-by-side before/after comparison with diff highlighting
- **Operations Log**: Real-time log of all modifications
- **Dark Theme**: Professional dark UI design

## Quick Start

### Requirements
- Python 3.10+
- PyQt5

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run the Application
```bash
python main.py
```

### Build Windows EXE
```bash
pyinstaller andols.spec
```
The executable will be created in the `dist/` folder as `Andols_ECU_Tool.exe`.

## Project Structure
```
andols-ecu-tool/
├── main.py                    # Application entry point
├── andols.spec                # PyInstaller build spec
├── requirements.txt           # Python dependencies
├── core/
│   ├── binary_reader.py       # Binary file I/O
│   ├── metadata_extractor.py  # ECU metadata extraction
│   ├── fingerprint.py         # ECU identification
│   ├── processing_engine.py   # Tuning operations engine
│   └── checksum.py            # Checksum & validation
├── database/
│   └── db_manager.py          # SQLite knowledge base
└── ui/
    ├── main_window.py         # Main application window
    ├── dashboard.py           # Tuning controls dashboard
    └── hex_viewer.py          # Hex viewer with diff
```

## Supported ECU Types
| Manufacturer | Models |
|---|---|
| Bosch | EDC15, EDC16, EDC17, MED17, ME7, MED9 |
| Continental/Siemens | SIMOS18, SID206, SID301, SID803, PCR2 |
| Delphi | DCM3, DCM6 |
| Denso | SH7058 |
| Magneti Marelli | IAW |

## Tuning Operations
| Operation | Description |
|---|---|
| Stage 1 | Performance tune with configurable boost/fuel/torque percentages |
| DPF Off | Disable Diesel Particulate Filter |
| EGR Off | Disable Exhaust Gas Recirculation |
| Lambda Off | Disable O2 sensor monitoring |
| AdBlue Off | Disable SCR/AdBlue system |
| CAT Off | Disable catalyst monitoring |
| Speed Limit Off | Remove speed limiter |
| DTC Remove | Remove individual diagnostic trouble codes |
