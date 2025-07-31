import os
import json
import sqlite3
import argparse
from collections import defaultdict
from datetime import datetime

class GBATrainingDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.setup_database()
    
    def setup_database(self):
        """Initialize the database with required tables."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
        # Create tables
        self.conn.executescript('''
            -- Sessions table
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_frames INTEGER DEFAULT 0
            );
            
            -- Frames table
            CREATE TABLE IF NOT EXISTS frames (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                frame_number INTEGER NOT NULL,
                timestamp INTEGER,
                pc TEXT,
                key_history TEXT,  -- JSON array
                current_keys TEXT, -- JSON array
                has_annotation BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (session_id) REFERENCES sessions (id),
                UNIQUE(session_id, frame_number)
            );
            
            -- Memory changes table
            CREATE TABLE IF NOT EXISTS memory_changes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frame_id INTEGER,
                region TEXT NOT NULL,
                address TEXT NOT NULL,
                prev_val TEXT,
                curr_val TEXT,
                freq INTEGER,
                freq_normalized REAL,
                FOREIGN KEY (frame_id) REFERENCES frames (id)
            );
            
            -- Annotations table
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                frame_id INTEGER UNIQUE,
                context TEXT,
                scene TEXT,
                tags TEXT,
                description TEXT,
                FOREIGN KEY (frame_id) REFERENCES frames (id)
            );
            
            -- Training samples table (for caching formatted samples)
            CREATE TABLE IF NOT EXISTS training_samples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                frame_range TEXT,  -- e.g., "100" or "100-115"
                prompt TEXT NOT NULL,
                completion TEXT NOT NULL,
                sample_type TEXT DEFAULT 'individual',  -- 'individual' or 'windowed'
                window_size INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            );
            
            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_frames_session ON frames(session_id);
            CREATE INDEX IF NOT EXISTS idx_frames_number ON frames(frame_number);
            CREATE INDEX IF NOT EXISTS idx_memory_changes_frame ON memory_changes(frame_id);
            CREATE INDEX IF NOT EXISTS idx_memory_changes_address ON memory_changes(address);
            CREATE INDEX IF NOT EXISTS idx_annotations_frame ON annotations(frame_id);
            CREATE INDEX IF NOT EXISTS idx_training_samples_session ON training_samples(session_id);
        ''')
        
        self.conn.commit()
    
    def load_data_from_directory(self, data_dir, session_name=None):
        """Load frame data from directory into database.
        
        Args:
            data_dir: Path to data directory containing either:
                     - Direct frame folders (legacy mode), or 
                     - Session subdirectories with UUID names
            session_name: Session name to use. If None and data_dir contains sessions,
                         will use the session directory name
        """
        # Check if data_dir contains session directories or frame directories directly
        items = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
        
        # Check if this looks like a session-based structure
        has_session_metadata = any(
            os.path.exists(os.path.join(data_dir, item, 'session_metadata.json'))
            for item in items
        )
        
        if has_session_metadata:
            # Session-based structure - find sessions
            sessions = []
            for item in items:
                metadata_path = os.path.join(data_dir, item, 'session_metadata.json')
                if os.path.exists(metadata_path):
                    sessions.append(item)
            
            if not sessions:
                raise ValueError("No valid sessions found in directory")
            
            if len(sessions) > 1 and not session_name:
                print(f"Multiple sessions found: {sessions}")
                print("Please specify --session_name or process one session at a time")
                return None
            
            # Use the specified session or the only available one
            if session_name:
                if session_name not in sessions:
                    raise ValueError(f"Session '{session_name}' not found. Available: {sessions}")
                session_dir = os.path.join(data_dir, session_name)
                actual_session_name = session_name
            else:
                session_dir = os.path.join(data_dir, sessions[0])
                actual_session_name = sessions[0]
            
            # Load session metadata if available
            metadata_path = os.path.join(session_dir, 'session_metadata.json')
            session_metadata = {}
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    session_metadata = json.load(f)
            
            print(f"Loading session-based data from {session_dir}")
            print(f"Session metadata: {session_metadata}")
            
        else:
            # Legacy structure - direct frame folders
            session_dir = data_dir
            actual_session_name = session_name or "default_session"
            print(f"Loading legacy data from {data_dir} into session '{actual_session_name}'...")
        
        return self._load_frames_from_session_directory(session_dir, actual_session_name)
    
    def _load_frames_from_session_directory(self, session_dir, session_name):
        """Load frame data from a specific session directory."""
        print(f"Loading data from {session_dir} into session '{session_name}'...")
        
        # Create or get session
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO sessions (name) VALUES (?)
        ''', (session_name,))
        session_id = cursor.lastrowid
        
        # Get existing session if it was already there
        if cursor.rowcount == 0:
            cursor.execute('SELECT id FROM sessions WHERE name = ?', (session_name,))
            session_id = cursor.fetchone()[0]
        
        # Get all frame directories
        frame_dirs = [d for d in os.listdir(session_dir) if d.isdigit()]
        frame_dirs.sort(key=int)
        
        frames_loaded = 0
        annotations_loaded = 0
        
        for frame_dir in frame_dirs:
            frame_path = os.path.join(session_dir, frame_dir)
            event_path = os.path.join(frame_path, 'event.json')
            annotation_path = os.path.join(frame_path, 'annotations.json')
            
            if not os.path.exists(event_path):
                continue
            
            # Load event data
            with open(event_path, 'r', encoding='utf-8') as f:
                event_data = json.load(f)
            
            frame_number = int(frame_dir)
            
            # Insert frame
            cursor.execute('''
                INSERT OR REPLACE INTO frames 
                (session_id, frame_number, timestamp, pc, key_history, current_keys, has_annotation)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                frame_number,
                event_data.get('timestamp'),
                event_data.get('pc'),
                json.dumps(event_data.get('key_history', [])),
                json.dumps(event_data.get('current_keys', [])),
                os.path.exists(annotation_path)
            ))
            
            frame_id = cursor.lastrowid
            if cursor.rowcount == 0:
                # Frame already exists, get its ID
                cursor.execute('''
                    SELECT id FROM frames WHERE session_id = ? AND frame_number = ?
                ''', (session_id, frame_number))
                frame_id = cursor.fetchone()[0]
                # Clear existing memory changes
                cursor.execute('DELETE FROM memory_changes WHERE frame_id = ?', (frame_id,))
            
            # Insert memory changes
            for change in event_data.get('memory_changes', []):
                cursor.execute('''
                    INSERT INTO memory_changes 
                    (frame_id, region, address, prev_val, curr_val, freq)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    frame_id,
                    change.get('region'),
                    change.get('address'),
                    change.get('prev_val'),
                    change.get('curr_val'),
                    change.get('freq')
                ))
            
            # Load annotation if exists
            if os.path.exists(annotation_path):
                with open(annotation_path, 'r', encoding='utf-8') as f:
                    annotation_data = json.load(f)
                
                cursor.execute('''
                    INSERT OR REPLACE INTO annotations 
                    (frame_id, context, scene, tags, description)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    frame_id,
                    annotation_data.get('context'),
                    annotation_data.get('scene'),
                    annotation_data.get('tags'),
                    annotation_data.get('description')
                ))
                annotations_loaded += 1
            
            frames_loaded += 1
        
        # Update session frame count
        cursor.execute('''
            UPDATE sessions SET total_frames = ? WHERE id = ?
        ''', (frames_loaded, session_id))
        
        self.conn.commit()
        print(f"Loaded {frames_loaded} frames and {annotations_loaded} annotations")
        return session_id
    
    def normalize_frequencies(self, session_id, freq_method='max_normalize'):
        """Normalize frequency values within a session."""
        print(f"Normalizing frequencies using method: {freq_method}")
        cursor = self.conn.cursor()
        
        if freq_method == 'max_normalize':
            # Traditional max normalization
            cursor.execute('''
                SELECT MAX(mc.freq) as max_freq
                FROM memory_changes mc
                JOIN frames f ON mc.frame_id = f.id
                WHERE f.session_id = ? AND mc.freq IS NOT NULL
            ''', (session_id,))
            
            result = cursor.fetchone()
            max_freq = result['max_freq'] if result and result['max_freq'] else 1
            
            if max_freq == 0:
                max_freq = 1
            
            # Update normalized frequencies
            cursor.execute('''
                UPDATE memory_changes 
                SET freq_normalized = CAST(freq AS REAL) / ?
                WHERE frame_id IN (
                    SELECT id FROM frames WHERE session_id = ?
                )
            ''', (max_freq, session_id))
            
            print(f"Max normalization applied (max_freq: {max_freq})")
            
        elif freq_method == 'percentile_clamp':
            # Clamp extreme outliers to 95th percentile, then normalize
            cursor.execute('''
                SELECT freq
                FROM memory_changes mc
                JOIN frames f ON mc.frame_id = f.id
                WHERE f.session_id = ? AND mc.freq IS NOT NULL
                ORDER BY mc.freq
            ''', (session_id,))
            
            freqs = [row['freq'] for row in cursor.fetchall()]
            if freqs:
                percentile_95 = freqs[int(len(freqs) * 0.95)]
                
                # Clamp and normalize
                cursor.execute('''
                    UPDATE memory_changes 
                    SET freq_normalized = CASE 
                        WHEN freq > ? THEN 1.0
                        ELSE CAST(freq AS REAL) / ?
                    END
                    WHERE frame_id IN (
                        SELECT id FROM frames WHERE session_id = ?
                    )
                ''', (percentile_95, percentile_95, session_id))
                
                print(f"Percentile clamping applied (95th percentile: {percentile_95})")
            
        elif freq_method == 'log_scale':
            # Logarithmic scaling to reduce extreme values
            cursor.execute('''
                UPDATE memory_changes 
                SET freq_normalized = (LOG(freq + 1) / LOG((
                    SELECT MAX(freq) + 1 
                    FROM memory_changes mc2 
                    JOIN frames f2 ON mc2.frame_id = f2.id 
                    WHERE f2.session_id = ?
                )))
                WHERE frame_id IN (
                    SELECT id FROM frames WHERE session_id = ?
                ) AND freq IS NOT NULL
            ''', (session_id, session_id))
            
            print("Logarithmic scaling applied")
            
        elif freq_method == 'rank_normalize':
            # Rank-based normalization (less sensitive to outliers)
            cursor.execute('''
                WITH ranked_freqs AS (
                    SELECT mc.id, 
                           RANK() OVER (ORDER BY mc.freq) as freq_rank,
                           COUNT(*) OVER () as total_count
                    FROM memory_changes mc
                    JOIN frames f ON mc.frame_id = f.id
                    WHERE f.session_id = ? AND mc.freq IS NOT NULL
                )
                UPDATE memory_changes 
                SET freq_normalized = (
                    SELECT CAST(freq_rank AS REAL) / total_count 
                    FROM ranked_freqs 
                    WHERE ranked_freqs.id = memory_changes.id
                )
                WHERE id IN (SELECT id FROM ranked_freqs)
            ''', (session_id,))
            
            print("Rank-based normalization applied")
        
        self.conn.commit()
    
    def generate_training_samples(self, session_id, include_freq=True, 
                                include_session_id=True, window_size=None):
        """Generate training samples and store them in the database."""
        print("Generating training samples...")
        
        # Clear existing training samples for this session
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM training_samples WHERE session_id = ?', (session_id,))
        
        if window_size:
            self._generate_windowed_samples(session_id, window_size, include_freq, include_session_id)
        else:
            self._generate_individual_samples(session_id, include_freq, include_session_id)
        
        self.conn.commit()
        
        # Get count of generated samples
        cursor.execute('''
            SELECT COUNT(*) as count FROM training_samples WHERE session_id = ?
        ''', (session_id,))
        count = cursor.fetchone()['count']
        print(f"Generated {count} training samples")
        return count
    
    def _generate_individual_samples(self, session_id, include_freq, include_session_id):
        """Generate individual frame samples."""
        cursor = self.conn.cursor()
        
        # Get all annotated frames
        cursor.execute('''
            SELECT f.*, a.context, a.scene, a.tags, a.description
            FROM frames f
            JOIN annotations a ON f.id = a.frame_id
            WHERE f.session_id = ?
            ORDER BY f.frame_number
        ''', (session_id,))
        
        frames = cursor.fetchall()
        
        for frame in frames:
            prompt = self._build_prompt(frame, session_id, include_freq, include_session_id)
            completion = self._build_completion(frame)
            
            if completion:
                cursor.execute('''
                    INSERT INTO training_samples 
                    (session_id, frame_range, prompt, completion, sample_type)
                    VALUES (?, ?, ?, ?, 'individual')
                ''', (session_id, str(frame['frame_number']), prompt, completion))
    
    def _generate_windowed_samples(self, session_id, window_size, include_freq, include_session_id):
        """Generate windowed samples."""
        cursor = self.conn.cursor()
        
        # Get all frames in order
        cursor.execute('''
            SELECT * FROM frames 
            WHERE session_id = ? 
            ORDER BY frame_number
        ''', (session_id,))
        
        frames = cursor.fetchall()
        
        # Create windows
        for i in range(0, len(frames), window_size):
            window = frames[i:i + window_size]
            if len(window) < window_size:
                continue
            
            last_frame = window[-1]
            
            # Check if last frame has annotation
            cursor.execute('''
                SELECT * FROM annotations WHERE frame_id = ?
            ''', (last_frame['id'],))
            annotation = cursor.fetchone()
            
            if not annotation:
                continue
            
            # Aggregate memory changes for this window
            frame_ids = [f['id'] for f in window]
            cursor.execute(f'''
                SELECT region, address, 
                       MIN(prev_val) as first_prev_val,
                       MAX(curr_val) as last_curr_val,
                       SUM(freq) as total_freq,
                       SUM(freq_normalized) as total_freq_normalized
                FROM memory_changes 
                WHERE frame_id IN ({','.join(['?'] * len(frame_ids))})
                GROUP BY region, address
            ''', frame_ids)
            
            aggregated_changes = cursor.fetchall()
            
            # Build aggregated frame data
            aggregated_frame = {
                'id': last_frame['id'],
                'frame_number': f"{window[0]['frame_number']}-{window[-1]['frame_number']}",
                'timestamp': last_frame['timestamp'],
                'pc': last_frame['pc'],
                'key_history': last_frame['key_history'],
                'current_keys': last_frame['current_keys'],
                'context': annotation['context'],
                'scene': annotation['scene'],
                'tags': annotation['tags'],
                'description': annotation['description'],
                'memory_changes': aggregated_changes
            }
            
            prompt = self._build_prompt_windowed(aggregated_frame, session_id, include_freq, include_session_id)
            completion = self._build_completion(annotation)
            
            if completion:
                cursor.execute('''
                    INSERT INTO training_samples 
                    (session_id, frame_range, prompt, completion, sample_type, window_size)
                    VALUES (?, ?, ?, ?, 'windowed', ?)
                ''', (session_id, aggregated_frame['frame_number'], prompt, completion, window_size))
    
    def _build_prompt(self, frame, session_id, include_freq, include_session_id):
        """Build prompt for individual frame."""
        cursor = self.conn.cursor()
        
        prompt_parts = []
        
        if include_session_id:
            cursor.execute('SELECT name FROM sessions WHERE id = ?', (session_id,))
            session_name = cursor.fetchone()['name']
            prompt_parts.append(f"Session: {session_name}")
        
        prompt_parts.append(f"Frame: {frame['frame_number']}")
        prompt_parts.append(f"PC: {frame['pc'] or 'N/A'}")
        
        # Key history
        key_history = json.loads(frame['key_history'] or '[]')
        if key_history:
            prompt_parts.append(f"Key history: {', '.join(key_history[-5:])}")
        else:
            prompt_parts.append("Key history: None")
        
        # Current keys
        current_keys = json.loads(frame['current_keys'] or '[]')
        if current_keys:
            prompt_parts.append(f"Current keys: {', '.join(current_keys)}")
        else:
            prompt_parts.append("Current keys: None")
        
        # Memory changes
        cursor.execute('''
            SELECT * FROM memory_changes WHERE frame_id = ?
        ''', (frame['id'],))
        memory_changes = cursor.fetchall()
        
        if memory_changes:
            prompt_parts.append("Memory changes:")
            for change in memory_changes:
                change_line = f"- {change['region']}: {change['address']}, {change['prev_val']} → {change['curr_val']}"
                if include_freq:
                    freq = change['freq_normalized'] if change['freq_normalized'] else change['freq']
                    change_line += f", freq={freq:.3f}"
                prompt_parts.append(change_line)
        else:
            prompt_parts.append("Memory changes: None")
        
        return "\n".join(prompt_parts)
    
    def _build_prompt_windowed(self, aggregated_frame, session_id, include_freq, include_session_id):
        """Build prompt for windowed sample."""
        cursor = self.conn.cursor()
        
        prompt_parts = []
        
        if include_session_id:
            cursor.execute('SELECT name FROM sessions WHERE id = ?', (session_id,))
            session_name = cursor.fetchone()['name']
            prompt_parts.append(f"Session: {session_name}")
        
        prompt_parts.append(f"Frame: {aggregated_frame['frame_number']}")
        prompt_parts.append(f"PC: {aggregated_frame['pc'] or 'N/A'}")
        
        # Key history
        key_history = json.loads(aggregated_frame['key_history'] or '[]')
        if key_history:
            prompt_parts.append(f"Key history: {', '.join(key_history[-5:])}")
        else:
            prompt_parts.append("Key history: None")
        
        # Current keys
        current_keys = json.loads(aggregated_frame['current_keys'] or '[]')
        if current_keys:
            prompt_parts.append(f"Current keys: {', '.join(current_keys)}")
        else:
            prompt_parts.append("Current keys: None")
        
        # Memory changes
        if aggregated_frame['memory_changes']:
            prompt_parts.append("Memory changes:")
            for change in aggregated_frame['memory_changes']:
                change_line = f"- {change['region']}: {change['address']}, {change['first_prev_val']} → {change['last_curr_val']}"
                if include_freq:
                    freq = change['total_freq_normalized'] if change['total_freq_normalized'] else change['total_freq']
                    change_line += f", freq={freq:.3f}"
                prompt_parts.append(change_line)
        else:
            prompt_parts.append("Memory changes: None")
        
        return "\n".join(prompt_parts)
    
    def _build_completion(self, annotation):
        """Build completion from annotation."""
        completion_parts = []
        
        # Handle both dict and sqlite3.Row objects
        if hasattr(annotation, 'get'):
            # Dictionary-like access
            context = annotation.get('context')
            scene = annotation.get('scene')
            tags = annotation.get('tags')
            description = annotation.get('description')
        else:
            # sqlite3.Row access
            context = annotation['context'] if annotation['context'] else None
            scene = annotation['scene'] if annotation['scene'] else None
            tags = annotation['tags'] if annotation['tags'] else None
            description = annotation['description'] if annotation['description'] else None
        
        if context:
            completion_parts.append(f"Context: {context}")
        if scene:
            completion_parts.append(f"Scene: {scene}")
        if tags:
            completion_parts.append(f"Tags: {tags}")
        if description:
            completion_parts.append(f"Description: {description}")
        
        return "\n".join(completion_parts) if completion_parts else None
    
    def export_training_data(self, session_id, output_file, format_type='jsonl'):
        """Export training samples to file."""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT prompt, completion FROM training_samples 
            WHERE session_id = ?
            ORDER BY id
        ''', (session_id,))
        
        samples = cursor.fetchall()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            if format_type == 'jsonl':
                for sample in samples:
                    json.dump({
                        'prompt': sample['prompt'],
                        'completion': sample['completion']
                    }, f, ensure_ascii=False)
                    f.write('\n')
            elif format_type == 'json':
                json.dump([{
                    'prompt': sample['prompt'],
                    'completion': sample['completion']
                } for sample in samples], f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(samples)} training samples to {output_file}")
    
    def get_session_stats(self, session_id):
        """Get statistics for a session."""
        cursor = self.conn.cursor()
        
        # Basic stats
        cursor.execute('''
            SELECT 
                s.name,
                s.total_frames,
                COUNT(DISTINCT a.frame_id) as annotated_frames,
                COUNT(DISTINCT mc.address) as unique_addresses,
                COUNT(mc.id) as total_memory_changes
            FROM sessions s
            LEFT JOIN frames f ON s.id = f.session_id
            LEFT JOIN annotations a ON f.id = a.frame_id
            LEFT JOIN memory_changes mc ON f.id = mc.frame_id
            WHERE s.id = ?
            GROUP BY s.id
        ''', (session_id,))
        
        stats = cursor.fetchone()
        return dict(stats) if stats else None
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    @staticmethod
    def list_sessions(data_dir):
        """List available sessions in a data directory."""
        sessions = []
        if not os.path.exists(data_dir):
            return sessions
            
        for item in os.listdir(data_dir):
            item_path = os.path.join(data_dir, item)
            if os.path.isdir(item_path):
                metadata_path = os.path.join(item_path, 'session_metadata.json')
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                        sessions.append({
                            'session_id': item,
                            'metadata': metadata
                        })
                    except Exception as e:
                        sessions.append({
                            'session_id': item,
                            'metadata': {'error': f'Failed to read metadata: {str(e)}'}
                        })
        return sessions

def main():
    parser = argparse.ArgumentParser(description="Prepare LLM training data using database storage")
    parser.add_argument("--data_dir", required=True, help="Path to data directory containing session folders or frame folders")
    parser.add_argument("--db_path", default="gba_training.db", help="Database file path")
    parser.add_argument("--session_name", help="Session name to process (required if multiple sessions exist)")
    parser.add_argument("--list_sessions", action='store_true', help="List available sessions and exit")
    parser.add_argument("--output", help="Output file path (optional)")
    parser.add_argument("--format", choices=['jsonl', 'json'], default='jsonl', help="Output format")
    parser.add_argument("--include_freq", action='store_true', default=True, help="Include frequency data")
    parser.add_argument("--include_session_id", action='store_true', default=True, help="Include session ID")
    parser.add_argument("--window_size", type=int, help="Aggregate frames into windows of this size")
    parser.add_argument("--freq_method", choices=['max_normalize', 'percentile_clamp', 'log_scale', 'rank_normalize'], 
                       default='percentile_clamp', help="Frequency normalization method")
    parser.add_argument("--stats_only", action='store_true', help="Only show statistics, don't generate samples")
    
    args = parser.parse_args()
    
    # List sessions if requested
    if args.list_sessions:
        sessions = GBATrainingDatabase.list_sessions(args.data_dir)
        if sessions:
            print("Available sessions:")
            for session in sessions:
                metadata = session['metadata']
                if 'error' in metadata:
                    print(f"  {session['session_id']}: {metadata['error']}")
                else:
                    print(f"  {session['session_id']}: {metadata.get('total_frames', 'N/A')} frames, created {metadata.get('created_at', 'N/A')}")
        else:
            print("No sessions found in directory")
        return
    
    # Initialize database
    db = GBATrainingDatabase(args.db_path)
    
    try:
        # Load data
        session_id = db.load_data_from_directory(args.data_dir, args.session_name)
        
        if session_id is None:
            print("Failed to load data. Exiting.")
            return
        
        # Normalize frequencies
        db.normalize_frequencies(session_id, args.freq_method)
        
        if not args.stats_only:
            # Generate training samples
            sample_count = db.generate_training_samples(
                session_id, 
                args.include_freq, 
                args.include_session_id, 
                args.window_size
            )
            
            # Export if output file specified
            if args.output:
                db.export_training_data(session_id, args.output, args.format)
        
        # Show statistics
        stats = db.get_session_stats(session_id)
        if stats:
            print(f"\nSession Statistics:")
            print(f"  Name: {stats['name']}")
            print(f"  Total frames: {stats['total_frames']}")
            print(f"  Annotated frames: {stats['annotated_frames']}")
            print(f"  Unique addresses: {stats['unique_addresses']}")
            print(f"  Total memory changes: {stats['total_memory_changes']}")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()
