#!/usr/bin/env python3
"""
Panic V3 API服务
提供数据查询接口
"""

from flask import Flask, jsonify, render_template, request
from pathlib import Path
import json
from datetime import datetime, timedelta
import pytz

app = Flask(__name__)
BEIJING_TZ = pytz.timezone('Asia/Shanghai')
DATA_DIR = Path(__file__).parent / 'data'


def load_daily_data(date_str):
    """
    加载指定日期的数据
    
    参数:
        date_str: YYYYMMDD格式的日期字符串
    
    返回:
        list: 数据列表
    """
    file_path = DATA_DIR / f'panic_{date_str}.jsonl'
    
    if not file_path.exists():
        return []
    
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except:
                    continue
    
    return data


def load_recent_data(days=7):
    """
    加载最近N天的数据
    
    参数:
        days: 天数
    
    返回:
        list: 数据列表（按时间排序）
    """
    all_data = []
    now = datetime.now(BEIJING_TZ)
    
    for i in range(days):
        date = now - timedelta(days=i)
        date_str = date.strftime('%Y%m%d')
        daily_data = load_daily_data(date_str)
        all_data.extend(daily_data)
    
    # 按时间戳排序
    all_data.sort(key=lambda x: x.get('timestamp', 0))
    
    return all_data


@app.route('/')
def index():
    """主页"""
    return render_template('panic_v3.html')


@app.route('/api/latest')
def get_latest():
    """
    获取最新一条数据
    
    返回:
    {
        "success": true,
        "data": {...}
    }
    """
    try:
        # 加载今天的数据
        today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
        data = load_daily_data(today)
        
        if not data:
            # 如果今天没有，尝试昨天
            yesterday = (datetime.now(BEIJING_TZ) - timedelta(days=1)).strftime('%Y%m%d')
            data = load_daily_data(yesterday)
        
        if not data:
            return jsonify({
                'success': False,
                'message': '暂无数据'
            })
        
        # 返回最后一条
        latest = data[-1]
        
        return jsonify({
            'success': True,
            'data': latest
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


@app.route('/api/history/24h')
def get_24h_history():
    """
    获取最近24小时的数据
    
    返回:
    {
        "success": true,
        "count": 100,
        "data": [...]
    }
    """
    try:
        # 加载最近2天的数据（确保覆盖24小时）
        data = load_recent_data(days=2)
        
        if not data:
            return jsonify({
                'success': True,
                'count': 0,
                'data': []
            })
        
        # 过滤最近24小时
        now_ts = int(datetime.now(BEIJING_TZ).timestamp() * 1000)
        cutoff_ts = now_ts - (24 * 60 * 60 * 1000)  # 24小时前
        
        filtered_data = [d for d in data if d.get('timestamp', 0) >= cutoff_ts]
        
        return jsonify({
            'success': True,
            'count': len(filtered_data),
            'data': filtered_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


@app.route('/api/history/daily')
def get_daily_history():
    """
    获取指定日期的数据
    
    参数:
        date: YYYYMMDD格式的日期 (可选，默认今天)
    
    返回:
    {
        "success": true,
        "date": "20260211",
        "count": 1440,
        "data": [...]
    }
    """
    try:
        date_str = request.args.get('date', datetime.now(BEIJING_TZ).strftime('%Y%m%d'))
        data = load_daily_data(date_str)
        
        return jsonify({
            'success': True,
            'date': date_str,
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


@app.route('/api/history/recent')
def get_recent_history():
    """
    获取最近N天的数据
    
    参数:
        days: 天数 (默认7)
    
    返回:
    {
        "success": true,
        "days": 7,
        "count": 10000,
        "data": [...]
    }
    """
    try:
        days = int(request.args.get('days', 7))
        data = load_recent_data(days=days)
        
        return jsonify({
            'success': True,
            'days': days,
            'count': len(data),
            'data': data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
