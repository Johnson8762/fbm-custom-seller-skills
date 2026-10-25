#!/usr/bin/env python3
"""
EverBee CSV 导入脚本
解析 EverBee 导出的 CSV 文件，标准化数据格式
"""

import csv
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

def parse_everbee_csv(csv_file: str) -> List[Dict[str, Any]]:
    """
    解析 EverBee CSV 文件

    Args:
        csv_file: CSV 文件路径

    Returns:
        标准化的数据列表
    """
    results = []

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            # 标准化字段名（EverBee 可能使用不同的列名）
            keyword = row.get('Keyword') or row.get('keyword') or row.get('Search Term')
            search_volume = row.get('Search Volume') or row.get('search_volume') or row.get('Volume')
            competition = row.get('Competition') or row.get('competition') or row.get('Comp')
            avg_price = row.get('Avg Price') or row.get('avg_price') or row.get('Price')

            if not keyword:
                continue

            # 清理数据
            try:
                search_volume = int(search_volume.replace(',', '')) if search_volume else 0
            except:
                search_volume = 0

            try:
                competition = float(competition) if competition else 0.0
            except:
                competition = 0.0

            try:
                avg_price = float(avg_price.replace('$', '').replace(',', '')) if avg_price else 0.0
            except:
                avg_price = 0.0

            results.append({
                "keyword": keyword.strip(),
                "search_volume": search_volume,
                "competition": competition,
                "avg_price": avg_price,
                "source": "everbee",
                "import_time": datetime.now().isoformat()
            })

    return results

def main():
    parser = argparse.ArgumentParser(description='EverBee CSV 导入工具')
    parser.add_argument('input', help='EverBee CSV 文件路径')
    parser.add_argument('-o', '--output', help='输出 JSON 文件路径', default='everbee_data.json')

    args = parser.parse_args()

    # 检查文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ 文件不存在: {args.input}")
        sys.exit(1)

    # 解析 CSV
    print(f"正在解析 EverBee CSV: {args.input}")
    data = parse_everbee_csv(args.input)

    if not data:
        print("❌ 未找到有效数据")
        sys.exit(1)

    # 保存结果
    output_data = {
        "total": len(data),
        "data": data,
        "generated_at": datetime.now().isoformat()
    }

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 成功导入 {len(data)} 个关键词")
    print(f"✅ 数据已保存到: {args.output}")

    # 显示统计信息
    total_volume = sum(d['search_volume'] for d in data)
    avg_volume = total_volume / len(data) if data else 0

    print(f"\n=== 数据统计 ===")
    print(f"总搜索量: {total_volume:,}")
    print(f"平均搜索量: {avg_volume:.0f}")
    print(f"最高搜索量: {max(d['search_volume'] for d in data):,}")
    print(f"最低搜索量: {min(d['search_volume'] for d in data):,}")

if __name__ == '__main__':
    main()
