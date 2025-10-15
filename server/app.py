# server/app.py
import os
from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
import numpy as np
from PIL import Image
import io
from fusion import guided_detail_injection

# --- CORS support (for cross-origin requests from Vercel UI hosted on a separate domain) ---
from flask_cors import CORS

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = Flask(__name__, static_folder="../web", static_url_path="/")

# Allow CORS for all origins for initial testing. IMPORTANT: for production,
# replace origins="*" with your frontend origin (e.g. "https://your-frontend.vercel.app")
CORS(app, origins="*")

ALLOWED = {"png", "jpg", "jpeg", "tif", "tiff", "bmp"}

def allowed(filename):
    ext = filename.rsplit(".",1)[-1].lower()
    return ext in ALLOWED

def pil_to_np(img):
    # returns numpy array
    return np.array(img)

@app.route("/")
def index():
    return app.send_static_file("index.html")

@app.route("/fuse", methods=["POST"])
def fuse():
    """
    Expects form-data:
      - optical: file (RGB high-res)
      - thermal: file (single-band or RGB low-res)
      optional form fields:
      - alpha (float)
      - blur_sigma (int)
      - edge_dilate (int)
    """
    if "optical" not in request.files or "thermal" not in request.files:
        return jsonify({"error":"optical and thermal files required"}), 400

    opt_file = request.files["optical"]
    th_file = request.files["thermal"]

    if not allowed(opt_file.filename) or not allowed(th_file.filename):
        return jsonify({"error":"unsupported file type"}), 400

    # read images into PIL
    opt_pil = Image.open(opt_file).convert("RGB")
    th_pil = Image.open(th_file).convert("L")  # convert thermal to single-band

    opt_np = pil_to_np(opt_pil)  # HxWx3 uint8
    th_np = pil_to_np(th_pil)    # h'xw' uint8

    # parameters
    try:
        alpha = float(request.form.get("alpha", 0.9))
    except:
        alpha = 0.9
    try:
        blur_sigma = float(request.form.get("blur_sigma", 5.0))
    except:
        blur_sigma = 5.0
    try:
        edge_dilate = int(request.form.get("edge_dilate", 3))
    except:
        edge_dilate = 3

    fused_rgb, fused_t, mask = guided_detail_injection(opt_np, th_np,
                                                       alpha=alpha,
                                                       blur_sigma=blur_sigma,
                                                       edge_dilate=edge_dilate)

    # save fused result to bytes (PNG)
    out_img = Image.fromarray(fused_rgb)
    bio = io.BytesIO()
    out_img.save(bio, format="PNG")
    bio.seek(0)

    return send_file(
        bio,
        mimetype="image/png",
        as_attachment=False,
        download_name="fused.png"
    )

if __name__ == "__main__":
    # When running locally for dev you can use this, but in production (Render),
    # we'll run with gunicorn and bind to the $PORT env var.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
