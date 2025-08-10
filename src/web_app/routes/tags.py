from flask import Blueprint, jsonify, abort
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('tags', __name__)

@bp.route('/api/tags/<session_id>')
def api_tags(session_id):
    session_base = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_base):
        abort(404)

    unique_tags = set()
    # Iterate over all frame directories in the session
    for frame_dir in os.listdir(session_base):
        frame_path = os.path.join(session_base, frame_dir)
        if os.path.isdir(frame_path):
            annotations_path = os.path.join(frame_path, 'annotations.json')
            if os.path.isfile(annotations_path):
                try:
                    with open(annotations_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        tags = data.get('tags', [])
                        if isinstance(tags, str):
                            tags = [tags]
                        for tag in tags:
                            if tag:
                                unique_tags.add(tag)
                except Exception:
                    continue

    return jsonify({'tags': sorted(unique_tags)})

    

