from flask import Blueprint, jsonify, request
import os, json
try:
    from config import FRAME_BASE_DIR
except ImportError:
    from ..app import FRAME_BASE_DIR

bp = Blueprint('frames', __name__)

@bp.route('/api/frames')
@bp.route('/api/frames/<session_id>')
def api_frames(session_id=None):
    filter_type = request.args.get('filter', 'all')
    print(f"DEBUG: Received filter parameter: '{filter_type}'")
    if session_id:
        session_dir = os.path.join(FRAME_BASE_DIR, session_id)
        if not os.path.isdir(session_dir):
            return jsonify({'error': f'Session {session_id} not found'}), 404
        base_dir = session_dir
    else:
        sessions = []
        for d in os.listdir(FRAME_BASE_DIR):
            dpath = os.path.join(FRAME_BASE_DIR, d)
            if os.path.isdir(dpath) and os.path.isfile(os.path.join(dpath, 'session_metadata.json')):
                sessions.append(d)
        if not sessions:
            return jsonify({'error': 'No sessions found'}), 404
        base_dir = os.path.join(FRAME_BASE_DIR, sessions[0])
    frames = []
    total_frames_checked = 0
    for d in os.listdir(base_dir):
        dpath = os.path.join(base_dir, d)
        if os.path.isdir(dpath) and d.isdigit():
            total_frames_checked += 1
            event_path = os.path.join(dpath, 'event.json')
            if os.path.isfile(event_path):
                annotations_path = os.path.join(dpath, 'annotations.json')
                is_complete = False
                has_partial_data = False
                if os.path.isfile(annotations_path):
                    try:
                        with open(annotations_path, 'r', encoding='utf-8') as f:
                            annotation_data = json.load(f)
                            is_complete = annotation_data.get('complete', False)
                            has_context = annotation_data.get('context', '').strip()
                            has_scene = annotation_data.get('scene', '').strip()
                            has_tags = annotation_data.get('tags', [])
                            has_action = annotation_data.get('action', '').strip()
                            has_intent = annotation_data.get('intent', '').strip()
                            has_outcome = annotation_data.get('outcome', '').strip()
                            has_partial_data = bool(has_context or has_scene or has_tags or has_action or has_intent or has_outcome)
                    except (json.JSONDecodeError, IOError):
                        is_complete = False
                        has_partial_data = False
                frame_data = {
                    'frame': int(d),
                    'annotated': is_complete,
                    'partial': has_partial_data and not is_complete
                }
                include_frame = False
                if filter_type == 'all':
                    include_frame = True
                elif filter_type == 'complete':
                    include_frame = is_complete
                elif filter_type == 'partial':
                    include_frame = has_partial_data and not is_complete
                elif filter_type == 'not_annotated':
                    include_frame = not is_complete and not has_partial_data
                elif filter_type == 'archived':
                    include_frame = False
                if include_frame:
                    frames.append(frame_data)
    frames.sort(key=lambda x: x['frame'])
    print(f"DEBUG: Filter '{filter_type}' - Total frames checked: {total_frames_checked}, Filtered result: {len(frames)}")
    return jsonify({'frames': frames, 'filter': filter_type, 'total_filtered': len(frames)})
