from flask import Blueprint, jsonify, abort, request
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('aggregate_fields', __name__)

@bp.route('/api/aggregate/<field>/<session_id>')
def api_aggregate_field(field, session_id):
    session_base = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_base):
        abort(404)
    unique_values = set()
    # Iterate over all frame directories in the session
    for frame_dir in os.listdir(session_base):
        frame_path = os.path.join(session_base, frame_dir)
        if os.path.isdir(frame_path):
            annotations_path = os.path.join(frame_path, 'annotations.json')
            cnn_annotations_path = os.path.join(frame_path, 'cnn_annotations.json')
            for path in [annotations_path, cnn_annotations_path]:
                if os.path.isfile(path):
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            if path == cnn_annotations_path:
                                prediction = data.get('prediction', None)
                                value = prediction.get(field, None) if prediction else None
                            else:
                                value = data.get(field, None)
                            if value is not None:
                                if isinstance(value, list):
                                    for v in value:
                                        if v:
                                            unique_values.add(v)
                                elif isinstance(value, str):
                                    if value:
                                        unique_values.add(value)
                                else:
                                    unique_values.add(str(value))
                    except Exception:
                        continue
    return jsonify({field: sorted(unique_values)})

@bp.route('/api/aggregate/actions/<session_id>')
def api_aggregate_actions(session_id):
    session_base = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_base):
        abort(404)
    unique_actions = set()
    unique_intents = set()
    unique_outcomes = set()
    for frame_dir in os.listdir(session_base):
        frame_path = os.path.join(session_base, frame_dir)
        if os.path.isdir(frame_path):
            annotations_path = os.path.join(frame_path, 'annotations.json')
            if os.path.isfile(annotations_path):
                try:
                    with open(annotations_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        action = data.get('action_type', None)
                        intent = data.get('intent', None)
                        outcome = data.get('outcome', None)
                        if action and isinstance(action, str):
                            unique_actions.add(action)
                        if intent and isinstance(intent, str):
                            unique_intents.add(intent)
                        if outcome and isinstance(outcome, str):
                            unique_outcomes.add(outcome)
                except Exception:
                    continue
    return jsonify({
        'actions': sorted(unique_actions),
        'intents': sorted(unique_intents),
        'outcomes': sorted(unique_outcomes)
    })

@bp.route('/api/aggregate/all/<session_id>')
def api_aggregate_all(session_id):
    session_base = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_base):
        abort(404)
    unique_contexts = set()
    unique_scenes = set()
    unique_tags = set()
    unique_actions = set()
    unique_intents = set()
    unique_outcomes = set()
    for frame_dir in os.listdir(session_base):
        frame_path = os.path.join(session_base, frame_dir)
        if os.path.isdir(frame_path):
            annotations_path = os.path.join(frame_path, 'annotations.json')
            cnn_annotations_path = os.path.join(frame_path, 'cnn_annotations.json')
            # Check annotations.json
            if os.path.isfile(annotations_path):
                try:
                    with open(annotations_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        context = data.get('context', None)
                        scene = data.get('scene', None)
                        tags = data.get('tags', None)
                        action = data.get('action_type', None)
                        intent = data.get('intent', None)
                        outcome = data.get('outcome', None)
                        if context:
                            if isinstance(context, list):
                                unique_contexts.update([c for c in context if c])
                            elif isinstance(context, str):
                                unique_contexts.add(context)
                        if scene:
                            if isinstance(scene, list):
                                unique_scenes.update([s for s in scene if s])
                            elif isinstance(scene, str):
                                unique_scenes.add(scene)
                        if tags:
                            if isinstance(tags, list):
                                unique_tags.update([t for t in tags if t])
                            elif isinstance(tags, str):
                                unique_tags.add(tags)
                        if action and isinstance(action, str):
                            unique_actions.add(action)
                        if intent and isinstance(intent, str):
                            unique_intents.add(intent)
                        if outcome and isinstance(outcome, str):
                            unique_outcomes.add(outcome)
                except Exception:
                    pass
            # Check cnn_annotations.json
            if os.path.isfile(cnn_annotations_path):
                try:
                    with open(cnn_annotations_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        prediction = data.get('prediction', {})
                        context = prediction.get('context', None)
                        scene = prediction.get('scene', None)
                        tags = prediction.get('tags', None)
                        if context:
                            if isinstance(context, list):
                                unique_contexts.update([c for c in context if c])
                            elif isinstance(context, str):
                                unique_contexts.add(context)
                        if scene:
                            if isinstance(scene, list):
                                unique_scenes.update([s for s in scene if s])
                            elif isinstance(scene, str):
                                unique_scenes.add(scene)
                        if tags:
                            if isinstance(tags, list):
                                unique_tags.update([t for t in tags if t])
                            elif isinstance(tags, str):
                                unique_tags.add(tags)
                except Exception:
                    pass
    return jsonify({
        'contexts': sorted(unique_contexts),
        'scenes': sorted(unique_scenes),
        'tags': sorted(unique_tags),
        'actions': sorted(unique_actions),
        'intents': sorted(unique_intents),
        'outcomes': sorted(unique_outcomes)
    })
