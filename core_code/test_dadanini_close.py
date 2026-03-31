#!/usr/bin/env python3
"""
DADANINI账户平仓诊断脚本
"""
import requests
import hmac
import base64
import json
from datetime import datetime, timezone

# DADANINI账户凭证
API_KEY = "1463198a-fad0-46ac-9ad8-2a386461782c"
API_SECRET = "1D112283B7456290056C253C56E9F3A6"
PASSPHRASE = "Tencent@123"

BASE_URL = 'https://www.okx.com'

def sign_request(timestamp, method, request_path, body=''):
    """生成OKX API签名"""
    message = timestamp + method + request_path + body
    mac = hmac.new(
        bytes(API_SECRET, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    return base64.b64encode(mac.digest()).decode()

def get_account_config():
    """获取账户配置"""
    print("\n=== 1. 检查账户配置 ===")
    request_path = '/api/v5/account/config'
    timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    signature = sign_request(timestamp, 'GET', request_path)
    
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
    }
    
    try:
        response = requests.get(BASE_URL + request_path, headers=headers, timeout=10)
        result = response.json()
        print(f"响应码: {result.get('code')}")
        
        if result.get('code') == '0' and result.get('data'):
            config = result['data'][0]
            print(f"✅ 账户ID: {config.get('uid')}")
            print(f"✅ 持仓模式: {config.get('posMode')} (long_short_mode=双向, net_mode=单向)")
            print(f"✅ 账户层级: {config.get('acctLv')} (1=简单, 2=单币种, 3=跨币种, 4=组合保证金)")
            print(f"✅ 自动借币: {config.get('autoLoan')}")
            return config
        else:
            print(f"❌ 获取失败: {result.get('msg')}")
            return None
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return None

def get_positions():
    """获取当前持仓"""
    print("\n=== 2. 检查当前持仓 ===")
    request_path = '/api/v5/account/positions'
    timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    signature = sign_request(timestamp, 'GET', request_path)
    
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
    }
    
    try:
        response = requests.get(BASE_URL + request_path, headers=headers, timeout=10)
        result = response.json()
        print(f"响应码: {result.get('code')}")
        
        if result.get('code') == '0':
            positions = result.get('data', [])
            print(f"✅ 总持仓数: {len(positions)}")
            
            active_positions = []
            for pos in positions:
                pos_value = float(pos.get('pos', 0))
                if abs(pos_value) > 0:  # 有持仓
                    active_positions.append(pos)
                    print(f"\n  📊 {pos.get('instId')}")
                    print(f"     持仓方向: {pos.get('posSide')}")
                    print(f"     持仓数量: {pos.get('pos')}")
                    print(f"     开仓均价: {pos.get('avgPx')}")
                    print(f"     保证金模式: {pos.get('mgnMode')}")
                    print(f"     杠杆倍数: {pos.get('lever')}")
                    print(f"     未实现盈亏: {pos.get('upl')} USDT")
                    print(f"     盈亏率: {float(pos.get('uplRatio', 0))*100:.2f}%")
            
            if len(active_positions) == 0:
                print("  ℹ️  当前无持仓")
            
            return active_positions
        else:
            print(f"❌ 获取失败: {result.get('msg')}")
            return []
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return []

def test_close_position(inst_id, pos_side, pos_mode):
    """测试平仓（不实际执行）"""
    print(f"\n=== 3. 测试平仓参数 ===")
    print(f"交易对: {inst_id}")
    print(f"持仓方向: {pos_side}")
    print(f"持仓模式: {pos_mode}")
    
    # 根据持仓模式构造平仓参数
    order_params = {
        'instId': inst_id,
        'mgnMode': 'isolated'
    }
    
    if pos_mode == 'long_short_mode':
        order_params['posSide'] = pos_side
        print("✅ 双向持仓模式 - 需要指定posSide")
    else:
        print("✅ 单向持仓模式 - 不需要指定posSide")
    
    print(f"\n平仓请求参数: {json.dumps(order_params, indent=2)}")
    
    # 检查是否有明显的参数问题
    if not inst_id:
        print("❌ 错误: instId不能为空")
        return False
    
    if not pos_side or pos_side not in ['long', 'short', 'net']:
        print("❌ 错误: posSide无效")
        return False
    
    print("✅ 参数检查通过")
    return True

def check_trading_permission():
    """检查交易权限"""
    print("\n=== 4. 检查交易权限 ===")
    
    # 尝试获取账户余额（需要交易权限）
    request_path = '/api/v5/account/balance'
    timestamp = datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00', 'Z')
    signature = sign_request(timestamp, 'GET', request_path)
    
    headers = {
        'OK-ACCESS-KEY': API_KEY,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': PASSPHRASE,
    }
    
    try:
        response = requests.get(BASE_URL + request_path, headers=headers, timeout=10)
        result = response.json()
        print(f"响应码: {result.get('code')}")
        
        if result.get('code') == '0':
            print("✅ API有余额查询权限")
            return True
        elif result.get('code') == '50111':
            print("❌ API权限不足 (code: 50111)")
            print("   请检查API Key是否有交易权限")
            return False
        else:
            print(f"❌ 权限检查失败: {result.get('msg')}")
            return False
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

def main():
    print("=" * 60)
    print("DADANINI账户平仓诊断工具")
    print("=" * 60)
    
    # 1. 检查账户配置
    config = get_account_config()
    if not config:
        print("\n⚠️  无法获取账户配置，请检查API凭证")
        return
    
    pos_mode = config.get('posMode', 'long_short_mode')
    
    # 2. 检查持仓
    positions = get_positions()
    
    # 3. 如果有持仓，测试平仓参数
    if positions:
        first_pos = positions[0]
        test_close_position(
            first_pos.get('instId'),
            first_pos.get('posSide'),
            pos_mode
        )
    else:
        print("\n  ℹ️  当前无持仓，无法测试平仓")
    
    # 4. 检查交易权限
    check_trading_permission()
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == '__main__':
    main()
