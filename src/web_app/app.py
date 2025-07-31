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

@app.route('/api/frames')
def api_frames():
    frames = []
    for d in os.listdir(FRAME_BASE_DIR):
        dpath = os.path.join(FRAME_BASE_DIR, d)
        if os.path.isdir(dpath) and d.isdigit():
            img_path = os.path.join(dpath, f"{d}.png")
            if os.path.isfile(img_path):
                frames.append({'frame': int(d)})
    frames.sort(key=lambda x: x['frame'])
    return jsonify({'frames': frames})

@app.route('/api/frame_image/<int:frame>')
def api_frame_image(frame):
    frame_dir = os.path.join(FRAME_BASE_DIR, str(frame))
    img_path = os.path.join(frame_dir, f"{frame}.png")
    if os.path.isfile(img_path):
        return send_file(img_path, mimetype='image/png')
    return '', 404

@app.route('/api/frame_context/<int:frame>')
def api_frame_context(frame):
    frame_dir = os.path.join(FRAME_BASE_DIR, str(frame))
    anno_path = os.path.join(frame_dir, 'annotations.json')
    if os.path.isfile(anno_path):
        return '', 200
    return '', 404

@app.route('/api/annotate', methods=['POST'])
def api_annotate():
    data = request.get_json()
    frames = data.get('frames', [])
    annotation = data.get('annotation', {})
    # Ensure only the four fields are saved
    annotation_obj = {
        'context': annotation.get('context', ''),
        'scene': annotation.get('scene', ''),
        'tags': annotation.get('tags', ''),
        'description': annotation.get('description', '')
    }
    for frame in frames:
        frame_dir = os.path.join(FRAME_BASE_DIR, str(frame))
        anno_path = os.path.join(frame_dir, 'annotations.json')
        with open(anno_path, 'w', encoding='utf-8') as f:
            json.dump(annotation_obj, f, indent=2)
    return jsonify({'message': f'Annotation saved for {len(frames)} frame(s).'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
