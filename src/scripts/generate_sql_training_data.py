#!/usr/bin/env python3

"""
GBA Memory Analysis Training Data Generator

Generates training data in OpenAI messages format for training an LLM
to convert natural language queries to SQL for GBA memory analysis database.

Output format matches exactly what src/ml/train_llm.py expects.
"""

import sqlite3
import json
import random
from typing import List, Dict, Tuple

class GBATrainingDataGenerator:
    """Generate training data for GBA memory analysis LLM in OpenAI format."""
    
    def __init__(self, db_path: str = "gba_training.db"):
        self.db_path = db_path
        self.schema_info = self._load_schema_info()
        self.sample_data = self._load_sample_data()
        
    def _load_schema_info(self) -> str:
        """Load database schema as a formatted string for the system message."""
        return """Database Schema:

Tables:
- sessions: Game sessions
  * session_uuid (TEXT): Unique session identifier
  * created_at (TIMESTAMP): Session creation time

- frame_sets: Individual game frames
  * id (INTEGER): Primary key
  * session_uuid (TEXT): References sessions
  * frame_set_id (INTEGER): Frame number in session
  * timestamp (INTEGER): Frame timestamp
  * buttons (TEXT): Controller input for this frame
  * frames_in_set (TEXT): Frame data
  * created_at (TIMESTAMP): Record creation time

- memory_changes: Memory address value changes
  * id (INTEGER): Primary key
  * session_uuid (TEXT): References sessions
  * frame_set_id (INTEGER): References frame_sets.id
  * region (TEXT): Memory region
  * frame (INTEGER): Frame number when change occurred
  * address (TEXT): Memory address (hex format)
  * prev_val (TEXT): Previous value
  * curr_val (TEXT): Current value
  * freq (INTEGER): Change frequency
  * created_at (TIMESTAMP): Record creation time

- annotations: Human annotations of game events
  * id (INTEGER): Primary key
  * session_uuid (TEXT): References sessions
  * frame_set_id (INTEGER): References frame_sets.id
  * context (TEXT): Game context (battle, menu, dialog, etc.)
  * scene (TEXT): Specific scene identifier
  * tags (TEXT): Comma-separated tags
  * description (TEXT): Human description of what's happening
  * action_type (TEXT): Type of action
  * intent (TEXT): Player intent
  * outcome (TEXT): Result of action
  * created_at (TIMESTAMP): Record creation time"""

    def _load_sample_data(self) -> Dict:
        """Load sample data to make realistic queries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        samples = {}
        
        # Get sample tags
        cursor.execute("SELECT DISTINCT tags FROM annotations WHERE tags IS NOT NULL LIMIT 30")
        all_tags = set()
        for row in cursor.fetchall():
            if row[0]:
                tags = [tag.strip() for tag in row[0].split(',')]
                all_tags.update(tags)
        samples['tags'] = sorted(list(all_tags))[:50]
        
        # Get sample addresses
        cursor.execute("SELECT DISTINCT address FROM memory_changes ORDER BY address LIMIT 20")
        samples['addresses'] = [row[0] for row in cursor.fetchall()]
        
        # Get sample contexts
        cursor.execute("SELECT DISTINCT context FROM annotations WHERE context IS NOT NULL")
        samples['contexts'] = [row[0] for row in cursor.fetchall()]
        
        # Get sample scenes
        cursor.execute("SELECT DISTINCT scene FROM annotations WHERE scene IS NOT NULL LIMIT 15")
        samples['scenes'] = [row[0] for row in cursor.fetchall()]
        
        conn.close()
        return samples

    def generate_training_examples(self) -> List[Dict]:
        """Generate comprehensive training examples in OpenAI messages format."""
        examples = []
        
        # System message template
        system_message = f"""You are an expert SQL assistant specialized in Game Boy Advance memory analysis. 

{self.schema_info}

Convert natural language queries into accurate SQL statements for this database. Focus on:
- Memory address changes and patterns
- Game event annotations and tags
- Temporal relationships between frames
- Correlations between memory changes and game events"""

        # Generate different types of queries
        examples.extend(self._generate_memory_address_queries(system_message))
        examples.extend(self._generate_annotation_queries(system_message))
        examples.extend(self._generate_temporal_queries(system_message))
        examples.extend(self._generate_join_queries(system_message))
        examples.extend(self._generate_aggregation_queries(system_message))
        examples.extend(self._generate_filtering_queries(system_message))
        
        return examples

    def _create_message_example(self, system_msg: str, user_query: str, sql_response: str) -> Dict:
        """Create a single training example in OpenAI messages format."""
        return {
            "messages": [
                {
                    "role": "system",
                    "content": system_msg
                },
                {
                    "role": "user", 
                    "content": user_query
                },
                {
                    "role": "assistant",
                    "content": sql_response
                }
            ]
        }

    def _generate_memory_address_queries(self, system_msg: str) -> List[Dict]:
        """Generate queries focused on memory addresses."""
        examples = []
        
        # Template-based examples
        templates = [
            {
                "user": "Show me all memory addresses that change when {event}",
                "sql": "SELECT DISTINCT mc.address, COUNT(*) as change_count FROM memory_changes mc JOIN annotations a ON mc.frame_set_id = a.frame_set_id WHERE a.tags LIKE '%{tag}%' GROUP BY mc.address ORDER BY change_count DESC"
            },
            {
                "user": "What memory addresses change during {context} events?",
                "sql": "SELECT DISTINCT mc.address FROM memory_changes mc JOIN annotations a ON mc.frame_set_id = a.frame_set_id WHERE a.context = '{context}'"
            },
            {
                "user": "Find the most frequently changing memory addresses",
                "sql": "SELECT address, COUNT(*) as change_frequency FROM memory_changes GROUP BY address ORDER BY change_frequency DESC LIMIT 10"
            }
        ]
        
        # Generate variations
        events_and_tags = [
            ("the player takes damage", "damage"),
            ("entering battle", "battle"), 
            ("opening menus", "menu"),
            ("enemies appear", "enemy"),
            ("health changes", "health"),
            ("animations play", "animation"),
            ("dialog appears", "dialog")
        ]
        
        for template in templates:
            if "{event}" in template["user"]:
                for event, tag in events_and_tags:
                    user_query = template["user"].format(event=event)
                    sql_query = template["sql"].format(tag=tag)
                    examples.append(self._create_message_example(system_msg, user_query, sql_query))
            elif "{context}" in template["user"]:
                for context in self.sample_data['contexts'][:5]:
                    if context:
                        user_query = template["user"].format(context=context)
                        sql_query = template["sql"].format(context=context)
                        examples.append(self._create_message_example(system_msg, user_query, sql_query))
            else:
                examples.append(self._create_message_example(system_msg, template["user"], template["sql"]))
        
        # Specific address queries
        for addr in self.sample_data['addresses'][:5]:
            examples.extend([
                self._create_message_example(
                    system_msg,
                    f"Show me all changes to memory address {addr}",
                    f"SELECT * FROM memory_changes WHERE address = '{addr}' ORDER BY frame"
                ),
                self._create_message_example(
                    system_msg,
                    f"When does address {addr} change value?",
                    f"SELECT frame_set_id, frame, prev_val, curr_val FROM memory_changes WHERE address = '{addr}'"
                )
            ])
            
        return examples

    def _generate_annotation_queries(self, system_msg: str) -> List[Dict]:
        """Generate queries focused on annotations and tags."""
        examples = []
        
        # Tag-based queries
        for tag in self.sample_data['tags'][:15]:
            if tag and len(tag) > 2:
                examples.extend([
                    self._create_message_example(
                        system_msg,
                        f"Find all annotations tagged with {tag}",
                        f"SELECT * FROM annotations WHERE tags LIKE '%{tag}%'"
                    ),
                    self._create_message_example(
                        system_msg,
                        f"Show me game events related to {tag}",
                        f"SELECT description, context, scene FROM annotations WHERE tags LIKE '%{tag}%'"
                    )
                ])
        
        # Multi-tag queries
        if len(self.sample_data['tags']) >= 2:
            for i in range(5):
                tag1, tag2 = random.sample(self.sample_data['tags'][:20], 2)
                examples.append(self._create_message_example(
                    system_msg,
                    f"Find events that involve both {tag1} and {tag2}",
                    f"SELECT * FROM annotations WHERE tags LIKE '%{tag1}%' AND tags LIKE '%{tag2}%'"
                ))
        
        # Context-based queries
        for context in self.sample_data['contexts'][:8]:
            if context:
                examples.append(self._create_message_example(
                    system_msg,
                    f"Show me all {context} related annotations",
                    f"SELECT * FROM annotations WHERE context = '{context}'"
                ))
        
        return examples

    def _generate_temporal_queries(self, system_msg: str) -> List[Dict]:
        """Generate time-based queries."""
        examples = []
        
        temporal_templates = [
            {
                "user": "Show me the first {n} frames of the session",
                "sql": "SELECT * FROM frame_sets ORDER BY frame_set_id LIMIT {n}"
            },
            {
                "user": "Find the last {n} memory changes",
                "sql": "SELECT * FROM memory_changes ORDER BY id DESC LIMIT {n}"
            },
            {
                "user": "Get frames between frame {start} and {end}",
                "sql": "SELECT * FROM frame_sets WHERE frame_set_id BETWEEN {start} AND {end}"
            },
            {
                "user": "What happened at frame {frame}?",
                "sql": "SELECT fs.*, a.description, a.tags FROM frame_sets fs LEFT JOIN annotations a ON fs.id = a.frame_set_id WHERE fs.frame_set_id = {frame}"
            }
        ]
        
        for template in temporal_templates:
            for _ in range(3):  # Generate 3 variations
                params = {}
                if "{n}" in template["sql"]:
                    params["n"] = random.choice([5, 10, 20, 50])
                elif "{start}" in template["sql"]:
                    start = random.randint(1, 100)
                    params["start"] = start
                    params["end"] = start + random.randint(10, 50)
                elif "{frame}" in template["sql"]:
                    params["frame"] = random.randint(1, 500)
                
                if params:
                    user_query = template["user"].format(**params)
                    sql_query = template["sql"].format(**params)
                    examples.append(self._create_message_example(system_msg, user_query, sql_query))
        
        return examples

    def _generate_join_queries(self, system_msg: str) -> List[Dict]:
        """Generate complex join queries."""
        examples = []
        
        join_templates = [
            {
                "user": "Show me memory changes with their corresponding annotations",
                "sql": "SELECT mc.address, mc.prev_val, mc.curr_val, a.description, a.tags FROM memory_changes mc JOIN annotations a ON mc.frame_set_id = a.frame_set_id"
            },
            {
                "user": "Find frame information along with memory changes for {tag} events",
                "sql": "SELECT fs.frame_set_id, fs.timestamp, mc.address, mc.curr_val, a.description FROM frame_sets fs JOIN annotations a ON fs.id = a.frame_set_id JOIN memory_changes mc ON fs.id = mc.frame_set_id WHERE a.tags LIKE '%{tag}%'"
            },
            {
                "user": "Get all data for frames that have both annotations and memory changes",
                "sql": "SELECT fs.*, a.description, a.tags, COUNT(mc.id) as change_count FROM frame_sets fs JOIN annotations a ON fs.id = a.frame_set_id JOIN memory_changes mc ON fs.id = mc.frame_set_id GROUP BY fs.id"
            }
        ]
        
        for template in join_templates:
            if "{tag}" in template["sql"]:
                for tag in self.sample_data['tags'][:8]:
                    if tag:
                        user_query = template["user"].format(tag=tag)
                        sql_query = template["sql"].format(tag=tag)
                        examples.append(self._create_message_example(system_msg, user_query, sql_query))
            else:
                examples.append(self._create_message_example(system_msg, template["user"], template["sql"]))
        
        return examples

    def _generate_aggregation_queries(self, system_msg: str) -> List[Dict]:
        """Generate aggregation and counting queries."""
        examples = []
        
        agg_templates = [
            {
                "user": "How many memory changes occurred in total?",
                "sql": "SELECT COUNT(*) FROM memory_changes"
            },
            {
                "user": "Count annotations by context type",
                "sql": "SELECT context, COUNT(*) as count FROM annotations WHERE context IS NOT NULL GROUP BY context ORDER BY count DESC"
            },
            {
                "user": "Show me tag frequency in annotations",
                "sql": "SELECT tags, COUNT(*) as frequency FROM annotations WHERE tags IS NOT NULL GROUP BY tags ORDER BY frequency DESC"
            },
            {
                "user": "What's the average number of memory changes per frame?",
                "sql": "SELECT AVG(change_count) FROM (SELECT frame_set_id, COUNT(*) as change_count FROM memory_changes GROUP BY frame_set_id)"
            },
            {
                "user": "Find frames with the most memory changes",
                "sql": "SELECT frame_set_id, COUNT(*) as change_count FROM memory_changes GROUP BY frame_set_id ORDER BY change_count DESC LIMIT 10"
            }
        ]
        
        for template in agg_templates:
            examples.append(self._create_message_example(system_msg, template["user"], template["sql"]))
        
        return examples

    def _generate_filtering_queries(self, system_msg: str) -> List[Dict]:
        """Generate filtering and conditional queries."""
        examples = []
        
        # Value change queries
        filter_templates = [
            {
                "user": "Find memory addresses where values increased",
                "sql": "SELECT address, prev_val, curr_val FROM memory_changes WHERE CAST(curr_val AS INTEGER) > CAST(prev_val AS INTEGER)"
            },
            {
                "user": "Show me addresses where values decreased",
                "sql": "SELECT address, prev_val, curr_val FROM memory_changes WHERE CAST(curr_val AS INTEGER) < CAST(prev_val AS INTEGER)"
            },
            {
                "user": "Find memory changes with large value differences",
                "sql": "SELECT * FROM memory_changes WHERE ABS(CAST(curr_val AS INTEGER) - CAST(prev_val AS INTEGER)) > 10"
            }
        ]
        
        for template in filter_templates:
            examples.append(self._create_message_example(system_msg, template["user"], template["sql"]))
        
        # Specific value queries
        for _ in range(5):
            old_val = random.choice(['0', '1', '255', '100'])
            new_val = random.choice(['0', '1', '255', '100'])
            if old_val != new_val:
                examples.append(self._create_message_example(
                    system_msg,
                    f"Show me addresses that changed from {old_val} to {new_val}",
                    f"SELECT * FROM memory_changes WHERE prev_val = '{old_val}' AND curr_val = '{new_val}'"
                ))
        
        return examples

    def save_training_data(self, filename: str = "gba_training_data.jsonl"):
        """Save training data in OpenAI JSONL format."""
        examples = self.generate_training_examples()
        
        with open(filename, 'w', encoding='utf-8') as f:
            for example in examples:
                f.write(json.dumps(example, ensure_ascii=False) + '\n')
        
        print(f"Generated {len(examples)} training examples")
        print(f"Saved to: {filename}")
        
        # Show sample
        print(f"\nSample training example:")
        sample = examples[0]
        for msg in sample["messages"]:
            print(f"{msg['role'].upper()}: {msg['content'][:100]}...")
        
        return examples

def main():
    """Generate training data for the existing LLM training script."""
    print("=== GBA Memory Analysis Training Data Generator ===")
    print("Generating training data in OpenAI messages format...")
    
    generator = GBATrainingDataGenerator()
    examples = generator.save_training_data()
    
    print(f"\n✅ Training data ready!")
    print(f"📁 File: gba_training_data.jsonl")
    print(f"📊 Examples: {len(examples)}")
    print(f"\n🚀 To train your model:")
    print(f"   python src/ml/train_llm.py gba_training_data.jsonl --output-dir ./models/gba-sql")

if __name__ == "__main__":
    main()
