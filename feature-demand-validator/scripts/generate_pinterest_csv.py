#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_pinterest_csv.py — 将 Pinterest Trends 数据导出为标准 CSV。

用法:
    python generate_pinterest_csv.py --data pinterest.json --source-ref "pinterest_trends:custom dog shirt" --output 06_pinterest.csv

输入 JSON 格式:
    {
        "query": "custom dog shirt",
        "trend_direction": "上升",
        "trend_period": "2025-04 至 2026-03",
        "related_terms": [
            {"term": "personalized dog apparel", "relevance": "高"},
            {"term": "custom pet clothing", "relevance": "中"}
        ],
        "hot_pins": [
            {"title": "Cute Custom Dog Shirt Ideas", "description": "..."}
        ]
    }
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

CSV_COLUMNS = [
    "查询词", "趋势方向", "趋势时间范围", "相关搜索词",
    "相关度(高/中/低)", "热门Pin内容摘要",
    "数据来源", "来源类型", "来源链接/查询词", "原始文件名", "采集时间",
]


def process_pinterest_data(data: dict, source_ref: str, raw_file: str,
                           captured_at: str | None = None) -> list[dict]:
    rows: list[dict] = []
    captured_at = captured_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = data.get("query", "")
    trend_dir = data.get("trend_direction", "")
    trend_period = data.get("trend_period", "")
    source_type = data.get("source_type", "pinterest_web")
    source_tool = data.get("source_tool", "pinterest_trends")

    for term in data.get("related_terms", []):
        rows.append({
            "查询词": query, "趋势方向": trend_dir, "趋势时间范围": trend_period,
            "相关搜索词": term.get("term", ""),
            "相关度(高/中/低)": term.get("relevance", "中"),
            "热门Pin内容摘要": "",
            "数据来源": source_tool, "来源类型": source_type,
            "来源链接/查询词": source_ref, "原始文件名": raw_file,
            "采集时间": captured_at,
        })

    for pin in data.get("hot_pins", []):
        rows.append({
            "查询词": query, "趋势方向": trend_dir, "趋势时间范围": trend_period,
            "相关搜索词": "", "相关度(高/中/低)": "",
            "热门Pin内容摘要": f"{pin.get('title', '')}: {pin.get('description', '')}"[:300],
            "数据来源": source_tool, "来源类型": source_type,
            "来源链接/查询词": source_ref, "原始文件名": raw_file,
            "采集时间": captured_at,
        })

    if not rows:
        rows.append({
            "查询词": query, "趋势方向": trend_dir, "趋势时间范围": trend_period,
            "相关搜索词": "", "相关度(高/中/低)": "", "热门Pin内容摘要": "",
            "数据来源": source_tool, "来源类型": source_type,
            "来源链接/查询词": source_ref, "原始文件名": raw_file,
            "采集时间": captured_at,
        })

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Pinterest Trends 数据导出为标准 CSV")
    parser.add_argument("--data", required=True, help="Pinterest 数据 JSON 文件")
    parser.add_argument("--source-ref", default="", help="来源标识")
    parser.add_argument("--raw-file", default=None, help="原始文件名")
    parser.add_argument("--captured-at", default=None, help="采集时间")
    parser.add_argument("--output", required=True, help="输出 CSV 路径")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = process_pinterest_data(
        data, args.source_ref,
        raw_file=args.raw_file or Path(args.data).name,
        captured_at=args.captured_at,
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps({"csv_path": args.output, "csv_rows": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
