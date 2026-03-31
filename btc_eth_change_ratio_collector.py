#!/usr/bin/env python3
"""
BTC vs ETH 涨跌幅比例采集器
功能：
1. 从 coin_change_tracker API 实时采集BTC和ETH的涨跌幅
2. 记录BTC涨跌幅 > ETH涨跌幅的次数和比例
3. 按北京时间每天0点重新计算
4. 数据按日期存储为JSONL格式

数据来源：
- 从 http://localhost:9002/api/coin-change-tracker/latest 获取BTC和ETH涨跌幅
- 使用主页面左上角卡片显示的相同数据

数据格式：
{
    "timestamp": "2026-03-21 10:30:45",
    "beijing_date": "20260321",
    "btc_change": 1.25,  // BTC涨跌幅 (%)
    "eth_change": 0.85,  // ETH涨跌幅 (%)
    "btc_price": 70000.0,  // BTC当前价格
    "eth_price": 2100.0,   // ETH当前价格
    "btc_greater": true,  // BTC涨跌幅是否大于ETH
    "today_stats": {
        "total_count": 630,  // 今日总采集次数
        "btc_greater_count": 380,  // BTC > ETH的次数
        "ratio": 60.32  // BTC > ETH的比例 (%)
    }
}
"""

import json
import time
import logging
import requests
from datetime import datetime
from pathlib import Path
from pytz import timezone

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/btc_eth_change_ratio.log'),
        logging.StreamHandler()
    ]
)

class BTCETHChangeRatioCollector:
    """BTC vs ETH 涨跌幅比例采集器"""
    
    def __init__(self, data_dir='data/btc_eth_change_ratio', api_url='http://localhost:9002'):
        """初始化采集器"""
        self.api_url = api_url
        self.api_endpoint = f"{api_url}/api/coin-change-tracker/latest"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 当日统计
        self.current_date = None
        self.total_count = 0
        self.btc_greater_count = 0
        
        logging.info("✅ BTC vs ETH 涨跌幅比例采集器初始化完成")
        logging.info(f"📡 数据来源: {self.api_endpoint}")
    
    def get_beijing_time(self):
        """获取北京时间"""
        beijing_tz = timezone('Asia/Shanghai')
        return datetime.now(beijing_tz)
    
    def get_beijing_date_str(self):
        """获取北京日期字符串 (YYYYMMDD)"""
        return self.get_beijing_time().strftime('%Y%m%d')
    
    def get_data_file_path(self, date_str=None):
        """获取数据文件路径"""
        if date_str is None:
            date_str = self.get_beijing_date_str()
        return self.data_dir / f"btc_eth_ratio_{date_str}.jsonl"
    
    def get_btc_eth_data_from_api(self):
        """从 coin_change_tracker API 获取BTC和ETH数据"""
        try:
            response = requests.get(self.api_endpoint, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            if not result.get('success'):
                logging.error(f"❌ API返回失败: {result.get('error', '未知错误')}")
                return None
            
            data = result.get('data', {})
            changes = data.get('changes', {})
            
            # 提取BTC数据
            btc_data = changes.get('BTC')
            eth_data = changes.get('ETH')
            
            if not btc_data or not eth_data:
                logging.error(f"❌ 未找到BTC或ETH数据")
                return None
            
            return {
                'btc_change': btc_data.get('change_pct', 0),
                'eth_change': eth_data.get('change_pct', 0),
                'btc_price': btc_data.get('current_price', 0),
                'eth_price': eth_data.get('current_price', 0),
                'timestamp': data.get('beijing_time')
            }
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ API请求失败: {e}")
            return None
        except Exception as e:
            logging.error(f"❌ 解析API数据失败: {e}")
            return None
    
    def check_and_reset_daily(self):
        """检查日期变化，必要时重置统计"""
        current_date = self.get_beijing_date_str()
        
        if self.current_date != current_date:
            if self.current_date is not None:
                logging.info(
                    f"📅 日期变更: {self.current_date} → {current_date}, "
                    f"昨日统计: 总次数={self.total_count}, "
                    f"BTC>ETH={self.btc_greater_count}, "
                    f"比例={self.btc_greater_count/self.total_count*100:.2f}%" if self.total_count > 0 else "比例=0%"
                )
            
            # 重置统计
            self.current_date = current_date
            self.total_count = 0
            self.btc_greater_count = 0
            
            logging.info(f"🔄 新的一天开始: {current_date}")
            
            return True
        
        return False
    
    def load_today_stats(self):
        """从文件加载今日统计数据"""
        file_path = self.get_data_file_path()
        
        if not file_path.exists():
            logging.info(f"📄 今日数据文件不存在，将创建新文件: {file_path}")
            return
        
        try:
            total = 0
            greater = 0
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        total += 1
                        if data.get('btc_greater', False):
                            greater += 1
            
            self.total_count = total
            self.btc_greater_count = greater
            
            logging.info(
                f"📊 加载今日统计: 总次数={total}, "
                f"BTC>ETH={greater}, "
                f"比例={greater/total*100:.2f}%" if total > 0 else "比例=0%"
            )
            
        except Exception as e:
            logging.error(f"❌ 加载今日统计失败: {e}")
    
    def collect_data(self):
        """采集一次数据"""
        try:
            # 检查日期变化
            date_changed = self.check_and_reset_daily()
            
            # 如果是新的一天，加载已有统计
            if date_changed:
                self.load_today_stats()
            
            # 从API获取BTC和ETH数据
            api_data = self.get_btc_eth_data_from_api()
            
            if api_data is None:
                logging.warning("⚠️ 从API获取数据失败，跳过本次采集")
                return
            
            # 提取数据
            btc_change = api_data['btc_change']
            eth_change = api_data['eth_change']
            btc_price = api_data['btc_price']
            eth_price = api_data['eth_price']
            
            # 判断BTC是否大于ETH
            btc_greater = btc_change > eth_change
            
            # 更新统计
            self.total_count += 1
            if btc_greater:
                self.btc_greater_count += 1
            
            # 计算比例
            ratio = (self.btc_greater_count / self.total_count * 100) if self.total_count > 0 else 0.0
            
            # 准备数据
            beijing_time = self.get_beijing_time()
            data = {
                'timestamp': beijing_time.strftime('%Y-%m-%d %H:%M:%S'),
                'beijing_date': self.current_date,
                'btc_price': round(btc_price, 2),
                'eth_price': round(eth_price, 2),
                'btc_change': round(btc_change, 2),
                'eth_change': round(eth_change, 2),
                'btc_greater': btc_greater,
                'today_stats': {
                    'total_count': self.total_count,
                    'btc_greater_count': self.btc_greater_count,
                    'ratio': round(ratio, 2)
                }
            }
            
            # 写入文件
            file_path = self.get_data_file_path()
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(data, ensure_ascii=False) + '\n')
            
            # 日志输出
            symbol = "📈" if btc_greater else "📉"
            logging.info(
                f"{symbol} BTC={btc_change:+.2f}% vs ETH={eth_change:+.2f}% | "
                f"今日: BTC>ETH {self.btc_greater_count}/{self.total_count} ({ratio:.2f}%)"
            )
            
        except Exception as e:
            logging.error(f"❌ 采集数据失败: {e}", exc_info=True)
    
    def run(self, interval=60):
        """运行采集器
        
        Args:
            interval: 采集间隔（秒），默认60秒
        """
        logging.info(f"🚀 开始运行 BTC vs ETH 涨跌幅比例采集器 (间隔={interval}秒)")
        
        while True:
            try:
                self.collect_data()
                time.sleep(interval)
            except KeyboardInterrupt:
                logging.info("⏹️ 收到停止信号，正在退出...")
                break
            except Exception as e:
                logging.error(f"❌ 运行出错: {e}", exc_info=True)
                time.sleep(interval)

if __name__ == '__main__':
    collector = BTCETHChangeRatioCollector()
    collector.run(interval=60)  # 每60秒采集一次
