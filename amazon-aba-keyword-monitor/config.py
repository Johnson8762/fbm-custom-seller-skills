"""配置 - 亚马逊 ABA 爆品关键词监测系统（box 移植版）

改动（相对 Mac 原版）：
  * 多类目合并：类目由 --category 参数 / 环境变量 ABA_CATEGORY 选择，
    每个类目一个目录 data/<slug>/（category_config.json / 词典 / 排除规则 / history.db / .exchange/）
  * Sorftime key 只从环境变量 SORFTIME_KEY（兼容 SORFTIME_API_KEY）读取，绝不打印
  * 不再自动 pip install；依赖装在 .venv
  * 报告输出到 reports/aba/<slug>/
"""
import os, json

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_ROOT = os.path.join(SKILL_DIR, "data")
REPORT_ROOT = os.environ.get("ABA_REPORT_ROOT", "reports/aba")

# ─── AMZ123 抓取配置 ───
AMZ123_BASE_URL = "https://www.amz123.com/usatopkeywords"
MAX_PAGES = int(os.environ.get("ABA_MAX_PAGES", "5"))
SCRAPE_COMBOS = [
    {"rank": "1_1000",      "uprank": "1001",     "label": "高排名+高涨幅"},
    {"rank": "1001_10000",  "uprank": "1001",     "label": "中排名+高涨幅"},
    {"rank": "10001_50000", "uprank": "1001",     "label": "低排名+高涨幅"},
    {"rank": "50001",       "uprank": "1001",     "label": "超低排名+高涨幅"},
    {"rank": "1_1000",      "uprank": "101_1000", "label": "高排名+中涨幅"},
    {"rank": "1001_10000",  "uprank": "101_1000", "label": "中排名+中涨幅"},
]
_combo_limit = os.environ.get("ABA_MAX_COMBOS")
if _combo_limit:
    SCRAPE_COMBOS = SCRAPE_COMBOS[: int(_combo_limit)]

# ─── Tier 分层阈值（与原版一致）───
TIER1_RANK_THRESHOLD = 1000
TIER2_RANK_THRESHOLD = 50000
TIER1_SURGE_RATIO = 0.5
TIER1_SURGE_ABS = 1000
TIER2_CROSS_FROM = 100000
TIER2_CROSS_TO = 50000
TIER3_CROSS_FROM = 200000
TIER3_CROSS_TO = 100000
REBOUND_PEAK_THRESHOLD = 100

# ─── Sorftime ───
SORFTIME_BASE_URL = "https://mcp.sorftime.com"
SORFTIME_SITE = os.environ.get("ABA_SITE", "US")
SORFTIME_CONCURRENCY = int(os.environ.get("SORFTIME_CONCURRENCY", "3"))  # 原版 10；Sorftime 建议 ≤3 并发
SORFTIME_TIMEOUT = 60
# 测试用上限：未设置 = 不限；设为 N（含 0）= 最多查 N 个
SORFTIME_MAX_TIER1 = int(os.environ["ABA_SORFTIME_MAX_TIER1"]) if os.environ.get("ABA_SORFTIME_MAX_TIER1") else None
SORFTIME_MAX_TIER2 = int(os.environ["ABA_SORFTIME_MAX_TIER2"]) if os.environ.get("ABA_SORFTIME_MAX_TIER2") else None
VERIFY_SSL = os.environ.get("VERIFY_SSL", "true").lower() == "true"
SORFTIME_API_KEY = os.environ.get("SORFTIME_KEY") or os.environ.get("SORFTIME_API_KEY", "")


# ─── 类目选择 ───
def list_categories():
    if not os.path.isdir(DATA_ROOT):
        return []
    return sorted(d for d in os.listdir(DATA_ROOT)
                  if os.path.isfile(os.path.join(DATA_ROOT, d, "category_config.json")))


def get_category_slug():
    slug = os.environ.get("ABA_CATEGORY", "").strip()
    if slug:
        return slug
    cats = list_categories()
    return cats[0] if len(cats) == 1 else ""


def get_data_dir():
    return os.path.join(DATA_ROOT, get_category_slug() or "default")


def _cfg_path():
    return os.path.join(get_data_dir(), "category_config.json")


def load_category_config() -> dict:
    p = _cfg_path()
    if not os.path.exists(p):
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_category_config(cfg: dict):
    os.makedirs(get_data_dir(), exist_ok=True)
    with open(_cfg_path(), "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get_category_name() -> str:
    return load_category_config().get("category_name", "未配置")


def get_category_name_en() -> str:
    return load_category_config().get("category_name_en", get_category_slug() or "unknown")


def get_dict_path():
    return os.path.join(get_data_dir(), "category_dict.json")


def get_exclusion_path():
    return os.path.join(get_data_dir(), "exclusion_rules.json")


def get_db_path():
    return os.path.join(get_data_dir(), "history.db")


def get_exchange_dir():
    return os.path.join(get_data_dir(), ".exchange")


def get_report_dir():
    return os.path.join(REPORT_ROOT, get_category_slug() or "default")


TEMPLATE_DIR = os.path.join(SKILL_DIR, "templates")


# 兼容旧代码中的 config.EXCHANGE_DIR / config.REPORT_DIR 引用
def __getattr__(name):
    if name == "EXCHANGE_DIR":
        return get_exchange_dir()
    if name == "REPORT_DIR":
        return get_report_dir()
    raise AttributeError(name)


# ─── 启动检查 ───
def check_sorftime_ready() -> bool:
    if not SORFTIME_API_KEY:
        print("❌ 环境变量 SORFTIME_KEY 未设置（box 上应已注入；不要把 key 写进文件）")
        return False
    return True


def check_category_ready() -> bool:
    if not get_category_slug():
        print(f"❌ 未指定类目。用 --category <slug> 或 ABA_CATEGORY。已有类目: {list_categories()}")
        return False
    cfg = load_category_config()
    if cfg.get("status") != "ready":
        print(f"⚠️ 类目 {get_category_slug()} 尚未初始化完成（status={cfg.get('status')}），先跑 init / init-confirm")
        return False
    return True


def get_bitable_config() -> dict:
    cfg = load_category_config()
    return {
        "bitable_token": cfg.get("bitable_token", ""),
        "bitable_url": cfg.get("bitable_url", ""),
        "table_ids": cfg.get("table_ids", {}),
        "dashboard_id": cfg.get("dashboard_id", ""),
    }


def save_bitable_config(bitable_token, bitable_url, table_ids, dashboard_id=""):
    cfg = load_category_config()
    cfg.update({"bitable_token": bitable_token, "bitable_url": bitable_url,
                "table_ids": table_ids, "dashboard_id": dashboard_id})
    save_category_config(cfg)
