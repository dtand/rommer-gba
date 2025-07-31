from routes.frame_event import bp as frame_event_bp
from flask import Flask, render_template, jsonify, send_file, request
import os
import json

app = Flask(__name__)
app.register_blueprint(frame_event_bp)
# Set this to your per-frame output directory
FRAME_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../', 'data'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<session_id>')
def index_session(session_id):
    # Validate session exists
    session_dir = os.path.join(FRAME_BASE_DIR, session_id)
    if not os.path.isdir(session_dir):
        return f"Session '{session_id}' not found", 404
    return render_template('index.html', session_id=session_id)

@app.route('/api/sessions')
def api_sessions():
    """List all available sessions"""
    sessions = []
    for d in os.listdir(FRAME_BASE_DIR):
        dpath = os.path.join(FRAME_BASE_DIR, d)
        if os.path.isdir(dpath):
            metadata_path = os.path.join(dpath, 'session_metadata.json')
            if os.path.isfile(metadata_path):
                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    sessions.append({
                        'session_id': d,
                        'metadata': metadata
                    })
                except:
                    # If metadata file is corrupted, still list the session
                    sessions.append({
                        'session_id': d,
                        'metadata': {'session_id': d, 'total_frames': 'unknown'}
                    })
    sessions.sort(key=lambda x: x['metadata'].get('created_timestamp', 0), reverse=True)
    return jsonify({'sessions': sessions})

@app.route('/api/frames')
@app.route('/api/frames/<session_id>')
def api_frames(session_id=None):
    if session_id:
        session_dir = os.path.join(FRAME_BASE_DIR, session_id)
        if not os.path.isdir(session_dir):
            return jsonify({'error': f'Session {session_id} not found'}), 404
        base_dir = session_dir
    else:
        # Default behavior for backward compatibility - look for first session
        sessions = []
        for d in os.listdir(FRAME_BASE_DIR):
            dpath = os.path.join(FRAME_BASE_DIR, d)
            if os.path.isdir(dpath) and os.path.isfile(os.path.join(dpath, 'session_metadata.json')):
                sessions.append(d)
        if not sessions:
            return jsonify({'error': 'No sessions found'}), 404
        base_dir = os.path.join(FRAME_BASE_DIR, sessions[0])
    
    frames = []
    for d in os.listdir(base_dir):
        dpath = os.path.join(base_dir, d)
        if os.path.isdir(dpath) and d.isdigit():
            event_path = os.path.join(dpath, 'event.json')
            if os.path.isfile(event_path):
                frames.append({'frame': int(d)})
    frames.sort(key=lambda x: x['frame'])
    return jsonify({'frames': frames})

@app.route('/api/frame_image/<int:frame>')
@app.route('/api/frame_image/<session_id>/<int:frame>')
def api_frame_image(frame, session_id=None):
    if session_id:
        session_dir = os.path.join(FRAME_BASE_DIR, session_id)
        if not os.path.isdir(session_dir):
            return '', 404
        frame_dir = os.path.join(session_dir, str(frame))
    else:
        # Backward compatibility - look in root data directory
        frame_dir = os.path.join(FRAME_BASE_DIR, str(frame))
    
    img_path = os.path.join(frame_dir, f"{frame}.png")
    if os.path.isfile(img_path):
        return send_file(img_path, mimetype='image/png')
    return '', 404

@app.route('/api/frame_context/<int:frame>')
@app.route('/api/frame_context/<session_id>/<int:frame>')
def api_frame_context(frame, session_id=None):
    if session_id:
        session_dir = os.path.join(FRAME_BASE_DIR, session_id)
        if not os.path.isdir(session_dir):
            return '', 404
        frame_dir = os.path.join(session_dir, str(frame))
    else:
        # Backward compatibility - look in root data directory
        frame_dir = os.path.join(FRAME_BASE_DIR, str(frame))
    
    anno_path = os.path.join(frame_dir, 'annotations.json')
    if os.path.isfile(anno_path):
        return '', 200
    return '', 404

@app.route('/api/annotate', methods=['POST'])
@app.route('/api/annotate/<session_id>', methods=['POST'])
def api_annotate(session_id=None):
    data = request.get_json()
    frames = data.get('frames', [])
    annotation = data.get('annotation', {})
    
    if session_id:
        session_dir = os.path.join(FRAME_BASE_DIR, session_id)
        if not os.path.isdir(session_dir):
            return jsonify({'error': f'Session {session_id} not found'}), 404
        base_dir = session_dir
    else:
        # Backward compatibility - look in root data directory
        base_dir = FRAME_BASE_DIR
    
    # Ensure only the four fields are saved
    annotation_obj = {
        'context': annotation.get('context', ''),
        'scene': annotation.get('scene', ''),
        'tags': annotation.get('tags', ''),
        'description': annotation.get('description', '')
    }
    
    for frame in frames:
        frame_dir = os.path.join(base_dir, str(frame))
        if not os.path.isdir(frame_dir):
            continue  # Skip non-existent frames
        anno_path = os.path.join(frame_dir, 'annotations.json')
        with open(anno_path, 'w', encoding='utf-8') as f:
            json.dump(annotation_obj, f, indent=2)
    
    return jsonify({'message': f'Annotation saved for {len(frames)} frame(s).'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
