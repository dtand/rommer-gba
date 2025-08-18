from flask import Blueprint, jsonify, abort
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('progress', __name__)

@bp.route('/api/progress/<session_id>')
def api_progress(session_id):
    session_dir = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_dir):
        abort(404)
    total_frames = 0
    complete = 0
    partial = 0
    for d in os.listdir(session_dir):
        dpath = os.path.join(session_dir, d)
        if os.path.isdir(dpath) and d.isdigit():
            total_frames += 1
            annotations_path = os.path.join(dpath, 'annotations.json')
            if os.path.isfile(annotations_path):
                try:
                    with open(annotations_path, 'r', encoding='utf-8') as f:
                        annotation_data = json.load(f)
                        if annotation_data.get('complete', False):
                            complete += 1
                        else:
                            has_context = annotation_data.get('context', '').strip()
                            has_scene = annotation_data.get('scene', '').strip()
                            has_tags = annotation_data.get('tags', [])
                            has_action = annotation_data.get('action', '').strip()
                            has_intent = annotation_data.get('intent', '').strip()
                            has_outcome = annotation_data.get('outcome', '').strip()
                            if has_context or has_scene or has_tags or has_action or has_intent or has_outcome:
                                partial += 1
                except (json.JSONDecodeError, IOError):
                    pass
    return jsonify({'total': total_frames, 'complete': complete, 'partial': partial})
