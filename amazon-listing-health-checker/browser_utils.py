"""
browser_utils.py — 通用网页抓取工具模块

提供基于 curl + BeautifulSoup 的网页抓取能力，模拟真实浏览器请求。
支持通过 Amazon 地址变更 API 设置配送邮编，解决非本地 IP 导致的
"Currently Unavailable" 问题。

其他 Skill 可以直接 import 使用：
    from browser_utils import fetch_page, fetch_page_with_location, get_site_config

依赖：pip install beautifulsoup4
"""

import subprocess
import time
import random
import re
import tempfile
import os
import sys

# 站点配置
SITE_CONFIG = {
    "US": {"domain": "amazon.com", "zip": "10010", "currency": "USD"},
    "UK": {"domain": "amazon.co.uk", "zip": "SW1A 1AA", "currency": "GBP"},
    "GB": {"domain": "amazon.co.uk", "zip": "SW1A 1AA", "currency": "GBP"},
    "DE": {"domain": "amazon.de", "zip": "10115", "currency": "EUR"},
    "FR": {"domain": "amazon.fr", "zip": "75001", "currency": "EUR"},
    "IT": {"domain": "amazon.it", "zip": "00100", "currency": "EUR"},
    "ES": {"domain": "amazon.es", "zip": "28001", "currency": "EUR"},
    "CA": {"domain": "amazon.ca", "zip": "M5V 2T6", "currency": "CAD"},
    "JP": {"domain": "amazon.co.jp", "zip": "100-0001", "currency": "JPY"},
    "MX": {"domain": "amazon.com.mx", "zip": "06600", "currency": "MXN"},
    "AU": {"domain": "amazon.com.au", "zip": "2000", "currency": "AUD"},
}

# 固定 Chrome macOS UA，验证过能通过亚马逊反爬
DEFAULT_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

# 浏览器 User-Agent 池（备用轮换）
USER_AGENTS = [
    DEFAULT_UA,
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:134.0) Gecko/20100101 Firefox/134.0",
]


def get_site_config(site_code: str) -> dict:
    """获取站点配置"""
    code = site_code.upper()
    if code not in SITE_CONFIG:
        raise ValueError(f"不支持的站点: {site_code}，支持: {', '.join(SITE_CONFIG.keys())}")
    return SITE_CONFIG[code]


def _curl_common_headers() -> list:
    """返回通用 curl header 参数"""
    return [
        "-H", f"User-Agent: {DEFAULT_UA}",
        "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H", "Accept-Language: en-US,en;q=0.9",
        "-H", "Connection: keep-alive",
    ]


def fetch_page(url: str, timeout: int = 30) -> str:
    """
    用 curl 抓取网页，返回完整 HTML（不设置配送地址）。

    Args:
        url: 目标 URL
        timeout: 超时秒数

    Returns:
        HTML 字符串。抓取失败返回空字符串。
    """
    try:
        result = subprocess.run(
            ["curl", "-sL", "--compressed", "--max-time", str(timeout)]
            + _curl_common_headers()
            + [url],
            capture_output=True,
            text=True, errors="replace",
            timeout=timeout + 5,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, Exception):
        return ""


def set_delivery_location(domain: str, zip_code: str, timeout: int = 15) -> str:
    """
    通过 Amazon 地址变更 API 设置配送邮编，返回 cookie jar 文件路径。

    流程：
    1. GET 首页 → 建立 session，获取 session-id cookie → 保存到 cookie jar
    2. POST /gp/delivery/ajax/address-change.html → 设置邮编 → 更新 cookie jar

    Args:
        domain: 亚马逊域名（如 amazon.com）
        zip_code: 目标邮编
        timeout: 每步超时秒数

    Returns:
        cookie jar 文件的绝对路径。调用者负责在使用后删除。
    """
    cookie_jar = tempfile.mktemp(suffix=".txt", prefix="amz_cookies_")
    base_url = f"https://www.{domain}"

    # Step 1: GET 首页，建立 session
    _log(f"[location] GET {base_url} → 建立 session ...")
    try:
        subprocess.run(
            ["curl", "-sL", "--compressed",
             "--max-time", str(timeout),
             "-c", cookie_jar,      # 写入 cookie
             "-b", cookie_jar,      # 读取 cookie（首次为空）
             ]
            + _curl_common_headers()
            + [base_url],
            capture_output=True,
            text=True, errors="replace",
            timeout=timeout + 5,
        )
    except (subprocess.TimeoutExpired, Exception) as e:
        _log(f"[location] ⚠️ GET 首页失败: {e}")
        return cookie_jar

    throttle(0.5, 1.5)

    # Step 2: POST 地址变更 API
    change_url = f"{base_url}/gp/delivery/ajax/address-change.html"
    _log(f"[location] POST {change_url} → 设置邮编 {zip_code} ...")
    try:
        result = subprocess.run(
            ["curl", "-sL", "--compressed",
             "--max-time", str(timeout),
             "-c", cookie_jar,
             "-b", cookie_jar,
             "-X", "POST",
             ]
            + _curl_common_headers()
            + [
             "-H", "Content-Type: application/x-www-form-urlencoded",
             "-H", f"Referer: {base_url}/",
             "-H", "X-Requested-With: XMLHttpRequest",
             "-d", f"locationType=LOCATION_INPUT&zipCode={zip_code}&storeContext=generic&deviceType=web&pageType=Gateway&actionSource=glow",
             change_url,
            ],
            capture_output=True,
            text=True, errors="replace",
            timeout=timeout + 5,
        )
        body = result.stdout.strip()
        if re.search(r'"isValidAddress":\s*"?1', body):
            _log(f"[location] ✅ 邮编 {zip_code} 设置成功")
        else:
            _log(f"[location] ⚠️ 地址变更响应: {body[:200]}")
    except (subprocess.TimeoutExpired, Exception) as e:
        _log(f"[location] ⚠️ POST 地址变更失败: {e}")

    throttle(0.5, 1.0)
    return cookie_jar


def fetch_page_with_location(url: str, domain: str, zip_code: str, timeout: int = 30) -> str:
    """
    先设置配送邮编，再用同一 cookie session 抓取目标页面。
    解决非本地 IP 访问 Amazon 时看到 "Currently Unavailable" 的问题。

    Args:
        url: 目标 URL（商品页 / 搜索页）
        domain: 亚马逊域名
        zip_code: 目标邮编
        timeout: 超时秒数

    Returns:
        HTML 字符串。抓取失败返回空字符串。
    """
    cookie_jar = set_delivery_location(domain, zip_code, timeout=15)

    _log(f"[fetch] GET {url} (with location cookie) ...")
    try:
        result = subprocess.run(
            ["curl", "-sL", "--compressed",
             "--max-time", str(timeout),
             "-b", cookie_jar,      # 带上设置好邮编的 cookie
             "-c", cookie_jar,
             ]
            + _curl_common_headers()
            + [url],
            capture_output=True,
            text=True, errors="replace",
            timeout=timeout + 5,
        )
        return result.stdout
    except (subprocess.TimeoutExpired, Exception):
        return ""
    finally:
        # 清理临时 cookie 文件
        try:
            os.unlink(cookie_jar)
        except OSError:
            pass


def check_captcha(html: str) -> bool:
    """检测是否命中验证码/拦截页面"""
    if len(html) < 10000:
        # 正常亚马逊商品页 > 500KB，小于 10KB 基本是拦截页
        lower = html.lower()
        captcha_signals = [
            "enter the characters you see below",
            "sorry, we just need to make sure you're not a robot",
            "api-services-support@amazon.com",
            "automated access to our website",
        ]
        return any(s in lower for s in captcha_signals)
    return False


def throttle(min_sec: float = 1.0, max_sec: float = 3.0):
    """请求间随机延迟，降低被限流概率"""
    time.sleep(random.uniform(min_sec, max_sec))


def _log(msg: str):
    """输出调试日志到 stderr（不影响 stdout 的 JSON）"""
    print(msg, file=sys.stderr)
