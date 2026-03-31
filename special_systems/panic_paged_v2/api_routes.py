"""
Panic Paged V2 API路由
添加到主Flask应用中
"""
from flask import jsonify, request
import sys
from pathlib import Path

# 添加路径
sys.path.insert(0, str(Path('/home/user/webapp/panic_paged_v2')))

from data_manager import PanicPagedDataManager

# 初始化数据管理器
panic_paged_manager = PanicPagedDataManager()

# ============================================================================
# API路由（添加到app.py中）
# ============================================================================

def register_panic_paged_routes(app):
    """注册Panic Paged V2的所有路由"""
    
    @app.route('/api/panic-paged/24h/latest')
    def panic_paged_24h_latest():
        """
        获取最新的24小时数据
        
        返回:
        {
            "success": true,
            "data": {
                "timestamp": 1770792843198,
                "beijing_time": "2026-02-11 14:54:03",
                "liquidation_24h": 16642.09,
                "liquidation_count_24h": 7.08,
                "open_interest": 56.27,
                "panic_index": 0.1258,
                "panic_level": "中等恐慌"
            }
        }
        """
        try:
            data = panic_paged_manager.get_24h_latest()
            if data:
                return jsonify({
                    'success': True,
                    'data': data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '暂无数据'
                }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/panic-paged/1h/latest')
    def panic_paged_1h_latest():
        """
        获取最新的1小时数据
        
        返回:
        {
            "success": true,
            "data": {
                "timestamp": 1770792843198,
                "beijing_time": "2026-02-11 14:54:03",
                "liquidation_1h": 3996.87
            }
        }
        """
        try:
            data = panic_paged_manager.get_1h_latest()
            if data:
                return jsonify({
                    'success': True,
                    'data': data
                })
            else:
                return jsonify({
                    'success': False,
                    'error': '暂无数据'
                }), 404
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/panic-paged/24h/by-date')
    def panic_paged_24h_by_date():
        """
        获取指定日期的24小时数据
        
        参数:
            date: 日期字符串，格式 YYYY-MM-DD，如 2026-02-11
        
        示例:
            /api/panic-paged/24h/by-date?date=2026-02-11
        
        返回:
        {
            "success": true,
            "date": "2026-02-11",
            "count": 42,
            "data": [{...}, {...}, ...]
        }
        """
        try:
            date = request.args.get('date')
            if not date:
                return jsonify({
                    'success': False,
                    'error': '缺少date参数'
                }), 400
            
            data = panic_paged_manager.get_24h_data_by_date(date)
            
            return jsonify({
                'success': True,
                'date': date,
                'count': len(data),
                'data': data
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/panic-paged/1h/by-date')
    def panic_paged_1h_by_date():
        """
        获取指定日期的1小时数据
        
        参数:
            date: 日期字符串，格式 YYYY-MM-DD，如 2026-02-11
        
        示例:
            /api/panic-paged/1h/by-date?date=2026-02-11
        
        返回:
        {
            "success": true,
            "date": "2026-02-11",
            "count": 42,
            "data": [{...}, {...}, ...]
        }
        """
        try:
            date = request.args.get('date')
            if not date:
                return jsonify({
                    'success': False,
                    'error': '缺少date参数'
                }), 400
            
            data = panic_paged_manager.get_1h_data_by_date(date)
            
            return jsonify({
                'success': True,
                'date': date,
                'count': len(data),
                'data': data
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/panic-paged/available-dates')
    def panic_paged_available_dates():
        """
        获取所有可用的日期列表
        
        返回:
        {
            "success": true,
            "dates_24h": ["2026-02-01", "2026-02-02", ...],
            "dates_1h": ["2026-02-01", "2026-02-02", ...]
        }
        """
        try:
            dates = panic_paged_manager.get_available_dates()
            return jsonify({
                'success': True,
                **dates
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/panic-paged/24h/date-range')
    def panic_paged_24h_date_range():
        """
        获取日期范围内的24小时数据
        
        参数:
            start_date: 开始日期，格式 YYYY-MM-DD
            end_date: 结束日期，格式 YYYY-MM-DD
        
        示例:
            /api/panic-paged/24h/date-range?start_date=2026-02-10&end_date=2026-02-11
        
        返回:
        {
            "success": true,
            "start_date": "2026-02-10",
            "end_date": "2026-02-11",
            "data": {
                "2026-02-10": [{...}, {...}],
                "2026-02-11": [{...}, {...}]
            }
        }
        """
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if not start_date or not end_date:
                return jsonify({
                    'success': False,
                    'error': '缺少start_date或end_date参数'
                }), 400
            
            data = panic_paged_manager.get_24h_date_range(start_date, end_date)
            
            return jsonify({
                'success': True,
                'start_date': start_date,
                'end_date': end_date,
                'data': data
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/api/panic-paged/1h/date-range')
    def panic_paged_1h_date_range():
        """
        获取日期范围内的1小时数据
        """
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if not start_date or not end_date:
                return jsonify({
                    'success': False,
                    'error': '缺少start_date或end_date参数'
                }), 400
            
            data = panic_paged_manager.get_1h_date_range(start_date, end_date)
            
            return jsonify({
                'success': True,
                'start_date': start_date,
                'end_date': end_date,
                'data': data
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    # 页面路由
    @app.route('/panic-paged-v2')
    def panic_paged_v2_page():
        """渲染Panic Paged V2页面"""
        return render_template('panic_paged_v2.html')

# ============================================================================
# 使用说明
# ============================================================================
"""
在 /home/user/webapp/code/python/app.py 中添加以下代码:

# 在文件开头导入
from panic_paged_v2.api_routes import register_panic_paged_routes

# 在创建app后调用
register_panic_paged_routes(app)
"""
