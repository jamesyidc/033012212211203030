#!/usr/bin/env python3
"""
ETH 5分钟 SAR + 布林带 独立采集器
- 完全独立，不依赖任何其他系统
- 数据来源：OKX 永续合约 ETH-USDT-SWAP 5分钟K线
- 计算指标：SAR (Parabolic SAR) + Bollinger Bands (20期, 2σ)
- SAR百分比 = (SAR - LB) / (UB - LB) * 100
- 多头/空头计数（从趋势切换时重置编号）
- 按日期存储 JSONL
"""

import os
import sys
import json
import time
import math
import requests
import pytz
from datetime import datetime, timedelta
from pathlib import Path

# ── Telegram 配置 ─────────────────────────────────────────────────────────────
TG_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8437045462:AAFePnwdC21cqeWhZISMQHGGgjmroVqE2H0")
TG_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID",   "-1003227444260")
# 开口比告警阈值
RATIO_ALERT_THRESHOLD = 2.2

# ── 常量 ──────────────────────────────────────────────────────────────────────
SYMBOL          = "ETH-USDT-SWAP"
BAR             = "5m"
FETCH_LIMIT     = 300          # 获取最近300根K线（SAR需要足够历史以稳定）
BOLL_PERIOD     = 20           # 布林带周期
BOLL_MULT       = 2.0          # 布林带倍数
SAR_AF_INIT     = 0.02         # SAR初始加速因子
SAR_AF_STEP     = 0.02         # SAR步长
SAR_AF_MAX      = 0.20         # SAR最大加速因子
COLLECT_INTERVAL= 30           # 采集间隔（秒）
DATA_DIR        = Path("/home/user/webapp/eth_sar_bollinger")
BEIJING_TZ      = pytz.timezone("Asia/Shanghai")

OKX_KLINE_URL   = "https://www.okx.com/api/v5/market/candles"

# ── 目录初始化 ─────────────────────────────────────────────────────────────────
DATA_DIR.mkdir(parents=True, exist_ok=True)
PID_FILE        = DATA_DIR / "eth_sar_collector.pid"  # 单例锁文件

# ── OKX K线获取 ────────────────────────────────────────────────────────────────
def fetch_klines(symbol: str, bar: str, limit: int) -> list:
    """
    从OKX获取K线数据，返回按时间升序排列的列表
    每条 = [ts_ms, open, high, low, close, vol, ...]
    """
    try:
        params = {"instId": symbol, "bar": bar, "limit": str(limit)}
        resp = requests.get(OKX_KLINE_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != "0":
            print(f"[ETH-SAR] OKX API error: {data.get('msg')}", flush=True)
            return []
        # OKX返回降序，反转为升序
        candles = data["data"][::-1]
        result = []
        for c in candles:
            result.append({
                "ts":      int(c[0]),
                "open":    float(c[1]),
                "high":    float(c[2]),
                "low":     float(c[3]),
                "close":   float(c[4]),
                "vol":     float(c[5]),
                "confirm": c[8] if len(c) > 8 else "1",  # "1"=已收盘 "0"=当前K线
            })
        return result
    except Exception as e:
        print(f"[ETH-SAR] fetch_klines error: {e}", flush=True)
        return []


# ── Bollinger Bands ────────────────────────────────────────────────────────────
def calc_bollinger(closes: list, period: int = 20, mult: float = 2.0):
    """
    计算布林带，返回与closes等长的列表，前(period-1)条为None
    每条 = {"mid": float, "ub": float, "lb": float}
    """
    result = [None] * len(closes)
    for i in range(period - 1, len(closes)):
        window = closes[i - period + 1 : i + 1]
        mid = sum(window) / period
        var = sum((x - mid) ** 2 for x in window) / period
        std = math.sqrt(var)
        result[i] = {"mid": mid, "ub": mid + mult * std, "lb": mid - mult * std}
    return result


# ── Parabolic SAR ──────────────────────────────────────────────────────────────
def calc_sar(candles: list,
             af_init: float = 0.02,
             af_step: float = 0.02,
             af_max:  float = 0.20) -> list:
    """
    计算 Parabolic SAR（与 OKX/TradingView 对齐版本）
    关键差异：使用收盘价（close）判断是否反转，而非影线（high/low）
      bull=True  → close > SAR（多头）
      bull=False → close < SAR（空头）
    返回与candles等长的列表，每条 = {"sar": float, "bull": bool}
    """
    n = len(candles)
    if n < 2:
        return [None] * n

    result = [None] * n

    # 初始化：用前两根K线的收盘价判断初始方向
    bull = candles[1]["close"] >= candles[0]["close"]
    ep   = candles[0]["high"] if bull else candles[0]["low"]
    sar  = candles[0]["low"]  if bull else candles[0]["high"]
    af   = af_init

    result[0] = {"sar": sar, "bull": bull}

    for i in range(1, n):
        high  = candles[i]["high"]
        low   = candles[i]["low"]
        close = candles[i]["close"]
        prev_high = candles[i - 1]["high"]
        prev_low  = candles[i - 1]["low"]

        # 计算新 SAR
        new_sar = sar + af * (ep - sar)

        if bull:
            # 多头：SAR 不能高于前两根K线的最低点
            new_sar = min(new_sar, prev_low)
            if i >= 2:
                new_sar = min(new_sar, candles[i - 2]["low"])
            # ★ 使用收盘价判断反转（与 OKX/TradingView 一致）
            if close < new_sar:
                bull    = False
                new_sar = ep        # SAR 跳到前极值点（最高点）
                ep      = low       # 新极值点 = 当根最低价
                af      = af_init
            else:
                if high > ep:       # 新高，更新极值点
                    ep = high
                    af = min(af + af_step, af_max)
        else:
            # 空头：SAR 不能低于前两根K线的最高点
            new_sar = max(new_sar, prev_high)
            if i >= 2:
                new_sar = max(new_sar, candles[i - 2]["high"])
            # ★ 使用收盘价判断反转（与 OKX/TradingView 一致）
            if close > new_sar:
                bull    = True
                new_sar = ep        # SAR 跳到前极值点（最低点）
                ep      = high      # 新极值点 = 当根最高价
                af      = af_init
            else:
                if low < ep:        # 新低，更新极值点
                    ep = low
                    af = min(af + af_step, af_max)

        sar = new_sar
        result[i] = {"sar": sar, "bull": bull}

    return result


# ── SAR百分比（相对布林带） ────────────────────────────────────────────────────
def sar_pct(sar_val: float, ub: float, lb: float) -> float:
    """
    SAR所处的百分比位置
    100% → SAR = UB（上轨）
      0% → SAR = LB（下轨）
    超出范围时可为负或>100
    """
    if ub == lb:
        return 0.0
    return round((sar_val - lb) / (ub - lb) * 100, 2)


# ── 趋势计数 ────────────────────────────────────────────────────────────────────
def build_trend_sequence(sar_list: list) -> list:
    """
    遍历SAR序列，为每根K线附加多空编号
    返回与sar_list等长的列表（None处也返回None）
    每条 = {
        "bull":      bool,
        "seq":       int,    # 当前趋势内的第几根K线（从1开始）
        "trend_id":  int,    # 全局趋势编号（多头奇数，空头偶数 或自增）
        "switched":  bool    # 是否是趋势切换的第一根
    }
    """
    result   = [None] * len(sar_list)
    cur_bull = None
    cur_seq  = 0
    trend_id = 0

    for i, s in enumerate(sar_list):
        if s is None:
            continue
        bull = s["bull"]
        if bull != cur_bull:
            cur_bull  = bull
            cur_seq   = 1
            trend_id += 1
            switched  = True
        else:
            cur_seq  += 1
            switched  = False
        result[i] = {
            "bull":     bull,
            "seq":      cur_seq,
            "trend_id": trend_id,
            "switched": switched,
        }
    return result


# ── 核心计算 ──────────────────────────────────────────────────────────────────
def compute_snapshot(candles: list) -> dict | None:
    """
    基于全量K线计算当前快照（最新5根K线的详细数据 + 当前状态）
    只用已收盘的K线（confirm=1）计算SAR，避免未收盘影线干扰判断

    关键修复：用时间戳判断已收盘K线，而非依赖confirm字段
    OKX的confirm字段有时在K线刚收盘时仍返回"0"，导致每次计算结果不同
    解决方案：将时间戳早于当前5分钟边界的K线一律视为已收盘
    """
    if len(candles) < BOLL_PERIOD + 2:
        return None

    # 用当前时间确定当前5分钟K线的开始时间戳
    now_ts_ms = int(datetime.now(BEIJING_TZ).timestamp() * 1000)
    # 当前5分钟边界（向下取整到5分钟）
    bar_interval_ms = 5 * 60 * 1000
    current_bar_start_ms = (now_ts_ms // bar_interval_ms) * bar_interval_ms

    # 区分已收盘 vs 当前未收盘
    # 已收盘：K线时间戳严格小于当前5分钟边界（即不是当前正在形成的K线）
    confirmed = [c for c in candles if c["ts"] < current_bar_start_ms]
    if len(confirmed) < BOLL_PERIOD + 2:
        # fallback: 用confirm字段判断，去掉最后一根
        confirmed = [c for c in candles if c.get("confirm", "1") == "1"]
        if len(confirmed) < BOLL_PERIOD + 2:
            confirmed = candles[:-1]

    closes = [c["close"] for c in confirmed]
    boll   = calc_bollinger(closes, BOLL_PERIOD, BOLL_MULT)
    sar_r  = calc_sar(confirmed, SAR_AF_INIT, SAR_AF_STEP, SAR_AF_MAX)
    trend  = build_trend_sequence(sar_r)

    # 最近5根已收盘K线
    last5 = []
    for idx in range(max(0, len(confirmed) - 10), len(confirmed)):
        c   = confirmed[idx]
        s   = sar_r[idx]
        b   = boll[idx]
        t   = trend[idx]

        if s is None or b is None or t is None:
            continue

        ts_ms = c["ts"]
        dt_bj = datetime.fromtimestamp(ts_ms / 1000, tz=BEIJING_TZ)

        pct = sar_pct(s["sar"], b["ub"], b["lb"])

        _open  = c["open"]
        _close = c["close"]
        _sar   = round(s["sar"], 4)
        _ub    = round(b["ub"], 4)
        _lb    = round(b["lb"], 4)

        # 后端预计算派生字段（前端无需任何数值运算）
        body_pct   = round((_close - _open) / _open * 100, 4) if _open and _open != 0 else None
        boll_width = round(_ub - _lb, 4)
        sar_dist   = round(_sar - _close, 4)  # 正=SAR在上方(空头/压力)，负=SAR在下方(多头/支撑)

        bar_info = {
            "beijing_time":  dt_bj.strftime("%Y-%m-%d %H:%M"),
            "ts_ms":         ts_ms,
            "open":          _open,
            "high":          c["high"],
            "low":           c["low"],
            "close":         _close,
            "sar":           _sar,
            "bull":          t["bull"],
            "sar_seq":       t["seq"],       # 第几根多/空
            "trend_id":      t["trend_id"],
            "switched":      t["switched"],  # 是否趋势切换
            "boll_ub":       _ub,
            "boll_mid":      round(b["mid"], 4),
            "boll_lb":       _lb,
            "sar_pct":       pct,            # SAR所处百分比
            # ── 后端预计算字段（前端直接读取，无需运算） ──
            "body_pct":      body_pct,       # 实体涨跌幅 %
            "boll_width":    boll_width,     # 布林带宽度 (UB-LB)
            "sar_dist":      sar_dist,       # SAR距离 (SAR-close)
        }
        last5.append(bar_info)

    if not last5:
        return None

    latest = last5[-1]

    # ── 当前未收盘K线（实时bar） ───────────────────────────────────────────────
    # 用时间戳判断当前K线：时间戳 >= 当前5分钟边界的K线为未收盘（实时bar）
    # 这样不依赖confirm字段，避免OKX的confirm字段不稳定导致的判断错误
    live_bar_raw = None
    for c in reversed(candles):
        if c["ts"] >= current_bar_start_ms:
            live_bar_raw = c
            break

    # ── 对实时K线计算其自身的 SAR/趋势 ──────────────────────────────────────────
    # 将未收盘K线拼入已收盘序列，重新计算最后一步，获取正确的 sar_seq/bull/sar
    # 布林带仍基于已收盘K线（不受未收盘影线干扰）
    live_price = live_bar_raw["close"] if live_bar_raw else candles[-1]["close"]

    # live bar的BOLL：用最新confirmed bar的BOLL（布林带基于已收盘K线）
    live_boll_ub  = latest["boll_ub"]
    live_boll_mid = latest["boll_mid"]
    live_boll_lb  = latest["boll_lb"]

    if live_bar_raw:
        live_ts_ms  = live_bar_raw["ts"]
        live_dt_bj  = datetime.fromtimestamp(live_ts_ms / 1000, tz=BEIJING_TZ)
        live_bar_time = live_dt_bj.strftime("%Y-%m-%d %H:%M")

        # 将live bar拼入confirmed列表，计算SAR/趋势的最后一步
        all_bars      = confirmed + [live_bar_raw]
        all_sar_r     = calc_sar(all_bars, SAR_AF_INIT, SAR_AF_STEP, SAR_AF_MAX)
        all_trend     = build_trend_sequence(all_sar_r)
        live_sar_info = all_sar_r[-1]
        live_t_info   = all_trend[-1]

        live_sar      = round(live_sar_info["sar"], 4) if live_sar_info else latest["sar"]
        live_bull     = live_t_info["bull"]      if live_t_info else latest["bull"]
        live_seq      = live_t_info["seq"]       if live_t_info else latest["sar_seq"]
        live_trend_id = live_t_info["trend_id"]  if live_t_info else latest["trend_id"]
        live_switched = live_t_info["switched"]  if live_t_info else False
    else:
        # 没有未收盘bar时：推算下一根K线时间，继承最后已收盘K线的值
        latest_ts_ms  = latest["ts_ms"]
        next_ts_ms    = latest_ts_ms + 5 * 60 * 1000
        next_dt_bj    = datetime.fromtimestamp(next_ts_ms / 1000, tz=BEIJING_TZ)
        live_bar_time = next_dt_bj.strftime("%Y-%m-%d %H:%M")
        live_bar_raw  = None  # 标记：无实际数据
        live_sar      = latest["sar"]
        live_bull     = latest["bull"]
        live_seq      = latest["sar_seq"]
        live_trend_id = latest["trend_id"]
        live_switched = False

    live_sar_pct  = sar_pct(live_sar, live_boll_ub, live_boll_lb)

    _live_open  = live_bar_raw["open"]  if live_bar_raw else latest["close"]
    _live_close = live_price
    _live_body_pct  = round((_live_close - _live_open) / _live_open * 100, 4) if _live_open and _live_open != 0 else None
    _live_boll_width = round(live_boll_ub - live_boll_lb, 4)
    _live_sar_dist   = round(live_sar - _live_close, 4)
    _live_price_pct  = round((_live_close - live_boll_lb) / (live_boll_ub - live_boll_lb) * 100, 4) if (live_boll_ub - live_boll_lb) != 0 else 0.0

    current_bar = {
        "bar_time":   live_bar_time,
        "price":      live_price,
        "sar":        live_sar,
        "bull":       live_bull,
        "sar_seq":    live_seq,
        "trend_id":   live_trend_id,
        "switched":   live_switched,
        "boll_ub":    live_boll_ub,
        "boll_mid":   live_boll_mid,
        "boll_lb":    live_boll_lb,
        "sar_pct":    live_sar_pct,
        "confirmed":  False,   # 标识这是未收盘的实时bar
        "open":       _live_open,
        "high":       live_bar_raw["high"]  if live_bar_raw else live_price,
        "low":        live_bar_raw["low"]   if live_bar_raw else live_price,
        "close":      _live_close,
        # ── 后端预计算字段 ──
        "body_pct":   _live_body_pct,
        "boll_width": _live_boll_width,
        "sar_dist":   _live_sar_dist,
        "price_pct":  _live_price_pct,   # 价格在布林带中的位置%（进度条用）
    }

    now_bj = datetime.now(BEIJING_TZ)
    snapshot = {
        "record_time":  now_bj.strftime("%Y-%m-%d %H:%M:%S"),
        "date":         now_bj.strftime("%Y-%m-%d"),
        "symbol":       SYMBOL,
        "bar":          BAR,
        # 当前状态（SAR基于最新收盘K线，price为最新tick价格）
        "current": {
            "price":        current_bar["price"],
            "sar":          current_bar["sar"],
            "bull":         current_bar["bull"],
            "sar_seq":      current_bar["sar_seq"],
            "trend_id":     current_bar["trend_id"],
            "sar_pct":      current_bar["sar_pct"],
            "boll_ub":      current_bar["boll_ub"],
            "boll_mid":     current_bar["boll_mid"],
            "boll_lb":      current_bar["boll_lb"],
            "bar_time":     current_bar["bar_time"],
        },
        # 实时未收盘K线（用于前端展示NOW行）
        "current_bar":  current_bar,
        # 最近5根已收盘K线详情
        "last5_bars":   last5,   # 最近10根已收盘K线（名称保持兼容）
    }
    return snapshot


# ── JSONL 存储 ─────────────────────────────────────────────────────────────────
def save_snapshot(snapshot: dict):
    date_str  = snapshot["date"]
    file_path = DATA_DIR / f"eth_sar_boll_{date_str}.jsonl"
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")


def load_today_snapshots(date_str: str = None) -> list:
    if date_str is None:
        date_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")
    file_path = DATA_DIR / f"eth_sar_boll_{date_str}.jsonl"
    if not file_path.exists():
        return []
    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return records


def get_latest_snapshot() -> dict | None:
    """从最近几天的JSONL中读取最新一条记录"""
    for i in range(3):
        d = (datetime.now(BEIJING_TZ) - timedelta(days=i)).strftime("%Y-%m-%d")
        records = load_today_snapshots(d)
        if records:
            return records[-1]
    return None


# ── 主循环 ────────────────────────────────────────────────────────────────────

# ── Telegram 通知 ─────────────────────────────────────────────────────────────
def send_telegram(msg: str):
    """发送 Telegram 消息"""
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        resp = requests.post(url, json={
            "chat_id":    TG_CHAT_ID,
            "text":       msg,
            "parse_mode": "HTML",
        }, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print(f"[ETH-SAR] Telegram发送失败: {e}", flush=True)


# ── 开口比告警状态 ─────────────────────────────────────────────────────────────
_ratio_alert_state = {
    "last_alerted_trend_id": None,  # 上次发出告警时的trend_id
    "last_alerted_ratio":    0.0,   # 上次发出告警时的ratio
}


def _get_trend_start_boll_width(snap: dict) -> float | None:
    """
    从今日JSONL文件中找到当前趋势(trend_id)的第一根K线(sar_seq==1)的boll_width
    """
    try:
        today = snap.get("date", datetime.now(BEIJING_TZ).strftime("%Y-%m-%d"))
        file_path = DATA_DIR / f"eth_sar_boll_{today}.jsonl"
        if not file_path.exists():
            return None

        cur_trend_id = snap.get("current", {}).get("trend_id")
        if cur_trend_id is None:
            return None

        # 扫描文件找到 trend_id 匹配且 sar_seq==1 的记录
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    cb = rec.get("current_bar") or {}
                    if (cb.get("trend_id") == cur_trend_id and
                            cb.get("sar_seq") == 1 and
                            cb.get("boll_width") is not None):
                        return float(cb["boll_width"])
                except Exception:
                    pass
        return None
    except Exception as e:
        print(f"[ETH-SAR] _get_trend_start_boll_width error: {e}", flush=True)
        return None


def check_ratio_alert(snap: dict):
    """
    检查布林带开口比，超过阈值时发送Telegram告警
    每个趋势只在首次突破时告警，之后每超出0.2再次告警（如2.4, 2.6...）
    """
    try:
        cur = snap.get("current", {})
        cur_bar = snap.get("current_bar", {})

        trend_id  = cur.get("trend_id")
        direction = "多头" if cur.get("bull") else "空头"
        sar_seq   = cur.get("sar_seq", 0)
        price     = cur.get("price", 0)
        boll_width = cur_bar.get("boll_width")

        if boll_width is None or boll_width <= 0:
            return

        # 获取本轮起始开口
        start_width = _get_trend_start_boll_width(snap)
        if start_width is None or start_width <= 0:
            return

        ratio = round(boll_width / start_width, 2)

        if ratio < RATIO_ALERT_THRESHOLD:
            # 低于阈值，重置状态（以便下次趋势重新告警）
            if _ratio_alert_state["last_alerted_trend_id"] == trend_id:
                # 同一趋势内比值降回阈值以下，允许再次告警
                _ratio_alert_state["last_alerted_ratio"] = 0.0
            return

        # 判断是否需要发出告警
        last_trend_id = _ratio_alert_state["last_alerted_trend_id"]
        last_ratio    = _ratio_alert_state["last_alerted_ratio"]

        # 新趋势首次突破 OR 同趋势内上涨超出上次告警0.2
        should_alert = (
            last_trend_id != trend_id or       # 新趋势
            ratio >= last_ratio + 0.2          # 同趋势但比值又升了0.2
        )

        if not should_alert:
            return

        # 发出告警
        bar_time = cur.get("bar_time", snap.get("record_time", ""))
        ub = cur.get("boll_ub", 0)
        lb = cur.get("boll_lb", 0)

        msg = (
            f"🚨 <b>ETH布林带开口扩张告警</b>\n\n"
            f"📊 当前方向：<b>{direction}</b> #{sar_seq}\n"
            f"📈 开口比：<b>{ratio:.2f}x</b>（≥{RATIO_ALERT_THRESHOLD}触发）\n"
            f"📏 当前开口：{boll_width:.2f}  起始开口：{start_width:.2f}\n"
            f"💰 当前价格：{price:.2f}\n"
            f"📐 UB={ub:.2f}  LB={lb:.2f}\n"
            f"🕐 时间：{bar_time}"
        )

        send_telegram(msg)

        _ratio_alert_state["last_alerted_trend_id"] = trend_id
        _ratio_alert_state["last_alerted_ratio"]    = ratio

        print(
            f"[ETH-SAR] ⚠️ 开口比告警发送: {direction}#{sar_seq} "
            f"ratio={ratio:.2f} boll_width={boll_width:.2f} start={start_width:.2f}",
            flush=True
        )

    except Exception as e:
        print(f"[ETH-SAR] check_ratio_alert error: {e}", flush=True)
def run_once():
    """执行一次采集+计算+存储"""
    candles = fetch_klines(SYMBOL, BAR, FETCH_LIMIT)
    if not candles:
        return None
    snap = compute_snapshot(candles)
    if snap:
        save_snapshot(snap)
        cur = snap["current"]
        direction = "多头" if cur["bull"] else "空头"
        print(
            f"[ETH-SAR] {snap['record_time']} | "
            f"price={cur['price']:.2f} SAR={cur['sar']:.2f} "
            f"{direction}#{cur['sar_seq']} "
            f"SAR%={cur['sar_pct']:.1f}% "
            f"UB={cur['boll_ub']:.2f} LB={cur['boll_lb']:.2f}",
            flush=True
        )
    return snap




def acquire_pid_lock() -> bool:
    """
    尝试获取 PID 锁文件，防止多个实例同时运行。
    如果已有实例在运行，返回 False；否则写入当前 PID 并返回 True。
    """
    my_pid = os.getpid()
    if PID_FILE.exists():
        try:
            old_pid = int(PID_FILE.read_text().strip())
            # 检查旧 PID 是否还在运行
            os.kill(old_pid, 0)   # 信号 0：不发送信号，只检查进程是否存在
            # 进程存在 → 有另一个实例正在运行
            print(f"[ETH-SAR] 已有实例在运行 (PID={old_pid})，退出。", flush=True)
            return False
        except (ProcessLookupError, ValueError):
            # 旧进程已退出，可以接管锁
            pass
    PID_FILE.write_text(str(my_pid))
    return True


def release_pid_lock():
    try:
        PID_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def main():
    # ── 单例保护：防止两个采集器并行写入，造成数据双链振荡 ──────────────────
    if not acquire_pid_lock():
        sys.exit(1)

    print(f"[ETH-SAR] 启动 ETH-USDT-SWAP 5分钟 SAR+Bollinger 采集器 (PID={os.getpid()})", flush=True)
    print(f"[ETH-SAR] 数据目录: {DATA_DIR}", flush=True)
    print(f"[ETH-SAR] 采集间隔: {COLLECT_INTERVAL}秒", flush=True)

    try:
        while True:
            try:
                run_once()
            except Exception as e:
                print(f"[ETH-SAR] 主循环异常: {e}", flush=True)
            time.sleep(COLLECT_INTERVAL)
    finally:
        release_pid_lock()


if __name__ == "__main__":
    main()
