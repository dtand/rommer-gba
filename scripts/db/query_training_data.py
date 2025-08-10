#!/usr/bin/env python3
"""
Test script to demonstrate the training data ingestion and query the results.
"""

import sqlite3
import json
from pathlib import Path

def query_database(db_path: str = "gba_training.db"):
    """Query the database to show some example data."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== DATABASE STATISTICS ===")
    
    # Overall stats
    cursor.execute("SELECT COUNT(*) FROM sessions")
    print(f"Total sessions: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM frame_sets")
    print(f"Total frame sets: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM memory_changes")
    print(f"Total memory changes: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM annotations")
    print(f"Total annotations: {cursor.fetchone()[0]}")
    
    print("\n=== SAMPLE ANNOTATIONS ===")
    cursor.execute("""
        SELECT session_uuid, frame_set_id, context, scene, description 
        FROM annotations 
        ORDER BY session_uuid, frame_set_id 
        LIMIT 5
    """)
    
    for row in cursor.fetchall():
        print(f"Session: {row[0][:8]}... | Frame Set: {row[1]} | Context: {row[2]} | Scene: {row[3]}")
        print(f"  Description: {row[4]}")
        print()
    
    print("=== MEMORY ADDRESSES BY CONTEXT ===")
    cursor.execute("""
        SELECT a.context, COUNT(DISTINCT mc.address) as unique_addresses, COUNT(mc.id) as total_changes
        FROM annotations a
        JOIN memory_changes mc ON a.session_uuid = mc.session_uuid AND a.frame_set_id = mc.frame_set_id
        GROUP BY a.context
        ORDER BY total_changes DESC
    """)
    
    for row in cursor.fetchall():
        print(f"Context: {row[0]} | Unique Addresses: {row[1]} | Total Changes: {row[2]}")
    
    print("\n=== SAMPLE MEMORY CHANGES FOR BATTLE CONTEXT ===")
    cursor.execute("""
        SELECT mc.address, mc.prev_val, mc.curr_val, a.description
        FROM memory_changes mc
        JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
        WHERE a.context = 'battle'
        ORDER BY mc.address
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"Address: {row[0]} | {row[1]} -> {row[2]} | Context: {row[3][:50]}...")
    
    conn.close()

def find_health_related_addresses(db_path: str = "gba_training.db"):
    """Example query to find memory addresses related to health changes."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("\n=== POTENTIAL HEALTH-RELATED ADDRESSES ===")
    cursor.execute("""
        SELECT mc.address, COUNT(*) as change_count, 
               GROUP_CONCAT(DISTINCT a.description) as contexts
        FROM memory_changes mc
        JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
        WHERE a.description LIKE '%health%' 
           OR a.description LIKE '%damage%' 
           OR a.description LIKE '%Function ceased%'
           OR a.description LIKE '%HP%'
        GROUP BY mc.address
        HAVING change_count > 1
        ORDER BY change_count DESC
        LIMIT 10
    """)
    
    for row in cursor.fetchall():
        print(f"Address: {row[0]} | Changes: {row[1]}")
        print(f"  Contexts: {row[2][:100]}...")
        print()
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else "gba_training.db"
    
    if not Path(db_path).exists():
        print(f"Database not found: {db_path}")
        print("Run the ingestion script first:")
        print(f"python ingest_training_data.py <session_uuid>")
        sys.exit(1)
    
    query_database(db_path)
    find_health_related_addresses(db_path)
