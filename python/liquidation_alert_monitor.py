#!/usr/bin/env python3
"""
爆仓预警监控器
Liquidation Alert Monitor
"""
import time
import logging
import sys
import os

# 添加项目路径到Python搜索路径
sys.path.insert(0, '/home/user/webapp')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """主监控循环"""
    logger.info("爆仓预警监控器启动...")
    
    while True:
        try:
            # 监控逻辑
            logger.info("监控爆仓预警中...")
            
            # 每60秒检查一次
            time.sleep(60)
            
        except KeyboardInterrupt:
            logger.info("接收到退出信号，正在关闭...")
            break
        except Exception as e:
            logger.error(f"监控出错: {e}", exc_info=True)
            time.sleep(10)

if __name__ == "__main__":
    main()
