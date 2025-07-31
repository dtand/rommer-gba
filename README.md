# GBA Memory Tracing & Annotation Project

## Overview
This project provides a comprehensive toolkit for automated memory event logging, frame set-based data organization, and synchronized visual snapshotting for Game Boy Advance (GBA) emulation using BizHawk and Python. It is designed to support machine learning training data generation, reinforcement learning research, and advanced gameplay analysis by capturing memory state changes with corresponding screenshots organized by frame sets.

## Key Features
- **Chunked Memory Scanning**: Optimized 5-chunk system for IWRAM/EWRAM monitoring with 50% performance improvement
- **Frame Set Organization**: Groups related frames (5 frames per set) for consistent data annotation
- **Robust Logging**: Enhanced safety with multiple exit handlers and periodic log flushing
- **Web Interface**: Flask-based annotation tool for labeling training data
- **Automatic Data Processing**: Seamless conversion from raw logs to organized training datasets

## Workflow
1. **BizHawk Lua Script (`event_logger.lua`)**
   - Monitors GBA memory regions (IWRAM/EWRAM) using optimized 5-chunk scanning per frame
   - Logs memory events with frame set tracking to CSV format (12 columns including frame_set_id and chunk_id)
   - Takes synchronized screenshots named by frame_set_id (`0.png`, `1.png`, etc.)
   - Enhanced safety with multiple exit handlers and periodic log flushing (every 300 frames)
   - Automatic log rotation and snapshot directory cleanup at script start

2. **Python Data Processing (`combine_event_data.py`)**
   - Processes CSV logs and organizes data by frame_set_id instead of individual frames
   - Creates directories named by frame_set_id (e.g., `1/`, `2/`, `3/`) containing:
     - `event.json` - Clean JSON with memory changes, timing, and metadata (no redundant fields)
     - `{frame_set_id}.png` - Corresponding screenshot
   - Maps console buttons using game configuration files
   - Generates session metadata with frame_set_id ranges and statistics
   - Optional cleanup of source snapshots directory

3. **Web Annotation Interface (`src/web_app/`)**
   - Flask-based web application for annotating training data
   - Browse frame sets and add labels/annotations
   - Network accessible for remote annotation work
   - RESTful API for programmatic access

## Frame Set System
The project uses a **frame set approach** where:
- Each frame set contains **5 frames** of memory scanning (chunks 0-4)
- Memory regions are scanned in chunks: IWRAM (4KB chunks) and EWRAM (32KB chunks)
- Screenshots are taken after completing each frame set to capture the final state
- All data is organized by `frame_set_id` for consistent annotation and training

## Directory Structure
```
├── bizhawk/
│   └── event_logger.lua          # BizHawk Lua script for memory monitoring
├── src/
│   ├── scripts/
│   │   └── combine_event_data.py # Data processing and organization
│   └── web_app/                  # Flask annotation interface
│       ├── app.py
│       ├── routes/
│       └── templates/
├── resources/
│   └── game_configs/             # Game-specific key mappings
├── data/                         # Output directory (gitignored)
│   └── <session_id>/             # Session-based organization
│       ├── session_metadata.json
│       ├── 1/                    # Frame set directories
│       │   ├── event.json
│       │   └── 1.png
│       ├── 2/
│       └── ...
└── requirements.txt
```

## Data Format

### CSV Log Format (12 columns):
```
timestamp,region,frame,address,prev_val,curr_val,freq,pc,key_history,current_keys,frame_set_id,chunk_id
```

### JSON Event Format:
```json
{
  "timestamp": 1753996829216,
  "pc": "000001F8",
  "current_keys": [],
  "frame_set_id": 1,
  "frames_in_set": [8, 9, 11, 12, 13],
  "memory_changes": [
    {
      "region": "iwram",
      "frame": 8,
      "address": "03000000",
      "prev_val": "00000000",
      "curr_val": "00000003",
      "freq": 1
    }
  ]
}
```

## Usage

### 1. Data Collection
```bash
# Start BizHawk and load your GBA ROM
# Run the event_logger.lua script in BizHawk's Lua Console
# The script will automatically:
#   - Clear old snapshots and rotate logs
#   - Begin monitoring memory changes
#   - Take screenshots every 5 frames (per frame set)
#   - Save data to configured directories
```

### 2. Data Processing
```bash
# Process the collected data into organized frame sets
python src/scripts/combine_event_data.py \
  --csv "C:\path\to\event_log.csv" \
  --snapshots "C:\path\to\snapshots" \
  --output data \
  --game_config resources/game_configs/metabots_rokusho.json \
  --cleanup false  # Set to true to clean up source snapshots
```

### 3. Web Annotation Interface
```bash
# Start the Flask web application
cd src/web_app
python app.py

# Access locally: http://localhost:5000
# Access from network: http://<your-ip>:5000
```

### 4. Network Access Setup (Windows)
To access the web interface from other devices:
1. **Configure Windows Firewall:**
   ```cmd
   netsh advfirewall firewall add rule name="Flask App Port 5000" dir=in action=allow protocol=TCP localport=5000
   ```
2. **Find your IP address:** `ipconfig`
3. **Access from other devices:** `http://<your-ip>:5000`

## Performance Optimizations
- **5-Chunk System**: Memory scanning optimized for 50% performance improvement over previous 4-chunk system
- **Buffered Logging**: 200-entry buffer with periodic flushing to minimize I/O impact
- **Combined Processing**: IWRAM and EWRAM processed together to reduce per-frame overhead
- **Robust Error Handling**: Multiple exit handlers ensure data preservation on script termination

## Requirements
- **BizHawk emulator** (tested with 2.10)
- **Python 3.x** with virtual environment
- **Required packages:**
  ```bash
  pip install flask
  # Additional packages as specified in requirements.txt
  ```

## Configuration
- Game-specific key mappings in `resources/game_configs/`
- Memory regions and chunk sizes configurable in `event_logger.lua`
- Web app settings in `src/web_app/app.py`

## Data Output
Each processing session creates:
- **Session directory** with unique UUID
- **Frame set directories** (1/, 2/, 3/, ...) containing event.json and screenshot
- **Session metadata** with statistics and configuration details
- **Clean JSON format** optimized for machine learning pipelines

## License
See [LICENSE](LICENSE).
