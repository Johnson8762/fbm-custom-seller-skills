"""Sorftime 并发查询客户端（适配 2026 版 Sorftime MCP 英文 JSON 返回）

调用：keyword_trend / keyword_detail / keyword_extends，参数 {keyword, keyword_support_site}
返回格式：content[0].text = '{"doc": {...}, "data": ...}'
  keyword_trend.data: search_volume_trend / rank_trend = 扁平 [yyyyMM, v, ...]；
                      cpc_trend 实测为 [yyyyMM, "1.31"(USD), ...] 两两一组（doc 写 4 元组/美分，两种都兼容）
  keyword_detail.data: dict（monthly_search_volume, cpc, weekly_search_rank, peak_season ...）
  keyword_extends.data: list[{keyword, weekly_search_volume, weekly_search_rank, monthly_search_volume,
                              recommended_cpc_bid, seasonality}]
"""
import asyncio, json, logging, re
import httpx
import config

logger = logging.getLogger(__name__)


async def _sorftime_call(client, tool, arguments):
    try:
        resp = await client.post(
            config.SORFTIME_BASE_URL, params={"key": config.SORFTIME_API_KEY},
            headers={"Accept": "application/json, text/event-stream"},
            json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                  "params": {"name": tool, "arguments": arguments}},
            timeout=config.SORFTIME_TIMEOUT)
        resp.raise_for_status()
        result = None
        for line in resp.text.split("\n"):
            line = line.strip()
            if line.startswith("data: "):
                try:
                    p = json.loads(line[6:])
                    if "result" in p:
                        result = p["result"]
                except json.JSONDecodeError:
                    continue
        return result
    except Exception as e:  # 不打印 URL（含 key）
        logger.warning(f"Sorftime {tool} error: {type(e).__name__}")
        return None


def _payload(raw):
    """MCP result -> parsed JSON (dict/list) or None."""
    if raw is None:
        return None
    if isinstance(raw, (dict, list)) and not (isinstance(raw, dict) and "content" in raw):
        return raw
    text = raw
    if isinstance(raw, dict):
        c = raw.get("content") or []
        text = "\n".join(x.get("text", "") for x in c if isinstance(x, dict))
    if not isinstance(text, str) or not text.strip():
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"[\{\[][\s\S]*[\}\]]", text)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                return None
    return None


def _data(raw):
    p = _payload(raw)
    if isinstance(p, dict) and "data" in p:
        return p["data"]
    return p


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _pairs(flat):
    out = []
    if not isinstance(flat, list):
        return out
    for i in range(0, len(flat) - 1, 2):
        out.append((str(flat[i]), flat[i + 1]))
    return out


def _month(p):
    p = str(p)
    return f"{p[:4]}-{p[4:6]}" if len(p) >= 6 else p


def _cpc_series(flat):
    """支持 [m, v, m, v] (USD) 与 [m, cpc, min, max, ...] (cent) 两种格式。"""
    if not isinstance(flat, list) or not flat:
        return {}
    is_period = lambda x: bool(re.fullmatch(r"\d{6}(\d{2})?", str(x)))
    step = 2
    if len(flat) >= 8 and is_period(flat[0]) and is_period(flat[4]) and not is_period(flat[2]):
        step = 4
    out = {}
    for i in range(0, len(flat) - 1, step):
        v = _num(flat[i + 1])
        if v is None:
            continue
        if step == 4:
            v = v / 100.0
        out[_month(flat[i])] = round(v, 2)
    return out


def parse_trend(raw):
    """keyword_trend -> [{month, searchVolume, searchRank, cpc}] 按月升序。"""
    d = _data(raw)
    if not isinstance(d, dict):
        return []
    md = {}
    for p, v in _pairs(d.get("search_volume_trend")):
        n = _num(v)
        if n is not None:
            md.setdefault(_month(p), {})["searchVolume"] = int(n)
    for p, v in _pairs(d.get("rank_trend")):
        n = _num(v)
        if n is not None:
            md.setdefault(_month(p), {})["searchRank"] = int(n)
    for m, c in _cpc_series(d.get("cpc_trend")).items():
        md.setdefault(m, {})["cpc"] = c
    for m in md:
        md[m]["month"] = m
    return sorted(md.values(), key=lambda x: x["month"])


def parse_detail(raw):
    d = _data(raw)
    if isinstance(d, list):
        d = d[0] if d and isinstance(d[0], dict) else None
    if not isinstance(d, dict):
        return {}
    keep = ["keyword", "keyword_cn_name", "weekly_search_rank", "rank_change_of_weekly",
            "monthly_search_volume", "cpc", "cpc_range", "search_conversion_rate",
            "peak_season", "top3_asin", "top3_brand", "top3_category", "update"]
    return {k: d.get(k) for k in keep if k in d}


def parse_extends(raw, limit=10):
    """keyword_extends -> list，键保持中文（与 bitable 写入映射一致）。"""
    d = _data(raw)
    if isinstance(d, dict):
        d = d.get("list") or d.get("items") or []
    if not isinstance(d, list):
        return []
    out = []
    for it in d:
        if not isinstance(it, dict):
            continue
        out.append({
            "关键词": it.get("keyword") or it.get("关键词", ""),
            "周搜索量": it.get("weekly_search_volume", it.get("周搜索量", 0)) or 0,
            "周搜索排名": it.get("weekly_search_rank", 0) or 0,
            "月搜索量": it.get("monthly_search_volume", it.get("月搜索量", 0)) or 0,
            "cpc推荐竞价": it.get("recommended_cpc_bid", it.get("cpc推荐竞价", "")),
            "季节性": it.get("seasonality", it.get("季节性", "")),
        })
    out.sort(key=lambda x: -(_num(x["月搜索量"]) or 0))
    return out[:limit]


def _args(kw):
    return {"keyword": kw, "keyword_support_site": config.SORFTIME_SITE}


async def query_full(client, kw, sem):
    async with sem:
        t = await _sorftime_call(client, "keyword_trend", _args(kw))
        d = await _sorftime_call(client, "keyword_detail", _args(kw))
        e = await _sorftime_call(client, "keyword_extends", _args(kw))
    r = {}
    if t:
        r["trend"] = parse_trend(t)
    if d:
        r["detail"] = parse_detail(d)
    r["extends"] = parse_extends(e)
    return kw, r


async def query_trend(client, kw, sem):
    async with sem:
        t = await _sorftime_call(client, "keyword_trend", _args(kw))
    return kw, ({"trend": parse_trend(t)} if t else {})


async def batch_query(tier1_kws, tier2_kws):
    sem = asyncio.Semaphore(config.SORFTIME_CONCURRENCY)
    results = {}
    async with httpx.AsyncClient(verify=config.VERIFY_SSL) as client:
        tasks = [query_full(client, kw, sem) for kw in tier1_kws]
        tasks += [query_trend(client, kw, sem) for kw in tier2_kws]
        for coro in asyncio.as_completed(tasks):
            kw, data = await coro
            if data:
                results[kw] = data
                logger.info(f"  ok {kw}")
    return results


def query_sorftime_batch(tier1_kws, tier2_kws):
    if config.SORFTIME_MAX_TIER1 is not None:
        tier1_kws = tier1_kws[: config.SORFTIME_MAX_TIER1]
    if config.SORFTIME_MAX_TIER2 is not None:
        tier2_kws = tier2_kws[: config.SORFTIME_MAX_TIER2]
    total = len(tier1_kws) * 3 + len(tier2_kws)
    logger.info(f"Sorftime: Tier1={len(tier1_kws)}x3 + Tier2={len(tier2_kws)}x1 = {total} calls")
    data = asyncio.run(batch_query(tier1_kws, tier2_kws))
    return data, {"tier1_keywords": len(tier1_kws), "tier2_keywords": len(tier2_kws),
                  "total_calls": total, "enriched": len(data)}
