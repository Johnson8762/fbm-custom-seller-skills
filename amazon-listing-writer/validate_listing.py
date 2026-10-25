#!/usr/bin/env python3
"""
Listing-Skill 合规校验脚本

用法:
    python3 validate_listing.py --input <listing.md>
    python3 validate_listing.py --test-blacklist  (运行内置测试)

检查项:
    1. 违禁词检测 (促销词、医疗声明、农药声明等)
    2. 标题字符数限制 (200/125)
    3. Search Terms 字节数限制 (249)
    4. Emoji 检测
    5. 同一单词重复次数检测
    6. 禁用特殊字符检测
"""

import argparse
import re
import sys
from pathlib import Path


# ============================================================
# 违禁词库
# ============================================================

PROMOTIONAL_TERMS = [
    "best seller", "#1 product", "#1 best", "free shipping", "discount",
    "on sale", "limited offer", "limited time", "best price",
    "unbeatable price", "super sale", "spring sale", "summer sale",
    "winter sale", "fall sale", "huge sale", "special promo",
    "wholesale price", "perfect gift", "gift idea", "buy now",
    "act now", "don't miss", "hurry", "clearance", "closeout",
    "liquidation", "new arrival", "just launched", "limited stock",
    "only x left", "back in stock", "pre-order",
]

MEDICAL_TERMS = [
    "cure", "cures", "treat", "treats", "treatment",
    "heal", "heals", "healing", "diagnose", "diagnosis",
    "prevent", "prevents", "prevention", "remedy",
    "therapeutic", "medicinal", "prescription", "antibiotic",
    "anti-inflammatory", "pain relief", "pain killer",
    "pain management", "blood pressure", "cholesterol",
    "diabetes", "cancer", "arthritis", "anxiety", "depression",
    "adhd", "aids", "hiv", "immune deficiency",
]

UNVERIFIED_CLAIMS = [
    "fda approved", "epa registered", "clinically proven",
    "clinically tested", "dermatologist tested",
    "doctor recommended", "lab tested", "scientifically proven",
    "100% natural", "100% organic", "100% quality guaranteed",
    "100% satisfaction guaranteed", "100% value",
]

PESTICIDE_TERMS = [
    "kills", "repels", "disinfects", "disinfectant",
    "sanitizes", "sanitizer", "antibacterial", "antifungal",
    "antimicrobial", "antiviral", "germicidal", "pesticide",
    "insecticide", "herbicide", "fungicide",
    "mold resistant", "mildew resistant",
]

SUPERLATIVE_TERMS = [
    "world's best", "industry leading", "revolutionary",
    "groundbreaking", "unmatched", "unparalleled",
    "one of a kind", "best in class", "top rated",
    "most popular", "number one", "no. 1",
]

FORBIDDEN_CHARS_TITLE = set('!$?_{}^¬¦')

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols extended-A
    "\u200d"                 # zero width joiner
    "\ufe0f"                 # variation selector
    "\u2764"                 # heart
    "\u2716"                 # heavy multiplication X
    "\u2714"                 # heavy check mark
    "\u27a4"                 # arrow
    "\u25ba"                 # play button
    "\u2605\u2606"           # stars
    "]+",
    flags=re.UNICODE,
)


# ============================================================
# 解析 Listing 文件
# ============================================================

def extract_section(content: str, heading: str) -> str:
    """Extract content under a specific markdown heading."""
    # 修复：原版在 DOTALL 下用 .* 会跨行贪婪匹配导致永远取不到内容；标题行内改用 [^\n]*
    pattern = rf"^#+[ \t]*[^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=\n#+\s|\Z)"
    match = re.search(pattern, content, re.DOTALL | re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_title(content: str) -> str:
    """Try to extract the title section."""
    section = extract_section(content, "Title") or extract_section(content, "标题")
    # Look for a line that looks like a title (non-heading, non-empty)
    for line in section.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-') and not line.startswith('|'):
            # Remove markdown formatting
            clean = re.sub(r'[`*]', '', line)
            if len(clean) > 20:
                return clean
    return ""


def extract_search_terms(content: str) -> str:
    """Try to extract Search Terms section."""
    section = extract_section(content, "Search Terms") or extract_section(content, "搜索词")
    for line in section.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-') and not line.startswith('|') and not line.startswith('```'):
            clean = re.sub(r'[`*]', '', line)
            if len(clean) > 10:
                return clean
    return ""


# ============================================================
# 检查函数
# ============================================================

def check_forbidden_terms(text: str, term_list: list, category: str) -> list:
    """Check for forbidden terms in text using word-boundary matching."""
    violations = []
    text_lower = text.lower()
    for term in term_list:
        # Use word boundaries to avoid partial matches (e.g., "cure" in "securely")
        pattern = r'\b' + re.escape(term.lower()) + r'\b'
        for match in re.finditer(pattern, text_lower):
            idx = match.start()
            context = text[max(0, idx-20):idx+len(term)+20]
            violations.append({
                "category": category,
                "term": term,
                "context": f"...{context}...",
            })
    return violations


def check_title_length(title: str, is_apparel: bool = False) -> list:
    """Check title character count."""
    limit = 125 if is_apparel else 200
    violations = []
    if len(title) > limit:
        violations.append({
            "category": "标题长度",
            "term": f"{len(title)} 字符 (上限 {limit})",
            "context": title[:80] + "...",
        })
    return violations


def check_search_terms_bytes(st: str) -> list:
    """Check Search Terms byte count."""
    violations = []
    byte_count = len(st.encode('utf-8'))
    if byte_count > 249:
        violations.append({
            "category": "Search Terms 字节数",
            "term": f"{byte_count} bytes (上限 249)",
            "context": st[:80] + "...",
        })
    return violations


def check_emoji(text: str) -> list:
    """Check for emoji in text."""
    violations = []
    matches = EMOJI_PATTERN.findall(text)
    for m in matches:
        violations.append({
            "category": "Emoji",
            "term": repr(m),
            "context": f"发现 emoji: {m}",
        })
    return violations


def check_forbidden_chars_in_title(title: str) -> list:
    """Check for forbidden special characters in title."""
    violations = []
    for char in title:
        if char in FORBIDDEN_CHARS_TITLE:
            violations.append({
                "category": "禁用特殊字符",
                "term": repr(char),
                "context": f"标题中发现禁用字符: {char}",
            })
    return violations


def check_word_repetition(title: str, max_repeat: int = 2) -> list:
    """Check for word repetition in title."""
    violations = []
    # Exclude prepositions, articles, conjunctions
    skip_words = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were',
        'be', 'been', 'being', 'it', 'its', 'as', 'not', 'no',
    }
    words = re.findall(r'\b[a-zA-Z]+\b', title.lower())
    word_count = {}
    for w in words:
        if w not in skip_words:
            word_count[w] = word_count.get(w, 0) + 1
    for word, count in word_count.items():
        if count > max_repeat:
            violations.append({
                "category": "单词重复",
                "term": f"'{word}' 出现 {count} 次 (上限 {max_repeat})",
                "context": f"标题中 '{word}' 重复过多",
            })
    return violations


# ============================================================
# 主检查流程
# ============================================================

def validate_listing(filepath: str, is_apparel: bool = False) -> dict:
    """Run all checks on a listing file."""
    path = Path(filepath)
    if not path.exists():
        return {"status": "ERROR", "message": f"文件不存在: {filepath}"}

    content = path.read_text(encoding='utf-8')
    title = extract_title(content)
    search_terms = extract_search_terms(content)

    all_violations = []

    # Full content checks
    all_violations.extend(check_forbidden_terms(content, PROMOTIONAL_TERMS, "促销/营销词"))
    all_violations.extend(check_forbidden_terms(content, MEDICAL_TERMS, "医疗/健康声明"))
    all_violations.extend(check_forbidden_terms(content, UNVERIFIED_CLAIMS, "未经验证的声明"))
    all_violations.extend(check_forbidden_terms(content, PESTICIDE_TERMS, "农药/抗菌声明"))
    all_violations.extend(check_forbidden_terms(content, SUPERLATIVE_TERMS, "最高级表达"))
    all_violations.extend(check_emoji(content))

    # Title-specific checks
    if title:
        all_violations.extend(check_title_length(title, is_apparel))
        all_violations.extend(check_forbidden_chars_in_title(title))
        all_violations.extend(check_word_repetition(title))
    else:
        all_violations.append({
            "category": "结构",
            "term": "未找到标题",
            "context": "无法从文件中解析出标题部分",
        })

    # Search Terms checks
    if search_terms:
        all_violations.extend(check_search_terms_bytes(search_terms))
    else:
        all_violations.append({
            "category": "结构",
            "term": "未找到 Search Terms",
            "context": "无法从文件中解析出 Search Terms 部分",
        })

    status = "PASS" if not all_violations else "FAIL"

    return {
        "status": status,
        "violations_count": len(all_violations),
        "violations": all_violations,
        "title_length": len(title) if title else 0,
        "search_terms_bytes": len(search_terms.encode('utf-8')) if search_terms else 0,
    }


# ============================================================
# 内置测试
# ============================================================

def run_tests():
    """Run built-in test cases to verify blacklist detection."""
    print("=" * 60)
    print("Listing-Skill 违禁词检测测试")
    print("=" * 60)

    test_cases = [
        ("促销词检测", "This is the Best Seller product with Free Shipping!", True),
        ("医疗声明检测", "This product can cure headaches and treat pain", True),
        ("未验证声明", "FDA Approved and Clinically Proven formula", True),
        ("农药声明", "Antibacterial coating that kills 99% of germs", True),
        ("最高级表达", "The world's best and most popular product", True),
        ("Emoji 检测", "Great product! 🎉 Love it! ❤️", True),
        ("干净文案", "Made from 180 GSM ring-spun cotton, soft and breathable for all-day wear", False),
        ("标题长度(通过)", "A" * 199, False),
        ("标题长度(违规)", "A" * 201, True),
    ]

    passed = 0
    failed = 0

    for name, text, should_have_violation in test_cases:
        violations = []
        violations.extend(check_forbidden_terms(text, PROMOTIONAL_TERMS, "促销"))
        violations.extend(check_forbidden_terms(text, MEDICAL_TERMS, "医疗"))
        violations.extend(check_forbidden_terms(text, UNVERIFIED_CLAIMS, "未验证"))
        violations.extend(check_forbidden_terms(text, PESTICIDE_TERMS, "农药"))
        violations.extend(check_forbidden_terms(text, SUPERLATIVE_TERMS, "最高级"))
        violations.extend(check_emoji(text))

        if name == "标题长度(通过)":
            violations.extend(check_title_length(text, False))
        elif name == "标题长度(违规)":
            violations.extend(check_title_length(text, False))

        has_violation = len(violations) > 0
        test_pass = has_violation == should_have_violation

        icon = "✅" if test_pass else "❌"
        print(f"  {icon} {name}: {'检测到违规' if has_violation else '无违规'}")
        if violations and test_pass:
            for v in violations[:2]:
                print(f"      → {v['category']}: {v['term']}")

        if test_pass:
            passed += 1
        else:
            failed += 1

    print(f"\n结果: {passed} 通过, {failed} 失败")
    return failed == 0


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Amazon Listing 合规校验")
    parser.add_argument("--input", type=str, help="Listing Markdown 文件路径")
    parser.add_argument("--apparel", action="store_true", help="服装类目 (标题上限 125 字符)")
    parser.add_argument("--test-blacklist", action="store_true", help="运行内置违禁词测试")

    args = parser.parse_args()

    if args.test_blacklist:
        success = run_tests()
        sys.exit(0 if success else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    result = validate_listing(args.input, args.apparel)

    print(f"\n{'=' * 60}")
    print(f"合规检查结果: {result['status']}")
    print(f"{'=' * 60}")
    print(f"标题字符数: {result['title_length']}")
    print(f"Search Terms 字节数: {result['search_terms_bytes']}")
    print(f"违规项数量: {result['violations_count']}")

    if result['violations']:
        print(f"\n{'─' * 60}")
        print("违规详情:")
        for i, v in enumerate(result['violations'], 1):
            print(f"\n  [{i}] 类别: {v['category']}")
            print(f"      违规: {v['term']}")
            print(f"      上下文: {v['context']}")

    print(f"\n{'=' * 60}")
    sys.exit(0 if result['status'] == 'PASS' else 1)


if __name__ == "__main__":
    main()
