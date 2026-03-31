#!/usr/bin/env python3
"""
临时脚本: 禁用 /api/okx-trading/place-order API
"""
from flask import Flask, jsonify, request, Blueprint
import sys

# 创建一个临时的Blueprint来覆盖原API
disable_bp = Blueprint('disable_trading', __name__)

@disable_bp.route('/api/okx-trading/place-order', methods=['POST', 'GET'])
def disabled_place_order():
    """禁用的下单API"""
    return jsonify({
        'success': False,
        'error': 'API_DISABLED',
        'message': 'API has been disabled by administrator',
        'reason': 'Prevent unauthorized automatic trading',
        'contact': 'Use ABC Position System instead'
    }), 403

def init_app(app):
    """注册禁用的路由"""
    app.register_blueprint(disable_bp)
    print("[禁用API] /api/okx-trading/place-order 已被禁用")

if __name__ == '__main__':
    print("此脚本需要在Flask app中导入使用")
