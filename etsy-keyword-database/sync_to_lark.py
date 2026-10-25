#!/usr/bin/env python3
"""
飞书多维表格同步脚本
合并 Etsy 和 EverBee 数据，计算蓝海指数，同步到飞书表格
"""

import json
import sys
import argparse
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "_shared"))
from feishu_bitable import Client, ts_ms  # noqa: E402

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lark_config.json")
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

def calculate_competition_score(search_volume: int, listing_count: int) -> float:
    """
    计算竞争度评分（0-100）

    Args:
        search_volume: 搜索量
        listing_count: Listing 数量

    Returns:
        竞争度评分
    """
    if search_volume == 0:
        return 100.0

    # 竞争度 = (Listing数量 / 搜索量) * 100
    # 归一化到 0-100
    ratio = (listing_count / search_volume) * 100
    return min(ratio * 10, 100.0)

def calculate_blue_ocean_index(search_volume: int, listing_count: int, competition_score: float) -> float:
    """
    计算蓝海指数

    Args:
        search_volume: 搜索量
        listing_count: Listing 数量
        competition_score: 竞争度评分

    Returns:
        蓝海指数
    """
    if listing_count == 0:
        return 0.0

    # 基础指数
    base_index = search_volume / listing_count

    # 权重系数
    if search_volume > 10000 and listing_count < 500:
        weight = 1.5
    elif 5000 <= search_volume <= 10000 and listing_count < 1000:
        weight = 1.2
    elif 1000 <= search_volume < 5000 and listing_count < 2000:
        weight = 1.0
    else:
        weight = 0.8

    return base_index * weight

def get_rating(blue_ocean_index: float) -> str:
    """
    根据蓝海指数获取评级

    Args:
        blue_ocean_index: 蓝海指数

    Returns:
        评级字符串
    """
    if blue_ocean_index > 20:
        return "⭐⭐⭐"
    elif blue_ocean_index >= 10:
        return "⭐⭐"
    elif blue_ocean_index >= 5:
        return "⭐"
    else:
        return "❌"

def merge_data(etsy_data: Dict, everbee_data: Dict) -> List[Dict[str, Any]]:
    """
    合并 Etsy 和 EverBee 数据

    Args:
        etsy_data: Etsy 数据字典
        everbee_data: EverBee 数据字典

    Returns:
        合并后的数据列表
    """
    # 创建关键词索引
    etsy_map = {item['keyword']: item for item in etsy_data.get('data', [])}
    everbee_map = {item['keyword']: item for item in everbee_data.get('data', [])}

    # 获取所有关键词
    all_keywords = set(etsy_map.keys()) | set(everbee_map.keys())

    merged = []

    for keyword in all_keywords:
        etsy_item = etsy_map.get(keyword, {})
        everbee_item = everbee_map.get(keyword, {})

        # 提取数据
        search_volume = everbee_item.get('search_volume', 0)
        listing_count = etsy_item.get('listing_count', 0)
        avg_price = etsy_item.get('avg_price') or everbee_item.get('avg_price', 0.0)

        # 计算指标
        competition_score = calculate_competition_score(search_volume, listing_count)
        blue_ocean_index = calculate_blue_ocean_index(search_volume, listing_count, competition_score)
        rating = get_rating(blue_ocean_index)

        # 确定数据来源
        if keyword in etsy_map and keyword in everbee_map:
            source = "混合"
        elif keyword in etsy_map:
            source = "Etsy"
        else:
            source = "EverBee"

        merged.append({
            "关键词": keyword,
            "搜索量": search_volume,
            "Listing数量": listing_count,
            "平均价格": round(avg_price, 2),
            "竞争度评分": round(competition_score, 1),
            "蓝海指数": round(blue_ocean_index, 2),
            "评级": rating,
            "数据来源": source,
            "更新时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "备注": ""
        })

    # 按蓝海指数降序排序
    merged.sort(key=lambda x: x['蓝海指数'], reverse=True)

    return merged

FIELDS = [
    {"field_name": "关键词", "type": 1},
    {"field_name": "搜索量", "type": 2},
    {"field_name": "Listing数量", "type": 2},
    {"field_name": "平均价格", "type": 2, "property": {"formatter": "0.00"}},
    {"field_name": "竞争度评分", "type": 2, "property": {"formatter": "0.0"}},
    {"field_name": "蓝海指数", "type": 2, "property": {"formatter": "0.00"}},
    {"field_name": "评级", "type": 1},
    {"field_name": "数据来源", "type": 3, "property": {"options": [{"name": "Etsy"}, {"name": "EverBee"}, {"name": "混合"}]}},
    {"field_name": "更新时间", "type": 5, "property": {"date_formatter": "yyyy/MM/dd HH:mm"}},
    {"field_name": "备注", "type": 1},
]


VIEWS = [("蓝海机会", "isGreater", "15"), ("待验证", "isGreater", "10"), ("红海预警", "isLess", "5")]


def _setup_views(cli, tid):
    """建 3 个视图 + 蓝海指数筛选。飞书 API 不支持视图排序/分组 → 提示用户在 UI 里手动设置。"""
    vids = {n: cli.create_view(tid, n) for n, _, _ in VIEWS}
    if cli.dry:
        return
    try:
        fid = next(f["field_id"] for f in cli.fields(tid) if f["field_name"] == "蓝海指数")
        for n, op, v in VIEWS:
            cli.set_view_filter(tid, vids[n], fid, op, json.dumps(v))
    except Exception as e:
        print(f"⚠️ 视图筛选设置失败（可在飞书 UI 手动设置）: {e}")
    print("ℹ️ 视图排序/分组需在飞书里手动设置：蓝海机会按蓝海指数降序，待验证按搜索量降序（「待验证」上限 15 也需手动加）")


def setup_table(name="Etsy 关键词数据库", dry_run=False):
    """新建多维表格 + 表（自动把所有权转给用户 open_id）。"""
    cli = Client(dry_run=dry_run)
    app_token, url = cli.create_app(name)  # 内部已 transfer_owner 给用户
    tid = cli.create_table("关键词库", FIELDS)
    _setup_views(cli, tid)
    cfg = {"app_token": app_token, "table_id": tid, "url": url}
    if not dry_run:
        json.dump(cfg, open(CONFIG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return cfg


def sync_to_lark_table(data, app_token, table_id, dry_run=False):
    """按「关键词」upsert：已存在 → batch_update；不存在 → batch_create。从不删除记录。"""
    cli = Client(app_token=app_token, dry_run=dry_run)
    now = ts_ms()
    rows = []
    for d in data:
        f = dict(d); f["更新时间"] = now  # 日期字段需要毫秒时间戳（原版传字符串会失败）
        rows.append(f)
    existing = {}
    if not dry_run:
        cli.ensure_fields(table_id, FIELDS)
        for r in cli.list_records(table_id, field_names=["关键词"]):
            kw = r["fields"].get("关键词")
            if isinstance(kw, list):
                kw = "".join(x.get("text", "") for x in kw)
            if kw:
                existing[kw] = r["record_id"]
    upd = [{"record_id": existing[r["关键词"]], "fields": r} for r in rows if r["关键词"] in existing]
    new = [r for r in rows if r["关键词"] not in existing]
    if upd:
        cli.batch_update(table_id, upd)
    if new:
        cli.batch_create(table_id, new)
    print(f"✅ 同步完成：新增 {len(new)} / 更新 {len(upd)}" + ("（DRY-RUN，未写入）" if dry_run else ""))
    return True


def generate_report(data: List[Dict]) -> str:
    """
    生成蓝海关键词分析报告

    Args:
        data: 合并后的数据

    Returns:
        报告文本
    """
    high_value = [d for d in data if d['蓝海指数'] > 20]
    medium_value = [d for d in data if 10 <= d['蓝海指数'] <= 20]
    red_ocean = [d for d in data if d['蓝海指数'] < 5]

    report = f"""
=== Etsy 蓝海关键词分析报告 ===
生成时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

【高价值蓝海】（蓝海指数 > 20）
"""

    for i, item in enumerate(high_value[:5], 1):
        report += f"""
{i}. {item['关键词']} - 指数 {item['蓝海指数']} {item['评级']}
   搜索量：{item['搜索量']:,} | Listing：{item['Listing数量']:,} | 价格：${item['平均价格']}
"""

    if not high_value:
        report += "\n   暂无高价值蓝海关键词\n"

    report += f"""
【中等机会】（蓝海指数 10-20）
"""

    for i, item in enumerate(medium_value[:5], 1):
        report += f"{i}. {item['关键词']} - 指数 {item['蓝海指数']} {item['评级']}\n"

    if not medium_value:
        report += "   暂无中等机会关键词\n"

    report += f"""
【红海预警】（蓝海指数 < 5）
"""

    for item in red_ocean[:3]:
        report += f"- {item['关键词']} - 指数 {item['蓝海指数']} {item['评级']}\n"

    if not red_ocean:
        report += "   暂无红海关键词\n"

    report += f"""
【总结】
- 共分析 {len(data)} 个关键词
- 发现 {len(high_value)} 个高价值蓝海
- 建议主推：{high_value[0]['关键词'] if high_value else '暂无'}
"""

    return report

def main():
    ap = argparse.ArgumentParser(description="Etsy 关键词库：合并 + 蓝海指数 + 同步飞书")
    ap.add_argument("--etsy", help="fetch_etsy_data.py 输出 JSON")
    ap.add_argument("--everbee", help="import_everbee.py 输出 JSON（可选）")
    ap.add_argument("--app-token", help="飞书多维表格 app_token（默认读 lark_config.json）")
    ap.add_argument("--table-id")
    ap.add_argument("--setup", action="store_true", help="新建多维表格（所有权转给用户）")
    ap.add_argument("--name", default="Etsy 关键词数据库")
    ap.add_argument("--report", default="reports/etsy-keyword-db/keyword_report.txt")
    ap.add_argument("--dry-run", action="store_true", help="不写飞书，只打印将写入的内容")
    a = ap.parse_args()
    if a.setup:
        print(json.dumps(setup_table(a.name, a.dry_run), ensure_ascii=False)); return
    if not (a.etsy or a.everbee):
        ap.error("至少需要 --etsy 或 --everbee")
    load = lambda p: json.load(open(p, encoding="utf-8")) if p else {"data": []}
    merged = merge_data(load(a.etsy), load(a.everbee))
    print(f"✅ 合并 {len(merged)} 个关键词")
    os.makedirs(os.path.dirname(a.report), exist_ok=True)
    rep = generate_report(merged); open(a.report, "w", encoding="utf-8").write(rep); print(rep)
    json.dump(merged, open(os.path.splitext(a.report)[0] + "_merged.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    app_token, table_id = a.app_token, a.table_id
    if not (app_token and table_id) and os.path.exists(CONFIG_PATH):
        c = json.load(open(CONFIG_PATH)); app_token = app_token or c["app_token"]; table_id = table_id or c["table_id"]
    if not (app_token and table_id):
        if a.dry_run:
            app_token, table_id = "dry_app", "dry_table"
        else:
            sys.exit("❌ 未配置飞书表格：先运行 --setup 或传 --app-token/--table-id")
    sync_to_lark_table(merged, app_token, table_id, dry_run=a.dry_run)


if __name__ == "__main__":
    main()
