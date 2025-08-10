from flask import Blueprint, jsonify
import os, json
from config import ANNOTATION_CONFIG_PATH

bp = Blueprint('annotation_config', __name__)

@bp.route('/static/annotation_config.json')
@bp.route('/static/annotation_config.json/<session_id>')
def api_annotation_config(session_id=None):
    if not os.path.isfile(ANNOTATION_CONFIG_PATH):
        return jsonify({'error': 'Config not found'}), 404
    with open(ANNOTATION_CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
    return jsonify(config)
