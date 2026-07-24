"""MHRA Products 抓取：利用其前端公开的 Azure Search 查询 API，
按别名库英文 API 名逐一检索 SmPC 文档，按 PL 号去重生成英国许可目录并入库。
原始响应缓存在 imports/mhra_raw/，可断点续抓。
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from src.db import get_conn, load_config, upsert_products  # noqa: E402

API = ("https://mhraproducts4853.search.windows.net/indexes/products-index/docs"
       "?api-key=17CCFC430C1A78A169B392A35A99C49D&api-version=2017-11-11")
RAW_DIR = BASE / "imports" / "mhra_raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

PROXY = urllib.request.ProxyHandler({"http": "http://127.0.0.1:10809",
                                     "https": "http://127.0.0.1:10809"})
OPENER = urllib.request.build_opener(PROXY)

PL_RE = re.compile(r"PL\s*(\d{4,5})\s*[/]?\s*(\d{4})")


def norm_pl(raw: str) -> str:
    m = PL_RE.search(raw.replace(" ", ""))
    return f"PL {m.group(1)}/{m.group(2)}" if m else ""


def fetch(en: str) -> list:
    """检索某 API 的 SmPC 文档（分页 $top=1000），返回 value 列表。"""
    cache = RAW_DIR / f"{en.replace('/', '_').replace(' ', '_')}.json"
    if cache.exists():
        return json.load(open(cache, encoding="utf-8"))
    docs, skip = [], 0
    while True:
        params = {
            "search": f'"{en}"',
            "$filter": "doc_type eq 'Spc'",
            "$select": "title,pl_number,product_name,substance_name,created,territory",
            "$count": "true", "$top": "1000", "$skip": str(skip),
            "queryType": "full", "searchMode": "all",
        }
        url = API + "&" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with OPENER.open(req, timeout=60) as r:
            data = json.loads(r.read().decode("utf-8"))
        docs.extend(data.get("value", []))
        total = data.get("@odata.count", 0)
        skip += 1000
        if skip >= total or skip >= 10000 or not data.get("value"):
            break
        time.sleep(0.3)
    json.dump(docs, open(cache, "w", encoding="utf-8"), ensure_ascii=False)
    return docs


def main():
    aliases = {k: v for k, v in load_config("api_aliases.json").items()
               if not k.startswith("_")}
    cfg = {a["code"]: a for a in load_config("sources.json")["authorities"]}["MHRA"]

    records, seen = [], set()
    items = list(aliases.items())
    for i, (en, info) in enumerate(items, 1):
        try:
            docs = fetch(en)
        except Exception as e:
            print(f"[{i}/{len(items)}] {en} 抓取失败：{e}")
            continue
        n = 0
        base = en.lower()
        for d in docs:
            subs = [s.lower() for s in (d.get("substance_name") or [])]
            if not any(base in s for s in subs):
                continue
            pls = set()
            for raw in (d.get("pl_number") or []):
                for m in PL_RE.finditer(str(raw).replace(" ", "")):
                    pls.add(f"PL {m.group(1)}/{m.group(2)}")
            title = (d.get("product_name") or d.get("title") or "").strip()
            title = re.sub(r"\.pdf$", "", title, flags=re.I)
            for pl in pls:
                if not pl or pl in seen:
                    continue
                seen.add(pl)
                records.append({
                    "country": cfg["country"],
                    "authority": cfg["authority"],
                    "product_name": title.split(" - PL")[0].strip().title() or en,
                    "api_en": en,
                    "api_zh": info.get("zh", ""),
                    "applicant": "",
                    "approval_date": "",
                    "license_number": pl,
                    "url": "https://products.mhra.gov.uk/product/?product="
                           + urllib.parse.quote(pl),
                    "source": "MHRA Products（Azure Search 公开 API）",
                })
                n += 1
        print(f"[{i}/{len(items)}] {en}: {n} 个 PL（累计 {len(records)}）")
        time.sleep(0.25)

    conn = get_conn()
    n_new, n_seen = upsert_products(conn, records)
    print(f"\n导入 {len(records)} 条（新增 {n_new}，已存在 {n_seen}）")


if __name__ == "__main__":
    main()
