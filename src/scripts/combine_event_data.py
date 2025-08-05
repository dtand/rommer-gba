import os
import csv
import json
import shutil
import argparse
import uuid

working_dir = os.getcwd()

parser = argparse.ArgumentParser(description="Process event logs and organize snapshots by frame set.")
parser.add_argument("--csv", required=True, help="Path to event_log.csv")
parser.add_argument("--snapshots", default=os.path.join(working_dir, "data", "snapshots"), help="Path to snapshots directory (default: working_dir/data/snapshots)")
parser.add_argument("--output", default=os.path.join(working_dir, "data"), help="Path to output directory for per-frame data (default: working_dir/data)")
parser.add_argument("--session_name", help="Custom session name (default: random UUID)")
parser.add_argument("--cleanup", type=lambda x: (str(x).lower() == 'true'), default=True, help="Whether to clear the snapshots directory after processing (default: True)")
parser.add_argument("--game_config", required=True, help="Path to game config JSON file with key mappings")
parser.add_argument("--num_frames", type=int, default=5, help="Number of frames in each set (default: 5)")

args = parser.parse_args()

csv_path = args.csv
snapshots_dir = args.snapshots
output_dir = args.output
game_config_path = args.game_config
num_frames = args.num_frames

# Generate a unique session ID
session_id = args.session_name if args.session_name else str(uuid.uuid4())
session_dir = os.path.join(output_dir, session_id)

print(f"Creating session: {session_id}")
print(f"Session directory: {session_dir}")

# Load key mapping from game config
with open(game_config_path, 'r', encoding='utf-8') as f:
    game_config = json.load(f)

key_map = game_config.get('keys', {})  # {console_button: keyboard_key}
# Build reverse mapping: {keyboard_key_lower: console_button}
key_map_rev = {v.lower(): k for k, v in key_map.items()}

# Ensure session directory exists
os.makedirs(session_dir, exist_ok=True)

# Parse CSV and write per-frame JSON

print(f"Parsing CSV and writing per-frame-set JSON arrays to {session_dir}...")
# Gather all events per frame set
frame_set_events = {}
frame_set_frames = {}  # Track which frames belong to each frame set
frame_pcs = {}  # Track PCs for each frame set
frame_keys = {}  # Track current keys for each frame set
with open(csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) != 12:  # Updated to expect 12 columns (added frame_set_id and chunk_id)
            continue  # skip malformed lines
        (timestamp, region, frame, addr, prev_val, curr_val, freq, pc, keys_str, current_key, frame_set_id, chunk_id) = row
        
        frame_set_id = int(frame_set_id)
        frame = int(frame)
        
        # Track frames in each frame set
        if frame_set_id not in frame_set_frames:
            frame_set_frames[frame_set_id] = set()
        frame_set_frames[frame_set_id].add(frame)
        
        # Parse current_key, mapping to console button
        def map_key_to_button(key_str):
            if key_str == 'None' or not key_str.strip():
                return 'None'
            key = key_str.strip().lower()
            btn = key_map_rev.get(key)
            return btn if btn else key  # fallback to original if not found

        mapped_current_key = map_key_to_button(current_key)
        # Build JSON object
        data = {
            "timestamp": int(timestamp),
            "region": region,
            "frame": frame,
            "chunk_id": int(chunk_id),
            "address": addr,
            "prev_val": prev_val,
            "curr_val": curr_val,
            "freq": int(freq),
            "pc": pc,
            "current_key": mapped_current_key
        }
        frame_pcs[frame] = pc
        frame_keys[frame] = mapped_current_key 
        if frame_set_id not in frame_set_events:
            frame_set_events[frame_set_id] = []
        frame_set_events[frame_set_id].append(data)


# Write new-style JSON object per frame set (only for frame sets with event data)
valid_frame_set_ids = set()
for frame_set_id, events in frame_set_events.items():
    if not events:
        continue
    
    # Find the final (highest) frame number in this frame set
    final_frame = max(frame_set_frames[frame_set_id])
    valid_frame_set_ids.add(frame_set_id)
    
    # Use the final frame's event data for top-level info (timestamp, pc, keys)
    final_frame_events = [e for e in events if e["frame"] == final_frame]
    if final_frame_events:
        first_final = final_frame_events[0]
    else:
        # Fallback to last event if no events from final frame
        first_final = events[-1]
    
    frames_in_set = sorted(list(frame_set_frames[frame_set_id]))
    current_key_values = [frame_keys.get(f, 'None') for f in frames_in_set]

    top_level = {
        "timestamp": first_final["timestamp"],
        "buttons": current_key_values,
        "frame_set_id": frame_set_id,
        "frames_in_set": frames_in_set,
        "memory_changes": []
    }
    
    # Add all memory changes from all frames in the set
    for e in events:
        mem_change = {
            "region": e["region"],
            "frame": e["frame"],
            "address": e["address"],
            "prev_val": e["prev_val"],
            "curr_val": e["curr_val"],
            "freq": e["freq"]
        }
        top_level["memory_changes"].append(mem_change)
    
    # Create directory named after the frame_set_id
    frame_set_dir = os.path.join(session_dir, str(frame_set_id))
    os.makedirs(frame_set_dir, exist_ok=True)
    json_path = os.path.join(frame_set_dir, "event.json")
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(top_level, jf, indent=2)
print("Finished writing per-frame-set JSON files.")

# Create session metadata file
import time
from datetime import datetime

session_metadata = {
    "session_id": session_id,
    "created_at": datetime.now().isoformat(),
    "created_timestamp": int(time.time()),
    "total_frame_sets": len(valid_frame_set_ids),
    "num_frames_per_set": num_frames,
    "frame_set_id_range": {
        "min": min(valid_frame_set_ids) if valid_frame_set_ids else 0,
        "max": max(valid_frame_set_ids) if valid_frame_set_ids else 0
    },
    "source_csv": os.path.basename(csv_path),
    "game_config": os.path.basename(game_config_path),
    "is_custom_name": args.session_name is not None
}

metadata_path = os.path.join(session_dir, "session_metadata.json")
with open(metadata_path, 'w', encoding='utf-8') as f:
    json.dump(session_metadata, f, indent=2)

print(f"Session metadata saved to: {metadata_path}")
print(f"Session contains {len(valid_frame_set_ids)} frame sets (frame_set_id range: {session_metadata['frame_set_id_range']['min']}-{session_metadata['frame_set_id_range']['max']})")

# Cleanup: Remove any frame set directories in session_dir that are not in valid_frame_set_ids
valid_frame_set_strs = {str(fid) for fid in valid_frame_set_ids}
for dname in os.listdir(session_dir):
    dpath = os.path.join(session_dir, dname)
    if os.path.isdir(dpath) and dname.isdigit() and dname not in valid_frame_set_strs:
        print(f"Removing stale frame set directory: {dpath}")
        shutil.rmtree(dpath)


# Find all available snapshots by frame_set_id (snapshots are now named by frame_set_id)
print(f"Scanning snapshots in {snapshots_dir}...")
snapshots = {}
for fname in os.listdir(snapshots_dir):
    fpath = os.path.join(snapshots_dir, fname)
    if os.path.isfile(fpath) and fname.endswith('.png'):
        try:
            frame_set_id = int(os.path.splitext(fname)[0])
            snapshots[frame_set_id] = fpath
        except Exception:
            continue
print(f"Found {len(snapshots)} snapshots.")

if len(snapshots) == 0:
    print("No snapshots found. Exiting.")
    exit(0)

# For each frame set directory, copy the snapshot matching the frame_set_id
print("Copying matching snapshot to each frame set directory...")
for frame_set_dir_name in os.listdir(session_dir):
    frame_set_dir_path = os.path.join(session_dir, frame_set_dir_name)
    if not os.path.isdir(frame_set_dir_path):
        continue
    json_file = os.path.join(frame_set_dir_path, "event.json")
    if not os.path.isfile(json_file):
        continue
    try:
        # Frame set ID is the directory name itself
        frame_set_id = int(frame_set_dir_name)
    except Exception:
        continue
    
    # Look for snapshot matching the frame_set_id
    snap_path = snapshots.get(frame_set_id)
    if not snap_path:
        print(f"Warning: No snapshot found for frame_set_id {frame_set_id}")
        # Fallback: Find the most recent previous snapshot
        prev_frame_set_ids = [f for f in snapshots.keys() if f < frame_set_id]
        if prev_frame_set_ids:
            closest_frame_set_id = max(prev_frame_set_ids)
            snap_path = snapshots[closest_frame_set_id]
            print(f"Using fallback snapshot from frame_set_id {closest_frame_set_id}")
    
    if snap_path and os.path.isfile(snap_path):
        dst = os.path.join(frame_set_dir_path, f"{frame_set_id}.png")
        shutil.copy2(snap_path, dst)
print("Finished moving snapshots.")

##Cleanup snapshots directory if requested
if args.cleanup:
    print(f"Cleaning up {snapshots_dir} ...")
    for dname in os.listdir(snapshots_dir):
        dpath = os.path.join(snapshots_dir, dname)
        if os.path.isdir(dpath):
            shutil.rmtree(dpath)
        elif os.path.isfile(dpath):
            os.remove(dpath)
    print("Snapshots directory cleaned up.")


