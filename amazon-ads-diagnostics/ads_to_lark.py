#!/usr/bin/env python3
"""把 ads_csv_analyzer.py 的 JSON 写入一个新的飞书多维表格（总览 / Campaign 监控 / 动作清单）。
默认 dry-run（只打印将要发送的请求，不写任何数据）；加 --live 才真正创建。
新建的多维表格会自动 transfer_owner 给用户（open_id 见 环境变量 FEISHU_OWNER_OPEN_ID）。从不删除任何表格。
  python ads_to_lark.py reports/ads/B0XXX/analysis.json [--live]
target_acos：JSON 里存 0.30 或 30 都能正确读取（>1 视为百分数，与 ads_csv_analyzer.norm_acos 一致）。
"""
import argparse, json, os, sys, datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from feishu_bitable import Client

T, N = 1, 2
PCT = {"formatter": "0.00%"}
OV = [("ASIN", T), ("报告日期", T), ("花费", N), ("销售额", N), ("展示", N), ("点击", N), ("订单", N),
      ("ACOS", N, PCT), ("ROAS", N), ("CTR", N, PCT), ("CVR", N, PCT), ("目标ACOS", N, PCT), ("数据来源", T)]
CAMP = [("Campaign 名称", T), ("健康度", 3, {"options": [{"name": n} for n in ("健康", "警告", "异常")]}), ("花费", N), ("销售额", N),
        ("展示", N), ("点击", N), ("订单", N), ("ACOS", N, PCT), ("ROAS", N), ("CTR", N, PCT), ("CVR", N, PCT),
        ("建议动作", T), ("优先级", 3, {"options": [{"name": n} for n in ("P0", "P1", "P2")]}), ("依据", T)]
ACT = [("关键词", T), ("Campaign", T), ("Ad Group", T), ("匹配类型", T),
       ("优先级", 3, {"options": [{"name": n} for n in ("P0", "P1", "P2")]}), ("建议动作", T), ("依据", T),
       ("出价", N), ("建议出价", N), ("花费", N), ("点击", N), ("订单", N), ("ACOS", N, PCT), ("CVR", N, PCT), ("执行状态", T)]


def norm_acos(v):
    """30 / 0.30 / '30%' → 0.30（与 ads_csv_analyzer.py 相同口径）"""
    v = float(str(v).replace("%", "").strip())
    return round(v / 100, 6) if v > 1 else v


def fdef(spec):
    d = {"field_name": spec[0], "type": spec[1]}
    if len(spec) > 2:
        d["property"] = spec[2]
    return d

def row(src, spec):
    out = {}
    for s in spec:
        v = src.get(s[0])
        if v is None or v == "":
            continue
        out[s[0]] = float(v) if s[1] == N else str(v)
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("analysis")
    ap.add_argument("--live", action="store_true", help="真正写入（默认 dry-run）")
    ap.add_argument("--name", default=None)
    a = ap.parse_args()
    d = json.load(open(a.analysis, encoding="utf-8"))
    today = datetime.date.today().strftime("%Y%m%d")
    cli = Client(dry_run=not a.live)
    token, url = cli.create_app(a.name or f"ads-report-{d['asin']}-{today}")
    ov = dict(d["overview"], ASIN=d["asin"], 报告日期=today, 目标ACOS=norm_acos(d.get("target_acos", 0.30)), 数据来源=d.get("source", ""))
    acts = [dict(k, 执行状态="待执行") for k in d["keywords"] if k.get("优先级") in ("P0", "P1", "P2")]
    for name, spec, rows in [("总览", OV, [ov]), ("Campaign 监控", CAMP, d["campaigns"]), ("动作清单", ACT, acts)]:
        tid = cli.create_table(name, [fdef(s) for s in spec]) or "DRY_TABLE"
        cli.batch_create(tid, [row(r, spec) for r in rows])
    print(json.dumps({"dry_run": cli.dry, "app_token": "(dry)" if cli.dry else "created", "url": url,
                      "目标ACOS": ov["目标ACOS"], "动作清单行数": len(acts)}, ensure_ascii=False))

if __name__ == "__main__":
    main()
