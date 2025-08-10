from flask import Blueprint, request, jsonify, abort
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('apply_field', __name__)

@bp.route('/api/apply_field/<session_id>/<frame_id>', methods=['POST'])
def api_apply_field(session_id, frame_id):
    field = request.args.get('field')
    value = request.args.get('value')
    if not field:
        return jsonify({'error': 'Field parameter required'}), 400
    frame_dir = os.path.join(FRAME_BASE_DIR, session_id, frame_id)
    if not os.path.isdir(frame_dir):
        abort(404)
    annotations_path = os.path.join(frame_dir, 'annotations.json')
    if os.path.isfile(annotations_path):
        with open(annotations_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {}
    data[field] = value
    with open(annotations_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return jsonify({'success': True})
