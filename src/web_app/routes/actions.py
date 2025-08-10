from flask import Blueprint, jsonify, abort
import os, json
from config import FRAME_BASE_DIR

bp = Blueprint('actions', __name__)

@bp.route('/api/actions/<session_id>')
def api_actions(session_id):
    session_base = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_base):
        abort(404)

    unique_actions = set()
    unique_intents = set()
    unique_outcomes = set()
    
    # Iterate over all frame directories in the session
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

    

