from flask import Blueprint, send_file, abort
import os
from config import FRAME_BASE_DIR

bp = Blueprint('frame_image', __name__)

@bp.route('/api/frame_image/<session_id>/<frame_id>')
def api_frame_image(session_id, frame_id):
    img_path = os.path.join(FRAME_BASE_DIR, session_id, frame_id, f'{frame_id}.png')
    if not os.path.isfile(img_path):
        print(f"[frame_image] Image not found: {img_path}")
        abort(404)
    return send_file(img_path, mimetype='image/png')
