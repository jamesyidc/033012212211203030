# 加密货币数据分析系统

> 完整的加密货币市场数据采集、分析和可视化平台

## 🚀 快速开始

### 系统访问

**Web应用地址**: https://9002-izdl7i89gq7ib3tbi6fq1-82b888ba.sandbox.novita.ai

### 快速状态检查

```bash
cd /home/user/webapp
./check_system_status.sh
```

## 📊 系统状态

- ✅ **18个服务** 全部运行中
- ✅ **Flask Web应用** 正常运行 (端口9002)
- ✅ **数据采集系统** 实时采集中
- ✅ **PM2进程管理** 自动重启保护

## 💻 常用命令

### 查看服务状态
```bash
pm2 list                 # 查看所有服务
pm2 logs flask-app       # 查看Flask日志
pm2 monit                # 实时资源监控
```

### 管理服务
```bash
pm2 restart all          # 重启所有服务
pm2 restart flask-app    # 重启单个服务
pm2 stop all             # 停止所有服务
pm2 save                 # 保存当前配置
```

## 📁 主要目录

```
/home/user/webapp/
├── core_code/           # Flask应用核心代码
├── source_code/         # 数据采集脚本
├── templates/           # Web界面模板 (138个)
├── data/                # 数据存储目录
└── logs/                # 运行日志
```

## 🎯 核心功能

### 数据采集 (14个采集器)
- 交易信号采集
- 币种变化追踪  
- 市场情绪分析
- SAR指标采集
- 恐慌指数数据
- 爆仓数据统计
- 价格速度监控

### Web界面 (138个页面)
- 控制中心
- 币种追踪面板
- 价格位置分析
- SAR趋势图表
- 恐慌指数监控
- OKX交易管理

### 系统监控 (2个监控器)
- 数据健康监控
- 系统健康监控

## 📖 详细文档

- [完整部署报告](DEPLOYMENT_COMPLETE.md) - 详细的部署状态和说明
- [部署指南](DEPLOYMENT_GUIDE.md) - 原始部署文档
- [部署状态](DEPLOYMENT_STATUS.md) - 系统状态概览

## 🔧 技术栈

- **Python**: 3.12.11
- **Flask**: 3.0.0
- **PM2**: 6.0.14
- **数据格式**: JSONL (时序数据)

## 📈 系统架构

```
                    ┌─────────────────┐
                    │   Flask Web     │
                    │  Application    │
                    │   (Port 9002)   │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────▼────┐         ┌───▼────┐        ┌────▼────┐
    │  Data   │         │ System │        │  Web    │
    │Collectors│        │Monitors│        │Interface│
    │ (14个)  │         │ (2个)  │        │(138个)  │
    └────┬────┘         └────────┘        └─────────┘
         │
    ┌────▼────┐
    │  Data   │
    │ Storage │
    │ (JSONL) │
    └─────────┘
```

## ⚠️ 注意事项

1. **数据目录**: 所有JSONL数据保存在 `/home/user/webapp/data/`
2. **日志文件**: PM2日志在 `/home/user/webapp/logs/`
3. **端口**: Flask应用运行在9002端口
4. **重启**: PM2配置自动重启,服务异常会自动恢复

## 🔄 导入数据

导入历史JSONL数据:

```bash
# 复制数据文件到对应目录
cp your_data.jsonl /home/user/webapp/data/[target_directory]/

# 重启相关服务
pm2 restart [service-name]
```

## 📞 支持

运行状态检查脚本查看详细状态:
```bash
./check_system_status.sh
```

查看服务日志排查问题:
```bash
pm2 logs [service-name] --lines 50
```

---

**部署时间**: 2026-03-15 17:09 UTC  
**状态**: ✅ 运行正常  
**版本**: v1.0
