from flask import Blueprint, jsonify, abort
import os
import json

bp = Blueprint('frame_event', __name__)

@bp.route('/api/frame_event/<frame>')
@bp.route('/api/frame_event/<session_id>/<frame>')
def frame_event(frame, session_id=None):
    # Find event.json for this frame
    if session_id:
        data_dir = os.path.join(os.getcwd(), 'data', session_id, frame)
    else:
        # Backward compatibility - look in root data directory first
        # Then try to find in any session directory
        data_dir = os.path.join(os.getcwd(), 'data', frame)
        if not os.path.isdir(data_dir):
            # Look for the frame in any session directory
            base_data_dir = os.path.join(os.getcwd(), 'data')
            for session_dir in os.listdir(base_data_dir):
                session_path = os.path.join(base_data_dir, session_dir)
                if os.path.isdir(session_path) and os.path.isfile(os.path.join(session_path, 'session_metadata.json')):
                    potential_frame_dir = os.path.join(session_path, frame)
                    if os.path.isdir(potential_frame_dir):
                        data_dir = potential_frame_dir
                        break
    
    event_path = os.path.join(data_dir, 'event.json')
    if not os.path.isfile(event_path):
        abort(404)
    
    with open(event_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Only return the top-level fields, ignore memory_changes
    result = {k: data[k] for k in ('timestamp', 'pc', 'key_history', 'current_keys') if k in data}
    
    # Try to load annotation.json if it exists
    annotation_path = os.path.join(data_dir, 'annotations.json')
    annotation = None
    if os.path.isfile(annotation_path):
        with open(annotation_path, 'r', encoding='utf-8') as af:
            try:
                annotation = json.load(af)
            except Exception:
                annotation = None
    
    result['annotations'] = annotation
    return jsonify(result)
