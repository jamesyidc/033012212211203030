"""
Panic恐慌清洗指数系统 - 清理后的路由配置
只保留真实API版本
"""

# ============================================================================
# Panic 主路由（真实API版本）
# ============================================================================

@app.route('/panic')
def panic_index():
    """Panic主页 - 重定向到真实API版本"""
    return redirect('/panic-real-api')

@app.route('/panic-real-api')
def panic_real_api():
    """Panic 真实API版本 - 直接调用/api/panic-v3/latest"""
    return render_template('panic_real_api.html')

# ============================================================================
# Panic V3 API路由（数据采集）
# ============================================================================

@app.route('/api/panic-v3/latest')
def api_panic_v3_latest():
    """获取最新的恐慌数据"""
    try:
        today = datetime.now(BEIJING_TZ).strftime('%Y%m%d')
        data_file = f'/home/user/webapp/panic_v3/data/panic_{today}.jsonl'
        
        if not os.path.exists(data_file):
            return jsonify({'success': False, 'error': '数据文件不存在'})
        
        # 读取最后一行（最新数据）
        with open(data_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if not lines:
                return jsonify({'success': False, 'error': '数据文件为空'})
            
            latest = json.loads(lines[-1])
            return jsonify({'success': True, 'data': latest})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================================================
# Panic Paged V2 API路由（按日翻页）
# ============================================================================

@app.route('/api/panic-paged/24h/latest')
def api_panic_paged_24h_latest():
    """获取最新的24小时数据"""
    try:
        from panic_paged_v2.data_manager import PanicPagedDataManager
        manager = PanicPagedDataManager()
        data = manager.get_24h_latest()
        if data:
            return jsonify({'success': True, 'data': data})
        else:
            return jsonify({'success': False, 'error': '暂无数据'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/panic-paged/1h/latest')
def api_panic_paged_1h_latest():
    """获取最新的1小时数据"""
    try:
        from panic_paged_v2.data_manager import PanicPagedDataManager
        manager = PanicPagedDataManager()
        data = manager.get_1h_latest()
        if data:
            return jsonify({'success': True, 'data': data})
        else:
            return jsonify({'success': False, 'error': '暂无数据'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/panic-paged/24h/by-date')
def api_panic_paged_24h_by_date():
    """获取指定日期的24小时数据"""
    try:
        date_str = request.args.get('date')  # YYYY-MM-DD格式
        if not date_str:
            return jsonify({'success': False, 'error': '缺少date参数'})
        
        from panic_paged_v2.data_manager import PanicPagedDataManager
        manager = PanicPagedDataManager()
        data = manager.get_24h_by_date(date_str)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/panic-paged/1h/by-date')
def api_panic_paged_1h_by_date():
    """获取指定日期的1小时数据"""
    try:
        date_str = request.args.get('date')  # YYYY-MM-DD格式
        if not date_str:
            return jsonify({'success': False, 'error': '缺少date参数'})
        
        from panic_paged_v2.data_manager import PanicPagedDataManager
        manager = PanicPagedDataManager()
        data = manager.get_1h_by_date(date_str)
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/panic-paged/available-dates')
def api_panic_paged_available_dates():
    """获取所有可用日期"""
    try:
        from panic_paged_v2.data_manager import PanicPagedDataManager
        manager = PanicPagedDataManager()
        dates = manager.get_available_dates()
        return jsonify({'success': True, 'dates': dates})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})
