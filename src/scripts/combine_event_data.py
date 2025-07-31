import os
import csv
import json
import shutil
import argparse

working_dir = os.getcwd()

parser = argparse.ArgumentParser(description="Process event logs and organize snapshots by frame.")
parser.add_argument("--csv", required=True, help="Path to event_log.csv")
parser.add_argument("--snapshots", default=os.path.join(working_dir, "data", "snapshots"), help="Path to snapshots directory (default: working_dir/data/snapshots)")
parser.add_argument("--output", default=os.path.join(working_dir, "data"), help="Path to output directory for per-frame data (default: working_dir/data)")
parser.add_argument("--cleanup", type=lambda x: (str(x).lower() == 'true'), default=True, help="Whether to clear the snapshots directory after processing (default: True)")
parser.add_argument("--game_config", required=True, help="Path to game config JSON file with key mappings")

args = parser.parse_args()

csv_path = args.csv
snapshots_dir = args.snapshots
output_dir = args.output
game_config_path = args.game_config

# Load key mapping from game config
with open(game_config_path, 'r', encoding='utf-8') as f:
    game_config = json.load(f)
key_map = game_config.get('keys', {})  # {console_button: keyboard_key}
# Build reverse mapping: {keyboard_key_lower: console_button}
key_map_rev = {v.lower(): k for k, v in key_map.items()}

# Ensure output directory exists
os.makedirs(output_dir, exist_ok=True)

# Parse CSV and write per-frame JSON

print(f"Parsing CSV and writing per-frame JSON arrays to {output_dir}...")
# Gather all events per frame
frame_events = {}
with open(csv_path, newline='', encoding='utf-8') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        if len(row) != 10:
            continue  # skip malformed lines
        (timestamp, region, frame, addr, prev_val, curr_val, freq, pc, keys_str, current_keys) = row
        # Parse key history and current_keys, mapping to console buttons
        def map_keys_to_buttons(key_str):
            if key_str == 'None':
                return []
            result = []
            for combo in key_str.split('|'):
                combo = combo.strip()
                if not combo:
                    continue
                # Handle combos like keyA+keyB
                mapped = []
                for key in combo.split('+'):
                    key = key.strip().lower()
                    btn = key_map_rev.get(key)
                    if btn:
                        mapped.append(btn)
                    else:
                        mapped.append(key)  # fallback to original if not found
                result.append('+'.join(mapped))
            return result

        keys_list = map_keys_to_buttons(keys_str)
        mapped_current_keys = map_keys_to_buttons(current_keys)
        # Build JSON object
        data = {
            "timestamp": int(timestamp),
            "region": region,
            "frame": int(frame),
            "address": addr,
            "prev_val": prev_val,
            "curr_val": curr_val,
            "freq": int(freq),
            "pc": pc,
            "key_history": keys_list,
            "current_keys": mapped_current_keys
        }
        if frame not in frame_events:
            frame_events[frame] = []
        frame_events[frame].append(data)


# Write new-style JSON object per frame (only for frames with event data)
valid_frames = set()
for frame, events in frame_events.items():
    if not events:
        continue
    valid_frames.add(str(frame))
    first = events[0]
    top_level = {
        "timestamp": first["timestamp"],
        "pc": first["pc"],
        "key_history": first["key_history"],
        "current_keys": first["current_keys"],
        "memory_changes": []
    }
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
    frame_dir = os.path.join(output_dir, str(frame))
    os.makedirs(frame_dir, exist_ok=True)
    json_path = os.path.join(frame_dir, "event.json")
    with open(json_path, 'w', encoding='utf-8') as jf:
        json.dump(top_level, jf, indent=2)
print("Finished writing per-frame JSON files.")

# Cleanup: Remove any frame directories in output_dir that are not in valid_frames
for dname in os.listdir(output_dir):
    dpath = os.path.join(output_dir, dname)
    if os.path.isdir(dpath) and dname.isdigit() and dname not in valid_frames:
        print(f"Removing stale frame directory: {dpath}")
        shutil.rmtree(dpath)


# Find all available snapshots by frame number
print(f"Scanning snapshots in {snapshots_dir}...")
snapshots = {}
for fname in os.listdir(snapshots_dir):
    fpath = os.path.join(snapshots_dir, fname)
    if os.path.isfile(fpath) and fname.endswith('.png'):
        try:
            frame_num = int(os.path.splitext(fname)[0])
            snapshots[frame_num] = fpath
        except Exception:
            continue
print(f"Found {len(snapshots)} snapshots.")

if len(snapshots) == 0:
    print("No snapshots found. Exiting.")
    exit(0)

# For each frame directory, copy the matching snapshot by frame number
# print("Copying matching snapshot to each frame directory...")
# for frame_dir_name in os.listdir(output_dir):
#     frame_dir_path = os.path.join(output_dir, frame_dir_name)
#     if not os.path.isdir(frame_dir_path):
#         continue
#     json_file = os.path.join(frame_dir_path, "event.json")
#     if not os.path.isfile(json_file):
#         continue
#     try:
#         with open(json_file, 'r', encoding='utf-8') as jf:
#             frame_data = json.load(jf)
#         frame_num = int(frame_data[0]['frame'])
#     except Exception:
#         continue
#     snap_path = snapshots.get(frame_num)
#     if not snap_path:
#         # Find the most recent previous snapshot
#         prev_frames = [f for f in snapshots.keys() if f < frame_num]
#         if prev_frames:
#             closest_frame = max(prev_frames)
#             snap_path = snapshots[closest_frame]
#     if snap_path and os.path.isfile(snap_path):
#         dst = os.path.join(frame_dir_path, f"{frame_num}.png")
#         shutil.copy2(snap_path, dst)
# print("Finished moving snapshots.")

# Cleanup snapshots directory if requested
# if args.cleanup:
#     print(f"Cleaning up {snapshots_dir} ...")
#     for dname in os.listdir(snapshots_dir):
#         dpath = os.path.join(snapshots_dir, dname)
#         if os.path.isdir(dpath):
#             shutil.rmtree(dpath)
#         elif os.path.isfile(dpath):
#             os.remove(dpath)
#     print("Snapshots directory cleaned up.")


