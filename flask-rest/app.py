from flask import Flask
from config import FRAME_BASE_DIR, ANNOTATION_CONFIG_PATH
import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])

# Import and register all Blueprints
from routes.sessions import bp as sessions_bp
from routes.frames import bp as frames_bp
from routes.frame_image import bp as frame_image_bp
from routes.frame_context import bp as frame_context_bp
from routes.annotate import bp as annotate_bp
from routes.apply_field import bp as apply_field_bp
from routes.apply_multiple_fields import bp as apply_multiple_fields_bp
from routes.progress import bp as progress_bp
from routes.annotation_config import bp as annotation_config_bp
from routes.index import bp as index_bp
from routes.tags import bp as tags_bp
from routes.scenes import bp as scenes_bp  
from routes.actions import bp as actions_bp
from routes.contexts import bp as contexts_bp

app.register_blueprint(sessions_bp)
app.register_blueprint(frames_bp)
app.register_blueprint(frame_image_bp)
app.register_blueprint(frame_context_bp)
app.register_blueprint(annotate_bp)
app.register_blueprint(apply_field_bp)
app.register_blueprint(apply_multiple_fields_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(annotation_config_bp)
app.register_blueprint(index_bp)
app.register_blueprint(tags_bp)
app.register_blueprint(scenes_bp)
app.register_blueprint(actions_bp)
app.register_blueprint(contexts_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
