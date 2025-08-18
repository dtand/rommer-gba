#!/usr/bin/env python3
"""
Advanced analysis script for GBA training data.
Provides detailed insights into memory patterns and potential relationships.
"""

import sqlite3
import json
import argparse
from pathlib import Path
from collections import defaultdict
import statistics

class TrainingDataAnalyzer:
    """Analyzes patterns in the training data for insights."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        
    def close(self):
        self.conn.close()
        
    def analyze_address_patterns_by_context(self, context: str = None):
        """Analyze memory address patterns by context."""
        cursor = self.conn.cursor()
        
        where_clause = "WHERE a.context = ?" if context else ""
        params = (context,) if context else ()
        
        query = f"""
        SELECT mc.address, mc.region, 
               COUNT(*) as total_changes,
               COUNT(DISTINCT mc.frame_set_id) as frame_sets_involved,
               AVG(CAST(mc.freq AS FLOAT)) as avg_frequency,
               GROUP_CONCAT(DISTINCT a.context) as contexts,
               GROUP_CONCAT(DISTINCT a.scene) as scenes
        FROM memory_changes mc
        JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
        {where_clause}
        GROUP BY mc.address, mc.region
        HAVING total_changes >= 5
        ORDER BY total_changes DESC
        LIMIT 20
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        context_str = f" for {context}" if context else ""
        print(f"\n=== TOP MEMORY ADDRESSES{context_str.upper()} ===")
        
        for row in results:
            print(f"Address: {row[0]} ({row[1]})")
            print(f"  Total Changes: {row[2]} | Frame Sets: {row[3]} | Avg Freq: {row[4]:.2f}")
            print(f"  Contexts: {row[5]}")
            print(f"  Scenes: {row[6][:100]}...")
            print()
            
    def find_value_transition_patterns(self):
        """Find interesting value transition patterns."""
        cursor = self.conn.cursor()
        
        print("\n=== INTERESTING VALUE TRANSITIONS ===")
        
        # Find addresses with significant value changes
        cursor.execute("""
        SELECT address, prev_val, curr_val, COUNT(*) as occurrences,
               GROUP_CONCAT(DISTINCT a.description) as contexts
        FROM memory_changes mc
        JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
        WHERE CAST('0x' || prev_val AS INTEGER) != CAST('0x' || curr_val AS INTEGER)
        GROUP BY address, prev_val, curr_val
        HAVING occurrences >= 3
        ORDER BY occurrences DESC
        LIMIT 15
        """)
        
        for row in cursor.fetchall():
            try:
                prev_int = int(row[1], 16)
                curr_int = int(row[2], 16)
                diff = curr_int - prev_int
                
                print(f"Address: {row[0]} | {row[1]} -> {row[2]} (Δ{diff:+}) | Count: {row[3]}")
                print(f"  Context: {row[4][:80]}...")
                print()
            except ValueError:
                # Skip non-numeric values
                continue
                
    def analyze_health_damage_correlations(self):
        """Analyze correlations between health/damage events and memory changes."""
        cursor = self.conn.cursor()
        
        print("\n=== HEALTH/DAMAGE EVENT ANALYSIS ===")
        
        # Find addresses that change during health-related events
        cursor.execute("""
        SELECT mc.address, 
               COUNT(CASE WHEN a.description LIKE '%damage%' THEN 1 END) as damage_events,
               COUNT(CASE WHEN a.description LIKE '%health%' THEN 1 END) as health_events,
               COUNT(CASE WHEN a.description LIKE '%Function ceased%' THEN 1 END) as defeat_events,
               COUNT(*) as total_changes,
               GROUP_CONCAT(DISTINCT 
                   CASE 
                       WHEN a.description LIKE '%damage%' OR a.description LIKE '%health%' 
                       THEN a.description 
                   END) as health_contexts
        FROM memory_changes mc
        JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
        WHERE a.description LIKE '%damage%' 
           OR a.description LIKE '%health%' 
           OR a.description LIKE '%Function ceased%'
           OR a.description LIKE '%HP%'
        GROUP BY mc.address
        HAVING (damage_events + health_events + defeat_events) >= 5
        ORDER BY (damage_events + health_events + defeat_events) DESC
        LIMIT 15
        """)
        
        for row in cursor.fetchall():
            print(f"Address: {row[0]}")
            print(f"  Damage Events: {row[1]} | Health Events: {row[2]} | Defeat Events: {row[3]} | Total: {row[4]}")
            if row[5]:
                print(f"  Context: {row[5][:100]}...")
            print()
            
    def analyze_sequential_patterns(self):
        """Analyze patterns in sequential frame sets."""
        cursor = self.conn.cursor()
        
        print("\n=== SEQUENTIAL FRAME ANALYSIS ===")
        
        # Find addresses that change in consecutive frames
        cursor.execute("""
        WITH consecutive_changes AS (
            SELECT mc1.address,
                   mc1.frame_set_id as frame1,
                   mc2.frame_set_id as frame2,
                   a1.description as desc1,
                   a2.description as desc2
            FROM memory_changes mc1
            JOIN memory_changes mc2 ON mc1.session_uuid = mc2.session_uuid 
                                   AND mc1.address = mc2.address
                                   AND mc2.frame_set_id = mc1.frame_set_id + 1
            JOIN annotations a1 ON mc1.session_uuid = a1.session_uuid AND mc1.frame_set_id = a1.frame_set_id
            JOIN annotations a2 ON mc2.session_uuid = a2.session_uuid AND mc2.frame_set_id = a2.frame_set_id
            WHERE a1.context = 'battle' AND a2.context = 'battle'
        )
        SELECT address, COUNT(*) as consecutive_count,
               GROUP_CONCAT(DISTINCT desc1 || ' -> ' || desc2) as transitions
        FROM consecutive_changes
        GROUP BY address
        HAVING consecutive_count >= 3
        ORDER BY consecutive_count DESC
        LIMIT 10
        """)
        
        for row in cursor.fetchall():
            print(f"Address: {row[0]} | Consecutive Changes: {row[1]}")
            print(f"  Transitions: {row[2][:150]}...")
            print()
            
    def export_training_samples(self, output_file: str, context_filter: str = None):
        """Export training samples for LLM training."""
        cursor = self.conn.cursor()
        
        where_clause = "WHERE a.context = ?" if context_filter else ""
        params = (context_filter,) if context_filter else ()
        
        query = f"""
        SELECT a.context, a.scene, a.description, a.action, a.intent, a.outcome,
               fs.buttons, fs.frames_in_set,
               GROUP_CONCAT(mc.address || ':' || mc.prev_val || '->' || mc.curr_val) as memory_changes
        FROM annotations a
        JOIN frame_sets fs ON a.session_uuid = fs.session_uuid AND a.frame_set_id = fs.frame_set_id
        JOIN memory_changes mc ON a.session_uuid = mc.session_uuid AND a.frame_set_id = mc.frame_set_id
        {where_clause}
        GROUP BY a.session_uuid, a.frame_set_id
        ORDER BY a.frame_set_id
        """
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        training_samples = []
        for row in results:
            sample = {
                "context": row[0],
                "scene": row[1], 
                "description": row[2],
                "action": row[3],
                "intent": row[4],
                "outcome": row[5],
                "buttons": json.loads(row[6]) if row[6] else [],
                "frames_in_set": json.loads(row[7]) if row[7] else [],
                "memory_changes": row[8].split(',') if row[8] else []
            }
            training_samples.append(sample)
            
        with open(output_file, 'w') as f:
            json.dump(training_samples, f, indent=2)
            
        print(f"Exported {len(training_samples)} training samples to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Analyze GBA training data patterns")
    parser.add_argument("--db-path", default="gba_training.db", help="SQLite database path")
    parser.add_argument("--context", help="Filter analysis by specific context")
    parser.add_argument("--export", help="Export training samples to JSON file")
    parser.add_argument("--export-context", help="Context filter for export")
    
    args = parser.parse_args()
    
    if not Path(args.db_path).exists():
        print(f"Database not found: {args.db_path}")
        print("Run the ingestion script first")
        return
        
    analyzer = TrainingDataAnalyzer(args.db_path)
    
    try:
        if args.export:
            analyzer.export_training_samples(args.export, args.export_context)
        else:
            analyzer.analyze_address_patterns_by_context(args.context)
            analyzer.find_value_transition_patterns()
            analyzer.analyze_health_damage_correlations()
            analyzer.analyze_sequential_patterns()
    finally:
        analyzer.close()


if __name__ == "__main__":
    main()
