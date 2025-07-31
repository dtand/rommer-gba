# GBA Agent Project

## Overview
This project provides a toolkit for automated memory event logging, keypress tracking, and synchronized visual snapshotting for Game Boy Advance (GBA) emulation using BizHawk and Python. It is designed to support research, reinforcement learning, and advanced gameplay analysis by capturing both in-game state changes and corresponding screenshots.

## Workflow
1. **BizHawk Lua Script (`event_logger.lua`)**
   - Monitors GBA memory regions (IWRAM/EWRAM) for changes.
   - Logs memory events, keypress history, and program counter to a CSV file (`event_log.csv`).
   - Takes periodic screenshots (snapshots) and saves them as `<frame>.png` in the snapshots directory.
   - Rotates logs and cleans up old snapshots at script start.

2. **Python Aggregation Script (`combine_event_data.py`)**
   - Parses the event log and creates per-frame JSON files with all event data.
   - Copies the matching or most recent snapshot into each frame's output directory for easy analysis.
   - Optionally cleans up the snapshots directory after processing.

## Directory Structure
- `bizhawk/` — Lua scripts for BizHawk emulator
- `src/scripts/` — Python scripts for snapshotting and data aggregation
- `data/event_log.csv` — Main event log file
- `data/snapshots/` — Snapshots as `<frame>.png`
- `data/<frame>/event.json` — Per-frame event data

## Usage
1. Start BizHawk and run `event_logger.lua` to begin logging and snapshotting.
2. Run `combine_event_data.py` to aggregate logs and snapshots into per-frame directories for analysis.

## Requirements
- BizHawk emulator (for Lua scripting)
- Python 3.x
- Python packages: `pyautogui`, `keyboard`, `Pillow`

## License
See [LICENSE](LICENSE).
