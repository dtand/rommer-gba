import os
import json
import glob
import sys
import argparse
from pathlib import Path

def load_annotation_config():
    """Load the current annotation configuration."""
    config_path = "src/web_app/annotation_config.json"
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Config file not found: {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error parsing config file: {e}")
        return None

def save_annotation_config(config):
    """Save the updated annotation configuration."""
    config_path = "src/web_app/annotation_config.json"
    try:
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"Updated config saved to: {config_path}")
        return True
    except Exception as e:
        print(f"Error saving config file: {e}")
        return False

def extract_values_from_annotations(session_uuid=None):
    """Extract all unique values from annotation files."""
    data_dir = "data"
    found_values = {
        'context': set(),
        'action_type': set(),
        'intent': set(),
        'outcome': set()
    }
    
    if session_uuid:
        # Process only the specified UUID directory
        session_dir = os.path.join(data_dir, session_uuid)
        if not os.path.exists(session_dir):
            print(f"Error: Session directory not found: {session_dir}")
            return found_values
        if not os.path.isdir(session_dir):
            print(f"Error: {session_dir} is not a directory")
            return found_values
        session_dirs = [session_dir]
        print(f"Processing specific session: {session_uuid}")
    else:
        # Find all UUID directories (original behavior)
        uuid_pattern = os.path.join(data_dir, "*")
        session_dirs = [d for d in glob.glob(uuid_pattern) if os.path.isdir(d)]
        print(f"Processing all sessions ({len(session_dirs)} found)")
    
    total_files = 0
    processed_files = 0
    
    for session_dir in session_dirs:
        session_name = os.path.basename(session_dir)
        print(f"Scanning session: {session_name}")
        
        # Find all frame directories within this session
        frame_pattern = os.path.join(session_dir, "*")
        frame_dirs = [d for d in glob.glob(frame_pattern) if os.path.isdir(d)]
        
        session_files = 0
        for frame_dir in frame_dirs:
            annotation_file = os.path.join(frame_dir, "annotations.json")
            if os.path.exists(annotation_file):
                total_files += 1
                session_files += 1
                try:
                    with open(annotation_file, 'r', encoding='utf-8') as f:
                        annotation = json.load(f)
                    
                    # Extract values for each field
                    for field in found_values.keys():
                        value = annotation.get(field, '').strip()
                        if value:  # Only add non-empty values
                            found_values[field].add(value)
                    
                    processed_files += 1
                    
                except json.JSONDecodeError as e:
                    print(f"Error parsing {annotation_file}: {e}")
                except Exception as e:
                    print(f"Error reading {annotation_file}: {e}")
        
        print(f"  Found {session_files} annotation files in this session")
    
    print(f"Processed {processed_files}/{total_files} annotation files total")
    return found_values

def get_existing_values(config, field_type):
    """Get existing values from config for a specific field type."""
    field_map = {
        'context': 'context_options',
        'action_type': 'action_type_options',
        'intent': 'intent_options',
        'outcome': 'outcome_options'
    }
    
    options_key = field_map.get(field_type)
    if not options_key or options_key not in config:
        return set()
    
    return {option['value'] for option in config[options_key]}

def add_missing_values(config, found_values):
    """Add missing values to the configuration."""
    field_map = {
        'context': 'context_options',
        'action_type': 'action_type_options',
        'intent': 'intent_options',
        'outcome': 'outcome_options'
    }
    
    changes_made = False
    
    for field_type, new_values in found_values.items():
        options_key = field_map[field_type]
        
        if options_key not in config:
            config[options_key] = []
        
        existing_values = get_existing_values(config, field_type)
        missing_values = new_values - existing_values
        
        if missing_values:
            print(f"\nFound {len(missing_values)} new {field_type} values:")
            for value in sorted(missing_values):
                print(f"  - {value}")
                
                # Create label from value (capitalize and replace underscores)
                label = value.replace('_', ' ').title()
                
                # Add new option to config
                new_option = {
                    "value": value,
                    "label": label
                }
                config[options_key].append(new_option)
                changes_made = True
            
            # Sort the options by value for consistency
            config[options_key].sort(key=lambda x: x['value'])
        else:
            print(f"No new {field_type} values found")
    
    return changes_made

def main():
    """Main function to update annotation config with found values."""
    parser = argparse.ArgumentParser(description='Sync annotation configuration with values found in annotation files')
    parser.add_argument('--uuid', type=str, help='Specific session UUID to process (optional, processes all sessions if not provided)')
    parser.add_argument('uuid_positional', nargs='?', help='Session UUID as positional argument')
    
    args = parser.parse_args()
    
    # Use positional argument if provided, otherwise use --uuid flag
    session_uuid = args.uuid_positional or args.uuid
    
    if session_uuid:
        print(f"Scanning annotation files for new values in session: {session_uuid}")
    else:
        print("Scanning annotation files for new values in all sessions...")
    
    # Load current configuration
    config = load_annotation_config()
    if config is None:
        return
    
    # Extract values from annotation files
    found_values = extract_values_from_annotations(session_uuid)
    
    # Show summary of found values
    print("\nSummary of found values:")
    for field_type, values in found_values.items():
        print(f"  {field_type}: {len(values)} unique values")
        if values:
            print(f"    Examples: {', '.join(sorted(list(values))[:5])}")
    
    # Add missing values to configuration
    changes_made = add_missing_values(config, found_values)
    
    if changes_made:
        # Save updated configuration
        if save_annotation_config(config):
            print("\n✅ Configuration updated successfully!")
        else:
            print("\n❌ Failed to save configuration")
    else:
        print("\n✅ No changes needed - all values already exist in configuration")

if __name__ == "__main__":
    main()