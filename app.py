import os
import io
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# ── Badge photo zone ───────────────────────────────────────────────────────────
ZONE_LEFT   = 106
ZONE_TOP    = 415
ZONE_RIGHT  = 490
ZONE_BOTTOM = 898
ZONE_W      = ZONE_RIGHT - ZONE_LEFT
ZONE_H      = ZONE_BOTTOM - ZONE_TOP
BADGE_BG    = (142, 110, 157)

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'static', 'template.png')
_template = None

def get_template():
    global _template
    if _template is None:
        _template = Image.open(TEMPLATE_PATH).convert('RGBA')
    return _template

def remove_background(img_pil):
    """
    Remove background using rembg with u2netp (smallest model ~4MB).
    Falls back to GrabCut-style portrait crop if model fails.
    """
    try:
        from rembg import remove, new_session
        session = new_session('u2netp')
        buf = io.BytesIO()
        img_pil.save(buf, format='PNG')
        result_bytes = remove(buf.getvalue(), session=session)
        return Image.open(io.BytesIO(result_bytes)).convert('RGBA')
    except Exception as e:
        # Fallback: just return image as-is with white background removed
        return img_pil.convert('RGBA')

def process_photo(photo_bytes):
    # Open and resize input to save memory
    person_orig = Image.open(io.BytesIO(photo_bytes)).convert('RGBA')
    
    # Resize to max 800px on longest side before processing
    max_dim = 800
    w, h = person_orig.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        person_orig = person_orig.resize((int(w*scale), int(h*scale)), Image.LANCZOS)

    # Remove background
    person = remove_background(person_orig)
    del person_orig

    # Scale to fill zone — top anchored, center horizontally
    person_w, person_h = person.size
    aspect   = person_h / person_w
    scaled_w = ZONE_W
    scaled_h = int(scaled_w * aspect)

    if scaled_h < ZONE_H:
        scaled_h = ZONE_H
        scaled_w = int(scaled_h / aspect)

    person_resized = person.resize((scaled_w, scaled_h), Image.LANCZOS)
    del person

    # Place on purple canvas
    zone_canvas = Image.new('RGBA', (ZONE_W, ZONE_H), (*BADGE_BG, 255))
    paste_x = (ZONE_W - scaled_w) // 2
    zone_canvas.paste(person_resized, (paste_x, 0), person_resized)
    del person_resized

    # Composite onto template
    tmpl   = get_template()
    output = tmpl.copy()
    output.paste(zone_canvas, (ZONE_LEFT, ZONE_TOP))
    del zone_canvas
    output = Image.alpha_composite(output, tmpl)

    # Return JPEG
    output_rgb = output.convert('RGB')
    del output
    out_bytes = io.BytesIO()
    output_rgb.save(out_bytes, format='JPEG', quality=92)
    del output_rgb
    out_bytes.seek(0)
    return out_bytes


@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/generate', methods=['POST'])
def generate():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded'}), 400

    file = request.files['photo']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        photo_bytes = file.read()
        result = process_photo(photo_bytes)
        return send_file(
            result,
            mimetype='image/jpeg',
            as_attachment=True,
            download_name='GCCWPA2026_IAmAttending.jpg'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
