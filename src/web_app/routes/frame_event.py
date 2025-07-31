from flask import Blueprint, jsonify, abort
import os
import json

bp = Blueprint('frame_event', __name__)

@bp.route('/api/frame_event/<frame>')
def frame_event(frame):
    # Find event.json for this frame
    data_dir = os.path.join(os.getcwd(), 'data', frame)
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
