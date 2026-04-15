#!/usr/bin/env python3
"""AI剪辑平台 - Render部署版"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'AI剪辑平台API已启动',
        'endpoints': ['/health', '/parse']
    })

@app.route('/health')
def health():
    return jsonify({'status': 'ok'})

@app.route('/parse', methods=['POST'])
def parse():
    data = request.get_json() or {}
    text = data.get('text', '')
    
    result = []
    if '开头' in text and '震撼' in text:
        result.append('开头: 震撼快节奏')
    if '中间' in text and '温馨' in text:
        result.append('中间: 温馨慢节奏')
    if '结尾' in text and '悬疑' in text:
        result.append('结尾: 悬疑风格')
    
    return jsonify({'success': True, 'instructions': result})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
