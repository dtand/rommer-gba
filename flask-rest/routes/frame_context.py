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
    start = int(request.args.get('start', 0))
    end = int(request.args.get('end', 0))
    filter_type = request.args.get('filter', 'ALL').upper()
    session_dir = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_dir):
        abort(404)
    frame_dirs = sorted([d for d in os.listdir(session_dir) if os.path.isdir(os.path.join(session_dir, d))])
    filtered_dirs = []
    for frame_id in frame_dirs:
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
            filtered_dirs.append(frame_id)
    # Apply start/end indices
    selected_dirs = filtered_dirs[start:end] if end > start else filtered_dirs[start:]
    contexts = []
    for frame_id in selected_dirs:
        context_path = os.path.join(session_dir, frame_id, 'event.json')
        annotations_path = os.path.join(session_dir, frame_id, 'annotations.json')
        cnn_annotations_path = os.path.join(session_dir, frame_id, 'cnn_annotations.json')
        if not os.path.isfile(context_path):
            continue
        result = {}
        result['frame_id'] = frame_id
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
    return jsonify({'contexts': contexts})


