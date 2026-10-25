"""飞书多维表格报告（box 移植版：lark-cli → 飞书 Open API，经 _shared/feishu_bitable.py）

首次运行：创建 Bitable（立即转移所有权给用户）+ 3 张表 + 2 个筛选视图
后续运行：复用 data/<slug>/category_config.json 中的 bitable_token / table_ids，追加本周数据
--dry-run：不发任何写请求，只打印将要写入的内容，并把记录落盘到报告目录 bitable_dryrun_<week>.json
限制：Open API 不支持创建仪表盘（原版 6 个图表）→ 需在飞书 UI 手动建；视图排序也需在 UI 设置。
"""
import json, logging, os, sys, time
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
import feishu_bitable as fb  # noqa: E402
import config  # noqa: E402
from analyzer import TrendData  # noqa: E402,F401

logger = logging.getLogger(__name__)

BURST_LABEL = {"first_burst": "首次爆发", "rebound": "回弹", "steady_rise": "持续上升",
               "declining": "下降中", "long_tail_expansion": "长尾扩展", "unknown": "未知"}
CATEGORY_LABEL = {"ingredient": "核心产品", "benefit": "功效/场景", "brand": "品牌",
                  "condition": "场景/症状", "form": "形态/规格", "irrelevant": "无关", "unrelated": "无关"}


def _sel(names):
    return {"options": [{"name": n} for n in names]}


def _numf(fmt="0"):
    return {"formatter": fmt}


KEYWORD_FIELDS = [
    {"field_name": "关键词", "type": fb.TEXT},
    {"field_name": "周次", "type": fb.TEXT},
    {"field_name": "中文名", "type": fb.TEXT},
    {"field_name": "Tier", "type": fb.SELECT, "property": _sel(["Tier 1", "Tier 2", "Tier 3"])},
    {"field_name": "当前排名", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "前周排名", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "排名变化", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "分类", "type": fb.SELECT, "property": _sel(list(dict.fromkeys(CATEGORY_LABEL.values())))},
    {"field_name": "爆发类型", "type": fb.SELECT, "property": _sel(list(BURST_LABEL.values()))},
    {"field_name": "月搜索量", "type": fb.NUMBER, "property": _numf("1,000")},
    {"field_name": "峰值搜索量", "type": fb.NUMBER, "property": _numf("1,000")},
    {"field_name": "CPC", "type": fb.NUMBER, "property": _numf("0.00")},
    {"field_name": "环比变化", "type": fb.NUMBER, "property": _numf("0.0")},
    {"field_name": "历史最佳排名", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "数据来源", "type": fb.TEXT},
    {"field_name": "AI分析", "type": fb.TEXT},
    {"field_name": "抓取时间", "type": fb.DATETIME, "property": {"date_formatter": "yyyy/MM/dd HH:mm"}},
]
EXTENDED_FIELDS = [
    {"field_name": "主关键词", "type": fb.TEXT},
    {"field_name": "周次", "type": fb.TEXT},
    {"field_name": "扩展词", "type": fb.TEXT},
    {"field_name": "周搜索量", "type": fb.NUMBER, "property": _numf("1,000")},
    {"field_name": "月搜索量", "type": fb.NUMBER, "property": _numf("1,000")},
    {"field_name": "CPC", "type": fb.NUMBER, "property": _numf("0.00")},
    {"field_name": "季节性", "type": fb.TEXT},
]
SUMMARY_FIELDS = [
    {"field_name": "周次", "type": fb.TEXT},
    {"field_name": "抓取总数", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "类目相关数", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "Tier1数量", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "Tier2数量", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "Tier3数量", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "排除数量", "type": fb.NUMBER, "property": _numf()},
    {"field_name": "核心发现", "type": fb.TEXT},
    {"field_name": "新增词典词", "type": fb.TEXT},
    {"field_name": "生成时间", "type": fb.DATETIME, "property": {"date_formatter": "yyyy/MM/dd HH:mm"}},
]


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _enrich(td, keyword_analysis):
    d = {"关键词": td.keyword, "中文名": td.zh_name or "", "Tier": f"Tier {td.tier}",
         "当前排名": td.current_rank, "前周排名": td.previous_rank or 0}
    d["排名变化"] = (td.previous_rank - td.current_rank) if td.previous_rank and td.previous_rank > 0 else td.rank_change
    d["分类"] = CATEGORY_LABEL.get(td.category, td.category)
    d["爆发类型"] = BURST_LABEL.get(td.burst_type, "未知")
    vols = [(m.get("searchVolume") or m.get("volume", 0)) for m in (td.monthly_volumes or [])]
    vols = [v for v in vols if v and v > 0]
    detail = (td.cpc_history or [{}])[-1] if td.cpc_history else {}
    d["月搜索量"] = (detail.get("monthly_search_volume") if isinstance(detail, dict) else None) or (vols[-1] if vols else 0)
    d["峰值搜索量"] = max(vols) if vols else 0
    cpc = None
    if isinstance(detail, dict) and _f(detail.get("cpc")) > 0:
        cpc = _f(detail["cpc"])
    if not cpc:
        for m in reversed(td.monthly_volumes or []):
            if _f(m.get("cpc")) > 0:
                cpc = _f(m["cpc"])
                break
    d["CPC"] = round(cpc, 2) if cpc else 0
    d["环比变化"] = round(td.volume_mom_change * 100, 1) if td.volume_mom_change is not None else 0
    d["历史最佳排名"] = td.historical_peak_rank or 0
    d["数据来源"] = td.combo_label
    d["AI分析"] = keyword_analysis.get(td.keyword, "")
    return d


def _setup_views(cli, kw_table):
    vids = {name: cli.create_view(kw_table, name) for name in ("Tier 1 高优先级", "Tier 2 观察区")}
    if cli.dry:
        return
    try:
        tier = next(f for f in cli.fields(kw_table) if f["field_name"] == "Tier")
        opt = {o["name"]: o["id"] for o in tier["property"]["options"]}
        for name, tname in (("Tier 1 高优先级", "Tier 1"), ("Tier 2 观察区", "Tier 2")):
            cli.set_view_filter(kw_table, vids[name], tier["field_id"], "is", json.dumps([opt[tname]]))
    except Exception as e:
        logger.warning(f"视图筛选设置失败（可在飞书 UI 手动设置）: {e}")


def ensure_bitable(cli):
    bt = config.get_bitable_config()
    if bt["bitable_token"] and bt["table_ids"].get("keywords"):
        cli.app = bt["bitable_token"]
        logger.info(f"复用已有多维表格: {bt['bitable_url']}")
        t = dict(bt["table_ids"])
        missing = [(k, n, f) for k, n, f in (("extended", "扩展关键词", EXTENDED_FIELDS),
                                              ("summary", "周报摘要", SUMMARY_FIELDS)) if not t.get(k)]
        # 旧表字段名可能与本版不一致：只新增缺失字段，不删除/重命名用户已有字段
        added = cli.ensure_fields(t["keywords"], KEYWORD_FIELDS)
        if added:
            logger.info(f"主表补齐字段: {added}")
        for k, n, f in missing:  # 旧表格只有主表时补建（只新增表，不删不改已有数据）
            t[k] = cli.create_table(n, f)
        if missing and not cli.dry:
            config.save_bitable_config(bt["bitable_token"], bt["bitable_url"], t, bt.get("dashboard_id", ""))
        bt["table_ids"] = t
        return bt
    name = f"{config.get_category_name()} ABA关键词监测"
    token, url = cli.create_app(name)  # create_app 内部已 transfer_owner 给用户
    kw = cli.create_table("关键词监测", KEYWORD_FIELDS)
    ext = cli.create_table("扩展关键词", EXTENDED_FIELDS)
    summ = cli.create_table("周报摘要", SUMMARY_FIELDS)
    _setup_views(cli, kw)
    table_ids = {"keywords": kw, "extended": ext, "summary": summ}
    if not cli.dry:
        config.save_bitable_config(token, url, table_ids, "")
    logger.info("多维表格已创建（仪表盘需在飞书 UI 手动添加，Open API 不支持）")
    return {"bitable_token": token, "bitable_url": url, "table_ids": table_ids}


def build_rows(results, tiered_data, analysis, now=None):
    now = now or datetime.now()
    week = f"{now.year}-W{now.isocalendar()[1]:02d}"
    ts = fb.ts_ms(now)
    ka = analysis.get("keyword_analysis", {})
    kw_rows, ext_rows = [], []
    for td in results:
        r = _enrich(td, ka)
        r["周次"], r["抓取时间"] = week, ts
        kw_rows.append(r)
        for ek in td.extended_keywords or []:
            ext_rows.append({"主关键词": td.keyword, "周次": week,
                             "扩展词": ek.get("关键词") or ek.get("keyword", ""),
                             "周搜索量": int(_f(ek.get("周搜索量"))), "月搜索量": int(_f(ek.get("月搜索量"))),
                             "CPC": round(_f(ek.get("cpc推荐竞价")), 2), "季节性": ek.get("季节性", "") or ""})
    tc = {1: 0, 2: 0, 3: 0}
    for td in results:
        tc[td.tier] = tc.get(td.tier, 0) + 1
    nw = tiered_data.get("new_words", {})
    summary = {"周次": week, "抓取总数": tiered_data.get("total_scraped", 0),
               "类目相关数": tiered_data.get("total_category", 0),
               "Tier1数量": tc[1], "Tier2数量": tc[2], "Tier3数量": tc[3],
               "排除数量": len(tiered_data.get("excluded_keywords", {})),
               "核心发现": "\n".join(f"{i+1}. {x}" for i, x in enumerate(analysis.get("core_findings", []))),
               "新增词典词": "; ".join(f"{k}: {', '.join(v)}" for k, v in nw.items() if v),
               "生成时间": ts}
    return week, kw_rows, ext_rows, summary


def generate_bitable_report(results, total_scraped, total_category, new_dict_words, analysis=None,
                            excluded_keywords=None, sorftime_stats=None, tiered_data=None, dry_run=False):
    analysis = analysis or {}
    tiered_data = tiered_data or {"total_scraped": total_scraped, "total_category": total_category,
                                  "new_words": new_dict_words, "excluded_keywords": excluded_keywords or {},
                                  "sorftime_stats": sorftime_stats or {}}
    week, kw_rows, ext_rows, summary = build_rows(results, tiered_data, analysis)
    os.makedirs(config.get_report_dir(), exist_ok=True)
    if dry_run:
        p = os.path.join(config.get_report_dir(), f"bitable_dryrun_{week}.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"keywords": kw_rows, "extended": ext_rows, "summary": summary}, f, ensure_ascii=False, indent=2)
        logger.info(f"[DRY-RUN] 记录已落盘: {p}")
    cli = fb.Client(dry_run=dry_run, log=logger.info)
    bt = ensure_bitable(cli)
    t = bt["table_ids"]
    n1 = len(cli.batch_create(t["keywords"], kw_rows)) if kw_rows else 0
    n2 = len(cli.batch_create(t["extended"], ext_rows)) if ext_rows else 0
    cli.batch_create(t["summary"], [summary])
    logger.info(f"写入: 关键词 {n1}/{len(kw_rows)} | 扩展词 {n2}/{len(ext_rows)} | 摘要 1 （{'DRY-RUN' if dry_run else 'LIVE'}，API 调用 {cli.calls}）")
    return bt.get("bitable_url", "")
