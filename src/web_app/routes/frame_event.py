from flask import Blueprint, jsonify, abort
import os
import json

bp = Blueprint('frame_event', __name__)

@bp.route('/api/frame_event/<frame>')
@bp.route('/api/frame_event/<session_id>/<frame>')
def frame_event(frame, session_id=None):
    # Find the frame directory
    # Get the project root (two levels up from current web app directory)
    project_root = os.path.dirname(os.path.dirname(os.getcwd()))
    
    if session_id:
        data_dir = os.path.join(project_root, 'data', session_id, frame)
    else:
        # Backward compatibility - look in root data directory first
        # Then try to find in any session directory
        data_dir = os.path.join(project_root, 'data', frame)
        if not os.path.isdir(data_dir):
            # Look for the frame in any session directory
            base_data_dir = os.path.join(project_root, 'data')
            for session_dir in os.listdir(base_data_dir):
                session_path = os.path.join(base_data_dir, session_dir)
                if os.path.isdir(session_path) and os.path.isfile(os.path.join(session_path, 'session_metadata.json')):
                    potential_frame_dir = os.path.join(session_path, frame)
                    if os.path.isdir(potential_frame_dir):
                        data_dir = potential_frame_dir
                        break
    
    # If frame directory doesn't exist, return 404
    if not os.path.isdir(data_dir):
        abort(404)
    
    event_path = os.path.join(data_dir, 'event.json')
    result = {}
    
    # Load event.json if it exists, but don't require it
    if os.path.isfile(event_path):
        with open(event_path, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Only return the top-level fields, ignore memory_changes
                result = {k: data[k] for k in ('timestamp', 'buttons') if k in data}
            except Exception:
                pass
    
    # Try to load annotation.json if it exists
    annotation_path = os.path.join(data_dir, 'annotations.json')
    annotation = None
    if os.path.isfile(annotation_path):
        with open(annotation_path, 'r', encoding='utf-8') as af:
            try:
                annotation = json.load(af)
            except Exception:
                annotation = None

    # Try to load cnn_annotations.json if it exists
    cnn_annotation_path = os.path.join(data_dir, 'cnn_annotations.json')
    cnn_annotation = None
    if os.path.isfile(cnn_annotation_path):
        with open(cnn_annotation_path, 'r', encoding='utf-8') as caf:
            try:
                cnn_annotation = json.load(caf)
            except Exception:
                cnn_annotation = None

    result['annotations'] = annotation
    result['cnn_predictions'] = cnn_annotation
    return jsonify(result)