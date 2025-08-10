from flask import Blueprint, request, jsonify, abort
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('apply_multiple_fields', __name__)

@bp.route('/api/apply_multiple_fields/<session_id>/<frame_id>', methods=['POST'])
def api_apply_multiple_fields(session_id, frame_id):
    frame_dir = os.path.join(FRAME_BASE_DIR, session_id, frame_id)
    if not os.path.isdir(frame_dir):
        abort(404)
    annotations_path = os.path.join(frame_dir, 'annotations.json')
    if os.path.isfile(annotations_path):
        with open(annotations_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}
    update_fields = request.get_json()
    if not isinstance(update_fields, dict):
        return jsonify({'error': 'Invalid data format'}), 400
    data.update(update_fields)
    with open(annotations_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True})
