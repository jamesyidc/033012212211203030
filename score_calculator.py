#!/usr/bin/env python3
"""
Score Calculator - 评分计算器
"""


class ScoreCalculator:
    """评分计算器"""
    
    def __init__(self):
        pass
    
    def calculate_score(self, data):
        """
        计算综合评分
        
        Args:
            data: 输入数据
            
        Returns:
            float: 评分结果
        """
        try:
            # 简单的评分逻辑
            score = 0.0
            
            if isinstance(data, dict):
                # 基于数据字段计算评分
                if 'price_change' in data:
                    score += abs(data['price_change']) * 10
                
                if 'volume' in data:
                    score += data['volume'] / 1000000
                
                if 'signal_strength' in data:
                    score += data['signal_strength']
            
            return min(max(score, 0), 100)  # 限制在0-100之间
            
        except Exception as e:
            print(f"[ScoreCalculator] 计算评分失败: {e}")
            return 0.0
