#!/usr/bin/env python3
"""
2月份暴跌预警统计可视化
生成HTML柱状图展示预警分布
"""
import json
from pathlib import Path
from datetime import datetime, timedelta

# 数据文件
DATA_FILE = Path('/home/user/webapp/data/crash_warning_events/february_analysis.json')
OUTPUT_HTML = Path('/home/user/webapp/static/february_warning_stats.html')

# 确保输出目录存在
OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)

# 读取分析数据
with open(DATA_FILE, 'r') as f:
    analysis = json.load(f)

# 提取预警日期
warning_dates = set()
for day_info in analysis['crash_warning_days']:
    date = day_info['date']
    warning_dates.add(date)

# 生成所有日期 (2月1日-24日)
all_days = []
start_date = datetime(2026, 2, 1)
for i in range(24):
    current_date = start_date + timedelta(days=i)
    date_str = current_date.strftime('%Y-%m-%d')
    
    day_data = {
        'date': date_str,
        'day_num': i + 1,  # 1-24
        'has_warning': date_str in warning_dates,
        'warning_type': None,
        'warning_level': None
    }
    
    # 如果有预警，获取详细信息
    if date_str in warning_dates:
        for day_info in analysis['crash_warning_days']:
            if day_info['date'] == date_str:
                warning = day_info['warning']
                day_data['warning_type'] = warning.get('pattern_name', '暴跌预警')
                day_data['warning_level'] = warning.get('warning_level', 'medium')
                day_data['peaks_count'] = day_info.get('peaks_count', 0)
                break
    
    all_days.append(day_data)

# 统计
total_days = len(all_days)
warning_days = len([d for d in all_days if d['has_warning']])
safe_days = total_days - warning_days
warning_rate = (warning_days / total_days * 100) if total_days > 0 else 0

# 生成HTML
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>2月份暴跌预警统计</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: "Microsoft YaHei", "微软雅黑", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            font-size: 36px;
            color: #2d3748;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 18px;
            color: #718096;
        }}
        
        .summary {{
            display: flex;
            justify-content: space-around;
            margin-bottom: 40px;
            gap: 20px;
        }}
        
        .summary-card {{
            flex: 1;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .summary-card.total {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        
        .summary-card.green {{
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            color: #2d3748;
        }}
        
        .summary-card.red {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
            color: white;
        }}
        
        .summary-card .number {{
            font-size: 48px;
            font-weight: bold;
            margin: 10px 0;
        }}
        
        .summary-card .label {{
            font-size: 16px;
            opacity: 0.9;
        }}
        
        .summary-card .percentage {{
            font-size: 24px;
            margin-top: 5px;
            opacity: 0.8;
        }}
        
        .chart-container {{
            margin-top: 40px;
        }}
        
        .chart-title {{
            font-size: 24px;
            font-weight: bold;
            color: #2d3748;
            margin-bottom: 20px;
            text-align: center;
        }}
        
        .chart {{
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            height: 400px;
            padding: 20px;
            border: 2px solid #e2e8f0;
            border-radius: 12px;
            background: #f7fafc;
            position: relative;
        }}
        
        .chart::before {{
            content: '';
            position: absolute;
            bottom: 20px;
            left: 20px;
            right: 20px;
            height: 2px;
            background: #cbd5e0;
        }}
        
        .bar-wrapper {{
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: flex-end;
            height: 100%;
            padding: 0 2px;
            position: relative;
        }}
        
        .bar {{
            width: 100%;
            max-width: 40px;
            border-radius: 8px 8px 0 0;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            box-shadow: 0 -2px 8px rgba(0,0,0,0.1);
        }}
        
        .bar:hover {{
            transform: translateY(-5px);
            box-shadow: 0 -4px 16px rgba(0,0,0,0.2);
        }}
        
        .bar.green {{
            background: linear-gradient(180deg, #48bb78 0%, #38a169 100%);
            height: 60px;
        }}
        
        .bar.red.critical {{
            background: linear-gradient(180deg, #f56565 0%, #e53e3e 100%);
            height: 200px;
        }}
        
        .bar.red.medium {{
            background: linear-gradient(180deg, #fc8181 0%, #f56565 100%);
            height: 150px;
        }}
        
        .bar-label {{
            margin-top: 8px;
            font-size: 12px;
            color: #4a5568;
            font-weight: 500;
        }}
        
        .bar-date {{
            font-size: 10px;
            color: #a0aec0;
            margin-top: 2px;
        }}
        
        .tooltip {{
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.9);
            color: white;
            padding: 12px;
            border-radius: 8px;
            font-size: 12px;
            white-space: nowrap;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.3s;
            margin-bottom: 10px;
            z-index: 1000;
        }}
        
        .tooltip::after {{
            content: '';
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            border: 6px solid transparent;
            border-top-color: rgba(0,0,0,0.9);
        }}
        
        .bar-wrapper:hover .tooltip {{
            opacity: 1;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 40px;
            margin-top: 30px;
            padding: 20px;
            background: #f7fafc;
            border-radius: 12px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .legend-color {{
            width: 30px;
            height: 20px;
            border-radius: 4px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .legend-color.green {{
            background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
        }}
        
        .legend-color.red {{
            background: linear-gradient(90deg, #f56565 0%, #e53e3e 100%);
        }}
        
        .legend-text {{
            font-size: 14px;
            color: #4a5568;
        }}
        
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e2e8f0;
            color: #718096;
            font-size: 14px;
        }}
        
        @media (max-width: 768px) {{
            .summary {{
                flex-direction: column;
            }}
            
            .chart {{
                height: 300px;
            }}
            
            .bar {{
                max-width: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚨 行情预判 (0-2分析)</h1>
            <p class="subtitle">2026年2月 暴跌预警统计分析</p>
        </div>
        
        <div class="summary">
            <div class="summary-card total">
                <div class="label">📊 总天数</div>
                <div class="number">{total_days}</div>
                <div class="label">2月1日 - 2月24日</div>
            </div>
            
            <div class="summary-card green">
                <div class="label">✅ 绿色</div>
                <div class="number">{safe_days}</div>
                <div class="percentage">无预警 = {safe_days}/{total_days} ≈ {100-warning_rate:.1f}%</div>
            </div>
            
            <div class="summary-card red">
                <div class="label">🚨 红色</div>
                <div class="number">{warning_days}</div>
                <div class="percentage">有预警 = {warning_days}/{total_days} ≈ {warning_rate:.1f}%</div>
            </div>
        </div>
        
        <div class="chart-container">
            <div class="chart-title">📈 每日预警状态分布图</div>
            <div class="chart">
'''

# 生成柱状图
for day in all_days:
    day_num = day['day_num']
    date = day['date']
    has_warning = day['has_warning']
    
    if has_warning:
        warning_level = day['warning_level']
        warning_type = day['warning_type']
        peaks_count = day.get('peaks_count', 0)
        
        bar_class = 'red critical' if warning_level == 'critical' else 'red medium'
        tooltip_text = f"{date}<br/>⚠️ {warning_type}<br/>波峰数: {peaks_count}"
    else:
        bar_class = 'green'
        tooltip_text = f"{date}<br/>✅ 无预警"
    
    html_content += f'''
                <div class="bar-wrapper">
                    <div class="bar {bar_class}"></div>
                    <div class="tooltip">{tooltip_text}</div>
                    <div class="bar-label">{day_num}</div>
                    <div class="bar-date">{date[5:]}</div>
                </div>
'''

html_content += '''
            </div>
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color green"></div>
                <span class="legend-text">✅ 绿色 = 无预警（安全）</span>
            </div>
            <div class="legend-item">
                <div class="legend-color red"></div>
                <span class="legend-text">🚨 红色 = 有预警（危险）</span>
            </div>
        </div>
        
        <div class="footer">
            <p>📊 数据分析时间: ''' + analysis['analysis_time'] + '''</p>
            <p>💡 暴跌预警说明: A点递减（A1 > A2 > A3 或 A2 > A3 > A4）触发时显示红色</p>
            <p>🔗 系统URL: https://9002-imp6ky5dtwten0w001hfy-82b888ba.sandbox.novita.ai/coin-change-tracker</p>
        </div>
    </div>
</body>
</html>
'''

# 写入文件
with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"✅ 统计图表已生成:")
print(f"   文件: {OUTPUT_HTML}")
print(f"   总天数: {total_days}")
print(f"   安全天数: {safe_days} (绿色)")
print(f"   预警天数: {warning_days} (红色)")
print(f"   预警率: {warning_rate:.1f}%")
print(f"\n预警日期:")
for day in all_days:
    if day['has_warning']:
        print(f"  - {day['date']}: {day['warning_type']}")
