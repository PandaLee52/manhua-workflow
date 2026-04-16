"""
简化版Flask应用 - 用于测试静态文件服务
"""
from flask import Flask, send_from_directory, jsonify
import os

app = Flask(__name__)

# 记录启动信息
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

print(f"Base dir: {BASE_DIR}")
print(f"Static dir: {STATIC_DIR}")
print(f"Static exists: {os.path.exists(STATIC_DIR)}")
print(f"Index.html exists: {os.path.exists(os.path.join(STATIC_DIR, 'index.html'))}")

@app.route("/")
def index():
    return jsonify({"status": "ok", "message": "Simplified app running", "base_dir": BASE_DIR})

@app.route("/app")
def serve_app():
    static_path = os.path.join(BASE_DIR, "static")
    return send_from_directory(static_path, "index.html")

@app.route("/app/assets/<path:filename>")
def serve_assets(filename):
    static_path = os.path.join(BASE_DIR, "static", "assets")
    return send_from_directory(static_path, filename)

@app.route("/favicon.svg")
def serve_favicon():
    static_path = os.path.join(BASE_DIR, "static")
    return send_from_directory(static_path, "favicon.svg")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
