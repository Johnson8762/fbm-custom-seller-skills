#!/usr/bin/env python3
"""
Image-Skill — HTML 可视化渲染器

将结构化图片 Prompt 数据渲染为交互式 HTML 页面，
包含分板块展示和一键复制功能。

用法：
    python render_image_prompts_html.py <input_json> <output_html>

输入 JSON 格式：
{
    "product_name": "Custom Leather Notebook",
    "generated_date": "2026-03-27",
    "visual_strategy": "...",
    "hero_image": {
        "strategy": "...",
        "prompt": "..."
    },
    "secondary_images": [
        {"type": "Usage Context", "strategy": "...", "prompt": "..."},
        ...
    ],
    "aplus_content": [
        {"module": "Brand Story Banner", "strategy": "...", "prompt": "..."},
        ...
    ],
    "ad_creatives": [
        {"variant": "A", "name": "Clean Product Focus", "prompt": "..."},
        ...
    ],
    "ab_tests": [
        {"dimension": "Lighting", "hypothesis": "...", "original": "...", "variation_prompt": "..."},
        ...
    ]
}
"""

import json
import sys
import os
from pathlib import Path


def load_html_template():
    """Load the HTML template from the scripts directory."""
    template_path = Path(__file__).parent / "image_prompt_template.html"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Fallback: generate inline
    return generate_inline_template()


def generate_inline_template():
    """Generate the HTML template inline as fallback."""
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{TITLE}}</title>
<style>{{STYLES}}</style>
</head>
<body>
{{CONTENT}}
<script>{{SCRIPTS}}</script>
</body>
</html>"""


def build_card_html(title: str, subtitle: str, prompt: str, strategy: str = "", card_id: str = "") -> str:
    """Build an individual prompt card."""
    strategy_section = ""
    if strategy:
        strategy_section = f"""
        <div class="card-strategy">
            <div class="strategy-label">设计策略</div>
            <div class="strategy-text">{strategy}</div>
        </div>"""

    return f"""
    <div class="prompt-card" id="{card_id}">
        <div class="card-header">
            <div class="card-title">{title}</div>
            <div class="card-subtitle">{subtitle}</div>
        </div>
        {strategy_section}
        <div class="card-prompt">
            <div class="prompt-label">
                <span>Prompt</span>
                <button class="copy-btn" onclick="copyPrompt(this)" data-prompt="{card_id}-prompt">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                    </svg>
                    Copy
                </button>
            </div>
            <pre class="prompt-text" id="{card_id}-prompt">{prompt}</pre>
        </div>
    </div>"""


def build_section_html(section_title: str, section_icon: str, cards_html: str, section_id: str) -> str:
    """Build a section container."""
    return f"""
    <section class="section" id="{section_id}">
        <div class="section-header">
            <span class="section-icon">{section_icon}</span>
            <h2 class="section-title">{section_title}</h2>
        </div>
        <div class="cards-grid">
            {cards_html}
        </div>
    </section>"""


def render_html(data: dict) -> str:
    """Render the full HTML page from structured data."""
    product_name = data.get("product_name", "Product")
    generated_date = data.get("generated_date", "")
    
    # Build navigation
    nav_items = []
    sections_html = ""
    
    # --- Visual Strategy ---
    if data.get("visual_strategy"):
        nav_items.append(("strategy", "📋", "视觉策略"))
        card = build_card_html(
            "Visual Strategy Brief",
            "视觉策略简报",
            data["visual_strategy"],
            card_id="strategy-card"
        )
        sections_html += build_section_html("视觉策略简报", "📋", card, "strategy")
    
    # --- Hero Image ---
    if data.get("hero_image"):
        nav_items.append(("hero", "🎯", "主图"))
        hero = data["hero_image"]
        card = build_card_html(
            "Hero Image — 主图",
            "决胜 CTR · 点击欲望",
            hero.get("prompt", ""),
            hero.get("strategy", ""),
            card_id="hero-card"
        )
        sections_html += build_section_html("Module 1: 主图 Hero Image", "🎯", card, "hero")
    
    # --- Secondary Images ---
    if data.get("secondary_images"):
        nav_items.append(("secondary", "🖼️", "辅图"))
        cards = ""
        for i, img in enumerate(data["secondary_images"]):
            cards += build_card_html(
                f"副图 {i+1}: {img.get('type', '')}",
                img.get("purpose", ""),
                img.get("prompt", ""),
                img.get("strategy", ""),
                card_id=f"secondary-{i+1}"
            )
        sections_html += build_section_html("Module 2: 辅图 Secondary Images", "🖼️", cards, "secondary")
    
    # --- A+ Content ---
    if data.get("aplus_content"):
        nav_items.append(("aplus", "✨", "A+"))
        cards = ""
        for i, mod in enumerate(data["aplus_content"]):
            cards += build_card_html(
                f"A+ 模块 {i+1}: {mod.get('module', '')}",
                mod.get("purpose", ""),
                mod.get("prompt", ""),
                mod.get("strategy", ""),
                card_id=f"aplus-{i+1}"
            )
        sections_html += build_section_html("Module 3: A+ Content", "✨", cards, "aplus")
    
    # --- Ad Creatives ---
    if data.get("ad_creatives"):
        nav_items.append(("ads", "📢", "广告"))
        cards = ""
        for i, ad in enumerate(data["ad_creatives"]):
            cards += build_card_html(
                f"Variant {ad.get('variant', chr(65+i))}: {ad.get('name', '')}",
                ad.get("campaign_type", ""),
                ad.get("prompt", ""),
                ad.get("strategy", ""),
                card_id=f"ad-{i+1}"
            )
        sections_html += build_section_html("Module 4: 广告素材 Ad Creatives", "📢", cards, "ads")
    
    # --- A/B Tests ---
    if data.get("ab_tests"):
        nav_items.append(("abtest", "🔬", "A/B"))
        cards = ""
        for i, test in enumerate(data["ab_tests"]):
            cards += build_card_html(
                f"Test {i+1}: {test.get('dimension', '')}",
                f"假设: {test.get('hypothesis', '')}",
                test.get("variation_prompt", ""),
                f"原始: {test.get('original', '')}",
                card_id=f"abtest-{i+1}"
            )
        sections_html += build_section_html("Module 5: A/B 测试变体", "🔬", cards, "abtest")
    
    # Build navigation HTML
    nav_html = ""
    for nav_id, icon, label in nav_items:
        nav_html += f'<a class="nav-item" href="#{nav_id}">{icon} {label}</a>\n'
    
    # Read template
    template_path = Path(__file__).parent / "image_prompt_template.html"
    if template_path.exists():
        html = template_path.read_text(encoding="utf-8")
    else:
        print("Warning: Template file not found, using inline template", file=sys.stderr)
        html = generate_inline_template()
    
    # Replace placeholders
    html = html.replace("{{PRODUCT_NAME}}", product_name)
    html = html.replace("{{GENERATED_DATE}}", generated_date)
    html = html.replace("{{NAV_ITEMS}}", nav_html)
    html = html.replace("{{SECTIONS}}", sections_html)
    
    return html


def main():
    if len(sys.argv) < 3:
        print("Usage: python render_image_prompts_html.py <input.json> <output.html>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2]
    
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    html = render_html(data)
    
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Generated: {output_path}")


if __name__ == "__main__":
    main()
