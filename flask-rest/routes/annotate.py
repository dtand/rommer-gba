from flask import Blueprint, request, jsonify, abort
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('annotate', __name__)

@bp.route('/api/annotate/<session_id>', methods=['POST'])
def api_annotate(session_id):
    req_data = request.get_json()
    frames = req_data.get('frames', [])
    annotation = req_data.get('annotation', {})
    if not isinstance(frames, list) or not annotation:
        return jsonify({'success': False, 'error': 'Invalid request format'}), 400

    success_frames = []
    failed_frames = []
    
    for frame_id in frames:
        frame_dir = os.path.join(FRAME_BASE_DIR, session_id, str(frame_id))
        annotations_path = os.path.join(frame_dir, 'annotations.json')
        if not os.path.isdir(frame_dir):
            failed_frames.append(frame_id)
            continue
        try:
            with open(annotations_path, 'w', encoding='utf-8') as f:
                json.dump(annotation, f, ensure_ascii=False, indent=2)
            success_frames.append(frame_id)
        except Exception as e:
            failed_frames.append(frame_id)

    return jsonify({
        'success': True,
        'annotated': success_frames,
        'failed': failed_frames
    })
