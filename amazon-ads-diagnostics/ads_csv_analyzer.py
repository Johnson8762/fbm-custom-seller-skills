#!/usr/bin/env python3
"""亚马逊广告诊断 —— CSV 模式（box 版，替代 SIF MCP）
输入：亚马逊广告后台 / 领星导出的 Sponsored Products 报告（搜索词 / 投放 / 关键词 / 广告活动报告，CSV 或 XLSX，中英文表头均可）。
按 SKILL「Campaign 健康度判断标准」「关键词优化建议逻辑（含样本量门槛）」逐行判定，输出 JSON（供 Agent 写报告/写飞书）。
  python ads_csv_analyzer.py report.xlsx --asin B0XXXX [--target-acos 30 | 0.30] [--target-roas 3.0] [--days 30] -o result.json
  --target-acos 接受 30 或 0.30（>1 视为百分数）；JSON 中统一存小数 target_acos=0.30，另存 target_acos_pct=30 便于阅读。
只读计算，不调用任何外部 API。

2026-10-25 规则更新（样本量门槛，来源见 SKILL_FULL.md「关键词优化建议逻辑」）：
  收割 ≥2 单且 ACoS ≤ 目标；否定 ≥10 次点击 0 单（或花费 ≥ 2×目标 CPA），≤9 次点击只对无关/竞品品牌词做「人工复核」标记；
  任何出价调整需 ≥20 次点击；单轮降价最多 -25%；提价（CVR>15% 且展示<1000）另需 ≥2 单且 ≥10 次点击。
"""
import argparse, json, re, sys
import pandas as pd

# ---- 样本量门槛（改这里即可全局生效）
GATES = {
    "harvest_min_orders": 2,      # 收割：≥2 单 且 ACoS ≤ 目标
    "negate_min_clicks": 10,      # 否定：≥10 次点击 0 单
    "negate_cpa_multiple": 2.0,   # 或 0 单花费 ≥ 2×目标 CPA
    "bid_change_min_clicks": 20,  # 任何调价（降/提）需 ≥20 次点击
    "max_bid_cut": 0.25,          # 单轮降价上限 -25%
    "bid_up_min_orders": 2,       # 提价额外门槛：≥2 单
    "bid_up_min_clicks": 10,      # 提价额外门槛：≥10 次点击
    "bid_up_pct": 0.20,
}

ALIASES = {  # 每个 key 先找完全相同的列名，再找前缀匹配；顺序即优先级
    "campaign": ["campaign name", "campaign", "广告活动名称", "广告活动"],
    "ad_group": ["ad group name", "ad group", "广告组名称", "广告组"],
    "term": ["customer search term", "用户搜索词", "客户搜索词", "search term", "keyword", "关键词"],
    "targeting": ["targeting", "投放"],
    "match": ["match type", "匹配类型", "匹配方式"],
    "impr": ["impressions", "展示量", "曝光量"],
    "clicks": ["clicks", "点击量", "点击"],
    "spend": ["spend", "cost", "花费", "支出"],
    "sales": ["7 day total sales", "14 day total sales", "total sales", "广告销售额", "sales", "7天总销售额", "销售额"],
    "orders": ["7 day total orders (#)", "14 day total orders (#)", "广告订单", "total orders", "orders", "7天总订单数(#)", "订单"],
    "bid": ["keyword bid", "bid", "投放竞价", "竞价($)", "竞价", "出价"],
}
AUTO_TARGETS = {"close-match", "loose-match", "substitutes", "complements", "紧密匹配", "宽泛匹配", "同类商品", "关联商品"}
EMPTY = {"", "-", "--", "nan", "none"}


def norm_acos(v):
    """30 / 0.30 / '30%' → 0.30。>1 视为百分数。"""
    v = float(str(v).replace("%", "").strip())
    return round(v / 100, 6) if v > 1 else v


def _num(s):
    return pd.to_numeric(s.astype(str).str.replace(r"[$,%￥€£\s]", "", regex=True), errors="coerce").fillna(0)


def _blank(v):
    return v is None or str(v).strip().lower() in EMPTY


def load(path):
    df = pd.read_excel(path) if re.search(r"\.xlsx?$", path, re.I) else pd.read_csv(path, encoding="utf-8-sig")
    cols = {str(c).lower().strip(): c for c in df.columns}
    m = {}
    for k, names in ALIASES.items():
        hit = next((cols[n] for n in names if n in cols), None)
        if hit is None:
            hit = next((cols[c] for n in names for c in cols if c.startswith(n)), None)
        if hit is not None and hit not in m.values():
            m[k] = hit
    miss = [k for k in ("campaign", "impr", "clicks", "spend", "sales", "orders") if k not in m]
    if miss:
        sys.exit(f"❌ 报告缺少列: {miss}（现有列: {list(df.columns)[:20]}）")
    out = pd.DataFrame({k: df[v] for k, v in m.items()})
    out = out[~out["campaign"].map(_blank)]  # 去掉领星导出首行的「汇总」行
    for k in ("impr", "clicks", "spend", "sales", "orders", "bid"):
        if k in out:
            out[k] = _num(out[k])
    if "term" not in out and "targeting" in out:      # 无搜索词列时，按投放/关键词分析
        out["term"] = out["targeting"]
    if "targeting" in out:                            # 自动活动的匹配方式为「--」，用投放组（紧密/宽泛…）代替
        if "match" not in out:
            out["match"] = out["targeting"]
        else:
            out["match"] = [t if _blank(mt) else mt for mt, t in zip(out["match"], out["targeting"])]
    return out, m


def kpis(g):
    s = g.sum(numeric_only=True)
    sp, sa, cl, im, od = s.get("spend", 0), s.get("sales", 0), s.get("clicks", 0), s.get("impr", 0), s.get("orders", 0)
    return {"花费": round(float(sp), 2), "销售额": round(float(sa), 2), "展示": int(im), "点击": int(cl), "订单": int(od),
            "ACOS": round(sp / sa, 4) if sa else None, "ROAS": round(sa / sp, 2) if sp else None,
            "CTR": round(cl / im, 4) if im else None, "CVR": round(od / cl, 4) if cl else None}


def health(k, t_acos, t_roas):
    lv = []
    a, r, ctr, cvr = k["ACOS"], k["ROAS"], k["CTR"], k["CVR"]
    if a is not None:
        lv.append(0 if a < t_acos else 1 if a <= t_acos * 1.2 else 2)
    elif k["花费"] > 0:
        lv.append(2)  # 有花费无销售
    if r is not None:
        lv.append(0 if r > t_roas else 1 if r >= t_roas * 0.8 else 2)
    if ctr is not None:
        lv.append(0 if ctr > 0.005 else 1 if ctr >= 0.003 else 2)
    if cvr is not None:
        lv.append(0 if cvr > 0.10 else 1 if cvr >= 0.05 else 2)
    return ["健康", "警告", "异常"][max(lv) if lv else 0]


def _has(term, words):
    t = str(term or "").lower()
    return next((w for w in words if w and w in t), None)


def is_auto(campaign, match):
    return str(match).strip().lower() in AUTO_TARGETS or bool(re.search(r"auto|自动", str(campaign), re.I))


def kw_action(k, t_acos, ctx):
    """返回 (建议动作, 优先级, 依据, 调价比例或 None)。优先级 "" = 保持，不进动作清单。"""
    G = GATES
    sp, cl, od, im = k["花费"], k["点击"], k["订单"], k["展示"]
    a, cvr, ctr = k["ACOS"], k["CVR"] or 0, k["CTR"] or 0
    term, auto, st = k.get("关键词"), ctx["auto"], ctx["search_term_report"]
    t_cpa = ctx.get("target_cpa")
    bid_ok = cl >= G["bid_change_min_clicks"]

    # 1) 0 单：否定 / 暂停 / 人工复核 / 样本不足
    if od == 0:
        cpa_hit = bool(t_cpa) and sp >= G["negate_cpa_multiple"] * t_cpa
        if cl >= G["negate_min_clicks"] or cpa_hit:
            why = f"{cl} 次点击 0 单" + (f"，花费 ${sp} ≥ 2×目标CPA ${t_cpa:.2f}" if cpa_hit else f"（≥{G['negate_min_clicks']} 次点击门槛）")
            core = _has(term, ctx["protect"])
            if core:
                if bid_ok:
                    return f"降价{G['max_bid_cut']:.0%}（核心相关词，不直接否定）", "P1", why + f"；含核心词「{core}」", -G["max_bid_cut"]
                return "核心相关词：不否定，移到手动精准低价单独测试，人工确认", "P1", why + f"；含核心词「{core}」", None
            pri = "P0" if sp > 20 else "P1"
            if st:
                return "否定精准（在本活动）", pri, why, None
            return "暂停该关键词/投放", pri, why, None
        flag = _has(term, ctx["competitor"]) or _has(term, ctx["irrelevant"])
        if flag:
            kind = "竞品品牌词" if _has(term, ctx["competitor"]) else "疑似无关词"
            return f"人工复核：{kind}，确认后可提前否定精准", "P2", f"{cl} 次点击 0 单，未达 {G['negate_min_clicks']} 次点击门槛；命中「{flag}」", None
        return "保持（样本不足）", "", f"0 单但仅 {cl} 次点击（<{G['negate_min_clicks']}）", None

    # 2) 收割：≥2 单且 ACoS ≤ 目标
    if od >= G["harvest_min_orders"] and a is not None and a <= t_acos:
        if auto:
            return "收割：加入手动精准投放 + 在本自动活动否定精准", "P1", f"{od} 单，ACoS {a:.1%} ≤ 目标 {t_acos:.0%}", None
        if cvr > 0.15 and im < 1000 and cl >= max(G["bid_up_min_clicks"], G["bid_change_min_clicks"]):
            return f"提价{G['bid_up_pct']:.0%}", "P1", f"高转化低曝光：CVR {cvr:.0%}、展示 {im}、{od} 单、{cl} 次点击", G["bid_up_pct"]
        return "保持（达标）", "", f"{od} 单，ACoS {a:.1%} ≤ 目标", None

    # 3) 高花费低转化
    if sp > 50 and cvr < 0.05 and bid_ok:
        return f"暂停或降价{G['max_bid_cut']:.0%}", "P0", f"花费 ${sp} > $50 且 CVR {cvr:.1%} < 5%", -G["max_bid_cut"]

    # 4) 高 ACoS → 降价（≥20 次点击；幅度 = 1 - 目标/实际，封顶 25%）
    if a is not None and a > t_acos * 1.5:
        if bid_ok:
            cut = round(min(G["max_bid_cut"], 1 - t_acos / a), 2)
            return f"降价{cut:.0%}", "P1", f"ACoS {a:.0%} > 目标×1.5，{cl} 次点击", -cut
        if od == 1:
            return "收割观察：1 单样本不足，可低价加入手动精准，不调价", "P2", f"{cl} 次点击 1 单，ACoS {a:.0%}；<{G['bid_change_min_clicks']} 次点击不调价", None
        return "观察（ACoS 偏高但样本不足，不调价）", "P2", f"ACoS {a:.0%}，仅 {cl} 次点击（<{G['bid_change_min_clicks']}）", None

    # 5) 高转化低曝光 → 提价（≥2 单 且 ≥10 次点击 且满足 ≥20 次点击调价门槛）
    if cvr > 0.15 and im < 1000 and od >= G["bid_up_min_orders"] and cl >= G["bid_up_min_clicks"] and bid_ok:
        return f"提价{G['bid_up_pct']:.0%}", "P1", f"高转化低曝光：CVR {cvr:.0%}、展示 {im}、{od} 单、{cl} 次点击", G["bid_up_pct"]

    # 6) 低 CTR（花费型规则，不受点击门槛影响）
    if ctr < 0.003 and sp > 30:
        return "优化主图/标题或暂停", "P1", f"CTR {ctr:.2%} < 0.3% 且花费 ${sp} > $30", None

    # 7) 1 单：收割观察
    if od == 1:
        return "收割观察：1 单样本不足，可低价加入手动精准，不提价", "P2", f"{cl} 次点击 1 单（<{G['harvest_min_orders']} 单收割门槛）", None
    return "保持", "", "", None


def campaign_action(k, t_acos, t_cpa):
    """活动级动作（同一套样本门槛）：返回 (建议动作, 优先级, 依据, 调价比例或 None)"""
    G = GATES
    sp, cl, od, a, cvr = k["花费"], k["点击"], k["订单"], k["ACOS"], k["CVR"] or 0
    bid_ok = cl >= G["bid_change_min_clicks"]
    if sp <= 0:
        return "", "", "", None
    if od == 0:
        if cl >= G["negate_min_clicks"] or (t_cpa and sp >= G["negate_cpa_multiple"] * t_cpa):
            return f"暂停活动，或默认竞价降{G['max_bid_cut']:.0%}后复查", "P0" if sp > 20 else "P1", f"{cl} 次点击 0 单，花费 ${sp}", -G["max_bid_cut"]
        return "保持（样本不足）", "", f"0 单但仅 {cl} 次点击", None
    if sp > 50 and cvr < 0.05 and bid_ok:
        return f"暂停或降价{G['max_bid_cut']:.0%}", "P0", f"花费 ${sp} > $50 且 CVR {cvr:.1%} < 5%", -G["max_bid_cut"]
    if a is not None and a > t_acos * 1.5:
        if bid_ok:
            cut = round(min(G["max_bid_cut"], 1 - t_acos / a), 2)
            return f"默认竞价降{cut:.0%}", "P1", f"ACoS {a:.0%} > 目标×1.5，{cl} 次点击（按 1-目标/实际，封顶 {G['max_bid_cut']:.0%}）", -cut
        return "观察（样本不足，不调价）", "P2", f"ACoS {a:.0%}，仅 {cl} 次点击", None
    return "保持", "", "", None


def split_terms(s):
    return [w.strip().lower() for w in (s or "").split(",") if w.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("report")
    ap.add_argument("--asin", default="")
    ap.add_argument("--target-acos", type=norm_acos, default=0.30, help="30 或 0.30 均可（>1 视为百分数）")
    ap.add_argument("--target-roas", type=float, default=3.0)
    ap.add_argument("--target-cpa", type=float, default=None, help="目标 CPA；缺省 = 报告平均客单价 × 目标 ACoS")
    ap.add_argument("--days", type=int, default=7, help="报告覆盖天数（仅记录）")
    ap.add_argument("--protect-terms", default="", help="核心相关词（逗号分隔）：达到否定门槛也不直接否，改为降价/单独测试")
    ap.add_argument("--irrelevant-terms", default="", help="明显无关词（逗号分隔）：<10 次点击时标记人工复核")
    ap.add_argument("--competitor-brands", default="", help="竞品品牌词（逗号分隔）：<10 次点击时标记人工复核")
    ap.add_argument("--campaign-report", default=None, help="可选：广告活动报告（全量花费），用于总览与活动级动作")
    ap.add_argument("-o", "--output", default="ads_diagnosis.json")
    a = ap.parse_args()
    df, colmap = load(a.report)
    ov = kpis(df)
    aov = ov["销售额"] / ov["订单"] if ov["订单"] else None
    t_cpa = a.target_cpa or (round(aov * a.target_acos, 2) if aov else None)
    ctx0 = {"protect": split_terms(a.protect_terms), "irrelevant": split_terms(a.irrelevant_terms),
            "competitor": split_terms(a.competitor_brands), "target_cpa": t_cpa,
            "search_term_report": str(colmap.get("term", "")).lower().strip() in ALIASES["term"][:4]}
    res = {"asin": a.asin, "source": a.report, "days": a.days,
           "target_acos": a.target_acos, "target_acos_pct": round(a.target_acos * 100, 2), "target_roas": a.target_roas,
           "target_cpa": t_cpa, "target_cpa_note": "缺省 = 报告平均客单价 × 目标 ACoS" if not a.target_cpa else "用户提供",
           "rules_version": "2026-10-25-sample-gates", "gates": GATES,
           "term_lists": {k: ctx0[k] for k in ("protect", "irrelevant", "competitor")},
           "overview": ov, "campaigns": [], "keywords": []}
    cdf = df
    if a.campaign_report:
        cdf, _ = load(a.campaign_report)
        res["overview_term_report"] = ov
        res["overview"] = kpis(cdf)
        res["campaign_source"] = a.campaign_report
    for name, g in cdf.groupby("campaign"):
        k = kpis(g)
        if k["花费"] <= 0 and k["展示"] <= 0:
            continue
        act, pri, why, pct = campaign_action(k, a.target_acos, t_cpa)
        k.update({"Campaign 名称": name, "健康度": health(k, a.target_acos, a.target_roas),
                  "建议动作": act, "优先级": pri, "依据": why, "建议调价比例": pct})
        res["campaigns"].append(k)
    res["campaigns_total_rows"] = int(cdf["campaign"].nunique())
    if "term" in df:
        keys = [c for c in ("campaign", "ad_group", "term", "match") if c in df]
        for key, g in df.groupby(keys, dropna=False):
            key = dict(zip(keys, key if isinstance(key, tuple) else (key,)))
            k = kpis(g)
            k.update({"关键词": key.get("term"), "Campaign": key.get("campaign"), "Ad Group": key.get("ad_group", ""),
                      "匹配类型": key.get("match", "")})
            ctx = dict(ctx0, auto=is_auto(key.get("campaign"), key.get("match", "")))
            act, pri, why, pct = kw_action(k, a.target_acos, ctx)
            k.update({"建议动作": act, "优先级": pri, "依据": why, "自动活动": ctx["auto"]})
            if "bid" in g:
                b = float(g["bid"].max()); k["出价"] = b
                k["建议出价"] = round(b * (1 + pct), 2) if pct is not None and b else None
            res["keywords"].append(k)
        order = {"P0": 0, "P1": 1, "P2": 2, "": 3}
        res["keywords"].sort(key=lambda x: (order.get(x["优先级"], 9), -x["花费"]))
    res["campaigns"].sort(key=lambda x: -(x["ACOS"] or 9))
    summ = {}
    for k in res["keywords"]:
        tag = re.sub(r"[（(].*$", "", k["建议动作"]).split("：")[0]
        summ[tag] = summ.get(tag, 0) + 1
    res["action_summary"] = summ
    json.dump(res, open(a.output, "w", encoding="utf-8"), ensure_ascii=False, indent=2, default=str)
    o = res["overview"]
    print(f"✅ {len(res['campaigns'])} 个 Campaign / {len(res['keywords'])} 个搜索词 | 花费 ${o['花费']} | ACOS {o['ACOS']} | 目标 ACoS {a.target_acos:.0%} | 目标 CPA {t_cpa} → {a.output}")
    for p in ("P0", "P1", "P2"):
        print(f"   {p}: {sum(1 for k in res['keywords'] if k['优先级'] == p)} 条")
    print("   动作分布:", json.dumps(summ, ensure_ascii=False))


if __name__ == "__main__":
    main()
