"""一次性脚本：把 CDE 化学药品目录集抓取结果（imports/cde_listed_drugs.json）导入 generics.db。
api_en 通过别名库尽力映射；未映射的保留 api_zh，中文查询仍可命中。
"""
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from src.db import get_conn, load_config, upsert_products  # noqa: E402

# 剂型后缀（长的在前，先匹配长的）
DOSAGE_FORMS = [
    "注射用无菌粉末", "注射用冻干粉针", "注射用粉针", "冻干粉针剂", "冻干粉针",
    "口腔崩解片", "缓释胶囊", "控释胶囊", "肠溶胶囊", "软胶囊", "硬胶囊",
    "缓释片", "控释片", "肠溶片", "分散片", "咀嚼片", "泡腾片", "含片", "舌下片",
    "薄膜衣片", "糖衣片", "素片",
    "小容量注射液", "大容量注射液", "注射液", "粉针剂", "粉针",
    "干混悬剂", "混悬液", "混悬剂", "口服溶液剂", "口服溶液", "口服液", "口服乳剂",
    "滴眼液", "滴鼻液", "滴耳液", "眼用凝胶", "眼膏剂", "眼膏",
    "乳膏剂", "乳膏", "软膏剂", "软膏", "凝胶剂", "凝胶", "贴剂", "贴片", "贴膏剂",
    "喷雾剂", "气雾剂", "吸入剂", "吸入溶液", "鼻喷雾剂",
    "颗粒剂", "颗粒", "散剂", "丸剂", "微丸", "栓剂", "酊剂", "膜剂",
    "洗剂", "搽剂", "涂剂", "涂膜剂", "灌肠剂", "糖浆剂", "糖浆", "合剂",
    "胶囊剂", "胶囊", "片剂", "片", "散", "丸", "栓", "酊", "膜", "膏", "霜",
    "注射剂",
]


def strip_dosage_form(name: str) -> str:
    n = name.strip()
    for form in DOSAGE_FORMS:
        if n.endswith(form) and len(n) > len(form) + 1:
            return n[: -len(form)].strip()
    return n


def main():
    raw = json.load(open(BASE / "imports" / "cde_listed_drugs.json", encoding="utf-8"))
    aliases = {k: v for k, v in load_config("api_aliases.json").items()
               if not k.startswith("_")}

    # zh 别名 → en（含 variants 中的英文不用于 zh 映射）
    zh_map = {}
    for en, info in aliases.items():
        if info.get("zh"):
            zh_map[info["zh"]] = en

    def guess_en(api_zh: str) -> str:
        # 中文通用名含别名中文（如「阿托伐他汀钙」含「阿托伐他汀」）
        best = ""
        for zh, en in zh_map.items():
            if zh and zh in api_zh and len(zh) > len(best):
                best = zh
        return zh_map.get(best, "")

    cfg = {a["code"]: a for a in load_config("sources.json")["authorities"]}["NMPA"]
    records, mapped = [], 0
    seen = set()
    for r in raw:
        pn = (r.get("ypmc") or "").strip()
        lic = (r.get("pzwh") or "").strip()
        if not pn or not lic:
            continue
        key = (lic, pn)
        if key in seen:
            continue
        seen.add(key)
        api_zh = strip_dosage_form(pn)
        api_en = guess_en(api_zh)
        if api_en:
            mapped += 1
        idcode = (r.get("idCode") or "").strip()
        records.append({
            "country": cfg["country"],
            "authority": cfg["authority"],
            "product_name": pn,
            "api_en": api_en,
            "api_zh": api_zh,
            "applicant": (r.get("ssxkzcyr") or r.get("sccs") or "").strip(),
            "approval_date": (r.get("scpzrq") or "").strip(),
            "license_number": lic,
            "url": f"https://www.cde.org.cn/hymlj/detailPage/{idcode}" if idcode
                   else cfg["official_url"],
            "source": "CDE 化学药品目录集（WebBridge 抓取）",
        })

    conn = get_conn()
    n_new, n_seen = upsert_products(conn, records)
    print(f"导入 {len(records)} 条（新增 {n_new}，已存在 {n_seen}）；"
          f"英文 API 映射成功 {mapped} 条，未映射 {len(records) - mapped} 条（保留中文名可检索）")


if __name__ == "__main__":
    main()
