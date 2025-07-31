import sqlite3
import json
import argparse
from datetime import datetime

class GBATrainingQueryTool:
    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
    
    def list_sessions(self):
        """List all sessions in the database."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT s.*, 
                   COUNT(DISTINCT f.id) as frame_count,
                   COUNT(DISTINCT a.frame_id) as annotated_count,
                   COUNT(DISTINCT ts.id) as training_samples
            FROM sessions s
            LEFT JOIN frames f ON s.id = f.session_id
            LEFT JOIN annotations a ON f.id = a.frame_id
            LEFT JOIN training_samples ts ON s.id = ts.session_id
            GROUP BY s.id
            ORDER BY s.created_at DESC
        ''')
        
        sessions = cursor.fetchall()
        
        print("Available Sessions:")
        print("-" * 80)
        for session in sessions:
            print(f"ID: {session['id']}")
            print(f"Name: {session['name']}")
            print(f"Created: {session['created_at']}")
            print(f"Frames: {session['frame_count']} ({session['annotated_count']} annotated)")
            print(f"Training samples: {session['training_samples']}")
            print("-" * 80)
    
    def show_session_details(self, session_id):
        """Show detailed information about a session."""
        cursor = self.conn.cursor()
        
        # Basic session info
        cursor.execute('SELECT * FROM sessions WHERE id = ?', (session_id,))
        session = cursor.fetchone()
        
        if not session:
            print(f"Session {session_id} not found")
            return
        
        print(f"Session Details: {session['name']}")
        print("=" * 50)
        
        # Frame statistics
        cursor.execute('''
            SELECT 
                MIN(frame_number) as min_frame,
                MAX(frame_number) as max_frame,
                COUNT(*) as total_frames,
                COUNT(CASE WHEN has_annotation THEN 1 END) as annotated_frames
            FROM frames WHERE session_id = ?
        ''', (session_id,))
        frame_stats = cursor.fetchone()
        
        print(f"Frame range: {frame_stats['min_frame']} - {frame_stats['max_frame']}")
        print(f"Total frames: {frame_stats['total_frames']}")
        print(f"Annotated frames: {frame_stats['annotated_frames']}")
        print(f"Annotation rate: {frame_stats['annotated_frames'] / frame_stats['total_frames'] * 100:.1f}%")
        
        # Memory change statistics
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT mc.address) as unique_addresses,
                COUNT(mc.id) as total_changes,
                AVG(mc.freq) as avg_freq,
                MAX(mc.freq) as max_freq,
                COUNT(DISTINCT mc.region) as regions
            FROM memory_changes mc
            JOIN frames f ON mc.frame_id = f.id
            WHERE f.session_id = ?
        ''', (session_id,))
        mem_stats = cursor.fetchone()
        
        print(f"Unique addresses: {mem_stats['unique_addresses']}")
        print(f"Total memory changes: {mem_stats['total_changes']}")
        print(f"Average frequency: {mem_stats['avg_freq']:.2f}")
        print(f"Max frequency: {mem_stats['max_freq']}")
        print(f"Memory regions: {mem_stats['regions']}")
        
        # Training sample statistics
        cursor.execute('''
            SELECT 
                sample_type,
                window_size,
                COUNT(*) as count
            FROM training_samples 
            WHERE session_id = ?
            GROUP BY sample_type, window_size
        ''', (session_id,))
        sample_stats = cursor.fetchall()
        
        if sample_stats:
            print("\nTraining Samples:")
            for stat in sample_stats:
                if stat['sample_type'] == 'windowed':
                    print(f"  {stat['sample_type']} (window={stat['window_size']}): {stat['count']}")
                else:
                    print(f"  {stat['sample_type']}: {stat['count']}")
    
    def query_frames(self, session_id, limit=10, has_annotation=None, address_filter=None):
        """Query frames with optional filters."""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT f.frame_number, f.pc, f.has_annotation,
                   COUNT(mc.id) as memory_changes
            FROM frames f
            LEFT JOIN memory_changes mc ON f.id = mc.frame_id
            WHERE f.session_id = ?
        '''
        params = [session_id]
        
        if has_annotation is not None:
            query += ' AND f.has_annotation = ?'
            params.append(has_annotation)
        
        if address_filter:
            query += ''' AND f.id IN (
                SELECT DISTINCT frame_id FROM memory_changes 
                WHERE address LIKE ?
            )'''
            params.append(f'%{address_filter}%')
        
        query += ' GROUP BY f.id ORDER BY f.frame_number LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        frames = cursor.fetchall()
        
        print(f"Frames (limit {limit}):")
        print("-" * 60)
        for frame in frames:
            annotation_status = "✓" if frame['has_annotation'] else " "
            print(f"[{annotation_status}] Frame {frame['frame_number']:6d} | PC: {frame['pc']:10s} | Changes: {frame['memory_changes']:3d}")
    
    def show_memory_hotspots(self, session_id, limit=20):
        """Show most frequently changed memory addresses."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT 
                mc.region,
                mc.address,
                COUNT(*) as change_count,
                SUM(mc.freq) as total_freq,
                AVG(mc.freq) as avg_freq,
                MIN(f.frame_number) as first_frame,
                MAX(f.frame_number) as last_frame
            FROM memory_changes mc
            JOIN frames f ON mc.frame_id = f.id
            WHERE f.session_id = ?
            GROUP BY mc.region, mc.address
            ORDER BY change_count DESC
            LIMIT ?
        ''', (session_id, limit))
        
        hotspots = cursor.fetchall()
        
        print(f"Memory Hotspots (top {limit}):")
        print("-" * 80)
        print(f"{'Region':<8} {'Address':<12} {'Changes':<8} {'Total Freq':<10} {'Avg Freq':<8} {'Frame Range'}")
        print("-" * 80)
        
        for spot in hotspots:
            frame_range = f"{spot['first_frame']}-{spot['last_frame']}"
            print(f"{spot['region']:<8} {spot['address']:<12} {spot['change_count']:<8} "
                  f"{spot['total_freq']:<10} {spot['avg_freq']:<8.2f} {frame_range}")
    
    def export_samples_by_criteria(self, session_id, output_file, sample_type=None, 
                                 window_size=None, limit=None):
        """Export training samples with specific criteria."""
        cursor = self.conn.cursor()
        
        query = '''
            SELECT prompt, completion FROM training_samples 
            WHERE session_id = ?
        '''
        params = [session_id]
        
        if sample_type:
            query += ' AND sample_type = ?'
            params.append(sample_type)
        
        if window_size:
            query += ' AND window_size = ?'
            params.append(window_size)
        
        query += ' ORDER BY id'
        
        if limit:
            query += ' LIMIT ?'
            params.append(limit)
        
        cursor.execute(query, params)
        samples = cursor.fetchall()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for sample in samples:
                json.dump({
                    'prompt': sample['prompt'],
                    'completion': sample['completion']
                }, f, ensure_ascii=False)
                f.write('\n')
        
        print(f"Exported {len(samples)} samples to {output_file}")
    
    def analyze_annotation_patterns(self, session_id):
        """Analyze patterns in annotations."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT context, scene, tags, description
            FROM annotations a
            JOIN frames f ON a.frame_id = f.id
            WHERE f.session_id = ?
        ''', (session_id,))
        
        annotations = cursor.fetchall()
        
        # Count unique values
        contexts = {}
        scenes = {}
        tags = {}
        
        for ann in annotations:
            if ann['context']:
                contexts[ann['context']] = contexts.get(ann['context'], 0) + 1
            if ann['scene']:
                scenes[ann['scene']] = scenes.get(ann['scene'], 0) + 1
            if ann['tags']:
                tags[ann['tags']] = tags.get(ann['tags'], 0) + 1
        
        print("Annotation Patterns:")
        print("=" * 50)
        
        if contexts:
            print("Most common contexts:")
            for context, count in sorted(contexts.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {context}: {count} times")
        
        if scenes:
            print("\nMost common scenes:")
            for scene, count in sorted(scenes.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {scene}: {count} times")
        
        if tags:
            print("\nMost common tags:")
            for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {tag}: {count} times")
    
    def close(self):
        """Close database connection."""
        self.conn.close()

def main():
    parser = argparse.ArgumentParser(description="Query and analyze GBA training database")
    parser.add_argument("--db_path", default="gba_training.db", help="Database file path")
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List sessions command
    subparsers.add_parser('list', help='List all sessions')
    
    # Session details command
    details_parser = subparsers.add_parser('details', help='Show session details')
    details_parser.add_argument('session_id', type=int, help='Session ID')
    
    # Query frames command
    query_parser = subparsers.add_parser('frames', help='Query frames')
    query_parser.add_argument('session_id', type=int, help='Session ID')
    query_parser.add_argument('--limit', type=int, default=10, help='Limit results')
    query_parser.add_argument('--annotated', action='store_true', help='Only annotated frames')
    query_parser.add_argument('--address', help='Filter by address pattern')
    
    # Memory hotspots command
    hotspots_parser = subparsers.add_parser('hotspots', help='Show memory hotspots')
    hotspots_parser.add_argument('session_id', type=int, help='Session ID')
    hotspots_parser.add_argument('--limit', type=int, default=20, help='Limit results')
    
    # Export samples command
    export_parser = subparsers.add_parser('export', help='Export training samples')
    export_parser.add_argument('session_id', type=int, help='Session ID')
    export_parser.add_argument('output_file', help='Output file path')
    export_parser.add_argument('--type', choices=['individual', 'windowed'], help='Sample type')
    export_parser.add_argument('--window_size', type=int, help='Window size for windowed samples')
    export_parser.add_argument('--limit', type=int, help='Limit number of samples')
    
    # Analyze annotations command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze annotation patterns')
    analyze_parser.add_argument('session_id', type=int, help='Session ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    query_tool = GBATrainingQueryTool(args.db_path)
    
    try:
        if args.command == 'list':
            query_tool.list_sessions()
        
        elif args.command == 'details':
            query_tool.show_session_details(args.session_id)
        
        elif args.command == 'frames':
            query_tool.query_frames(
                args.session_id, 
                args.limit, 
                True if args.annotated else None,
                args.address
            )
        
        elif args.command == 'hotspots':
            query_tool.show_memory_hotspots(args.session_id, args.limit)
        
        elif args.command == 'export':
            query_tool.export_samples_by_criteria(
                args.session_id,
                args.output_file,
                args.type,
                args.window_size,
                args.limit
            )
        
        elif args.command == 'analyze':
            query_tool.analyze_annotation_patterns(args.session_id)
    
    finally:
        query_tool.close()

if __name__ == "__main__":
    main()
