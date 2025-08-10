#!/usr/bin/env python3
"""
Memory Analysis Agent for the GBA Web Application

Provides LLM-powered natural language querying of the GBA training database.
"""

import sqlite3
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging
from pathlib import Path
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class QueryResult:
    """Represents a database query result with metadata."""
    query: str
    results: List[Dict[str, Any]]
    explanation: str
    confidence: float
    execution_time: float
    sql_query: str

class MemoryAnalysisAgent:
    """LLM-powered agent for analyzing GBA memory data."""
    
    def __init__(self, db_path: str = "gba_training.db"):
        self.db_path = db_path
        self.schema_info = self._load_schema_info()
        self.query_templates = self._load_query_templates()
        
    def _load_schema_info(self) -> Dict[str, Any]:
        """Load database schema information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            schema = {}
            
            # Get table schemas with descriptions
            tables = ['sessions', 'frame_sets', 'memory_changes', 'annotations']
            
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table})")
                    schema[table] = [
                        {"name": row[1], "type": row[2], 
                         "description": self._get_column_description(table, row[1])}
                        for row in cursor.fetchall()
                    ]
                except:
                    schema[table] = []
            
            # Get context values for filtering
            try:
                cursor.execute("SELECT DISTINCT context FROM annotations WHERE context IS NOT NULL LIMIT 20")
                schema['available_contexts'] = [row[0] for row in cursor.fetchall()]
            except:
                schema['available_contexts'] = []
            
            # Get scene values
            try:
                cursor.execute("SELECT DISTINCT scene FROM annotations WHERE scene IS NOT NULL LIMIT 20") 
                schema['available_scenes'] = [row[0] for row in cursor.fetchall()]
            except:
                schema['available_scenes'] = []
            
            # Get sample addresses for reference
            try:
                cursor.execute("SELECT DISTINCT address FROM memory_changes ORDER BY address LIMIT 50")
                schema['sample_addresses'] = [row[0] for row in cursor.fetchall()]
            except:
                schema['sample_addresses'] = []
            
            conn.close()
            return schema
            
        except Exception as e:
            logger.error(f"Error loading schema: {e}")
            return {}
    
    def _get_column_description(self, table: str, column: str) -> str:
        """Get human-readable description for database columns."""
        descriptions = {
            'sessions': {
                'uuid': 'Unique identifier for each gaming session',
                'created_at': 'Timestamp when session was recorded',
                'metadata': 'JSON metadata about the session'
            },
            'frame_sets': {
                'session_uuid': 'References the parent gaming session',
                'frame_set_id': 'Sequential ID within the session',
                'frame_count': 'Number of frames in this set',
                'created_at': 'When this frame set was captured'
            },
            'memory_changes': {
                'session_uuid': 'References the gaming session',
                'frame_set_id': 'References the frame set',
                'region': 'Memory region (EWRAM, IWRAM, etc)',
                'frame': 'Frame number within the set',
                'address': 'Memory address that changed (hexadecimal string)',
                'prev_val': 'Previous value at this address (as string)',
                'curr_val': 'Current value at this address (as string)',
                'freq': 'Frequency or occurrence count'
            },
            'annotations': {
                'session_uuid': 'References the gaming session',
                'frame_set_id': 'References the frame set',
                'context': 'Game context (battle, overworld, menu, etc)',
                'scene': 'Specific scene or location in the game',
                'tags': 'Tags for categorization',
                'description': 'Human-readable description of what was happening',
                'action_type': 'Type of action taken',
                'intent': 'Player intent or goal',
                'outcome': 'Result or outcome of the action'
            }
        }
        
        return descriptions.get(table, {}).get(column, f"Column {column} in table {table}")
    
    def _load_query_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load pre-defined query templates for common questions."""
        return {
            'battle_addresses': {
                'description': 'Find memory addresses active during battle',
                'keywords': ['battle', 'combat', 'fight', 'attack', 'enemy'],
                'template': """
                    SELECT mc.address, 
                           COUNT(*) as change_count,
                           printf('0x%s', mc.address) as hex_address,
                           AVG(ABS(CAST(mc.curr_val as INTEGER) - CAST(mc.prev_val as INTEGER))) as avg_change_magnitude,
                           MIN(CAST(mc.prev_val as INTEGER)) as min_prev_val,
                           MAX(CAST(mc.curr_val as INTEGER)) as max_curr_val,
                           GROUP_CONCAT(DISTINCT SUBSTR(a.description, 1, 100)) as sample_descriptions,
                           GROUP_CONCAT(DISTINCT mc.region) as regions
                    FROM memory_changes mc
                    JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
                    WHERE a.context LIKE '%battle%' OR a.context LIKE '%combat%' OR a.context LIKE '%fight%'
                       OR a.description LIKE '%battle%' OR a.description LIKE '%attack%' OR a.description LIKE '%enemy%'
                    GROUP BY mc.address
                    HAVING change_count >= {min_changes}
                    ORDER BY change_count DESC, avg_change_magnitude DESC
                    LIMIT {limit}
                """,
                'default_params': {'min_changes': 3, 'limit': 25}
            },
            
            'health_addresses': {
                'description': 'Find addresses potentially related to health/HP',
                'keywords': ['health', 'hp', 'damage', 'enemy health', 'player health', 'hurt'],
                'template': """
                    SELECT mc.address,
                           printf('0x%s', mc.address) as hex_address,
                           COUNT(*) as change_count,
                           AVG(CAST(mc.prev_val as INTEGER)) as avg_prev_val,
                           AVG(CAST(mc.curr_val as INTEGER)) as avg_curr_val,
                           AVG(CAST(mc.curr_val as INTEGER) - CAST(mc.prev_val as INTEGER)) as avg_change,
                           GROUP_CONCAT(DISTINCT SUBSTR(a.description, 1, 100)) as descriptions,
                           GROUP_CONCAT(DISTINCT a.context) as contexts,
                           GROUP_CONCAT(DISTINCT mc.region) as regions
                    FROM memory_changes mc
                    JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
                    WHERE (a.description LIKE '%health%' OR a.description LIKE '%HP%' 
                           OR a.description LIKE '%damage%' OR a.description LIKE '%hurt%'
                           OR a.description LIKE '%enemy%' OR a.description LIKE '%player%'
                           OR a.description LIKE '%life%' OR a.description LIKE '%wounded%')
                          AND ABS(CAST(mc.curr_val as INTEGER) - CAST(mc.prev_val as INTEGER)) > 0
                    GROUP BY mc.address
                    HAVING change_count >= {min_changes}
                    ORDER BY change_count DESC
                    LIMIT {limit}
                """,
                'default_params': {'min_changes': 2, 'limit': 30}
            },
            
            'movement_buttons': {
                'description': 'Find button presses related to overworld movement',
                'keywords': ['movement', 'moving', 'overworld', 'button', 'walk', 'direction'],
                'template': """
                    SELECT fs.buttons, 
                           COUNT(*) as frequency,
                           GROUP_CONCAT(DISTINCT a.scene) as scenes,
                           GROUP_CONCAT(DISTINCT SUBSTR(a.description, 1, 50)) as sample_descriptions,
                           GROUP_CONCAT(DISTINCT a.context) as contexts
                    FROM frame_sets fs
                    JOIN annotations a ON fs.session_uuid = a.session_uuid AND fs.frame_set_id = a.frame_set_id
                    WHERE (a.context LIKE '%overworld%' OR a.context LIKE '%field%' OR a.context LIKE '%world%')
                          AND fs.buttons IS NOT NULL 
                          AND fs.buttons != '[]'
                          AND fs.buttons != 'null'
                          AND fs.buttons != ''
                          AND (a.description LIKE '%mov%' OR a.description LIKE '%walk%' 
                               OR a.description LIKE '%run%' OR a.description LIKE '%direction%'
                               OR a.description LIKE '%up%' OR a.description LIKE '%down%'
                               OR a.description LIKE '%left%' OR a.description LIKE '%right%')
                    GROUP BY fs.buttons
                    HAVING frequency >= {min_frequency}
                    ORDER BY frequency DESC
                    LIMIT {limit}
                """,
                'default_params': {'min_frequency': 2, 'limit': 20}
            },
            
            'experience_addresses': {
                'description': 'Find addresses related to experience/medal XP',
                'keywords': ['experience', 'xp', 'medal', 'points', 'level', 'gain'],
                'template': """
                    SELECT mc.address,
                           printf('0x%s', mc.address) as hex_address,
                           COUNT(*) as change_count,
                           AVG(CAST(mc.prev_val as INTEGER)) as avg_prev_val,
                           AVG(CAST(mc.curr_val as INTEGER)) as avg_curr_val,
                           AVG(CAST(mc.curr_val as INTEGER) - CAST(mc.prev_val as INTEGER)) as avg_increase,
                           GROUP_CONCAT(DISTINCT SUBSTR(a.description, 1, 100)) as descriptions,
                           GROUP_CONCAT(DISTINCT a.context) as contexts,
                           GROUP_CONCAT(DISTINCT mc.region) as regions
                    FROM memory_changes mc
                    JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
                    WHERE (a.description LIKE '%experience%' OR a.description LIKE '%XP%' 
                           OR a.description LIKE '%medal%' OR a.description LIKE '%points%'
                           OR a.description LIKE '%level%' OR a.description LIKE '%gain%'
                           OR a.description LIKE '%reward%' OR a.description LIKE '%earned%')
                          AND CAST(mc.curr_val as INTEGER) > CAST(mc.prev_val as INTEGER)
                    GROUP BY mc.address
                    ORDER BY avg_increase DESC, change_count DESC
                    LIMIT {limit}
                """,
                'default_params': {'limit': 30}
            },
            
            'address_exploration': {
                'description': 'General address exploration with context',
                'keywords': ['address', 'memory', 'what', 'show', 'find'],
                'template': """
                    SELECT mc.address,
                           printf('0x%s', mc.address) as hex_address,
                           COUNT(*) as total_changes,
                           COUNT(DISTINCT a.context) as unique_contexts,
                           GROUP_CONCAT(DISTINCT a.context) as contexts,
                           AVG(ABS(CAST(mc.curr_val as INTEGER) - CAST(mc.prev_val as INTEGER))) as avg_change_magnitude,
                           MIN(CAST(mc.prev_val as INTEGER)) as min_value,
                           MAX(CAST(mc.curr_val as INTEGER)) as max_value,
                           GROUP_CONCAT(DISTINCT SUBSTR(a.description, 1, 100)) as sample_descriptions,
                           GROUP_CONCAT(DISTINCT mc.region) as regions
                    FROM memory_changes mc
                    JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
                    GROUP BY mc.address
                    HAVING total_changes >= {min_changes}
                    ORDER BY total_changes DESC, unique_contexts DESC
                    LIMIT {limit}
                """,
                'default_params': {'min_changes': 5, 'limit': 30}
            }
        }
    
    def parse_natural_language_query(self, query: str) -> Dict[str, Any]:
        """Parse natural language query and determine intent."""
        query_lower = query.lower()
        
        analysis = {
            'type': 'address_exploration',  # default
            'keywords': [],
            'context_filters': [],
            'description_filters': [],
            'parameters': {},
            'confidence': 0.5
        }
        
        # Check each template for keyword matches
        best_match_score = 0
        best_match_type = 'address_exploration'
        
        for template_name, template_info in self.query_templates.items():
            score = 0
            matched_keywords = []
            
            for keyword in template_info['keywords']:
                if keyword in query_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Bonus for exact phrase matches
            if template_name == 'health_addresses' and any(phrase in query_lower for phrase in ['enemy health', 'player health', 'hp']):
                score += 2
            
            if template_name == 'movement_buttons' and any(phrase in query_lower for phrase in ['button press', 'overworld', 'moving around']):
                score += 2
                
            if template_name == 'experience_addresses' and any(phrase in query_lower for phrase in ['medal xp', 'experience points', 'after battle']):
                score += 2
                
            if template_name == 'battle_addresses' and any(phrase in query_lower for phrase in ['battle context', 'during battle']):
                score += 2
            
            if score > best_match_score:
                best_match_score = score
                best_match_type = template_name
                analysis['keywords'] = matched_keywords
                analysis['confidence'] = min(0.9, 0.3 + (score * 0.15))
        
        analysis['type'] = best_match_type
        
        # Extract specific filters from query
        if 'enemy' in query_lower:
            analysis['description_filters'].append("a.description LIKE '%enemy%'")
        if 'player' in query_lower:
            analysis['description_filters'].append("a.description LIKE '%player%'")
        if 'overworld' in query_lower:
            analysis['context_filters'].append("a.context LIKE '%overworld%'")
        if 'battle' in query_lower:
            analysis['context_filters'].append("a.context LIKE '%battle%'")
        
        # Extract numeric parameters
        numbers = re.findall(r'\d+', query)
        if numbers:
            analysis['parameters']['limit'] = min(int(numbers[0]), 100)
        
        return analysis
    
    def generate_sql_query(self, analysis: Dict[str, Any]) -> str:
        """Generate SQL query based on analysis."""
        query_type = analysis['type']
        
        if query_type in self.query_templates:
            template = self.query_templates[query_type]['template']
            params = {**self.query_templates[query_type]['default_params'], **analysis['parameters']}
            
            # Add additional WHERE conditions if needed
            additional_where = []
            if analysis['description_filters']:
                additional_where.extend(analysis['description_filters'])
            if analysis['context_filters']:
                additional_where.extend(analysis['context_filters'])
            
            if additional_where:
                # Insert additional conditions into the WHERE clause
                where_addition = " AND " + " AND ".join(additional_where)
                template = template.replace("GROUP BY", where_addition + "\n                    GROUP BY", 1)
            
            try:
                return template.format(**params)
            except KeyError as e:
                logger.error(f"Missing parameter {e} in template")
                return template
        
        return self._generate_fallback_query(analysis)
    
    def _generate_fallback_query(self, analysis: Dict[str, Any]) -> str:
        """Generate a simple fallback query."""
        return """
            SELECT mc.address, COUNT(*) as changes,
                   GROUP_CONCAT(DISTINCT a.context) as contexts,
                   GROUP_CONCAT(DISTINCT a.description) as descriptions
            FROM memory_changes mc
            JOIN annotations a ON mc.session_uuid = a.session_uuid AND mc.frame_set_id = a.frame_set_id
            GROUP BY mc.address
            ORDER BY changes DESC
            LIMIT 20
        """
    
    def execute_query(self, sql_query: str) -> QueryResult:
        """Execute SQL query and return results."""
        start_time = time.time()
        
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(sql_query)
            rows = cursor.fetchall()
            results = [dict(row) for row in rows]
            
            conn.close()
            execution_time = time.time() - start_time
            
            return QueryResult(
                query="",  # Will be filled by caller
                results=results,
                explanation=f"Found {len(results)} results",
                confidence=0.85,
                execution_time=execution_time,
                sql_query=sql_query
            )
            
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return QueryResult(
                query="",
                results=[],
                explanation=f"Query failed: {str(e)}",
                confidence=0.0,
                execution_time=time.time() - start_time,
                sql_query=sql_query
            )
    
    def process_natural_language_query(self, user_query: str) -> QueryResult:
        """Main method to process natural language queries."""
        logger.info(f"Processing query: {user_query}")
        
        # Parse the query
        analysis = self.parse_natural_language_query(user_query)
        
        # Generate SQL
        sql_query = self.generate_sql_query(analysis)
        
        # Execute query
        result = self.execute_query(sql_query)
        result.query = user_query
        result.confidence = analysis['confidence']
        
        # Generate explanation
        result.explanation = self._generate_explanation(user_query, analysis, result)
        
        return result
    
    def _generate_explanation(self, user_query: str, analysis: Dict[str, Any], result: QueryResult) -> str:
        """Generate human-readable explanation."""
        if not result.results:
            return f"No results found for '{user_query}'. Try different keywords or rephrasing your question."
        
        count = len(result.results)
        query_type = analysis['type']
        confidence = analysis['confidence']
        
        explanations = {
            'battle_addresses': f"Found {count} memory addresses that change during battle contexts. Confidence: {confidence:.1%}",
            'health_addresses': f"Identified {count} potential health-related addresses showing value changes. Confidence: {confidence:.1%}",
            'movement_buttons': f"Discovered {count} button combinations used for overworld movement. Confidence: {confidence:.1%}",
            'experience_addresses': f"Located {count} addresses potentially tracking experience or medal XP. Confidence: {confidence:.1%}",
            'address_exploration': f"Found {count} memory addresses matching your criteria. Confidence: {confidence:.1%}"
        }
        
        explanation = explanations.get(query_type, f"Found {count} results for your query.")
        
        if result.execution_time > 1.0:
            explanation += f" (Query executed in {result.execution_time:.2f}s)"
        
        return explanation
