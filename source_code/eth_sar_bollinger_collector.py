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
    """
    if len(candles) < BOLL_PERIOD + 2:
        return None

    # 区分已收盘 vs 当前未收盘
    confirmed = [c for c in candles if c.get("confirm", "1") == "1"]
    if len(confirmed) < BOLL_PERIOD + 2:
        confirmed = candles[:-1]   # fallback: 去掉最后一根

    closes = [c["close"] for c in confirmed]
    boll   = calc_bollinger(closes, BOLL_PERIOD, BOLL_MULT)
    sar_r  = calc_sar(confirmed, SAR_AF_INIT, SAR_AF_STEP, SAR_AF_MAX)
    trend  = build_trend_sequence(sar_r)

    # 最近5根已收盘K线
    last5 = []
    for idx in range(max(0, len(confirmed) - 5), len(confirmed)):
        c   = confirmed[idx]
        s   = sar_r[idx]
        b   = boll[idx]
        t   = trend[idx]

        if s is None or b is None or t is None:
            continue

        ts_ms = c["ts"]
        dt_bj = datetime.fromtimestamp(ts_ms / 1000, tz=BEIJING_TZ)

        pct = sar_pct(s["sar"], b["ub"], b["lb"])

        bar_info = {
            "beijing_time":  dt_bj.strftime("%Y-%m-%d %H:%M"),
            "ts_ms":         ts_ms,
            "open":          c["open"],
            "high":          c["high"],
            "low":           c["low"],
            "close":         c["close"],
            "sar":           round(s["sar"], 4),
            "bull":          t["bull"],
            "sar_seq":       t["seq"],       # 第几根多/空
            "trend_id":      t["trend_id"],
            "switched":      t["switched"],  # 是否趋势切换
            "boll_ub":       round(b["ub"], 4),
            "boll_mid":      round(b["mid"], 4),
            "boll_lb":       round(b["lb"], 4),
            "sar_pct":       pct,            # SAR所处百分比
        }
        last5.append(bar_info)

    if not last5:
        return None

    latest = last5[-1]

    # ── 当前未收盘K线（实时bar） ───────────────────────────────────────────────
    # 从全量candles中找未收盘的bar（confirm="0"），若无则用最新已收盘bar替代
    live_bar_raw = None
    for c in reversed(candles):
        if c.get("confirm", "1") == "0":
            live_bar_raw = c
            break

    # 计算live bar的SAR/BOLL：用最新已收盘bar的SAR和BOLL值（实时价格来自live_bar）
    live_price = live_bar_raw["close"] if live_bar_raw else candles[-1]["close"]

    # live bar的BOLL：用最新confirmed bar的BOLL（布林带基于已收盘K线）
    live_boll_ub  = latest["boll_ub"]
    live_boll_mid = latest["boll_mid"]
    live_boll_lb  = latest["boll_lb"]

    # live bar的SAR：用已收盘序列最后一个SAR值（不用未收盘影线影响SAR）
    live_sar      = latest["sar"]
    live_bull     = latest["bull"]
    live_seq      = latest["sar_seq"]
    live_trend_id = latest["trend_id"]
    live_switched = False  # 未收盘K线不算切换

    live_sar_pct  = sar_pct(live_sar, live_boll_ub, live_boll_lb)

    if live_bar_raw:
        live_ts_ms  = live_bar_raw["ts"]
        live_dt_bj  = datetime.fromtimestamp(live_ts_ms / 1000, tz=BEIJING_TZ)
        live_bar_time = live_dt_bj.strftime("%Y-%m-%d %H:%M")
    else:
        # 没有未收盘bar时：推算下一根K线时间
        latest_ts_ms = latest["ts_ms"]
        next_ts_ms   = latest_ts_ms + 5 * 60 * 1000
        next_dt_bj   = datetime.fromtimestamp(next_ts_ms / 1000, tz=BEIJING_TZ)
        live_bar_time = next_dt_bj.strftime("%Y-%m-%d %H:%M")
        live_bar_raw  = None  # 标记：无实际数据

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
        "open":       live_bar_raw["open"]  if live_bar_raw else latest["close"],
        "high":       live_bar_raw["high"]  if live_bar_raw else live_price,
        "low":        live_bar_raw["low"]   if live_bar_raw else live_price,
        "close":      live_price,
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
        "last5_bars":   last5,
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


def main():
    print(f"[ETH-SAR] 启动 ETH-USDT-SWAP 5分钟 SAR+Bollinger 采集器", flush=True)
    print(f"[ETH-SAR] 数据目录: {DATA_DIR}", flush=True)
    print(f"[ETH-SAR] 采集间隔: {COLLECT_INTERVAL}秒", flush=True)

    while True:
        try:
            run_once()
        except Exception as e:
            print(f"[ETH-SAR] 主循环异常: {e}", flush=True)
        time.sleep(COLLECT_INTERVAL)


if __name__ == "__main__":
    main()
