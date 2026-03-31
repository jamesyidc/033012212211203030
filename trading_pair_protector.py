#!/usr/bin/env python3
"""
Trading Pair Protector - 交易对保护器
"""
import time
from datetime import datetime

# 全局保护状态
_protected_pairs = {}


def start_protection(symbol, reason='', duration=3600):
    """
    开始保护交易对
    
    Args:
        symbol: 交易对符号
        reason: 保护原因
        duration: 保护时长（秒）
        
    Returns:
        dict: 保护结果
    """
    global _protected_pairs
    _protected_pairs[symbol] = {
        'symbol': symbol,
        'reason': reason,
        'start_time': time.time(),
        'duration': duration,
        'protected': True
    }
    return {
        'success': True,
        'symbol': symbol,
        'message': f'已启动保护: {reason}'
    }


def stop_protection(symbol):
    """
    停止保护交易对
    
    Args:
        symbol: 交易对符号
        
    Returns:
        dict: 停止结果
    """
    global _protected_pairs
    if symbol in _protected_pairs:
        del _protected_pairs[symbol]
        return {
            'success': True,
            'symbol': symbol,
            'message': '已停止保护'
        }
    return {
        'success': False,
        'symbol': symbol,
        'message': '未找到保护记录'
    }


def get_protection_status(symbol=None):
    """
    获取交易对保护状态
    
    Args:
        symbol: 交易对符号（可选，None表示获取所有）
        
    Returns:
        dict or list: 保护状态
    """
    global _protected_pairs
    
    # 清理过期的保护
    current_time = time.time()
    expired_symbols = []
    for sym, info in _protected_pairs.items():
        if current_time - info['start_time'] > info['duration']:
            expired_symbols.append(sym)
    
    for sym in expired_symbols:
        del _protected_pairs[sym]
    
    if symbol is None:
        return list(_protected_pairs.values())
    
    if symbol in _protected_pairs:
        return _protected_pairs[symbol]
    
    return {
        'symbol': symbol,
        'protected': False,
        'reason': '',
        'timestamp': 0
    }


def check_and_protect(symbol, conditions=None):
    """
    检查并保护交易对
    
    Args:
        symbol: 交易对符号
        conditions: 检查条件
        
    Returns:
        dict: 检查结果
    """
    status = get_protection_status(symbol)
    
    if isinstance(status, dict) and status.get('protected'):
        return {
            'allowed': False,
            'symbol': symbol,
            'message': f"交易对已被保护: {status.get('reason', '')}"
        }
    
    return {
        'allowed': True,
        'symbol': symbol,
        'message': '允许交易'
    }


def get_protected_pairs():
    """
    获取所有受保护的交易对
    
    Returns:
        list: 受保护交易对列表
    """
    return get_protection_status()
