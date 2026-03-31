#!/usr/bin/env python3
"""
正数占比转换点查询工具
用于查询和分析历史转换数据
"""

import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

class TransitionQueryTool:
    """转换点查询工具"""
    
    def __init__(self, data_file: str = "data/coin_change_tracker/transitions/positive_ratio_transitions.jsonl"):
        self.data_file = Path(data_file)
        self.transitions = self._load_transitions()
    
    def _load_transitions(self) -> List[Dict]:
        """加载转换数据"""
        transitions = []
        if not self.data_file.exists():
            print(f"❌ 数据文件不存在: {self.data_file}")
            return transitions
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    transitions.append(json.loads(line))
        return transitions
    
    def query_by_date(self, date: str) -> Optional[Dict]:
        """按日期查询"""
        for t in self.transitions:
            if t['date'] == date:
                return t
        return None
    
    def query_date_range(self, start_date: str, end_date: str) -> List[Dict]:
        """查询日期范围"""
        results = []
        for t in self.transitions:
            if start_date <= t['date'] <= end_date:
                results.append(t)
        return sorted(results, key=lambda x: x['date'])
    
    def filter_by_transition(self, has_transition: bool = True) -> List[Dict]:
        """筛选是否有转换"""
        return [t for t in self.transitions if t['has_transition'] == has_transition]
    
    def filter_by_peak(self, min_peak: float = 50.0) -> List[Dict]:
        """筛选最高占比大于指定值的"""
        return [t for t in self.transitions if t['max_ratio'] >= min_peak]
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        if not self.transitions:
            return {}
        
        with_transition = self.filter_by_transition(True)
        peak_over_50 = self.filter_by_peak(50.0)
        
        stats = {
            'total_days': len(self.transitions),
            'with_transition': len(with_transition),
            'without_transition': len(self.transitions) - len(with_transition),
            'transition_rate': f"{len(with_transition) / len(self.transitions) * 100:.1f}%",
            'peak_over_50_days': len(peak_over_50),
            'max_peak': max(t['max_ratio'] for t in self.transitions),
            'min_peak': min(t['max_ratio'] for t in self.transitions),
            'avg_peak': sum(t['max_ratio'] for t in self.transitions) / len(self.transitions),
        }
        
        if with_transition:
            stats['avg_threshold'] = sum(t['threshold'] for t in with_transition) / len(with_transition)
            stats['avg_transition_ratio'] = sum(t['transition_ratio'] for t in with_transition) / len(with_transition)
        
        return stats
    
    def format_transition(self, t: Dict, verbose: bool = False) -> str:
        """格式化输出单条转换记录"""
        date = t['date']
        max_ratio = t['max_ratio']
        has_trans = t['has_transition']
        
        if not has_trans:
            return f"📅 {date}: 最高 {max_ratio:.2f}% ❌ 无转换 (未达到50%或未跌破临界点)"
        
        max_time = t.get('max_time', 'N/A')
        threshold = t['threshold']
        trans_time = t.get('transition_time', 'N/A')
        trans_ratio = t['transition_ratio']
        trans_change = t.get('transition_total_change', 'N/A')
        
        output = f"📅 {date}: 最高 {max_ratio:.2f}% ({max_time}) → 转空 {trans_ratio:.2f}% ({trans_time})"
        
        if verbose:
            output += f"\n   临界点: {threshold:.2f}%"
            output += f"\n   累计涨跌: {trans_change}"
            if 'data_points_after_peak' in t:
                output += f"\n   转换延迟: {t['data_points_after_peak']} 个数据点"
        
        return output
    
    def display_results(self, results: List[Dict], title: str = "查询结果", verbose: bool = False):
        """显示查询结果"""
        print(f"\n{'='*80}")
        print(f"🔍 {title}")
        print(f"{'='*80}")
        
        if not results:
            print("❌ 没有找到符合条件的数据")
            return
        
        print(f"📊 找到 {len(results)} 条记录\n")
        
        for t in results:
            print(self.format_transition(t, verbose))
            if verbose:
                print()

def main():
    parser = argparse.ArgumentParser(description="正数占比转换点查询工具")
    parser.add_argument('-d', '--date', help='查询指定日期 (格式: 20260311)')
    parser.add_argument('-r', '--range', nargs=2, metavar=('START', 'END'), 
                       help='查询日期范围 (格式: 20260301 20260311)')
    parser.add_argument('-t', '--transition-only', action='store_true',
                       help='只显示有转换的日期')
    parser.add_argument('-p', '--peak', type=float, default=None,
                       help='筛选最高占比大于指定值的记录')
    parser.add_argument('-s', '--stats', action='store_true',
                       help='显示统计信息')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='显示详细信息')
    parser.add_argument('--recent', type=int, metavar='N',
                       help='显示最近N天的数据')
    
    args = parser.parse_args()
    
    tool = TransitionQueryTool()
    
    if not tool.transitions:
        print("❌ 没有可用的转换数据")
        return
    
    # 显示统计信息
    if args.stats:
        stats = tool.get_statistics()
        print("\n" + "="*80)
        print("📊 统计信息")
        print("="*80)
        print(f"总天数: {stats['total_days']}")
        print(f"有转换: {stats['with_transition']} ({stats['transition_rate']})")
        print(f"无转换: {stats['without_transition']}")
        print(f"最高占比>50%: {stats['peak_over_50_days']} 天")
        print(f"最高峰值: {stats['max_peak']:.2f}%")
        print(f"最低峰值: {stats['min_peak']:.2f}%")
        print(f"平均峰值: {stats['avg_peak']:.2f}%")
        if 'avg_threshold' in stats:
            print(f"平均临界点: {stats['avg_threshold']:.2f}%")
            print(f"平均转换占比: {stats['avg_transition_ratio']:.2f}%")
        print()
    
    # 按日期查询
    if args.date:
        result = tool.query_by_date(args.date)
        if result:
            tool.display_results([result], f"日期查询: {args.date}", args.verbose)
        else:
            print(f"❌ 没有找到日期 {args.date} 的数据")
        return
    
    # 日期范围查询
    if args.range:
        start, end = args.range
        results = tool.query_date_range(start, end)
        tool.display_results(results, f"日期范围: {start} ~ {end}", args.verbose)
        return
    
    # 最近N天
    if args.recent:
        all_sorted = sorted(tool.transitions, key=lambda x: x['date'], reverse=True)
        results = all_sorted[:args.recent]
        tool.display_results(results, f"最近 {args.recent} 天", args.verbose)
        return
    
    # 筛选查询
    results = tool.transitions
    
    if args.transition_only:
        results = tool.filter_by_transition(True)
    
    if args.peak is not None:
        results = [t for t in results if t['max_ratio'] >= args.peak]
    
    if results != tool.transitions:
        title = "筛选结果"
        if args.transition_only:
            title += " (仅有转换)"
        if args.peak:
            title += f" (峰值≥{args.peak}%)"
        tool.display_results(results, title, args.verbose)
    else:
        # 默认显示所有
        tool.display_results(tool.transitions, "全部数据", args.verbose)

if __name__ == "__main__":
    main()
