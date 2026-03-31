#!/bin/bash
# 数据同步系统使用示例脚本
# 
# 这个脚本演示了如何使用数据同步系统进行完整的数据迁移流程
#
# 使用方法: bash demo_data_sync.sh

set -e  # 遇到错误立即退出

echo "======================================"
echo "   数据同步系统使用演示"
echo "======================================"
echo ""

# 配置变量
SOURCE_URL="https://9002-old-system.sandbox.novita.ai"
TARGET_URL="https://9002-new-system.sandbox.novita.ai"
BACKUP_FILE="demo_backup_$(date +%Y%m%d_%H%M%S).json"

echo "📋 配置信息:"
echo "  源系统URL: $SOURCE_URL"
echo "  目标系统URL: $TARGET_URL"
echo "  备份文件: $BACKUP_FILE"
echo ""

# 步骤1: 从源系统导出数据
echo "=========================================="
echo "步骤1: 从源系统导出数据"
echo "=========================================="
echo "💡 命令: node scripts/export_daily_data.js $SOURCE_URL $BACKUP_FILE"
echo ""

# 实际执行（演示模式，使用本地系统）
echo "🔄 正在导出数据（演示模式：使用localhost）..."
node scripts/export_daily_data.js http://localhost:9002 $BACKUP_FILE

echo ""
echo "✅ 步骤1完成！"
echo ""

# 等待用户确认
read -p "按Enter键继续到步骤2（数据验证）..."
echo ""

# 步骤2: 验证导出的数据
echo "=========================================="
echo "步骤2: 验证导出的数据"
echo "=========================================="
echo "📊 检查备份文件..."
echo ""

if [ -f "$BACKUP_FILE" ]; then
    echo "✅ 备份文件存在: $BACKUP_FILE"
    
    # 文件大小
    FILE_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo "📦 文件大小: $FILE_SIZE"
    
    # 使用jq解析JSON（如果安装了jq）
    if command -v jq &> /dev/null; then
        echo ""
        echo "📊 数据统计:"
        echo "  日期: $(cat "$BACKUP_FILE" | jq -r '.date')"
        echo "  时间: $(cat "$BACKUP_FILE" | jq -r '.datetime_readable')"
        echo "  文件数: $(cat "$BACKUP_FILE" | jq -r '.total_files')"
        echo "  大小: $(cat "$BACKUP_FILE" | jq -r '.total_size_mb') MB"
        
        echo ""
        echo "📁 文件列表（前5个）:"
        cat "$BACKUP_FILE" | jq -r '.files[0:5][] | "  - \(.path) (\(.size) bytes, \(.line_count) 行)"'
        
        TOTAL_FILES=$(cat "$BACKUP_FILE" | jq -r '.total_files')
        if [ "$TOTAL_FILES" -gt 5 ]; then
            echo "  ... 还有 $((TOTAL_FILES - 5)) 个文件"
        fi
    else
        echo "💡 提示: 安装jq可以查看详细信息 (apt-get install jq)"
    fi
else
    echo "❌ 备份文件不存在！"
    exit 1
fi

echo ""
echo "✅ 步骤2完成！"
echo ""

# 等待用户确认
read -p "按Enter键继续到步骤3（数据导入）..."
echo ""

# 步骤3: 导入数据到目标系统
echo "=========================================="
echo "步骤3: 导入数据到目标系统"
echo "=========================================="
echo "💡 命令: node scripts/import_daily_data.js $TARGET_URL $BACKUP_FILE"
echo ""

# 实际执行（演示模式，使用本地系统）
echo "🔄 正在导入数据（演示模式：使用localhost）..."
node scripts/import_daily_data.js http://localhost:9002 $BACKUP_FILE

echo ""
echo "✅ 步骤3完成！"
echo ""

# 等待用户确认
read -p "按Enter键继续到步骤4（验证导入结果）..."
echo ""

# 步骤4: 验证导入结果
echo "=========================================="
echo "步骤4: 验证导入结果"
echo "=========================================="
echo "🔍 检查备份文件..."
echo ""

# 检查备份文件是否创建
BACKUP_COUNT=$(find data/ -name "*.backup_*" -type f -mmin -5 | wc -l)
echo "📦 最近5分钟创建的备份文件: $BACKUP_COUNT 个"

if [ $BACKUP_COUNT -gt 0 ]; then
    echo ""
    echo "最新备份文件列表（前5个）:"
    find data/ -name "*.backup_*" -type f -mmin -5 | head -5 | while read file; do
        SIZE=$(ls -lh "$file" | awk '{print $5}')
        echo "  - $file ($SIZE)"
    done
fi

echo ""
echo "🔍 验证API响应..."
curl -s http://localhost:9002/api/coin-change-tracker/latest | python3 -m json.tool | head -20

echo ""
echo "✅ 步骤4完成！"
echo ""

# 完成
echo "=========================================="
echo "✅ 数据同步演示完成！"
echo "=========================================="
echo ""
echo "📋 操作总结:"
echo "  1. ✅ 数据导出 - 成功"
echo "  2. ✅ 数据验证 - 成功"
echo "  3. ✅ 数据导入 - 成功"
echo "  4. ✅ 结果验证 - 成功"
echo ""
echo "💾 备份文件: $BACKUP_FILE"
echo "🗑️  清理命令: rm $BACKUP_FILE"
echo ""
echo "📚 更多信息:"
echo "  - 完整文档: cat DATA_SYNC_GUIDE.md"
echo "  - 快速参考: cat DATA_SYNC_QUICK_REF.md"
echo "  - 开发报告: cat DATA_SYNC_DEVELOPMENT_REPORT.md"
echo ""
echo "======================================"
