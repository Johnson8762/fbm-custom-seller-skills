#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""parse_reviews.py — 解析 Sorftime product_reviews 返回数据，筛选相关评论并导出 CSV。

支持两种模式:
  --mode feature   (默认) 原功能微创新模式
  --mode custom    定制化产品需求验证模式（按子维度分类）

定制化模式用法:
    python parse_reviews.py --mode custom --input reviews.json --asin B0XXXXXX12 \\
        --keywords-file custom_keywords.json --output 01_review.csv

功能模式用法（向后兼容）:
    python parse_reviews.py --input reviews.json --asin B0XXXXXX12 \\
        --keywords "steam,steamer" --output 01_review.csv

输入:
    Sorftime product_reviews 的 JSON 返回文件（支持嵌套结构和直接数组）

输出:
    - CSV 文件（列定义见 references/csv_schema.md）
    - stdout: JSON 格式统计摘要
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path

# ── 默认关键词 ──────────────────────────────────────────────────────

DEFAULT_DEMAND_SIGNALS = [
    "wish it had", "wish it could", "would be nice if",
    "missing", "if only", "should have", "needs a",
    "wish there was", "would love", "i want", "i wish",
]

DEFAULT_MOISTURE_KEYWORDS = [
    "moisture", "moist", "humid",
    "dry out", "dries out", "too dry", "dried out",
]

# ── 定制化模式默认子维度关键词 ────────────────────────────────────────

DEFAULT_CUSTOM_SUBDIMENSIONS = {
    "材质需求": [
        "cotton", "polyester", "breathable", "soft", "organic",
        "material quality", "fabric", "mesh", "nylon", "fleece", "stretchy",
    ],
    "定制形式": [
        "name", "photo", "logo", "text", "embroidered", "embroidery",
        "printed", "print", "sublimation", "custom design", "personalize",
        "monogram", "engraved",
    ],
    "工艺质量": [
        "print quality", "fade", "faded", "wash", "peel", "peeling",
        "crack", "cracked", "color", "lasting", "durable", "blurry", "blur",
        "smudge", "crooked", "misaligned", "cheap looking",
    ],
    "尺码合身": [
        "size", "sizing", "fit", "too small", "too big", "too large",
        "too tight", "sizing chart", "measure", "doesn't fit", "doesnt fit",
        "snug", "loose", "runs small", "runs large",
    ],
    "设计满意度": [
        "cute", "adorable", "love the design", "exactly what I wanted",
        "looks great", "perfect", "beautiful", "amazing quality",
        "exceeded expectations", "disappointed", "not what expected",
        "looks different", "ugly", "nothing like the picture",
        "poor quality", "false advertising",
    ],
    "排除维度:交付周期": [
        "shipping", "delivery", "arrived late", "took forever",
        "slow shipping", "fast delivery", "quick shipping",
    ],
}

# ── CSV 列定义 ──────────────────────────────────────────────────────

CSV_COLUMNS_FEATURE = [
    "ASIN", "评论日期", "星级", "评论内容",
    "功能相关(Y/N)", "情感(正/负/中)", "功能直接提及", "水分/干燥提及",
    "需求信号", "数据来源", "来源类型", "来源链接/查询词", "原始文件名", "采集时间",
]

CSV_COLUMNS_CUSTOM = [
    "ASIN", "产品组别", "评论日期", "星级", "评论内容",
    "定制化相关(Y/N)", "子维度分类", "情感(正/负/中)", "需求信号",
    "数据来源", "来源类型", "来源链接/查询词", "原始文件名", "采集时间",
]


# ── 核心函数 ─────────────────────────────────────────────────────────

def load_reviews(path: str) -> list[dict]:
    """读取 Sorftime product_reviews 的 JSON，兼容嵌套结构。"""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        if isinstance(first, dict) and "text" in first:
            text = first["text"]
            idx = text.find("[")
            if idx >= 0:
                return json.loads(text[idx:])
        elif "评论" in first or "评星" in first:
            return data

    return data


def default_captured_at() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def classify_sentiment(rating: float) -> str:
    if rating >= 4:
        return "正"
    if rating >= 3:
        return "中"
    return "负"


def matches_any(text: str, keywords: list[str]) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def classify_subdimension(text: str, subdimensions: dict[str, list[str]]) -> list[str]:
    """返回一条 Review 命中的所有子维度名称。"""
    matched = []
    for dim_name, keywords in subdimensions.items():
        if matches_any(text, keywords):
            matched.append(dim_name)
    return matched if matched else ["无关"]


# ── Feature 模式处理（向后兼容）──────────────────────────────────────

def process_reviews_feature(
    reviews: list[dict],
    asin: str,
    feature_keywords: list[str],
    moisture_keywords: list[str],
    demand_signals: list[str],
    source_tool: str = "mcp_sorftime_product_reviews",
    source_type: str = "sorftime_mcp",
    source_ref: str = "",
    raw_file: str = "",
    captured_at: str | None = None,
) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    captured_at = captured_at or default_captured_at()
    stats = {
        "total": len(reviews), "feature_mentions": 0,
        "moisture_mentions": 0, "demand_signals": 0,
        "positive_feature": 0, "negative_feature": 0, "neutral_feature": 0,
    }

    for r in reviews:
        title = r.get("标题", "")
        body = r.get("评论", "")
        text = f"{title} {body}"
        rating = float(r.get("评星", 0))
        date = r.get("评论日期", "")
        sentiment = classify_sentiment(rating)

        is_feature = matches_any(text, feature_keywords)
        is_moisture = matches_any(text, moisture_keywords)
        is_demand = matches_any(text, demand_signals)
        func_related = "Y" if (is_feature or is_moisture) else "N"

        if is_feature:
            stats["feature_mentions"] += 1
            if sentiment == "正": stats["positive_feature"] += 1
            elif sentiment == "负": stats["negative_feature"] += 1
            else: stats["neutral_feature"] += 1
        if is_moisture: stats["moisture_mentions"] += 1
        if is_demand: stats["demand_signals"] += 1

        rows.append({
            "ASIN": asin, "评论日期": date, "星级": rating,
            "评论内容": f"{title}: {body}"[:300],
            "功能相关(Y/N)": func_related, "情感(正/负/中)": sentiment,
            "功能直接提及": "Y" if is_feature else "N",
            "水分/干燥提及": "Y" if is_moisture else "N",
            "需求信号": "Y" if is_demand else "N",
            "数据来源": r.get("__source_tool", source_tool),
            "来源类型": r.get("__source_type", source_type),
            "来源链接/查询词": r.get("__source_ref", source_ref),
            "原始文件名": r.get("__raw_file", raw_file),
            "采集时间": r.get("__captured_at", captured_at),
        })

    return rows, stats


# ── Custom 模式处理 ──────────────────────────────────────────────────

def process_reviews_custom(
    reviews: list[dict],
    asin: str,
    subdimensions: dict[str, list[str]],
    demand_signals: list[str],
    product_group: str = "A组:定制化产品",
    source_tool: str = "mcp_sorftime_product_reviews",
    source_type: str = "sorftime_mcp",
    source_ref: str = "",
    raw_file: str = "",
    captured_at: str | None = None,
) -> tuple[list[dict], dict]:
    rows: list[dict] = []
    captured_at = captured_at or default_captured_at()

    # 按子维度统计
    dim_stats = {name: 0 for name in subdimensions}
    dim_stats["无关"] = 0
    stats = {
        "total": len(reviews), "custom_related": 0,
        "demand_signals": 0, "subdimension_stats": dim_stats,
    }

    for r in reviews:
        title = r.get("标题", "")
        body = r.get("评论", "")
        text = f"{title} {body}"
        rating = float(r.get("评星", 0))
        date = r.get("评论日期", "")
        sentiment = classify_sentiment(rating)

        matched_dims = classify_subdimension(text, subdimensions)
        is_custom = any(d != "无关" and not d.startswith("排除维度") for d in matched_dims)
        is_demand = matches_any(text, demand_signals)

        if is_custom:
            stats["custom_related"] += 1
        if is_demand:
            stats["demand_signals"] += 1

        for dim in matched_dims:
            dim_stats[dim] = dim_stats.get(dim, 0) + 1

        rows.append({
            "ASIN": asin,
            "产品组别": r.get("__product_group", product_group),
            "评论日期": date, "星级": rating,
            "评论内容": f"{title}: {body}"[:300],
            "定制化相关(Y/N)": "Y" if is_custom else "N",
            "子维度分类": "|".join(matched_dims),
            "情感(正/负/中)": sentiment,
            "需求信号": "Y" if is_demand else "N",
            "数据来源": r.get("__source_tool", source_tool),
            "来源类型": r.get("__source_type", source_type),
            "来源链接/查询词": r.get("__source_ref", source_ref),
            "原始文件名": r.get("__raw_file", raw_file),
            "采集时间": r.get("__captured_at", captured_at),
        })

    return rows, stats


def load_custom_keywords(path: str) -> dict[str, list[str]]:
    """加载自定义子维度关键词配置。"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_csv(rows: list[dict], output_path: str, columns: list[str] | None = None) -> None:
    columns = columns or CSV_COLUMNS_FEATURE
    if not rows:
        print(json.dumps({"error": "no data to write"}))
        return
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


# 兼容旧接口（parse_review_source_pack.py 仍按 feature 模式调用）
process_reviews = process_reviews_feature


# ── CLI ──────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="解析 Sorftime product_reviews，筛选相关评论并导出 CSV",
    )
    parser.add_argument("--mode", choices=["feature", "custom"], default="feature",
                        help="分析模式: feature=功能微创新, custom=定制化产品 (默认: feature)")
    parser.add_argument("--input", required=True, help="Sorftime reviews JSON 文件路径")
    parser.add_argument("--asin", required=True, help="产品 ASIN")
    parser.add_argument("--keywords", default=None,
                        help="[feature模式] 功能关键词（逗号分隔）")
    parser.add_argument("--keywords-file", default=None,
                        help="[custom模式] 子维度关键词 JSON 配置文件路径")
    parser.add_argument("--product-group", default="A组:定制化产品",
                        help="[custom模式] 产品组别标签 (默认: A组:定制化产品)")
    parser.add_argument("--moisture-keywords", default=None,
                        help="[feature模式] 水分/干燥关键词（逗号分隔）")
    parser.add_argument("--source-url", default="", help="来源链接或查询词")
    parser.add_argument("--source-type", default="sorftime_mcp", help="来源类型")
    parser.add_argument("--raw-file", default=None, help="原始文件名")
    parser.add_argument("--captured-at", default=None, help="采集时间")
    parser.add_argument("--output", required=True, help="输出 CSV 路径")
    args = parser.parse_args()

    reviews = load_reviews(args.input)

    if args.mode == "custom":
        # 定制化模式
        if args.keywords_file:
            subdimensions = load_custom_keywords(args.keywords_file)
        else:
            subdimensions = DEFAULT_CUSTOM_SUBDIMENSIONS

        rows, stats = process_reviews_custom(
            reviews, args.asin, subdimensions, DEFAULT_DEMAND_SIGNALS,
            product_group=args.product_group,
            source_type=args.source_type,
            source_ref=args.source_url,
            raw_file=args.raw_file or Path(args.input).name,
            captured_at=args.captured_at,
        )
        write_csv(rows, args.output, CSV_COLUMNS_CUSTOM)
    else:
        # 功能模式（向后兼容）
        if not args.keywords:
            parser.error("feature 模式必须提供 --keywords")
        feature_kws = [k.strip() for k in args.keywords.split(",") if k.strip()]
        moisture_kws = (
            [k.strip() for k in args.moisture_keywords.split(",") if k.strip()]
            if args.moisture_keywords else DEFAULT_MOISTURE_KEYWORDS
        )
        rows, stats = process_reviews_feature(
            reviews, args.asin, feature_kws, moisture_kws, DEFAULT_DEMAND_SIGNALS,
            source_type=args.source_type,
            source_ref=args.source_url,
            raw_file=args.raw_file or Path(args.input).name,
            captured_at=args.captured_at,
        )
        write_csv(rows, args.output, CSV_COLUMNS_FEATURE)

    stats["csv_path"] = args.output
    stats["csv_rows"] = len(rows)
    print(json.dumps(stats, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
