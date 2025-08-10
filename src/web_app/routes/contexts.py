from flask import Blueprint, jsonify, abort
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('contexts', __name__)

@bp.route('/api/contexts/<session_id>')
def api_contexts(session_id):
    session_base = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_base):
        abort(404)

    unique_contexts = set()
    # Iterate over all frame directories in the session
    for frame_dir in os.listdir(session_base):
        frame_path = os.path.join(session_base, frame_dir)
        if os.path.isdir(frame_path):
            annotations_path = os.path.join(frame_path, 'annotations.json')
            cnn_annotations_path = os.path.join(frame_path, 'cnn_annotations.json')
            if os.path.isfile(annotations_path):
                try:
                    with open(annotations_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        context = data.get('context', None)
                        if context and isinstance(context, str):
                            unique_contexts.add(context)
                except Exception:
                    continue
            elif os.path.isfile(cnn_annotations_path):
                try:
                    with open(cnn_annotations_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        context = data.get('context', None)
                        if context and isinstance(context, str):
                            unique_contexts.add(context)
                except Exception:
                    continue


    return jsonify({'contexts': sorted(unique_contexts)})

    

