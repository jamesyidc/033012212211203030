/**
 * 交易信号分发系统 - JS客户端库
 * @version 1.0
 * @date 2026-03-08
 * 
 * 用途：主系统与副系统（交易信号分发系统）的通信接口
 */

class TradingSignalsAPI {
    /**
     * 初始化API客户端
     * @param {Object} config - 配置项
     * @param {string} config.baseURL - API基础URL，默认 '/api/trading-signals-system'
     * @param {number} config.timeout - 请求超时时间（毫秒），默认 5000
     */
    constructor(config = {}) {
        this.baseURL = config.baseURL || '/api/trading-signals-system';
        this.timeout = config.timeout || 5000;
        this.listeners = [];
    }

    /**
     * 发送HTTP请求的通用方法
     * @private
     */
    async _request(method, endpoint, data = null) {
        const url = `${this.baseURL}${endpoint}`;
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data && (method === 'POST' || method === 'PUT')) {
            options.body = JSON.stringify(data);
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);
            
            options.signal = controller.signal;
            
            const response = await fetch(url, options);
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('请求超时');
            }
            throw error;
        }
    }

    // ==================== 核心API方法 ====================

    /**
     * 1. 获取待执行信号队列
     * @returns {Promise<Object>} 返回信号列表
     */
    async getPending() {
        return await this._request('GET', '/pending');
    }

    /**
     * 2. 执行信号
     * @param {Object} params - 执行参数
     * @param {string} params.model_id - 模型ID
     * @param {string} params.trigger_time - 触发时间
     * @param {string} params.execution_subsystem - 执行子系统
     * @param {string} params.execution_account - 执行账户
     * @param {Object} params.execution_params - 执行参数
     * @returns {Promise<Object>}
     */
    async execute(params) {
        if (!params.model_id || !params.trigger_time) {
            throw new Error('model_id 和 trigger_time 是必填参数');
        }
        return await this._request('POST', '/execute', params);
    }

    /**
     * 3. 取消信号
     * @param {Object} params - 取消参数
     * @param {string} params.model_id - 模型ID
     * @param {string} params.trigger_time - 触发时间
     * @param {string} params.reason - 取消原因
     * @returns {Promise<Object>}
     */
    async cancel(params) {
        if (!params.model_id || !params.trigger_time) {
            throw new Error('model_id 和 trigger_time 是必填参数');
        }
        return await this._request('POST', '/cancel', params);
    }

    /**
     * 4. 获取系统状态
     * @returns {Promise<Object>}
     */
    async getStatus() {
        return await this._request('GET', '/status');
    }

    /**
     * 5. 报告执行结果（主系统→副系统）
     * @param {Object} params - 执行结果
     * @param {string} params.model_id - 模型ID
     * @param {string} params.trigger_time - 触发时间
     * @param {Object} params.execution_result - 执行结果详情
     * @returns {Promise<Object>}
     */
    async reportExecution(params) {
        if (!params.model_id || !params.trigger_time || !params.execution_result) {
            throw new Error('model_id, trigger_time 和 execution_result 是必填参数');
        }
        return await this._request('POST', '/execution-report', params);
    }

    /**
     * 6. 获取历史信号
     * @param {Object} params - 查询参数
     * @param {number} params.limit - 返回数量，默认50
     * @param {string} params.date - 日期筛选（YYYY-MM-DD）
     * @param {string} params.model_id - 模型筛选
     * @returns {Promise<Object>}
     */
    async getHistory(params = {}) {
        const queryParams = new URLSearchParams();
        if (params.limit) queryParams.append('limit', params.limit);
        if (params.date) queryParams.append('date', params.date);
        if (params.model_id) queryParams.append('model_id', params.model_id);
        
        const query = queryParams.toString();
        const endpoint = query ? `/history?${query}` : '/history';
        
        return await this._request('GET', endpoint);
    }

    // ==================== 高级功能 ====================

    /**
     * 轮询监听新信号（自动模式）
     * @param {Function} callback - 发现新信号时的回调函数
     * @param {number} interval - 轮询间隔（毫秒），默认30000（30秒）
     * @returns {number} 定时器ID，可用于停止轮询
     */
    startPolling(callback, interval = 30000) {
        const timerId = setInterval(async () => {
            try {
                const response = await this.getPending();
                
                if (response.success && response.pending_count > 0) {
                    // 过滤未执行的信号
                    const newSignals = response.signals.filter(s => !s.executed);
                    
                    if (newSignals.length > 0) {
                        callback(newSignals, response);
                    }
                }
            } catch (error) {
                console.error('[TradingSignalsAPI] 轮询错误:', error);
            }
        }, interval);

        // 保存定时器ID
        this.listeners.push(timerId);
        
        console.log(`[TradingSignalsAPI] 开始轮询，间隔 ${interval}ms，定时器ID: ${timerId}`);
        
        return timerId;
    }

    /**
     * 停止轮询
     * @param {number} timerId - 定时器ID
     */
    stopPolling(timerId) {
        if (timerId) {
            clearInterval(timerId);
            this.listeners = this.listeners.filter(id => id !== timerId);
            console.log(`[TradingSignalsAPI] 已停止轮询，定时器ID: ${timerId}`);
        }
    }

    /**
     * 停止所有轮询
     */
    stopAllPolling() {
        this.listeners.forEach(timerId => clearInterval(timerId));
        console.log(`[TradingSignalsAPI] 已停止所有轮询，共 ${this.listeners.length} 个`);
        this.listeners = [];
    }

    /**
     * 批量执行信号
     * @param {Array} signals - 信号数组
     * @param {Object} commonParams - 公共执行参数
     * @returns {Promise<Array>} 执行结果数组
     */
    async batchExecute(signals, commonParams = {}) {
        const results = [];
        
        for (const signal of signals) {
            try {
                const result = await this.execute({
                    model_id: signal.model_id,
                    trigger_time: signal.trigger_time,
                    ...commonParams
                });
                results.push({ signal, result, success: true });
            } catch (error) {
                results.push({ signal, error: error.message, success: false });
            }
        }
        
        return results;
    }

    // ==================== 工具方法 ====================

    /**
     * 格式化信号数据（用于显示）
     * @param {Object} signal - 原始信号数据
     * @returns {string} 格式化后的字符串
     */
    formatSignal(signal) {
        return `
【${signal.model_name}】
方向: ${signal.direction === 'long' ? '做多' : '做空'}
触发时间: ${signal.trigger_time}
市场趋势: ${signal.market_trend === 'bull' ? '牛市' : '熊市'}
正比例: ${signal.positive_ratio}%
速度(1.5分钟): ${signal.velocity_1_5min}%
状态: ${signal.executed ? '已执行' : '待执行'}
        `.trim();
    }

    /**
     * 检查信号是否过期
     * @param {Object} signal - 信号对象
     * @param {number} maxAge - 最大有效期（分钟），默认60分钟
     * @returns {boolean} 是否过期
     */
    isSignalExpired(signal, maxAge = 60) {
        const triggerTime = new Date(signal.trigger_time);
        const now = new Date();
        const ageMinutes = (now - triggerTime) / (1000 * 60);
        return ageMinutes > maxAge;
    }

    /**
     * 过滤有效信号（未执行 + 未过期）
     * @param {Array} signals - 信号数组
     * @param {number} maxAge - 最大有效期（分钟）
     * @returns {Array} 有效信号数组
     */
    filterValidSignals(signals, maxAge = 60) {
        return signals.filter(signal => {
            return !signal.executed && !this.isSignalExpired(signal, maxAge);
        });
    }
}

// 导出到全局
if (typeof window !== 'undefined') {
    window.TradingSignalsAPI = TradingSignalsAPI;
    console.log('[TradingSignalsAPI] 客户端库已加载 v1.0');
}

// 支持CommonJS模块（Node.js）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TradingSignalsAPI;
}
