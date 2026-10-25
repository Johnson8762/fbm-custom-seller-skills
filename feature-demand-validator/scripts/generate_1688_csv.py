#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generate_1688_csv.py — 将 1688 供应商数据导出为标准 CSV。

用法:
    python generate_1688_csv.py --data 1688.json --source-ref "1688_search:定制狗衣服" --output 09_1688.csv

输入 JSON 格式:
    {
        "query": "定制狗衣服",
        "suppliers": [
            {
                "supplier_name": "XX宠物用品厂",
                "product_title": "定制印花宠物T恤",
                "price_range": "8-15元",
                "moq": 50,
                "craft_types": "热转印,刺绣,丝网印",
                "supports_custom": true,
                "qualification": "实力商家",
                "product_url": "https://detail.1688.com/..."
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
    "供应商名称", "产品标题", "价格区间", "起订量",
    "支持工艺", "是否支持定制", "供应商资质", "产品链接",
    "数据来源", "来源类型", "来源链接/查询词", "原始文件名", "采集时间",
]


def process_1688_data(data: dict, source_ref: str, raw_file: str,
                      captured_at: str | None = None) -> list[dict]:
    rows: list[dict] = []
    captured_at = captured_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    source_type = data.get("source_type", "sorftime_mcp")
    source_tool = data.get("source_tool", "mcp_sorftime_ali1688_similar_product")

    for s in data.get("suppliers", []):
        rows.append({
            "供应商名称": s.get("supplier_name", ""),
            "产品标题": s.get("product_title", ""),
            "价格区间": s.get("price_range", ""),
            "起订量": s.get("moq", ""),
            "支持工艺": s.get("craft_types", ""),
            "是否支持定制": "Y" if s.get("supports_custom") else "N",
            "供应商资质": s.get("qualification", ""),
            "产品链接": s.get("product_url", ""),
            "数据来源": source_tool, "来源类型": source_type,
            "来源链接/查询词": source_ref, "原始文件名": raw_file,
            "采集时间": captured_at,
        })

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="1688 供应商数据导出为标准 CSV")
    parser.add_argument("--data", required=True, help="1688 数据 JSON 文件")
    parser.add_argument("--source-ref", default="", help="来源标识")
    parser.add_argument("--raw-file", default=None, help="原始文件名")
    parser.add_argument("--captured-at", default=None, help="采集时间")
    parser.add_argument("--output", required=True, help="输出 CSV 路径")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = process_1688_data(
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
