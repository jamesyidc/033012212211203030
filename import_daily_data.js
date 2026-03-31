#!/usr/bin/env node
/**
 * 数据导入脚本
 * 将导出的JSONL数据导入到新系统
 * 
 * 使用方法:
 * node scripts/import_daily_data.js <target_url> <data_file>
 * 
 * 示例:
 * node scripts/import_daily_data.js https://9002-imp6ky5dtwten0w001hfy-82b888ba.sandbox.novita.ai data_export_20260224.json
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const url = require('url');

// 命令行参数
const args = process.argv.slice(2);
if (args.length < 2) {
    console.error('❌ 缺少必要参数');
    console.log('使用方法: node scripts/import_daily_data.js <target_url> <data_file>');
    console.log('示例: node scripts/import_daily_data.js https://9002-imp6ky5dtwten0w001hfy-82b888ba.sandbox.novita.ai data_export_20260224.json');
    process.exit(1);
}

const targetUrl = args[0];
const dataFile = args[1];

console.log('🚀 开始导入数据...');
console.log(`📍 目标系统: ${targetUrl}`);
console.log(`📁 数据文件: ${dataFile}`);

// 检查数据文件是否存在
if (!fs.existsSync(dataFile)) {
    console.error(`❌ 数据文件不存在: ${dataFile}`);
    process.exit(1);
}

// 读取数据文件
let exportData;
try {
    const fileContent = fs.readFileSync(dataFile, 'utf8');
    exportData = JSON.parse(fileContent);
    
    if (!exportData.success || !exportData.files) {
        console.error('❌ 无效的数据文件格式');
        process.exit(1);
    }
    
    console.log(`✅ 数据文件已加载`);
    console.log(`  导出日期: ${exportData.date}`);
    console.log(`  文件数量: ${exportData.total_files}`);
    console.log(`  总大小: ${exportData.total_size_mb} MB`);
    
} catch (error) {
    console.error('❌ 读取数据文件失败:', error.message);
    process.exit(1);
}

// 构建API URL
const apiUrl = `${targetUrl.replace(/\/$/, '')}/api/data-sync/import`;

console.log(`\n🔗 API地址: ${apiUrl}`);
console.log('📤 准备发送数据...\n');

// 准备请求数据
const postData = JSON.stringify({
    files: exportData.files
});

// 解析URL
const parsedUrl = url.parse(apiUrl);
const isHttps = parsedUrl.protocol === 'https:';

const options = {
    hostname: parsedUrl.hostname,
    port: parsedUrl.port || (isHttps ? 443 : 80),
    path: parsedUrl.path,
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(postData)
    }
};

// 发起HTTP请求
const httpModule = isHttps ? https : http;
const request = httpModule.request(options, (response) => {
    let data = '';
    
    console.log(`📥 响应状态码: ${response.statusCode}`);
    
    // 接收数据
    response.on('data', (chunk) => {
        data += chunk;
    });
    
    // 数据接收完成
    response.on('end', () => {
        console.log('✅ 响应接收完成\n');
        
        try {
            const jsonData = JSON.parse(data);
            
            if (!jsonData.success) {
                console.error('❌ 导入失败:', jsonData.error || '未知错误');
                if (jsonData.traceback) {
                    console.error('\n错误堆栈:\n', jsonData.traceback);
                }
                process.exit(1);
            }
            
            console.log('📊 导入统计:');
            console.log(`  成功: ${jsonData.imported_count} 个文件`);
            console.log(`  失败: ${jsonData.failed_count} 个文件`);
            console.log(`  总大小: ${jsonData.total_size_mb} MB`);
            
            if (jsonData.imported_files && jsonData.imported_files.length > 0) {
                console.log('\n✅ 成功导入的文件:');
                jsonData.imported_files.forEach((file, index) => {
                    console.log(`  ${index + 1}. ${file.path} (${(file.size / 1024).toFixed(2)} KB, ${file.line_count} 行)`);
                });
            }
            
            if (jsonData.failed_files && jsonData.failed_files.length > 0) {
                console.log('\n❌ 导入失败的文件:');
                jsonData.failed_files.forEach((file, index) => {
                    console.log(`  ${index + 1}. ${file.path}: ${file.error}`);
                });
            }
            
            console.log('\n✅ 数据导入完成！');
            
            if (jsonData.failed_count === 0) {
                console.log('🎉 所有文件都已成功导入！');
            } else {
                console.log(`⚠️  有 ${jsonData.failed_count} 个文件导入失败，请检查日志`);
                process.exit(1);
            }
            
        } catch (error) {
            console.error('❌ 解析响应JSON失败:', error.message);
            console.error('原始响应:', data.substring(0, 500));
            process.exit(1);
        }
    });
});

request.on('error', (error) => {
    console.error('❌ 请求失败:', error.message);
    process.exit(1);
});

request.setTimeout(120000, () => {
    console.error('❌ 请求超时（120秒）');
    request.destroy();
    process.exit(1);
});

// 发送请求数据
request.write(postData);
request.end();

console.log('⏳ 正在发送数据，请稍候...');
