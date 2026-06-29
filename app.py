import os
import io
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from PIL import Image
from rembg import remove

app = Flask(__name__, static_folder='static', static_url_path='')
CORS(app)

# ── Badge photo zone (mapped from your blue marking) ──────────────────────────
ZONE_LEFT   = 106
ZONE_TOP    = 415
ZONE_RIGHT  = 490
ZONE_BOTTOM = 898
ZONE_W      = ZONE_RIGHT - ZONE_LEFT   # 384px
ZONE_H      = ZONE_BOTTOM - ZONE_TOP   # 498px
BADGE_BG    = (142, 110, 157)          # Purple background color

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'static', 'template.png')

# Pre-load template once on startup so every request is fast
template = Image.open(TEMPLATE_PATH).convert('RGBA')


def process_photo(photo_bytes):
    """Full pipeline: remove bg → place on purple → fit into badge zone → composite onto template"""

    # Step 1 — Remove background
    removed = remove(photo_bytes)
    person  = Image.open(io.BytesIO(removed)).convert('RGBA')

    # Step 2 — Scale to fill zone width, anchor top
    person_w, person_h = person.size
    aspect   = person_h / person_w
    scaled_w = ZONE_W
    scaled_h = int(scaled_w * aspect)

    # If scaled height is less than zone height, scale up to fill zone height instead
    if scaled_h < ZONE_H:
        scaled_h = ZONE_H
        scaled_w = int(scaled_h / aspect)

    person_resized = person.resize((scaled_w, scaled_h), Image.LANCZOS)

    # Step 3 — Place person on purple canvas, top-anchored, centered horizontally
    zone_canvas = Image.new('RGBA', (ZONE_W, ZONE_H), (*BADGE_BG, 255))
    paste_x     = (ZONE_W - scaled_w) // 2
    paste_y     = 0  # top anchored — head at top of zone
    zone_canvas.paste(person_resized, (paste_x, paste_y), person_resized)

    # Step 4 — Composite zone onto template at badge position
    output = template.copy()
    output.paste(zone_canvas, (ZONE_LEFT, ZONE_TOP))

    # Step 5 — Re-overlay template so badge frame/border stays sharp on top
    output = Image.alpha_composite(output, template)

    # Step 6 — Convert to RGB JPEG
    output_rgb = output.convert('RGB')
    out_bytes  = io.BytesIO()
    output_rgb.save(out_bytes, format='JPEG', quality=95)
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
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        photo_bytes = file.read()
        result      = process_photo(photo_bytes)
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
