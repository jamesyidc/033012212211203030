#!/usr/bin/env python3
"""
Price Comparison JSONL Manager - 比价系统JSONL数据管理器
管理币种价格比较数据的读写
"""
import json
from pathlib import Path
from datetime import datetime
import pytz

BEIJING_TZ = pytz.timezone('Asia/Shanghai')


class PriceComparisonJSONLManager:
    """比价系统JSONL数据管理器"""
    
    def __init__(self, data_dir='/home/user/webapp/data/price_comparison_jsonl'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.stats_file = self.data_dir / 'price_comparison_stats.jsonl'
    
    def get_all_coins(self):
        """获取所有币种的最新数据"""
        coins_data = {}
        
        if not self.stats_file.exists():
            return []
        
        # 读取所有数据
        with open(self.stats_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        symbol = data.get('symbol', '')
                        if symbol:
                            # 保存最新的数据（后面的行覆盖前面的）
                            coins_data[symbol] = data
                    except json.JSONDecodeError:
                        continue
        
        # 转换为列表并按symbol排序
        result = list(coins_data.values())
        result.sort(key=lambda x: x.get('symbol', ''))
        
        return result
    
    def get_coin(self, symbol):
        """获取单个币种的数据"""
        all_coins = self.get_all_coins()
        for coin in all_coins:
            if coin.get('symbol') == symbol:
                return coin
        return None
    
    def update_coin(self, symbol, price_data):
        """更新币种数据
        
        Args:
            symbol: 币种符号 (如 'BTC')
            price_data: 价格数据字典，包含:
                - current_price: 当前价格
                - highest_price: 最高价
                - lowest_price: 最低价
                - highest_count: 最高计次
                - lowest_count: 最低计次
                - last_update: 最后更新时间
        """
        # 读取当前所有数据
        coins_data = {}
        if self.stats_file.exists():
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            sym = data.get('symbol', '')
                            if sym:
                                coins_data[sym] = data
                        except json.JSONDecodeError:
                            continue
        
        # 更新或添加数据
        if symbol not in coins_data:
            coins_data[symbol] = {
                'symbol': symbol,
                'created_at': datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
            }
        
        # 更新价格数据
        coins_data[symbol].update(price_data)
        coins_data[symbol]['last_update'] = datetime.now(BEIJING_TZ).strftime('%Y-%m-%d %H:%M:%S')
        
        # 写回文件
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            for sym in sorted(coins_data.keys()):
                f.write(json.dumps(coins_data[sym], ensure_ascii=False) + '\n')
        
        return coins_data[symbol]
    
    def reset_coin(self, symbol):
        """重置币种数据"""
        coins_data = {}
        if self.stats_file.exists():
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            sym = data.get('symbol', '')
                            if sym and sym != symbol:
                                coins_data[sym] = data
                        except json.JSONDecodeError:
                            continue
        
        # 写回文件（不包含被重置的币种）
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            for sym in sorted(coins_data.keys()):
                f.write(json.dumps(coins_data[sym], ensure_ascii=False) + '\n')
        
        return True
    
    def delete_coin(self, symbol):
        """删除币种数据"""
        return self.reset_coin(symbol)


if __name__ == '__main__':
    # 测试代码
    manager = PriceComparisonJSONLManager()
    
    # 测试获取所有币种
    print("所有币种数据:")
    coins = manager.get_all_coins()
    for coin in coins:
        print(f"  {coin.get('symbol')}: {coin.get('current_price')}")
    
    # 测试更新币种
    print("\n更新BTC数据...")
    manager.update_coin('BTC', {
        'current_price': 50000,
        'highest_price': 52000,
        'lowest_price': 48000,
        'highest_count': 5,
        'lowest_count': 3
    })
    
    # 再次获取
    btc = manager.get_coin('BTC')
    print(f"BTC数据: {btc}")
