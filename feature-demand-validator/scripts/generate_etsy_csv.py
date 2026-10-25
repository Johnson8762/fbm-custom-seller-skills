#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_etsy_csv.py — 将 Etsy 市场信号数据导出为标准 CSV。

用法:
    python generate_etsy_csv.py --data etsy.json --source-ref "etsy_search:custom dog shirt" --output 07_etsy.csv

输入 JSON 格式:
    {
        "query": "custom dog shirt",
        "competition_density": "搜索翻页约 35 页",
        "market_stage": "新兴市场",
        "products": [
            {
                "title": "Custom Dog Shirt with Name",
                "price": 24.99,
                "review_count": 1234,
                "rating": 4.8,
                "custom_options": "name, photo, color",
                "material": "cotton",
                "shop_name": "PetLoveShop",
                "shop_sales": 5000
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
    "查询词", "竞争密度评估", "市场阶段",
    "产品标题", "价格", "Review数量", "星级",
    "定制选项", "材质", "店铺名", "店铺销量",
    "数据来源", "来源类型", "来源链接/查询词", "原始文件名", "采集时间",
]


def process_etsy_data(data: dict, source_ref: str, raw_file: str,
                      captured_at: str | None = None) -> list[dict]:
    rows: list[dict] = []
    captured_at = captured_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    query = data.get("query", "")
    density = data.get("competition_density", "")
    market_stage = data.get("market_stage", "")
    source_type = data.get("source_type", "etsy_web")
    source_tool = data.get("source_tool", "etsy_search")

    for p in data.get("products", []):
        rows.append({
            "查询词": query, "竞争密度评估": density, "市场阶段": market_stage,
            "产品标题": p.get("title", ""),
            "价格": p.get("price", ""),
            "Review数量": p.get("review_count", ""),
            "星级": p.get("rating", ""),
            "定制选项": p.get("custom_options", ""),
            "材质": p.get("material", ""),
            "店铺名": p.get("shop_name", ""),
            "店铺销量": p.get("shop_sales", ""),
            "数据来源": source_tool, "来源类型": source_type,
            "来源链接/查询词": source_ref, "原始文件名": raw_file,
            "采集时间": captured_at,
        })

    if not rows:
        rows.append({
            "查询词": query, "竞争密度评估": density, "市场阶段": market_stage,
            "产品标题": "", "价格": "", "Review数量": "", "星级": "",
            "定制选项": "", "材质": "", "店铺名": "", "店铺销量": "",
            "数据来源": source_tool, "来源类型": source_type,
            "来源链接/查询词": source_ref, "原始文件名": raw_file,
            "采集时间": captured_at,
        })

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Etsy 市场数据导出为标准 CSV")
    parser.add_argument("--data", required=True, help="Etsy 数据 JSON 文件")
    parser.add_argument("--source-ref", default="", help="来源标识")
    parser.add_argument("--raw-file", default=None, help="原始文件名")
    parser.add_argument("--captured-at", default=None, help="采集时间")
    parser.add_argument("--output", required=True, help="输出 CSV 路径")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = process_etsy_data(
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
