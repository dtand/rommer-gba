from flask import Blueprint, jsonify
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('sessions', __name__)

@bp.route('/api/sessions')
def api_sessions():
    """List all available sessions"""
    sessions = []
    for d in os.listdir(FRAME_BASE_DIR):
        dpath = os.path.join(FRAME_BASE_DIR, d)
        if os.path.isdir(dpath):
            metadata_path = os.path.join(dpath, 'session_metadata.json')
            if os.path.isfile(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    sessions.append({
                        'session_id': d,
                        'metadata': metadata
                    })
                except:
                    sessions.append({
                        'session_id': d,
                        'metadata': {'session_id': d, 'total_frames': 'unknown'}
                    })
    sessions.sort(key=lambda x: x['metadata'].get('created_timestamp', 0), reverse=True)
    return jsonify({'sessions': sessions})
