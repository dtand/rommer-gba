#!/usr/bin/env python3
"""
Script to ingest GBA training data from event.json and annotations.json files
into a SQLite database for analysis and training.
"""

import argparse
import json
import sqlite3
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TrainingDataIngestor:
    """Handles ingestion of training data into SQLite database."""
    
    def __init__(self, db_path: str):
        """Initialize the ingestor with database path."""
        self.db_path = db_path
        self.conn = None
        
    def connect(self):
        """Connect to SQLite database and create tables if they don't exist."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()
        
    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            
    def _create_tables(self):
        """Create database tables for storing training data."""
        cursor = self.conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_uuid TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Frame sets table (from event.json)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS frame_sets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_uuid TEXT NOT NULL,
                frame_set_id INTEGER NOT NULL,
                timestamp INTEGER NOT NULL,
                buttons TEXT NOT NULL,
                frames_in_set TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_uuid) REFERENCES sessions (session_uuid),
                UNIQUE(session_uuid, frame_set_id)
            )
        """)
        
        # Memory changes table (from event.json)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_uuid TEXT NOT NULL,
                frame_set_id INTEGER NOT NULL,
                region TEXT NOT NULL,
                frame INTEGER NOT NULL,
                address TEXT NOT NULL,
                prev_val TEXT NOT NULL,
                curr_val TEXT NOT NULL,
                freq INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_uuid) REFERENCES sessions (session_uuid)
            )
        """)
        
        # Annotations table (from annotations.json)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_uuid TEXT NOT NULL,
                frame_set_id INTEGER NOT NULL,
                context TEXT,
                scene TEXT,
                tags TEXT,
                description TEXT,
                action_type TEXT,
                intent TEXT,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_uuid) REFERENCES sessions (session_uuid),
                UNIQUE(session_uuid, frame_set_id)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_frame_sets_session ON frame_sets(session_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_changes_session ON memory_changes(session_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_changes_address ON memory_changes(address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_annotations_session ON annotations(session_uuid)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_annotations_context ON annotations(context)")
        
        self.conn.commit()
        logger.info("Database tables created/verified successfully")
        
    def insert_session(self, session_uuid: str):
        """Insert session record if it doesn't exist."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO sessions (session_uuid) VALUES (?)
        """, (session_uuid,))
        self.conn.commit()
        
    def insert_frame_set(self, session_uuid: str, event_data: Dict[str, Any]):
        """Insert frame set data from event.json."""
        cursor = self.conn.cursor()
        
        buttons_json = json.dumps(event_data.get('buttons', []))
        frames_json = json.dumps(event_data.get('frames_in_set', []))
        
        cursor.execute("""
            INSERT OR REPLACE INTO frame_sets 
            (session_uuid, frame_set_id, timestamp, buttons, frames_in_set)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session_uuid,
            event_data.get('frame_set_id'),
            event_data.get('timestamp'),
            buttons_json,
            frames_json
        ))
        self.conn.commit()
        
    def insert_memory_changes(self, session_uuid: str, frame_set_id: int, memory_changes: List[Dict[str, Any]]):
        """Insert memory change records from event.json."""
        cursor = self.conn.cursor()
        
        # Clear existing memory changes for this frame set
        cursor.execute("""
            DELETE FROM memory_changes WHERE session_uuid = ? AND frame_set_id = ?
        """, (session_uuid, frame_set_id))
        
        # Insert new memory changes
        for change in memory_changes:
            cursor.execute("""
                INSERT INTO memory_changes 
                (session_uuid, frame_set_id, region, frame, address, prev_val, curr_val, freq)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                session_uuid,
                frame_set_id,
                change.get('region'),
                change.get('frame'),
                change.get('address'),
                change.get('prev_val'),
                change.get('curr_val'),
                change.get('freq')
            ))
        
        self.conn.commit()
        
    def insert_annotation(self, session_uuid: str, frame_set_id: int, annotation_data: Dict[str, Any]):
        """Insert annotation data from annotations.json."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO annotations 
            (session_uuid, frame_set_id, context, scene, tags, description, action_type, intent, outcome)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_uuid,
            frame_set_id,
            annotation_data.get('context'),
            annotation_data.get('scene'),
            annotation_data.get('tags'),
            annotation_data.get('description'),
            annotation_data.get('action_type'),
            annotation_data.get('intent'),
            annotation_data.get('outcome')
        ))
        self.conn.commit()
        
    def process_directory(self, data_dir: Path, session_uuid: str):
        """Process all directories in a session data directory."""
        session_dir = data_dir / session_uuid
        
        if not session_dir.exists():
            logger.error(f"Session directory not found: {session_dir}")
            return
            
        logger.info(f"Processing session: {session_uuid}")
        self.insert_session(session_uuid)
        
        # Get all numbered directories that contain both event.json and annotations.json
        processed_count = 0
        
        for frame_dir in session_dir.iterdir():
            if not frame_dir.is_dir():
                continue
                
            try:
                frame_set_id = int(frame_dir.name)
            except ValueError:
                # Skip non-numeric directories
                continue
                
            event_file = frame_dir / "event.json"
            annotation_file = frame_dir / "annotations.json"
            
            # Only process directories that have annotations
            if not annotation_file.exists():
                continue
                
            if not event_file.exists():
                logger.warning(f"Missing event.json in {frame_dir}")
                continue
                
            try:
                # Load event data
                with open(event_file, 'r') as f:
                    event_data = json.load(f)
                    
                # Load annotation data
                with open(annotation_file, 'r') as f:
                    annotation_data = json.load(f)
                    
                # Insert into database
                self.insert_frame_set(session_uuid, event_data)
                self.insert_memory_changes(session_uuid, frame_set_id, event_data.get('memory_changes', []))
                self.insert_annotation(session_uuid, frame_set_id, annotation_data)
                
                processed_count += 1
                
                if processed_count % 100 == 0:
                    logger.info(f"Processed {processed_count} frame sets...")
                    
            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"Error processing {frame_dir}: {e}")
                continue
                
        logger.info(f"Successfully processed {processed_count} frame sets for session {session_uuid}")
        
    def get_stats(self):
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) FROM sessions")
        stats['sessions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM frame_sets")
        stats['frame_sets'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memory_changes")
        stats['memory_changes'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM annotations")
        stats['annotations'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT address) FROM memory_changes")
        stats['unique_addresses'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT context) FROM annotations")
        stats['unique_contexts'] = cursor.fetchone()[0]
        
        return stats


def main():
    """Main function to handle command line arguments and run the ingestion."""
    parser = argparse.ArgumentParser(description="Ingest GBA training data into SQLite database")
    parser.add_argument("session_uuid", help="Session UUID to process")
    parser.add_argument("--data-dir", default="data", help="Base data directory (default: data)")
    parser.add_argument("--db-path", default="gba_training.db", help="SQLite database path (default: gba_training.db)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        
    # Validate inputs
    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        logger.error(f"Data directory not found: {data_dir}")
        sys.exit(1)
        
    session_dir = data_dir / args.session_uuid
    if not session_dir.exists():
        logger.error(f"Session directory not found: {session_dir}")
        sys.exit(1)
        
    # Initialize ingestor
    ingestor = TrainingDataIngestor(args.db_path)
    
    try:
        ingestor.connect()
        logger.info(f"Connected to database: {args.db_path}")
        
        # Process the session
        ingestor.process_directory(data_dir, args.session_uuid)
        
        # Print statistics
        stats = ingestor.get_stats()
        logger.info("Database Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
            
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        sys.exit(1)
        
    finally:
        ingestor.disconnect()
        logger.info("Database connection closed")


if __name__ == "__main__":
    main()
