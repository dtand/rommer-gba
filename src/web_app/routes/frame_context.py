from flask import Blueprint, jsonify, abort
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('frame_context', __name__)

@bp.route('/api/frame_context/<session_id>/<frame_id>')
def api_frame_context(session_id, frame_id):
    context_path = os.path.join(FRAME_BASE_DIR, session_id, frame_id, 'event.json')
    annotations_path = os.path.join(FRAME_BASE_DIR, session_id, frame_id, 'annotations.json')
    cnn_annotations_path = os.path.join(FRAME_BASE_DIR, session_id, frame_id, 'cnn_annotations.json')
    if not os.path.isfile(context_path):
        abort(404)

    result = {}
    # Load event.json
    with open(context_path, 'r', encoding='utf-8') as f:
        result = json.load(f)

    # Load annotations.json if present
    if os.path.isfile(annotations_path):
        with open(annotations_path, 'r', encoding='utf-8') as f:
            result['annotations'] = json.load(f)
    else:
        result['annotations'] = {}

    # Load cnn_annotations.json if present
    if os.path.isfile(cnn_annotations_path):
        with open(cnn_annotations_path, 'r', encoding='utf-8') as f:
            result['cnn_annotations'] = json.load(f)
    else:
        result['cnn_annotations'] = {}

    return jsonify(result)
