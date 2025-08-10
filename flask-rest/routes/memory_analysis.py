"""
Memory Analysis routes for natural language querying
"""

from flask import Blueprint, render_template, request, jsonify
from memory_agent import MemoryAnalysisAgent
import logging
import os

logger = logging.getLogger(__name__)

bp = Blueprint('memory_analysis', __name__, url_prefix='/memory')

# Initialize the agent
db_path = os.path.join(os.path.dirname(__file__), '../../../gba_training.db')
agent = MemoryAnalysisAgent(db_path)

@bp.route('/')
def memory_index():
    """Memory analysis main page."""
    return render_template('memory_analysis.html')

@bp.route('/api/query', methods=['POST'])
def api_memory_query():
    """Process natural language memory queries."""
    try:
        data = request.get_json()
        user_query = data.get('query', '').strip()
        
        if not user_query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Process the query
        result = agent.process_natural_language_query(user_query)
        
        return jsonify({
            'success': True,
            'query': result.query,
            'sql_query': result.sql_query,
            'results': result.results,
            'explanation': result.explanation,
            'confidence': result.confidence,
            'execution_time': result.execution_time,
            'result_count': len(result.results)
        })
        
    except Exception as e:
        logger.error(f"Memory query API error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/schema')
def api_memory_schema():
    """Get database schema information."""
    try:
        return jsonify({
            'success': True,
            'schema': agent.schema_info
        })
    except Exception as e:
        logger.error(f"Schema API error: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/examples')
def api_memory_examples():
    """Get example queries."""
    examples = [
        {
            'query': 'Which addresses are likely used in the battle context?',
            'description': 'Find memory addresses that change frequently during battles'
        },
        {
            'query': 'Can you find me addresses that are likely related to enemy health?',
            'description': 'Identify addresses that might store enemy HP or health data'
        },
        {
            'query': 'Which button presses are related to the player moving around in the overworld?',
            'description': 'Discover input patterns used for navigation and movement'
        },
        {
            'query': 'After the battle is over the player gains medal xp - can you identify which memory addresses could be related?',
            'description': 'Find addresses tracking experience points and post-battle rewards'
        },
        {
            'query': 'Show me memory addresses that change during combat',
            'description': 'General exploration of combat-related memory activity'
        },
        {
            'query': 'Find addresses that might store player health or HP',
            'description': 'Look for player health tracking addresses'
        },
        {
            'query': 'What are the most active memory addresses overall?',
            'description': 'See which addresses change most frequently across all contexts'
        },
        {
            'query': 'Which addresses change when the player levels up?',
            'description': 'Find progression and leveling system addresses'
        }
    ]
    
    return jsonify({
        'success': True,
        'examples': examples
    })

@bp.route('/api/stats')
def api_memory_stats():
    """Get database statistics."""
    try:
        import sqlite3
        conn = sqlite3.connect(agent.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Get basic counts
        cursor.execute("SELECT COUNT(*) FROM sessions")
        stats['total_sessions'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM frame_sets")
        stats['total_frame_sets'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM memory_changes")
        stats['total_memory_changes'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM annotations")
        stats['total_annotations'] = cursor.fetchone()[0]
        
        # Get unique addresses
        cursor.execute("SELECT COUNT(DISTINCT address) FROM memory_changes")
        stats['unique_addresses'] = cursor.fetchone()[0]
        
        # Get context distribution
        cursor.execute("""
            SELECT context, COUNT(*) as count 
            FROM annotations 
            WHERE context IS NOT NULL 
            GROUP BY context 
            ORDER BY count DESC
        """)
        stats['context_distribution'] = [
            {'context': row[0], 'count': row[1]} 
            for row in cursor.fetchall()
        ]
        
        # Get most active addresses
        cursor.execute("""
            SELECT mc.address, 
                   printf('0x%08X', CAST(mc.address as INTEGER)) as hex_address,
                   COUNT(*) as changes
            FROM memory_changes mc
            GROUP BY mc.address
            ORDER BY changes DESC
            LIMIT 10
        """)
        stats['most_active_addresses'] = [
            {'address': row[0], 'hex_address': row[1], 'changes': row[2]}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Stats API error: {e}")
        return jsonify({'error': str(e)}), 500
