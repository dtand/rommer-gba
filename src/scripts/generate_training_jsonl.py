#!/usr/bin/env python3
"""
Generate JSONL training files from the SQLite database with configurable inputs and outputs.
This script queries the training data and creates formatted training samples for LLM fine-tuning.
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TrainingDataGenerator:
    """Generates JSONL training files from the SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to the database."""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(f"Database not found: {self.db_path}")
        self.conn = sqlite3.connect(self.db_path)
        
    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            
    def get_training_data(self, session_uuid: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query all training data from the database.
        
        Args:
            session_uuid: Optional UUID to filter by specific session
            
        Returns:
            List of training records with all available data
        """
        cursor = self.conn.cursor()
        
        # Build query with optional session filter
        where_clause = "WHERE a.session_uuid = ?" if session_uuid else ""
        params = (session_uuid,) if session_uuid else ()
        
        query = f"""
        SELECT 
            a.session_uuid,
            a.frame_set_id,
            a.context,
            a.scene,
            a.tags,
            a.description,
            a.action_type,
            a.intent,
            a.outcome,
            fs.timestamp,
            fs.buttons,
            fs.frames_in_set,
            GROUP_CONCAT(
                mc.address || '|' || mc.prev_val || '|' || mc.curr_val || '|' || 
                mc.freq || '|' || mc.frame || '|' || mc.region, 
                ';'
            ) as memory_changes
        FROM annotations a
        JOIN frame_sets fs ON a.session_uuid = fs.session_uuid AND a.frame_set_id = fs.frame_set_id
        LEFT JOIN memory_changes mc ON a.session_uuid = mc.session_uuid AND a.frame_set_id = mc.frame_set_id
        {where_clause}
        GROUP BY a.session_uuid, a.frame_set_id
        ORDER BY a.session_uuid, a.frame_set_id
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        training_records = []
        for row in results:
            # Parse the aggregated data
            buttons = json.loads(row[10]) if row[10] else []
            frames_in_set = json.loads(row[11]) if row[11] else []
            
            # Parse memory changes
            memory_changes = []
            if row[12]:  # memory_changes string
                for change_str in row[12].split(';'):
                    if change_str:
                        parts = change_str.split('|')
                        if len(parts) == 6:
                            memory_changes.append({
                                'address': parts[0],
                                'prev_val': parts[1],
                                'curr_val': parts[2],
                                'freq': int(parts[3]),
                                'frame': int(parts[4]),
                                'region': parts[5]
                            })
            
            # Calculate frame range
            frame_range = 0
            if frames_in_set and len(frames_in_set) > 1:
                frame_range = max(frames_in_set) - min(frames_in_set)
            
            record = {
                'session_uuid': row[0],
                'frame_set_id': row[1],
                'context': row[2],
                'scene': row[3],
                'tags': row[4],
                'description': row[5],
                'action_type': row[6],
                'intent': row[7],
                'outcome': row[8],
                'timestamp': row[9],
                'buttons': buttons,
                'frames_in_set': frames_in_set,
                'frame_range': frame_range,
                'memory_changes': memory_changes
            }
            
            training_records.append(record)
            
        logger.info(f"Retrieved {len(training_records)} training records")
        return training_records
        
    def filter_memory_changes(self, memory_changes: List[Dict[str, Any]], 
                            include_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Filter memory change objects to include only specified fields.
        
        Args:
            memory_changes: List of memory change objects
            include_fields: List of field names to include
            
        Returns:
            Filtered memory change objects
        """
        filtered_changes = []
        for change in memory_changes:
            filtered_change = {field: change.get(field) for field in include_fields if field in change}
            filtered_changes.append(filtered_change)
        return filtered_changes
        
    def build_training_sample(self, record: Dict[str, Any], 
                            input_fields: List[str],
                            output_fields: List[str],
                            memory_change_fields: List[str]) -> Dict[str, Any]:
        """
        Build a training sample with specified inputs and outputs.
        
        Args:
            record: Raw training record from database
            input_fields: List of fields to include in inputs
            output_fields: List of fields to include in outputs
            memory_change_fields: List of fields to include in memory changes
            
        Returns:
            Formatted training sample
        """
        # Build inputs
        inputs = {}
        
        for field in input_fields:
            if field == 'buttons':
                inputs['buttons'] = record.get('buttons', [])
            elif field == 'frame_range':
                inputs['frame_range'] = record.get('frame_range', 0)
            elif field == 'memory_changes':
                filtered_changes = self.filter_memory_changes(
                    record.get('memory_changes', []), 
                    memory_change_fields
                )
                inputs['memory_changes'] = filtered_changes
            elif field in record:
                inputs[field] = record[field]
                
        # Build outputs
        outputs = {}
        for field in output_fields:
            if field in record:
                outputs[field] = record[field]
                
        return {
            'inputs': inputs,
            'outputs': outputs
        }
        
    def generate_jsonl_file(self, session_uuid: Optional[str],
                          output_file: str,
                          input_fields: List[str],
                          output_fields: List[str],
                          memory_change_fields: List[str]) -> int:
        """
        Generate JSONL training file.
        
        Args:
            session_uuid: Optional session UUID filter
            output_file: Output JSONL file path
            input_fields: Fields to include in inputs
            output_fields: Fields to include in outputs
            memory_change_fields: Fields to include in memory changes
            
        Returns:
            Number of samples generated
        """
        logger.info(f"Generating training file: {output_file}")
        logger.info(f"Input fields: {input_fields}")
        logger.info(f"Output fields: {output_fields}")
        logger.info(f"Memory change fields: {memory_change_fields}")
        
        # Get training data
        records = self.get_training_data(session_uuid)
        
        # Generate training samples
        samples_written = 0
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in records:
                sample = self.build_training_sample(
                    record, input_fields, output_fields, memory_change_fields
                )
                
                # Write as JSONL (single line per record)
                f.write(json.dumps(sample, ensure_ascii=False) + '\n')
                samples_written += 1
                
                if samples_written % 100 == 0:
                    logger.info(f"Generated {samples_written} samples...")
                    
        logger.info(f"Successfully generated {samples_written} training samples in {output_file}")
        return samples_written
        
    def get_available_fields(self, session_uuid: Optional[str] = None) -> Dict[str, List[str]]:
        """
        Get all available fields from the data for configuration help.
        
        Args:
            session_uuid: Optional session UUID to sample from
            
        Returns:
            Dictionary with available fields by category
        """
        # Get a sample record to inspect available fields
        records = self.get_training_data(session_uuid)
        if not records:
            return {'annotation_fields': [], 'memory_change_fields': []}
            
        sample_record = records[0]
        
        # Annotation/frame set fields
        annotation_fields = [
            'session_uuid', 'frame_set_id', 'context', 'scene', 'tags', 
            'description', 'action_type', 'intent', 'outcome', 'timestamp',
            'buttons', 'frames_in_set', 'frame_range'
        ]
        
        # Memory change fields
        memory_change_fields = []
        if sample_record.get('memory_changes'):
            memory_change_fields = list(sample_record['memory_changes'][0].keys())
            
        return {
            'annotation_fields': annotation_fields,
            'memory_change_fields': memory_change_fields
        }


def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate JSONL training files from GBA training database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate with default settings
  python generate_training_jsonl.py abc123-uuid

  # Custom inputs and outputs
  python generate_training_jsonl.py abc123-uuid \\
    --inputs buttons frame_range memory_changes context \\
    --outputs description action_type \\
    --memory-fields address prev_val curr_val

  # List available fields
  python generate_training_jsonl.py abc123-uuid --list-fields
        """
    )
    
    parser.add_argument("session_uuid", help="Session UUID to process")
    parser.add_argument("--db-path", default="gba_training.db", 
                       help="SQLite database path (default: gba_training.db)")
    parser.add_argument("--output", "-o", default="training_data.jsonl",
                       help="Output JSONL file path (default: training_data.jsonl)")
    
    # Input/output configuration
    parser.add_argument("--inputs", nargs='+', 
                       default=['buttons', 'frame_range', 'memory_changes'],
                       help="Input fields to include (default: buttons frame_range memory_changes)")
    parser.add_argument("--outputs", nargs='+',
                       default=['context', 'scene', 'description', 'action_type', 'intent', 'outcome'],
                       help="Output fields to include (default: context scene description action_type intent outcome)")
    parser.add_argument("--memory-fields", nargs='+',
                       default=['address', 'prev_val', 'curr_val'],
                       help="Memory change fields to include (default: address prev_val curr_val)")
    
    # Utility options
    parser.add_argument("--list-fields", action="store_true",
                       help="List all available fields and exit")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Initialize generator
    generator = TrainingDataGenerator(args.db_path)
    
    try:
        generator.connect()
        
        # List fields if requested
        if args.list_fields:
            fields = generator.get_available_fields(args.session_uuid)
            print("\n=== AVAILABLE FIELDS ===")
            print(f"Annotation/Frame fields: {', '.join(fields['annotation_fields'])}")
            print(f"Memory change fields: {', '.join(fields['memory_change_fields'])}")
            return
            
        # Validate that session exists
        records = generator.get_training_data(args.session_uuid)
        if not records:
            logger.error(f"No training data found for session: {args.session_uuid}")
            sys.exit(1)
            
        # Generate JSONL file
        samples_count = generator.generate_jsonl_file(
            args.session_uuid,
            args.output,
            args.inputs,
            args.outputs,
            args.memory_fields
        )
        
        # Print summary
        print(f"\n=== GENERATION SUMMARY ===")
        print(f"Session UUID: {args.session_uuid}")
        print(f"Output file: {args.output}")
        print(f"Samples generated: {samples_count}")
        print(f"Input fields: {', '.join(args.inputs)}")
        print(f"Output fields: {', '.join(args.outputs)}")
        print(f"Memory change fields: {', '.join(args.memory_fields)}")
        
    except Exception as e:
        logger.error(f"Error during generation: {e}")
        sys.exit(1)
        
    finally:
        generator.disconnect()


if __name__ == "__main__":
    main()
