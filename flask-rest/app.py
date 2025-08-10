from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Import and register all Blueprints
from routes.index import bp as index_bp
from routes.sessions import bp as sessions_bp
from routes.frames import bp as frames_bp
from routes.annotate import bp as annotate_bp
from routes.progress import bp as progress_bp
from routes.aggregate_fields import bp as aggregate_fields_bp
from routes.apply_fields import bp as apply_fields_bp
from routes.frame_context import bp as frame_context_bp
from routes.frame_image import bp as frame_image_bp
from routes.memory_analysis import bp as memory_analysis_bp

app.register_blueprint(index_bp)
app.register_blueprint(sessions_bp)
app.register_blueprint(frames_bp)
app.register_blueprint(annotate_bp)
app.register_blueprint(progress_bp)
app.register_blueprint(aggregate_fields_bp)
app.register_blueprint(apply_fields_bp)
app.register_blueprint(frame_context_bp)
app.register_blueprint(frame_image_bp)
app.register_blueprint(memory_analysis_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
