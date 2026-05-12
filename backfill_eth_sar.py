#!/usr/bin/env python3
"""
ETH SAR+布林带 缺口数据补全脚本
==================================================
核心原则：
  - 只追加（append），绝不重写文件
  - 只补充缺失的 K 线，不改动任何已有记录
  - 幂等：重复运行不产生重复数据

用法：
  python3 backfill_eth_sar.py [YYYY-MM-DD]
  不传日期时默认补全今天
"""
import sys, json, math, requests, pytz
from datetime import datetime, timedelta
from pathlib import Path

# ── 参数（与 collector 完全一致）──────────────────────────────────────────────
SYMBOL        = "ETH-USDT-SWAP"
BAR           = "5m"
BOLL_PERIOD   = 20
BOLL_MULT     = 2.0
SAR_AF_INIT   = 0.02
SAR_AF_STEP   = 0.02
SAR_AF_MAX    = 0.20
DATA_DIR      = Path("/home/user/webapp/eth_sar_bollinger")
BEIJING_TZ    = pytz.timezone("Asia/Shanghai")
OKX_HIST_URL  = "https://www.okx.com/api/v5/market/history-candles"
OKX_NOW_URL   = "https://www.okx.com/api/v5/market/candles"

# ── OKX K线获取 ────────────────────────────────────────────────────────────────
def _fetch(url, params):
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    d = resp.json()
    if d.get("code") != "0":
        raise RuntimeError(f"OKX API error: {d.get('msg')}")
    return [{"ts": int(c[0]), "open": float(c[1]), "high": float(c[2]),
             "low": float(c[3]), "close": float(c[4]),
             "confirm": c[8] if len(c) > 8 else "1"}
            for c in reversed(d["data"])]          # 升序

def fetch_history(limit=300):
    """获取最近 limit 根已收盘 K 线（history-candles）"""
    return _fetch(OKX_HIST_URL, {"instId": SYMBOL, "bar": BAR, "limit": str(limit)})

# ── 指标计算（与 collector 完全一致）──────────────────────────────────────────
def calc_bollinger(closes):
    result = [None] * len(closes)
    for i in range(BOLL_PERIOD - 1, len(closes)):
        w = closes[i - BOLL_PERIOD + 1: i + 1]
        mid = sum(w) / BOLL_PERIOD
        std = math.sqrt(sum((x - mid) ** 2 for x in w) / BOLL_PERIOD)
        result[i] = {"mid": mid, "ub": mid + BOLL_MULT * std,
                     "lb": mid - BOLL_MULT * std}
    return result

def calc_sar(candles):
    n = len(candles)
    if n < 2:
        return [None] * n
    res = [None] * n
    bull = candles[1]["close"] >= candles[0]["close"]
    ep   = candles[0]["high"] if bull else candles[0]["low"]
    sar  = candles[0]["low"]  if bull else candles[0]["high"]
    af   = SAR_AF_INIT
    res[0] = {"sar": sar, "bull": bull}
    for i in range(1, n):
        h, l, c = candles[i]["high"], candles[i]["low"], candles[i]["close"]
        ph, pl  = candles[i-1]["high"], candles[i-1]["low"]
        ns = sar + af * (ep - sar)
        if bull:
            ns = min(ns, pl, candles[i-2]["low"] if i >= 2 else pl)
            if c < ns:
                bull, ns, ep, af = False, ep, l, SAR_AF_INIT
            else:
                if h > ep: ep = h; af = min(af + SAR_AF_STEP, SAR_AF_MAX)
        else:
            ns = max(ns, ph, candles[i-2]["high"] if i >= 2 else ph)
            if c > ns:
                bull, ns, ep, af = True, ep, h, SAR_AF_INIT
            else:
                if l < ep: ep = l; af = min(af + SAR_AF_STEP, SAR_AF_MAX)
        sar = ns
        res[i] = {"sar": sar, "bull": bull}
    return res

def build_trend(sar_list):
    res = [None] * len(sar_list)
    cur_bull, seq, tid = None, 0, 0
    for i, s in enumerate(sar_list):
        if s is None: continue
        if s["bull"] != cur_bull:
            cur_bull, seq, tid = s["bull"], 1, tid + 1
        else:
            seq += 1
        res[i] = {"bull": s["bull"], "seq": seq, "trend_id": tid, "switched": seq == 1}
    return res

def sar_pct(sar_v, ub, lb):
    return round((sar_v - lb) / (ub - lb) * 100, 2) if ub != lb else 0.0

def ts_to_bj(ts_ms):
    return datetime.fromtimestamp(ts_ms / 1000, tz=BEIJING_TZ).strftime("%Y-%m-%d %H:%M")

# ── 主逻辑 ─────────────────────────────────────────────────────────────────────
def main(date_str=None):
    if date_str is None:
        date_str = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d")

    jsonl_file = DATA_DIR / f"eth_sar_boll_{date_str}.jsonl"
    print(f"=== ETH SAR 缺口补全 (只追加) for {date_str} ===")
    print(f"目标文件: {jsonl_file}")

    # ── Step 1: 读现有文件，收集已有 record_time（去重用）和已有 bar 时间 ──────
    existing_rts  = set()   # 已有快照的 record_time，防止重复写入
    existing_bars = set()   # 已有 last5_bars 中的 beijing_time
    line_count    = 0

    if jsonl_file.exists():
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                    line_count += 1
                    rt = r.get("record_time", "")
                    if rt:
                        existing_rts.add(rt)
                    for bar in r.get("last5_bars") or []:
                        bt = bar.get("beijing_time", "")
                        if bt:
                            existing_bars.add(bt)
                    # current_bar 中也可能有 bar_time
                    cb = r.get("current_bar") or {}
                    bt2 = cb.get("bar_time") or cb.get("beijing_time", "")
                    if bt2:
                        existing_bars.add(bt2)
                except:
                    pass

    print(f"现有行数: {line_count}  |  已有快照数: {len(existing_rts)}  |  已有K线时间: {len(existing_bars)}")

    # ── Step 2: 从 OKX 获取历史 K 线 ─────────────────────────────────────────
    print("从 OKX history-candles 获取 300 根 K 线...")
    candles = fetch_history(300)
    if len(candles) < BOLL_PERIOD + 5:
        print(f"❌ K 线数不足 ({len(candles)})，退出")
        return

    print(f"获取到 {len(candles)} 根 K 线  {ts_to_bj(candles[0]['ts'])} → {ts_to_bj(candles[-1]['ts'])}")

    # ── Step 3: 计算全量指标 ───────────────────────────────────────────────────
    closes   = [c["close"] for c in candles]
    boll_arr = calc_bollinger(closes)
    sar_arr  = calc_sar(candles)
    trnd_arr = build_trend(sar_arr)

    # ── Step 4: 筛出目标日期的 K 线，排除已有 bar 时间 ────────────────────────
    day_bars = []   # 目标日期全部已收盘 K 线
    for i, c in enumerate(candles):
        if boll_arr[i] is None or sar_arr[i] is None or trnd_arr[i] is None:
            continue
        if c.get("confirm") == "0":           # 跳过未收盘
            continue
        bj = ts_to_bj(c["ts"])
        if not bj.startswith(date_str):
            continue
        b, s, t = boll_arr[i], sar_arr[i], trnd_arr[i]
        day_bars.append({
            "idx": i,               # 在 candles[] 中的位置，供生成 last5_bars 用
            "beijing_time": bj,
            "ts_ms":   c["ts"],
            "open":    round(c["open"],  4),
            "high":    round(c["high"],  4),
            "low":     round(c["low"],   4),
            "close":   round(c["close"], 4),
            "sar":     round(s["sar"],   4),
            "bull":    t["bull"],
            "sar_seq": t["seq"],
            "trend_id":t["trend_id"],
            "switched":t["switched"],
            "boll_ub": round(b["ub"],  4),
            "boll_mid":round(b["mid"], 4),
            "boll_lb": round(b["lb"],  4),
            "sar_pct": sar_pct(s["sar"], b["ub"], b["lb"]),
        })

    missing = [b for b in day_bars if b["beijing_time"] not in existing_bars]
    print(f"今日 K 线总数: {len(day_bars)}  |  需补充: {len(missing)}")

    if not missing:
        print("✅ 无缺口，无需补全")
        return

    print(f"缺口范围: {missing[0]['beijing_time']} → {missing[-1]['beijing_time']}")

    # ── Step 5: 构造补全快照并追加到文件末尾 ──────────────────────────────────
    # 建立 idx→bar 的映射，方便生成 last5_bars
    idx_to_bar = {b["idx"]: b for b in day_bars}
    # 也要包含今日之前的 bars（用于边界的 last5）
    for i, c in enumerate(candles):
        if boll_arr[i] is None or sar_arr[i] is None or trnd_arr[i] is None:
            continue
        bj = ts_to_bj(c["ts"])
        if bj.startswith(date_str):
            break
        b, s, t = boll_arr[i], sar_arr[i], trnd_arr[i]
        idx_to_bar[i] = {
            "idx": i, "beijing_time": bj, "ts_ms": c["ts"],
            "open": round(c["open"],4), "high": round(c["high"],4),
            "low": round(c["low"],4),   "close": round(c["close"],4),
            "sar": round(s["sar"],4),   "bull": t["bull"],
            "sar_seq": t["seq"],        "trend_id": t["trend_id"],
            "switched": t["switched"],
            "boll_ub": round(b["ub"],4), "boll_mid": round(b["mid"],4),
            "boll_lb": round(b["lb"],4),
            "sar_pct": sar_pct(s["sar"], b["ub"], b["lb"]),
        }

    appended = 0
    with open(jsonl_file, "a", encoding="utf-8") as out:   # ← 追加模式
        for bar in missing:
            rt = bar["beijing_time"] + ":30"   # 伪造 record_time（K线结束后30秒）

            # 防止 record_time 重复（极低概率，但做防护）
            if rt in existing_rts:
                rt = bar["beijing_time"] + ":31"
            if rt in existing_rts:
                print(f"  ⚠️ 跳过 {bar['beijing_time']}（record_time 冲突）")
                continue

            existing_rts.add(rt)

            # last5_bars：取当前 bar 及之前最多4根（共5根）
            cur_idx = bar["idx"]
            l5 = []
            for j in range(max(0, cur_idx - 4), cur_idx + 1):
                if j in idx_to_bar:
                    b2 = dict(idx_to_bar[j])
                    b2.pop("idx", None)   # idx 是内部字段，不写入 JSONL
                    l5.append(b2)

            bar_clean = dict(bar)
            bar_clean.pop("idx", None)

            rec = {
                "record_time":  rt,
                "date":         date_str.replace("-", ""),
                "symbol":       SYMBOL,
                "bar":          BAR,
                "_backfilled":  True,           # 标记，方便审计
                "current": {
                    "price":     bar["close"],
                    "sar":       bar["sar"],
                    "bull":      bar["bull"],
                    "sar_seq":   bar["sar_seq"],
                    "trend_id":  bar["trend_id"],
                    "boll_ub":   bar["boll_ub"],
                    "boll_mid":  bar["boll_mid"],
                    "boll_lb":   bar["boll_lb"],
                    "sar_pct":   bar["sar_pct"],
                },
                "current_bar": {
                    "bar_time":  bar["beijing_time"],
                    "open":      bar["open"],
                    "high":      bar["high"],
                    "low":       bar["low"],
                    "close":     bar["close"],
                    "confirmed": True,
                    "sar":       bar["sar"],
                    "bull":      bar["bull"],
                    "sar_seq":   bar["sar_seq"],
                    "trend_id":  bar["trend_id"],
                    "boll_ub":   bar["boll_ub"],
                    "boll_mid":  bar["boll_mid"],
                    "boll_lb":   bar["boll_lb"],
                    "sar_pct":   bar["sar_pct"],
                },
                "last5_bars": l5,
            }
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            appended += 1

    print(f"\n✅ 追加完成：共写入 {appended} 条补全记录（原有 {line_count} 行完全未动）")

    # ── Step 6: 验证 ──────────────────────────────────────────────────────────
    all_bars = set()
    total_lines = 0
    with open(jsonl_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try:
                r = json.loads(line)
                total_lines += 1
                for b in r.get("last5_bars") or []:
                    bt = b.get("beijing_time", "")
                    if bt and bt.startswith(date_str):
                        all_bars.add(bt)
            except: pass

    sorted_bars = sorted(all_bars)
    print(f"\n验证：总行数 {total_lines}  |  唯一K线时间 {len(sorted_bars)}")
    if sorted_bars:
        print(f"  范围: {sorted_bars[0]} → {sorted_bars[-1]}")
    # 找缺口
    gaps = []
    prev = None
    for t in sorted_bars:
        dt = datetime.strptime(t[:16], "%Y-%m-%d %H:%M")
        if prev and (dt - prev).total_seconds() > 600:
            gaps.append(f"{prev.strftime('%H:%M')} → {dt.strftime('%H:%M')} ({int((dt-prev).total_seconds()//60)}min)")
        prev = dt
    if gaps:
        print(f"  ⚠️ 仍有缺口: {gaps}")
    else:
        print("  ✅ 无缺口！")


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(date_arg)
