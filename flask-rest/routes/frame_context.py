from flask import Blueprint, jsonify, abort, request
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

@bp.route('/api/frame_contexts/<session_id>')
def api_frame_contexts(session_id):
    start_id = request.args.get('start', None)
    page_size = int(request.args.get('page_size', 50))
    filter_type = request.args.get('filter', 'ALL').upper()
    session_dir = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_dir):
        abort(404)
    frame_dirs = sorted([d for d in os.listdir(session_dir) if os.path.isdir(os.path.join(session_dir, d))], key=lambda x: int(x))
    contexts = []
    found = False
    count = 0
    for frame_id in frame_dirs:
        if start_id is not None and not found:
            if frame_id == start_id:
                found = True
            else:
                continue
        # Apply filter
        annotations_path = os.path.join(session_dir, frame_id, 'annotations.json')
        include = False
        if filter_type == 'ALL':
            include = True
        elif filter_type == 'ANNOTATED':
            if os.path.isfile(annotations_path):
                with open(annotations_path, 'r', encoding='utf-8') as f:
                    ann = json.load(f)
                    if ann.get('complete') is True:
                        include = True
        elif filter_type == 'PARTIALLY_ANNOTATED':
            if os.path.isfile(annotations_path):
                with open(annotations_path, 'r', encoding='utf-8') as f:
                    ann = json.load(f)
                    if any(v for k, v in ann.items() if v not in [None, '', False] and k != 'complete'):
                        include = True
        elif filter_type == 'NOT_ANNOTATED':
            if not os.path.isfile(annotations_path):
                include = True
            else:
                with open(annotations_path, 'r', encoding='utf-8') as f:
                    ann = json.load(f)
                    if not any(v for k, v in ann.items() if v not in [None, '', False] and k != 'complete'):
                        include = True
        if include:
            context_path = os.path.join(session_dir, frame_id, 'event.json')
            annotations_path = os.path.join(session_dir, frame_id, 'annotations.json')
            cnn_annotations_path = os.path.join(session_dir, frame_id, 'cnn_annotations.json')
            if not os.path.isfile(context_path):
                continue
            result = {}
            with open(context_path, 'r', encoding='utf-8') as f:
                result = json.load(f)
            if os.path.isfile(annotations_path):
                with open(annotations_path, 'r', encoding='utf-8') as f:
                    result['annotations'] = json.load(f)
            else:
                result['annotations'] = {}
            if os.path.isfile(cnn_annotations_path):
                with open(cnn_annotations_path, 'r', encoding='utf-8') as f:
                    result['cnn_annotations'] = json.load(f)
            else:
                result['cnn_annotations'] = {}
            contexts.append(result)
            count += 1
            if count >= page_size:
                break
    return jsonify({'contexts': contexts})


