"""互认/依赖规则引擎：根据某 API 已获批的监管机构集合，
推断相同技术证明文件还可在哪些国家/经济体使用。"""
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load_rules():
    with open(CONFIG_DIR / "reliance_rules.json", "r", encoding="utf-8") as f:
        return json.load(f)["rules"]


def reliance_hints(authority_codes):
    """authority_codes: 该 API 已获批产品所属的监管机构代码集合。
    返回命中的规则列表，每条含 doc_type/scope/usable_in/note。"""
    codes = set(authority_codes)
    hints = []
    for rule in _load_rules():
        if codes & set(rule["from"]):
            hints.append(rule)
    return hints
