#!/usr/bin/env python3
"""
Example script demonstrating different training data generation configurations
and showing sample outputs for the JSONL training file generator.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import our generator
sys.path.append(str(Path(__file__).parent.parent))

from scripts.generate_training_jsonl import TrainingDataGenerator


def show_sample_data(session_uuid: str, db_path: str = "gba_training.db"):
    """Show sample data from the database."""
    generator = TrainingDataGenerator(db_path)
    
    try:
        generator.connect()
        
        # Get available fields
        fields = generator.get_available_fields(session_uuid)
        print("=== AVAILABLE FIELDS ===")
        print(f"Annotation/Frame fields: {', '.join(fields['annotation_fields'])}")
        print(f"Memory change fields: {', '.join(fields['memory_change_fields'])}")
        
        # Get sample records
        records = generator.get_training_data(session_uuid)
        if not records:
            print(f"No records found for session: {session_uuid}")
            return
            
        print(f"\n=== SAMPLE RECORD (1 of {len(records)}) ===")
        sample = records[0]
        
        print(f"Frame Set ID: {sample['frame_set_id']}")
        print(f"Context: {sample['context']}")
        print(f"Scene: {sample['scene']}")
        print(f"Description: {sample['description']}")
        print(f"Buttons: {sample['buttons']}")
        print(f"Frame Range: {sample['frame_range']}")
        print(f"Memory Changes: {len(sample['memory_changes'])} changes")
        
        if sample['memory_changes']:
            print("Sample memory changes:")
            for i, change in enumerate(sample['memory_changes'][:3]):
                print(f"  {i+1}. {change['address']}: {change['prev_val']} -> {change['curr_val']}")
                
    finally:
        generator.disconnect()


def show_training_examples(session_uuid: str, db_path: str = "gba_training.db"):
    """Show examples of different training configurations."""
    generator = TrainingDataGenerator(db_path)
    
    try:
        generator.connect()
        records = generator.get_training_data(session_uuid)
        
        if not records:
            print(f"No records found for session: {session_uuid}")
            return
            
        sample_record = records[0]
        
        print("\n" + "="*60)
        print("TRAINING CONFIGURATION EXAMPLES")
        print("="*60)
        
        # Example 1: Default configuration
        print("\n--- Example 1: Default Configuration ---")
        print("Inputs: buttons, frame_range, memory_changes")
        print("Outputs: description")
        print("Memory fields: address, prev_val, curr_val")
        
        sample1 = generator.build_training_sample(
            sample_record,
            ['buttons', 'frame_range', 'memory_changes'],
            ['description'],
            ['address', 'prev_val', 'curr_val']
        )
        print(json.dumps(sample1, indent=2)[:500] + "...")
        
        # Example 2: Battle analysis configuration
        print("\n--- Example 2: Battle Analysis Configuration ---")
        print("Inputs: context, buttons, memory_changes")
        print("Outputs: description, action_type, intent")
        print("Memory fields: address, prev_val, curr_val")
        
        sample2 = generator.build_training_sample(
            sample_record,
            ['context', 'buttons', 'memory_changes'],
            ['description', 'action_type', 'intent'],
            ['address', 'prev_val', 'curr_val']
        )
        print(json.dumps(sample2, indent=2)[:500] + "...")
        
        # Example 3: Memory pattern analysis
        print("\n--- Example 3: Memory Pattern Analysis ---")
        print("Inputs: frame_range, memory_changes")
        print("Outputs: context, scene")
        print("Memory fields: address, prev_val, curr_val, freq")
        
        sample3 = generator.build_training_sample(
            sample_record,
            ['frame_range', 'memory_changes'],
            ['context', 'scene'],
            ['address', 'prev_val', 'curr_val', 'freq']
        )
        print(json.dumps(sample3, indent=2)[:500] + "...")
        
        # Example 4: Comprehensive configuration
        print("\n--- Example 4: Comprehensive Configuration ---")
        print("Inputs: context, scene, buttons, frame_range, memory_changes")
        print("Outputs: description, action_type, intent, outcome")
        print("Memory fields: address, prev_val, curr_val, freq, region")
        
        sample4 = generator.build_training_sample(
            sample_record,
            ['context', 'scene', 'buttons', 'frame_range', 'memory_changes'],
            ['description', 'action_type', 'intent', 'outcome'],
            ['address', 'prev_val', 'curr_val', 'freq', 'region']
        )
        print(json.dumps(sample4, indent=2)[:500] + "...")
        
    finally:
        generator.disconnect()


def show_usage_examples():
    """Show command-line usage examples."""
    print("\n" + "="*60)
    print("COMMAND LINE USAGE EXAMPLES")
    print("="*60)
    
    examples = [
        {
            "description": "Basic usage with default settings",
            "command": "python generate_training_jsonl.py 98cc9f85-0567-4392-8b0e-636a8d65b3a2"
        },
        {
            "description": "Custom output file",
            "command": "python generate_training_jsonl.py 98cc9f85-0567-4392-8b0e-636a8d65b3a2 -o battle_training.jsonl"
        },
        {
            "description": "Battle analysis configuration",
            "command": """python generate_training_jsonl.py 98cc9f85-0567-4392-8b0e-636a8d65b3a2 \\
    --inputs context buttons memory_changes \\
    --outputs description action_type intent"""
        },
        {
            "description": "Memory pattern analysis",
            "command": """python generate_training_jsonl.py 98cc9f85-0567-4392-8b0e-636a8d65b3a2 \\
    --inputs frame_range memory_changes \\
    --outputs context scene \\
    --memory-fields address prev_val curr_val freq"""
        },
        {
            "description": "Health-focused training",
            "command": """python generate_training_jsonl.py 98cc9f85-0567-4392-8b0e-636a8d65b3a2 \\
    --inputs buttons memory_changes \\
    --outputs description \\
    --memory-fields address prev_val curr_val \\
    -o health_training.jsonl"""
        },
        {
            "description": "List available fields",
            "command": "python generate_training_jsonl.py 98cc9f85-0567-4392-8b0e-636a8d65b3a2 --list-fields"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}:")
        print(f"   {example['command']}")


def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python training_examples.py <session_uuid> [db_path]")
        print("Example: python training_examples.py 98cc9f85-0567-4392-8b0e-636a8d65b3a2")
        sys.exit(1)
        
    session_uuid = sys.argv[1]
    db_path = sys.argv[2] if len(sys.argv) > 2 else "gba_training.db"
    
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        print("Make sure to run the ingestion script first:")
        print(f"python ingest_training_data.py {session_uuid}")
        sys.exit(1)
    
    print(f"Analyzing training data for session: {session_uuid}")
    print(f"Database: {db_path}")
    
    show_sample_data(session_uuid, db_path)
    show_training_examples(session_uuid, db_path)
    show_usage_examples()


if __name__ == "__main__":
    main()
