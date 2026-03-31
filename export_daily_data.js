#!/usr/bin/env node
/**
 * 数据导出脚本
 * 从旧系统导出当天的所有JSONL数据
 * 
 * 使用方法:
 * node scripts/export_daily_data.js <source_url> [output_file]
 * 
 * 示例:
 * node scripts/export_daily_data.js https://9002-it9wfu5ka4bz8qx2ukowr-b32ec7bb.sandbox.novita.ai
 * node scripts/export_daily_data.js https://9002-it9wfu5ka4bz8qx2ukowr-b32ec7bb.sandbox.novita.ai backup.json
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');
const url = require('url');

// 命令行参数
const args = process.argv.slice(2);
if (args.length < 1) {
    console.error('❌ 缺少源URL参数');
    console.log('使用方法: node scripts/export_daily_data.js <source_url> [output_file]');
    console.log('示例: node scripts/export_daily_data.js https://9002-it9wfu5ka4bz8qx2ukowr-b32ec7bb.sandbox.novita.ai');
    process.exit(1);
}

const sourceUrl = args[0];
const outputFile = args[1] || `data_export_${new Date().toISOString().split('T')[0].replace(/-/g, '')}.json`;

// 确保输出目录存在
const outputDir = path.dirname(outputFile);
if (outputDir && outputDir !== '.' && !fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
}

console.log('🚀 开始导出数据...');
console.log(`📍 源系统: ${sourceUrl}`);
console.log(`💾 输出文件: ${outputFile}`);

// 构建API URL
const apiUrl = `${sourceUrl.replace(/\/$/, '')}/api/data-sync/export`;

console.log(`🔗 API地址: ${apiUrl}`);

// 解析URL
const parsedUrl = url.parse(apiUrl);
const isHttps = parsedUrl.protocol === 'https:';
const httpModule = isHttps ? https : http;

// 发起HTTP请求
const request = httpModule.get(apiUrl, (response) => {
    let data = '';
    
    console.log(`📥 响应状态码: ${response.statusCode}`);
    
    if (response.statusCode !== 200) {
        console.error(`❌ 请求失败，状态码: ${response.statusCode}`);
        process.exit(1);
    }
    
    // 接收数据
    response.on('data', (chunk) => {
        data += chunk;
        process.stdout.write('.');
    });
    
    // 数据接收完成
    response.on('end', () => {
        console.log('\n✅ 数据接收完成');
        
        try {
            const jsonData = JSON.parse(data);
            
            if (!jsonData.success) {
                console.error('❌ 导出失败:', jsonData.error || '未知错误');
                process.exit(1);
            }
            
            // 保存到文件
            fs.writeFileSync(outputFile, JSON.stringify(jsonData, null, 2), 'utf8');
            
            console.log('\n📊 导出统计:');
            console.log(`  日期: ${jsonData.date}`);
            console.log(`  时间: ${jsonData.datetime_readable}`);
            console.log(`  文件数量: ${jsonData.total_files}`);
            console.log(`  总大小: ${jsonData.total_size_mb} MB`);
            console.log('\n📁 导出的文件列表:');
            
            jsonData.files.forEach((file, index) => {
                console.log(`  ${index + 1}. ${file.path} (${(file.size / 1024).toFixed(2)} KB, ${file.line_count} 行)`);
            });
            
            console.log(`\n✅ 数据已成功导出到: ${outputFile}`);
            console.log(`💡 下一步: 使用 import_daily_data.js 脚本导入到新系统`);
            
        } catch (error) {
            console.error('❌ 解析JSON失败:', error.message);
            console.error('原始响应:', data.substring(0, 500));
            process.exit(1);
        }
    });
});

request.on('error', (error) => {
    console.error('❌ 请求失败:', error.message);
    process.exit(1);
});

request.setTimeout(60000, () => {
    console.error('❌ 请求超时（60秒）');
    request.destroy();
    process.exit(1);
});
