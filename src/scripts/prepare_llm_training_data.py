import os
import json
import argparse
from collections import defaultdict

def load_frame_data(data_dir):
    """Load all frame data."""
    frames = []
    
    # Get all frame directories
    frame_dirs = [d for d in os.listdir(data_dir) if d.isdigit()]
    frame_dirs.sort(key=int)
    
    for frame_dir in frame_dirs:
        frame_path = os.path.join(data_dir, frame_dir)
        event_path = os.path.join(frame_path, 'event.json')
        annotation_path = os.path.join(frame_path, 'annotations.json')
        
        if not os.path.exists(event_path):
            continue
            
        # Load event data
        with open(event_path, 'r', encoding='utf-8') as f:
            event_data = json.load(f)
        
        # Load annotation data if available
        annotation_data = None
        if os.path.exists(annotation_path):
            with open(annotation_path, 'r', encoding='utf-8') as f:
                annotation_data = json.load(f)
        
        frames.append({
            'frame': int(frame_dir),
            'event_data': event_data,
            'annotation_data': annotation_data
        })
    
    return frames

def format_training_sample(frame_bundle, include_session_id=False):
    """Format a bundle of 8 frames into LLM training format."""
    # Use the last frame for annotation and final state
    last_frame = frame_bundle[-1]
    annotation = last_frame['annotation_data']
    
    # Build prompt without frame numbers or session IDs
    prompt_parts = []
    
    # Use the last frame's PC and keys (final state)
    last_event = last_frame['event_data']
    prompt_parts.append(f"PC: {last_event.get('pc', 'N/A')}")
    
    # Key history from last frame
    key_history = last_event.get('key_history', [])
    if key_history:
        prompt_parts.append(f"Key history: {', '.join(key_history[-5:])}")  # Last 5 keys
    else:
        prompt_parts.append("Key history: None")
    
    # Current keys from last frame
    current_keys = last_event.get('current_keys', [])
    if current_keys:
        prompt_parts.append(f"Current keys: {', '.join(current_keys)}")
    else:
        prompt_parts.append("Current keys: None")
    
    # Aggregate memory changes across all 8 frames
    aggregated_changes = defaultdict(list)
    for frame in frame_bundle:
        for change in frame['event_data'].get('memory_changes', []):
            key = (change.get('region'), change.get('address'))
            aggregated_changes[key].append(change)
    
    if aggregated_changes:
        prompt_parts.append("Memory changes:")
        for (region, address), changes in aggregated_changes.items():
            # Use first change's prev_val and last change's curr_val
            first_change = changes[0]
            last_change = changes[-1]
            
            region = region or 'unknown'
            address = address or 'N/A'
            prev_val = first_change.get('prev_val', 'N/A')
            curr_val = last_change.get('curr_val', 'N/A')
            
            change_line = f"- {region}: {address}, {prev_val} → {curr_val}"
            prompt_parts.append(change_line)
    else:
        prompt_parts.append("Memory changes: None")
    
    prompt = "\n".join(prompt_parts)
    
    # Build completion (if annotation exists)
    completion = None
    if annotation:
        completion_parts = []
        if annotation.get('context'):
            completion_parts.append(f"Context: {annotation['context']}")
        if annotation.get('scene'):
            completion_parts.append(f"Scene: {annotation['scene']}")
        if annotation.get('tags'):
            completion_parts.append(f"Tags: {annotation['tags']}")
        if annotation.get('description'):
            completion_parts.append(f"Description: {annotation['description']}")
        
        if completion_parts:
            completion = "\n".join(completion_parts)
    
    return {
        'prompt': prompt,
        'completion': completion,
        'has_annotation': completion is not None
    }

def create_training_dataset(data_dir, output_file, format_type='jsonl'):
    """Create training dataset from frame data, bundling every 8 consecutive frames."""
    print("Loading frame data...")
    frames = load_frame_data(data_dir)
    
    print(f"Loaded {len(frames)} frames")
    
    training_samples = []
    
    # Bundle frames into groups of 8 consecutive frames
    frame_bundle_size = 8
    
    # Sort frames by frame number to ensure proper order
    frames.sort(key=lambda x: x['frame'])
    
    print(f"Creating 8-frame bundles...")
    
    # Find the range of frame numbers
    if not frames:
        print("No frames to process")
        return training_samples
    
    min_frame = min(frame['frame'] for frame in frames)
    max_frame = max(frame['frame'] for frame in frames)
    
    # Create a lookup dictionary for faster frame access
    frame_lookup = {frame['frame']: frame for frame in frames}
    
    print(f"Frame range: {min_frame} to {max_frame}")
    
    # Create bundles based on frame number ranges (handling gaps)
    for range_start in range(min_frame, max_frame + 1, frame_bundle_size):
        range_end = range_start + frame_bundle_size - 1  # inclusive
        
        # Collect frames within this range
        frame_bundle = []
        for frame_num in range(range_start, range_start + frame_bundle_size):
            if frame_num in frame_lookup:
                frame_bundle.append(frame_lookup[frame_num])
        
        # Skip empty bundles
        if not frame_bundle:
            continue
        
        print(f"Bundle {range_start}-{range_end}: found {len(frame_bundle)} frames")
        
        # Only create training sample if any frame in the bundle has annotation
        # Use the frame with the highest frame number that has annotation
        annotated_frame = None
        for frame in reversed(sorted(frame_bundle, key=lambda x: x['frame'])):
            if frame['annotation_data']:
                annotated_frame = frame
                break
        
        if not annotated_frame:
            continue  # Skip bundles without annotated frames
        
        sample = format_training_sample(frame_bundle)
        if sample['completion']:  # Only include annotated samples
            training_samples.append(sample)
    
    total_possible_ranges = (max_frame - min_frame + 1) // frame_bundle_size if frames else 0
    print(f"Created {len(training_samples)} training samples from {total_possible_ranges} possible 8-frame ranges")
    
    # Write output
    with open(output_file, 'w', encoding='utf-8') as f:
        if format_type == 'jsonl':
            for sample in training_samples:
                json.dump({
                    'prompt': sample['prompt'],
                    'completion': sample['completion']
                }, f, ensure_ascii=False)
                f.write('\n')
        elif format_type == 'json':
            json.dump(training_samples, f, indent=2, ensure_ascii=False)
    
    print(f"Training data saved to {output_file}")
    return training_samples

def main():
    parser = argparse.ArgumentParser(description="Prepare LLM training data from GBA memory traces")
    parser.add_argument("--data_dir", required=True, help="Path to data directory containing frame folders")
    parser.add_argument("--output", required=True, help="Output file path")
    parser.add_argument("--format", choices=['jsonl', 'json'], default='jsonl', help="Output format")
    
    args = parser.parse_args()
    
    create_training_dataset(
        args.data_dir,
        args.output,
        args.format
    )

if __name__ == "__main__":
    main()
