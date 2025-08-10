from flask import Blueprint, render_template

bp = Blueprint('index', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/<session_id>')
def index_with_session(session_id):
    # Render your main page, passing session_id to the template or frontend
    return render_template('index.html', session_id=session_id)

