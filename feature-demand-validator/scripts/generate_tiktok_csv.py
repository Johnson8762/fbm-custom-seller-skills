#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_tiktok_csv.py — 将 TikTok 电商数据导出为标准 CSV。

用法:
    python generate_tiktok_csv.py --data tiktok.json --source-ref "tiktok_similar:custom dog shirt" --output 08_tiktok.csv

输入 JSON 格式:
    {
        "query": "custom dog shirt",
        "products": [
            {
                "product_id": "123456",
                "title": "Custom Dog Shirt Personalized",
                "price": 15.99,
                "total_sales": 5000,
                "month_sales": 800,
                "rating": 4.7,
                "video_count": 25,
                "author_count": 10,
                "category": "Pet Supplies"
            }
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
    "产品ID", "产品标题", "价格", "总销量", "月销量",
    "星级", "带货视频数", "带货达人数", "品类",
    "数据来源", "来源类型", "来源链接/查询词", "原始文件名", "采集时间",
]


def process_tiktok_data(data: dict, source_ref: str, raw_file: str,
                        captured_at: str | None = None) -> list[dict]:
    rows: list[dict] = []
    captured_at = captured_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_type = data.get("source_type", "sorftime_mcp")
    source_tool = data.get("source_tool", "mcp_sorftime_tiktok_similar_product")

    for p in data.get("products", []):
        rows.append({
            "产品ID": p.get("product_id", ""),
            "产品标题": p.get("title", ""),
            "价格": p.get("price", ""),
            "总销量": p.get("total_sales", ""),
            "月销量": p.get("month_sales", ""),
            "星级": p.get("rating", ""),
            "带货视频数": p.get("video_count", ""),
            "带货达人数": p.get("author_count", ""),
            "品类": p.get("category", ""),
            "数据来源": source_tool, "来源类型": source_type,
            "来源链接/查询词": source_ref, "原始文件名": raw_file,
            "采集时间": captured_at,
        })

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="TikTok 电商数据导出为标准 CSV")
    parser.add_argument("--data", required=True, help="TikTok 数据 JSON 文件")
    parser.add_argument("--source-ref", default="", help="来源标识")
    parser.add_argument("--raw-file", default=None, help="原始文件名")
    parser.add_argument("--captured-at", default=None, help="采集时间")
    parser.add_argument("--output", required=True, help="输出 CSV 路径")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = process_tiktok_data(
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
