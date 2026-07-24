"""API 中英双语别名解析。"""
import json
from pathlib import Path

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _load():
    with open(CONFIG_DIR / "api_aliases.json", "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


class AliasResolver:
    def __init__(self):
        self._table = _load()
        # zh -> en, en-variant -> en
        self._zh2en = {}
        self._var2en = {}
        for en, info in self._table.items():
            self._zh2en[info["zh"]] = en
            for v in info.get("variants", []):
                self._var2en[v.lower()] = en

    def normalize(self, text):
        """输入中文或英文名，返回 (标准英文名, 中文名或None)。"""
        t = (text or "").strip()
        low = t.lower()
        if t in self._zh2en:
            en = self._zh2en[t]
            return en, t
        if low in self._table:
            return low, self._table[low]["zh"]
        if low in self._var2en:
            en = self._var2en[low]
            return en, self._table[en]["zh"]
        # 未知名词：原样返回，交由数据库 LIKE 匹配
        return low, None

    def zh_for(self, en):
        info = self._table.get((en or "").lower())
        return info["zh"] if info else None
