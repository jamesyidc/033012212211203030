#!/usr/bin/env python3
"""
SAR API JSONL - SAR指标数据API
"""
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

# 交易对列表
SYMBOLS = [
    'BTC-USDT', 'ETH-USDT', 'BNB-USDT', 'XRP-USDT', 'ADA-USDT',
    'DOGE-USDT', 'SOL-USDT', 'DOT-USDT', 'MATIC-USDT', 'LTC-USDT',
    'LINK-USDT', 'HBAR-USDT', 'TAO-USDT', 'CFX-USDT', 'TRX-USDT',
    'TON-USDT', 'NEAR-USDT', 'LDO-USDT', 'CRO-USDT', 'ETC-USDT',
    'XLM-USDT', 'BCH-USDT', 'UNI-USDT', 'SUI-USDT', 'FIL-USDT',
    'STX-USDT', 'CRV-USDT', 'AAVE-USDT', 'APT-USDT'
]


def get_sar_current_cycle(symbol='BTC-USDT', limit=500, include_history=False):
    """
    获取指定交易对的当前SAR完整周期
    
    注意：此函数返回从最近转换点到当前的完整周期数据
    不是最近N条记录，而是当前完整的多头或空头周期
    
    Args:
        symbol: 交易对符号
        limit: 最大返回记录数（默认500条，防止极长周期）
        include_history: 是否包含历史数据（默认False，只返回当前周期）
        
    Returns:
        dict: 包含success, data, current_status等字段的响应字典
    """
    try:
        data_dir = Path('/home/user/webapp/data/sar_jsonl')
        
        if not data_dir.exists():
            return {
                'success': False,
                'message': 'SAR数据目录不存在',
                'data': []
            }
        
        # 读取symbol对应的文件
        symbol_short = symbol.replace('-USDT', '').replace('-USDT-SWAP', '')
        symbol_file = data_dir / f"{symbol_short}.jsonl"
        
        if not symbol_file.exists():
            return {
                'success': False,
                'message': f'未找到{symbol}的数据文件',
                'data': []
            }
        
        # 读取所有数据（至少最近1000条，确保能找到完整周期）
        all_records = []
        try:
            with open(symbol_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 读取最后1000条（应该足够包含最长的周期）
                for line in lines[-1000:]:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            all_records.append(data)
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            print(f"[SAR API] 读取{symbol_file}失败: {e}")
            return {
                'success': False,
                'message': f'读取数据失败: {str(e)}',
                'data': []
            }
        
        if not all_records:
            return {
                'success': False,
                'message': '未找到有效数据',
                'data': []
            }
        
        # 当前状态（最后一条记录）
        current_position = all_records[-1]['position']
        
        if include_history:
            # 返回所有历史数据（最近limit条）
            current_cycle_records = all_records[-limit:]
        else:
            # 从最后往前找，找到当前周期的所有记录（直到遇到不同的position）
            current_cycle_records = [all_records[-1]]
            for i in range(len(all_records) - 2, -1, -1):
                if all_records[i]['position'] == current_position:
                    current_cycle_records.insert(0, all_records[i])
                else:
                    # 遇到转换点，停止
                    break
            
            # 限制返回数量（防止极长周期）
            current_cycle_records = current_cycle_records[:limit]
        
        # 转换为API格式
        results = []
        
        if include_history:
            # 历史模式：需要正确计算每个点的序号（根据周期变化）
            current_seq = 1
            last_position = None
            
            for data in current_cycle_records:
                position = data.get('position', 'unknown')
                
                # 如果position变化，重置序号
                if last_position is not None and last_position != position:
                    current_seq = 1
                
                result = {
                    'symbol': symbol,
                    'cycle': position,
                    'position': position,
                    'sar_value': data.get('sar', 0),
                    'sar': data.get('sar', 0),
                    'price': data.get('close', 0),
                    'timestamp': data.get('timestamp', 0),
                    'duration': current_seq,
                    'sequence': current_seq,
                    'time': data.get('beijing_time', ''),
                    'slope_value': data.get('slope_value', 0),
                    'slope_direction': data.get('slope_direction', 'unknown'),
                    'quadrant': data.get('quadrant', 'unknown'),
                    'beijing_time': data.get('beijing_time', '')
                }
                results.append(result)
                
                last_position = position
                current_seq += 1
        else:
            # 当前周期模式：序号简单递增
            for idx, data in enumerate(current_cycle_records, 1):
                result = {
                    'symbol': symbol,
                    'cycle': data.get('position', 'unknown'),
                    'position': data.get('position', 'unknown'),
                    'sar_value': data.get('sar', 0),
                    'sar': data.get('sar', 0),
                    'price': data.get('close', 0),
                    'timestamp': data.get('timestamp', 0),
                    'duration': idx,
                    'sequence': idx,
                    'time': data.get('beijing_time', ''),
                    'slope_value': data.get('slope_value', 0),
                    'slope_direction': data.get('slope_direction', 'unknown'),
                    'quadrant': data.get('quadrant', 'unknown'),
                    'beijing_time': data.get('beijing_time', '')
                }
                results.append(result)
        
        # 返回结果
        if results:
            # 计算增强字段（SAR差值等）
            results = _enhance_with_calculations(results)
            
            # 构建current_status字段（前端需要）
            latest = results[-1] if results else {}  # 最后一条是最新的
            position = latest.get('cycle', 'unknown')
            position_cn = '多头' if position == 'bullish' else '空头' if position == 'bearish' else '未知'
            
            if include_history:
                # 历史模式：统计多空比例
                bullish_count = sum(1 for r in results if r.get('position') == 'bullish')
                bearish_count = sum(1 for r in results if r.get('position') == 'bearish')
                total = len(results)
                
                # 找到当前周期的长度（从后往前数同position的记录）
                current_cycle_length = 1
                for i in range(len(results) - 2, -1, -1):
                    if results[i].get('position') == position:
                        current_cycle_length += 1
                    else:
                        break
                
                current_sequence = f"{position_cn}{str(current_cycle_length).zfill(2)}"
                cycle_info = f"序列{current_sequence}"
            else:
                # 当前周期模式：序号就是当前周期的长度
                sequence_number = len(results)
                current_sequence = f"{position_cn}{str(sequence_number).zfill(2)}"
                cycle_info = f"序列{current_sequence}"
                
                # 构建偏差统计（当前周期全是同一状态）
                total = len(results)
                if position == 'bullish':
                    bullish_count = total
                    bearish_count = 0
                else:
                    bullish_count = 0
                    bearish_count = total
            
            current_status = {
                'position': position,
                'position_cn': position_cn,
                'current_sequence': current_sequence,
                'cycle_info': cycle_info,
                'last_update': latest.get('beijing_time', ''),
                'duration_minutes': latest.get('duration', 0),
                'price': latest.get('price', 0),
                'sar_value': latest.get('sar_value', 0),
                'slope_value': latest.get('slope_value', 0),
                'slope_direction': latest.get('slope_direction', ''),
                'quadrant': latest.get('quadrant', '')
            }
            
            # 计算基于SAR差值的偏多偏空统计
            bias_statistics = _calculate_bias_by_sar_diff(results, include_history)
            
            return {
                'success': True,
                'data': results,
                'sequences': results,  # 前端期望sequences字段
                'count': len(results),
                'symbol': symbol,
                'current_status': current_status,
                'bias_statistics': bias_statistics,
                'total_sequences': total
            }
        
        # 没有找到数据
        return {
            'success': False,
            'message': f'未找到{symbol}的SAR数据',
            'data': [],
            'symbol': symbol
        }
        
    except Exception as e:
        print(f"[SAR API] 获取SAR周期失败: {e}")
        return {
            'success': False,
            'message': f'获取数据失败: {str(e)}',
            'data': [],
            'symbol': symbol
        }


def _enhance_with_calculations(results):
    """
    为序列数据添加计算字段
    包括：sar_diff, sequence_change_percent, 1天偏多偏空判断 等
    
    Args:
        results: 原始数据列表（按时间倒序，最新的在前）
    
    Returns:
        增强后的数据列表
    """
    if len(results) < 2:
        return results
    
    from collections import defaultdict
    
    # 第一步：按序号分组，计算每个序号的1天历史平均差值
    # 格式: {(position, sequence): [diff1, diff2, ...]}
    sequence_diffs_1day = defaultdict(list)
    
    # 收集所有数据的差值（用于计算1天平均）
    for r in results:
        position = r.get('position')  # 'bullish' or 'bearish'
        sequence = r.get('sequence') or r.get('duration')  # 序号
        sar_diff_abs = r.get('sar_diff_abs')
        
        # 如果原始数据没有 sar_diff_abs，临时计算
        if sar_diff_abs is None:
            price = r.get('price', 0)
            sar = r.get('sar', 0)
            if price > 0 and sar > 0:
                sar_diff_abs = abs(price - sar)
        
        if position and sequence is not None and sar_diff_abs and sar_diff_abs > 0:
            key = (position, sequence)
            sequence_diffs_1day[key].append(sar_diff_abs)
    
    # 计算每个序号的1天平均差值
    sequence_avg_1day = {}
    for key, diffs in sequence_diffs_1day.items():
        if len(diffs) > 0:
            sequence_avg_1day[key] = sum(diffs) / len(diffs)
    
    # 第二步：反转列表，使其按时间正序（最旧的在前）
    results_ordered = list(reversed(results))
    enhanced = []
    
    for i, current in enumerate(results_ordered):
        enhanced_item = current.copy()
        
        # 计算 SAR 差值（价格 - SAR）
        price = current.get('price', 0)
        sar = current.get('sar', 0)
        position = current.get('position')
        sequence = current.get('sequence') or current.get('duration')
        
        if price > 0 and sar > 0:
            # SAR差值 = |价格 - SAR|
            sar_diff_abs = abs(price - sar)
            enhanced_item['sar_diff_abs'] = round(sar_diff_abs, 6)
            
            # SAR差值百分比 = SAR差值 / 价格 * 100
            sar_diff_pct = (sar_diff_abs / price) * 100
            enhanced_item['sar_diff_pct'] = round(sar_diff_pct, 4)
            
            # 计算1天平均差值并判断偏多偏空
            key = (position, sequence) if position and sequence is not None else None
            if key and key in sequence_avg_1day:
                avg_diff_1day = sequence_avg_1day[key]
                enhanced_item['avg_diff_1day'] = round(avg_diff_1day, 6)
                
                # 计算当前差值占平均的百分比
                diff_ratio_1day = (sar_diff_abs / avg_diff_1day) * 100 if avg_diff_1day > 0 else 0
                enhanced_item['diff_ratio_1day'] = round(diff_ratio_1day, 2)
                
                # 判断偏多偏空
                if position == 'bullish':  # 多头状态
                    if sar_diff_abs < avg_diff_1day:
                        enhanced_item['bias_1day'] = '偏多'  # 差值小于平均，偏多
                    else:
                        enhanced_item['bias_1day'] = '偏空'  # 差值大于平均，偏空
                elif position == 'bearish':  # 空头状态
                    if sar_diff_abs < avg_diff_1day:
                        enhanced_item['bias_1day'] = '偏空'  # 差值小于平均，偏空
                    else:
                        enhanced_item['bias_1day'] = '偏多'  # 差值大于平均，偏多
                else:
                    enhanced_item['bias_1day'] = '-'
            else:
                enhanced_item['avg_diff_1day'] = None
                enhanced_item['diff_ratio_1day'] = None
                enhanced_item['bias_1day'] = '-'
        
        # 计算 SAR 变化（与前一条记录比较）
        if i > 0:
            prev = results_ordered[i - 1]
            current_sar = current.get('sar', 0)
            prev_sar = prev.get('sar', 0)
            
            if prev_sar != 0:
                sar_change = current_sar - prev_sar
                enhanced_item['sar_change'] = round(sar_change, 4)
                
                # 序列变化百分比（SAR变化百分比）
                sequence_change_pct = (sar_change / abs(prev_sar)) * 100
                enhanced_item['sequence_change_percent'] = round(sequence_change_pct, 4)
        
        enhanced.append(enhanced_item)
    
    # 再次反转回原来的顺序（最新的在前）
    return list(reversed(enhanced))



def _calculate_bias_by_sar_diff(results, include_history=False):
    """
    基于SAR差值计算偏多偏空统计（按序号分组）
    
    核心逻辑：
    1. 识别每个数据点的序号（多头01/多头02/空头01/空头02...）
    2. 按序号分组，计算每个序号的历史平均差值
       - 多头01: 历史所有多头01的差值平均
       - 多头02: 历史所有多头02的差值平均
       - 空头01: 历史所有空头01的差值平均
       - ...
    3. 对最近2小时的每个数据点：
       - 找到该点的序号（如多头02）
       - 比较当前差值 vs 该序号的历史平均差值
       - 多头: 差值 < 平均 → 偏多; 差值 > 平均 → 偏空
       - 空头: 差值 < 平均 → 偏空; 差值 > 平均 → 偏多
    4. 统计偏多/偏空的数量和比例
    
    Args:
        results: 增强后的数据列表（包含sar_diff_abs、sequence字段）
        include_history: 是否包含历史数据
    
    Returns:
        dict: 包含bullish_count, bearish_count, bullish_ratio, bearish_ratio
    """
    from collections import defaultdict
    
    if not results or len(results) < 10:
        # 数据不足，返回简单统计
        bullish_count = sum(1 for r in results if r.get('position') == 'bullish')
        bearish_count = sum(1 for r in results if r.get('position') == 'bearish')
        total = len(results)
        return {
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'bullish_ratio': round(bullish_count / total * 100, 2) if total > 0 else 0,
            'bearish_ratio': round(bearish_count / total * 100, 2) if total > 0 else 0,
            'method': 'simple_count',
            'reason': '数据不足'
        }
    
    # 第1步：按序号分组，计算每个序号的历史平均差值
    # 格式: {(position, sequence): [diff1, diff2, ...]}
    sequence_diffs = defaultdict(list)
    
    for r in results:
        position = r.get('position')  # 'bullish' or 'bearish'
        sequence = r.get('sequence') or r.get('duration')  # 序号
        diff_abs = r.get('sar_diff_abs')
        
        if not position or sequence is None or diff_abs is None or diff_abs <= 0:
            continue
        
        # 使用 (position, sequence) 作为key
        sequence_diffs[(position, sequence)].append(diff_abs)
    
    if not sequence_diffs:
        # 没有有效数据，返回简单统计
        bullish_count = sum(1 for r in results if r.get('position') == 'bullish')
        bearish_count = sum(1 for r in results if r.get('position') == 'bearish')
        total = len(results)
        return {
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'bullish_ratio': round(bullish_count / total * 100, 2) if total > 0 else 0,
            'bearish_ratio': round(bearish_count / total * 100, 2) if total > 0 else 0,
            'method': 'simple_count',
            'reason': '无有效序号数据'
        }
    
    # 计算每个序号的平均差值
    # 格式: {(position, sequence): avg_diff}
    sequence_avg = {}
    for key, diffs in sequence_diffs.items():
        if len(diffs) > 0:
            sequence_avg[key] = sum(diffs) / len(diffs)
    
    # 第2步：取最近2小时的数据（约24条，5分钟一条）
    # results已经是按时间倒序（最新在前）
    recent_data = results[:24] if len(results) >= 24 else results
    
    # 第3步：判断每个数据点的偏向
    bullish_bias_count = 0  # 偏多
    bearish_bias_count = 0  # 偏空
    analyzed_count = 0
    
    for r in recent_data:
        position = r.get('position')
        sequence = r.get('sequence') or r.get('duration')
        diff_abs = r.get('sar_diff_abs')
        
        if not position or sequence is None or diff_abs is None or diff_abs <= 0:
            continue
        
        # 查找该序号的历史平均差值
        key = (position, sequence)
        avg_diff = sequence_avg.get(key)
        
        if avg_diff is None:
            # 该序号没有历史数据，跳过
            continue
        
        analyzed_count += 1
        
        # 判断逻辑
        if position == 'bullish':  # 多头状态
            if diff_abs < avg_diff:
                # 当前多头N的差值 < 历史多头N的平均差值 → 偏多
                bullish_bias_count += 1
            else:
                # 当前多头N的差值 > 历史多头N的平均差值 → 偏空
                bearish_bias_count += 1
        elif position == 'bearish':  # 空头状态
            if diff_abs < avg_diff:
                # 当前空头N的差值 < 历史空头N的平均差值 → 偏空
                bearish_bias_count += 1
            else:
                # 当前空头N的差值 > 历史空头N的平均差值 → 偏多
                bullish_bias_count += 1
    
    # 第4步：计算比例
    total_bias = bullish_bias_count + bearish_bias_count
    
    if total_bias == 0:
        # 全部数据无效，返回简单统计
        bullish_count = sum(1 for r in results if r.get('position') == 'bullish')
        bearish_count = sum(1 for r in results if r.get('position') == 'bearish')
        total = len(results)
        return {
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'bullish_ratio': round(bullish_count / total * 100, 2) if total > 0 else 0,
            'bearish_ratio': round(bearish_count / total * 100, 2) if total > 0 else 0,
            'method': 'simple_count',
            'reason': '最近2小时无有效数据'
        }
    
    bullish_ratio = round((bullish_bias_count / total_bias) * 100, 2)
    bearish_ratio = round((bearish_bias_count / total_bias) * 100, 2)
    
    # 构建调试信息
    sequence_stats_sample = {}
    for key, avg in list(sequence_avg.items())[:5]:  # 只返回前5个样本
        pos, seq = key
        pos_cn = '多头' if pos == 'bullish' else '空头'
        sequence_stats_sample[f"{pos_cn}{seq:02d}"] = round(avg, 6)
    
    return {
        'bullish_count': bullish_bias_count,
        'bearish_count': bearish_bias_count,
        'bullish_ratio': bullish_ratio,
        'bearish_ratio': bearish_ratio,
        'total_analyzed': total_bias,
        'total_sequences': len(sequence_avg),
        'method': 'sar_diff_by_sequence',
        'time_range': '最近2小时',
        'baseline': f'{len(results)}条历史数据，{len(sequence_avg)}个序号',
        'sequence_stats_sample': sequence_stats_sample
    }



def get_sar_sequence_statistics(hours=24):
    """
    获取所有币种的序号统计数据
    
    计算逻辑：
    1. 对每个币种，读取最近N小时的数据
    2. 识别所有完整周期及其序号
    3. 计算每个序号的SAR差值（SAR - 价格）
    4. 统计同一序号的平均差值
    
    判断逻辑：
    - 多头序号：差值越大（更正）→ 偏空；差值越小（更负）→ 偏多
    - 空头序号：差值越大（更正）→ 偏多；差值越小（更负）→ 偏空
    
    Args:
        hours: 统计最近N小时的数据（默认24小时）
        
    Returns:
        dict: 包含所有币种的序号统计数据
    """
    try:
        from collections import defaultdict
        import pytz
        
        data_dir = Path('/home/user/webapp/data/sar_jsonl')
        
        if not data_dir.exists():
            return {
                'success': False,
                'message': 'SAR数据目录不存在',
                'data': {}
            }
        
        # 计算时间范围
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        start_time = now - timedelta(hours=hours)
        
        # 存储所有币种的统计结果
        all_symbols_stats = {}
        
        # 遍历所有币种
        for symbol in SYMBOLS:
            symbol_short = symbol.replace('-USDT', '')
            symbol_file = data_dir / f"{symbol_short}.jsonl"
            
            if not symbol_file.exists():
                continue
            
            # 读取数据
            records = []
            try:
                with open(symbol_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 读取最近的数据（估算：5分钟一条，24小时约288条）
                    for line in lines[-(hours * 15):]:  # 多读一些确保覆盖
                        if line.strip():
                            try:
                                data = json.loads(line)
                                # 解析时间
                                beijing_time_str = data.get('beijing_time', '')
                                if beijing_time_str:
                                    data_time = datetime.strptime(beijing_time_str, '%Y-%m-%d %H:%M:%S')
                                    data_time = tz.localize(data_time)
                                    
                                    # 只保留时间范围内的数据
                                    if data_time >= start_time:
                                        records.append(data)
                            except (json.JSONDecodeError, ValueError):
                                continue
            except Exception as e:
                print(f"[SAR Stats] 读取{symbol_short}失败: {e}")
                continue
            
            if len(records) < 2:
                continue
            
            # 识别所有完整周期并分配序号
            # 格式：{(position, sequence): [差值列表]}
            sequence_diffs = defaultdict(list)
            
            # 扫描records，识别周期和序号
            current_cycle = []
            last_position = None
            
            for record in records:
                position = record.get('position')
                close = record.get('close', 0)
                sar = record.get('sar', 0)
                
                if close == 0 or sar == 0:
                    continue
                
                # 计算差值（SAR - 价格）
                diff = sar - close
                
                if last_position is None or position == last_position:
                    # 同一周期，序号递增
                    current_cycle.append({
                        'position': position,
                        'diff': diff,
                        'close': close,
                        'sar': sar,
                        'time': record.get('beijing_time', '')
                    })
                else:
                    # 转换点，保存上一个周期的数据
                    if current_cycle:
                        pos_cn = '多头' if last_position == 'bullish' else '空头'
                        for idx, item in enumerate(current_cycle, 1):
                            key = (pos_cn, idx)
                            sequence_diffs[key].append(item['diff'])
                    
                    # 开始新周期
                    current_cycle = [{
                        'position': position,
                        'diff': diff,
                        'close': close,
                        'sar': sar,
                        'time': record.get('beijing_time', '')
                    }]
                
                last_position = position
            
            # 保存最后一个周期（当前周期）
            if current_cycle and last_position:
                pos_cn = '多头' if last_position == 'bullish' else '空头'
                for idx, item in enumerate(current_cycle, 1):
                    key = (pos_cn, idx)
                    sequence_diffs[key].append(item['diff'])
            
            # 计算每个序号的平均差值
            symbol_stats = {
                '多头': {},
                '空头': {}
            }
            
            for (pos_cn, seq_num), diffs in sequence_diffs.items():
                if len(diffs) > 0:
                    avg_diff = sum(diffs) / len(diffs)
                    
                    # 判断偏向
                    if pos_cn == '多头':
                        # 多头：差值越大→偏空；差值越小→偏多
                        if avg_diff > 0.001:
                            bias = '偏空'
                        elif avg_diff < -0.001:
                            bias = '偏多'
                        else:
                            bias = '中性'
                    else:  # 空头
                        # 空头：差值越大→偏多；差值越小→偏空
                        if avg_diff > 0.001:
                            bias = '偏多'
                        elif avg_diff < -0.001:
                            bias = '偏空'
                        else:
                            bias = '中性'
                    
                    symbol_stats[pos_cn][seq_num] = {
                        'avg_diff': round(avg_diff, 6),
                        'count': len(diffs),
                        'bias': bias,
                        'min_diff': round(min(diffs), 6),
                        'max_diff': round(max(diffs), 6)
                    }
            
            all_symbols_stats[symbol_short] = symbol_stats
        
        return {
            'success': True,
            'data': all_symbols_stats,
            'hours': hours,
            'symbol_count': len(all_symbols_stats),
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def get_sar_bias_ratio_2h():
    """
    获取最近2小时的多空占比（基于1天序号统计）
    
    计算逻辑：
    1. 先获取1天的序号统计（每个序号的偏向）
    2. 读取最近2小时的所有数据点
    3. 对每个数据点，查找其序号在1天统计中的偏向
    4. 统计偏多和偏空的数量
    5. 计算比例
    
    Returns:
        dict: 包含所有币种的2小时多空占比数据
    """
    try:
        from collections import defaultdict
        import pytz
        
        data_dir = Path('/home/user/webapp/data/sar_jsonl')
        
        if not data_dir.exists():
            return {
                'success': False,
                'message': 'SAR数据目录不存在',
                'data': {}
            }
        
        # 计算时间范围
        tz = pytz.timezone('Asia/Shanghai')
        now = datetime.now(tz)
        start_time_2h = now - timedelta(hours=2)
        
        # 第1步：获取1天的序号统计（作为基准）
        stats_24h = get_sar_sequence_statistics(hours=24)
        
        if not stats_24h.get('success'):
            return {
                'success': False,
                'message': '获取1天统计数据失败',
                'error': stats_24h.get('error', 'Unknown error')
            }
        
        baseline_stats = stats_24h.get('data', {})
        
        # 存储所有币种的2小时占比结果
        all_symbols_ratio = {}
        
        # 遍历所有币种
        for symbol in SYMBOLS:
            symbol_short = symbol.replace('-USDT', '')
            symbol_file = data_dir / f"{symbol_short}.jsonl"
            
            if not symbol_file.exists():
                continue
            
            # 获取该币种的1天统计数据（基准）
            baseline = baseline_stats.get(symbol_short, {})
            if not baseline:
                continue
            
            # 读取最近2小时的数据
            records_2h = []
            try:
                with open(symbol_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 读取最近的数据（2小时约24条，读30条确保覆盖）
                    for line in lines[-30:]:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                # 解析时间
                                beijing_time_str = data.get('beijing_time', '')
                                if beijing_time_str:
                                    data_time = datetime.strptime(beijing_time_str, '%Y-%m-%d %H:%M:%S')
                                    data_time = tz.localize(data_time)
                                    
                                    # 只保留最近2小时的数据
                                    if data_time >= start_time_2h:
                                        records_2h.append(data)
                            except (json.JSONDecodeError, ValueError):
                                continue
            except Exception as e:
                print(f"[2H Bias] 读取{symbol_short}失败: {e}")
                continue
            
            if len(records_2h) < 2:
                continue
            
            # 第2步：识别每个数据点的序号
            # 需要扫描更多历史数据来识别周期和序号
            all_records = []
            try:
                with open(symbol_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # 读取最近100条（确保能识别完整周期）
                    for line in lines[-100:]:
                        if line.strip():
                            try:
                                data = json.loads(line)
                                all_records.append(data)
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                print(f"[2H Bias] 读取{symbol_short}历史数据失败: {e}")
                continue
            
            if not all_records:
                continue
            
            # 第3步：为每个数据点分配序号
            # 格式：{beijing_time: (position_cn, sequence)}
            point_sequences = {}
            
            current_cycle = []
            last_position = None
            
            for record in all_records:
                position = record.get('position')
                beijing_time = record.get('beijing_time', '')
                
                if not position or not beijing_time:
                    continue
                
                if last_position is None or position == last_position:
                    # 同一周期
                    current_cycle.append(record)
                else:
                    # 转换点，保存上一个周期的序号
                    if current_cycle:
                        pos_cn = '多头' if last_position == 'bullish' else '空头'
                        for idx, item in enumerate(current_cycle, 1):
                            item_time = item.get('beijing_time', '')
                            if item_time:
                                point_sequences[item_time] = (pos_cn, idx)
                    
                    # 开始新周期
                    current_cycle = [record]
                
                last_position = position
            
            # 保存最后一个周期（当前周期）
            if current_cycle and last_position:
                pos_cn = '多头' if last_position == 'bullish' else '空头'
                for idx, item in enumerate(current_cycle, 1):
                    item_time = item.get('beijing_time', '')
                    if item_time:
                        point_sequences[item_time] = (pos_cn, idx)
            
            # 第4步：统计最近2小时内的偏向
            bullish_bias_count = 0  # 偏多的数据点数量
            bearish_bias_count = 0  # 偏空的数据点数量
            neutral_count = 0       # 中性的数据点数量
            unknown_count = 0       # 未找到统计数据的点
            
            for record in records_2h:
                beijing_time = record.get('beijing_time', '')
                
                if beijing_time not in point_sequences:
                    unknown_count += 1
                    continue
                
                pos_cn, seq_num = point_sequences[beijing_time]
                
                # 查找该序号在1天统计中的偏向
                pos_stats = baseline.get(pos_cn, {})
                seq_stat = pos_stats.get(seq_num, {})
                bias = seq_stat.get('bias', '未知')
                
                if bias == '偏多':
                    bullish_bias_count += 1
                elif bias == '偏空':
                    bearish_bias_count += 1
                elif bias == '中性':
                    neutral_count += 1
                else:
                    unknown_count += 1
            
            # 计算比例
            total_valid = bullish_bias_count + bearish_bias_count + neutral_count
            
            if total_valid > 0:
                bullish_ratio = round((bullish_bias_count / total_valid) * 100, 2)
                bearish_ratio = round((bearish_bias_count / total_valid) * 100, 2)
                neutral_ratio = round((neutral_count / total_valid) * 100, 2)
                
                all_symbols_ratio[symbol_short] = {
                    'bullish_bias_count': bullish_bias_count,
                    'bearish_bias_count': bearish_bias_count,
                    'neutral_count': neutral_count,
                    'unknown_count': unknown_count,
                    'total_points': len(records_2h),
                    'valid_points': total_valid,
                    'bullish_ratio': bullish_ratio,
                    'bearish_ratio': bearish_ratio,
                    'neutral_ratio': neutral_ratio,
                    'dominant_bias': '偏多' if bullish_ratio > bearish_ratio else '偏空' if bearish_ratio > bullish_ratio else '中性'
                }
        
        return {
            'success': True,
            'data': all_symbols_ratio,
            'time_range': '最近2小时',
            'baseline': '1天序号统计',
            'symbol_count': len(all_symbols_ratio),
            'timestamp': now.strftime('%Y-%m-%d %H:%M:%S')
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }

