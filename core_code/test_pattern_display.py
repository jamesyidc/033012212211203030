#!/usr/bin/env python3
"""测试模式显示功能的临时脚本，生成测试数据"""
import json

# 生成测试数据
test_data = {
    "success": True,
    "date": "2026-02-25",
    "daily_prediction": "等待新低",
    "total_bars": 84,
    "total_change": -47.44,
    "summary": {
        "total_count": 5,
        "qualified_count": 1,
        "unqualified_count": 4
    },
    "qualified_patterns": [
        {
            "pattern_type": "pattern_1_3",
            "pattern_name": "诱多等待新低",
            "bar_type": "绿→黄→红 (3根)",
            "signal": "预高做空",
            "time_range": "04:50-05:10",
            "bars": [
                {"time": "04:50", "up_ratio": 67.59, "color": "绿", "emoji": "🟢"},
                {"time": "05:00", "up_ratio": 48.61, "color": "黄", "emoji": "🟡"},
                {"time": "05:10", "up_ratio": 42.59, "color": "红", "emoji": "🔴"}
            ],
            "trigger_ratio": 72.30,
            "threshold": 65.0
        }
    ],
    "unqualified_patterns": [
        {
            "pattern_type": "pattern_1_3",
            "pattern_name": "诱多等待新低",
            "bar_type": "红→黄→绿 (3根)",
            "signal": "预高做空",
            "time_range": "05:50-06:10",
            "bars": [
                {"time": "05:50", "up_ratio": 42.59, "color": "红", "emoji": "🔴"},
                {"time": "06:00", "up_ratio": 53.24, "color": "黄", "emoji": "🟡"},
                {"time": "06:10", "up_ratio": 62.04, "color": "绿", "emoji": "🟢"}
            ],
            "trigger_ratio": 62.04,
            "threshold": 65.0,
            "failure_reasons": [
                "最后一根柱子上涨占比 62.04% < 65.00%"
            ]
        },
        {
            "pattern_type": "pattern_1_3",
            "pattern_name": "诱多等待新低",
            "bar_type": "红→黄→绿 (3根)",
            "signal": "预高做空",
            "time_range": "08:40-09:00",
            "bars": [
                {"time": "08:40", "up_ratio": 40.74, "color": "红", "emoji": "🔴"},
                {"time": "08:50", "up_ratio": 48.61, "color": "黄", "emoji": "🟡"},
                {"time": "09:00", "up_ratio": 55.09, "color": "绿", "emoji": "🟢"}
            ],
            "trigger_ratio": 55.09,
            "threshold": 65.0,
            "failure_reasons": [
                "最后一根柱子上涨占比 55.09% < 65.00%"
            ]
        },
        {
            "pattern_type": "pattern_3",
            "pattern_name": "筑底信号",
            "bar_type": "黄→绿→黄 (3根)",
            "signal": "预低做多",
            "time_range": "06:00-06:20",
            "bars": [
                {"time": "06:00", "up_ratio": 53.24, "color": "黄", "emoji": "🟡"},
                {"time": "06:10", "up_ratio": 62.04, "color": "绿", "emoji": "🟢"},
                {"time": "06:20", "up_ratio": 54.63, "color": "黄", "emoji": "🟡"}
            ],
            "trigger_ratio": 54.63,
            "threshold": 10.0,
            "failure_reasons": [
                "最后一根柱子上涨占比 54.63% >= 10.00% (需要 < 10.00%)",
                "当日涨跌幅总和 -47.44% >= -50.00% (需要 < -50.00%)"
            ]
        },
        {
            "pattern_type": "pattern_4_3",
            "pattern_name": "诱空信号",
            "bar_type": "绿→红→绿 (3根)",
            "signal": "预低做多",
            "time_range": "00:20-00:40",
            "bars": [
                {"time": "00:20", "up_ratio": 93.06, "color": "绿", "emoji": "🟢"},
                {"time": "00:30", "up_ratio": 33.33, "color": "红", "emoji": "🔴"},
                {"time": "00:40", "up_ratio": 72.22, "color": "绿", "emoji": "🟢"}
            ],
            "trigger_ratio": 33.33,
            "threshold": 10.0,
            "failure_reasons": [
                "中间红柱子上涨占比 33.33% >= 10.00% (需要 < 10.00%)"
            ]
        }
    ]
}

print(json.dumps(test_data, ensure_ascii=False, indent=2))
