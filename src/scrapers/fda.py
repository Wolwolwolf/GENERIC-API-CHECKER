"""美国 FDA 数据源：openFDA drugfda 端点（Drugs@FDA 官方数据）。
仅取 ANDA（仿制药申请）。支持：
- fetch_window(start_yyyymmdd, end_yyyymmdd): 按批准时间窗抓取（每周更新用）
- fetch_api(api_en): 按 API 定向抓取（查询时即时补充用）
"""
import json
import time
import urllib.parse
import urllib.request

from .base import BaseScraper

API_URL = "https://api.fda.gov/drug/drugsfda.json"
PAGE = 1000
SLEEP = 0.3  # openFDA 限速：无 key 时 240 次/分钟


def _get(params):
    url = API_URL + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "generic-drug-tracker/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        if e.code == 404:  # openFDA 无匹配结果时返回 404
            return {"results": [], "meta": {"results": {"total": 0}}}
        raise


def _to_records(app, authority_cfg, resolver):
    products = app.get("products", [])
    subs = app.get("submissions", [])
    # 最近的获批日期
    ap_dates = [s.get("submission_status_date") for s in subs if s.get("submission_status") == "AP"]
    ap_date = max(ap_dates) if ap_dates else None
    if ap_date and len(ap_date) == 8:
        ap_date = f"{ap_date[:4]}-{ap_date[4:6]}-{ap_date[6:]}"
    appl_no = (app.get("application_number") or "").replace("ANDA", "")
    link = ("https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?"
            f"event=overview.process&ApplNo={appl_no}") if appl_no else authority_cfg.get("official_url", "")
    out = []
    for p in products:
        for ing in p.get("active_ingredients", []):
            name = (ing.get("name") or "").strip()
            if not name:
                continue
            out.append({
                "country": authority_cfg["country"],
                "authority": authority_cfg["authority"],
                "product_name": p.get("brand_name") or "",
                "api_en": name.lower(),
                "api_zh": resolver.zh_for(name),
                "applicant": app.get("sponsor_name"),
                "approval_date": ap_date,
                "license_number": app.get("application_number"),
                "url": link,
                "source": "openFDA/Drugs@FDA",
            })
    return out


class FdaScraper(BaseScraper):
    code = "FDA"

    def _search(self, search):
        records, skip = [], 0
        while True:
            data = _get({"search": search, "limit": PAGE, "skip": skip})
            results = data.get("results", [])
            for app in results:
                records.extend(_to_records(app, self.cfg, self.resolver))
            total = data["meta"]["results"]["total"]
            skip += PAGE
            if skip >= total or not results:
                break
            time.sleep(SLEEP)
        return records

    def fetch_window(self, start, end):
        search = (f'application_number:ANDA* AND submissions.submission_status_date:'
                  f'[{start} TO {end}]')
        try:
            return self._search(search)
        except Exception as e:
            print(f"[FDA] 抓取失败：{e}")
            return []

    def fetch_api(self, api_en):
        api = api_en.upper().strip()
        attempts = [
            f'application_number:ANDA* AND products.active_ingredients.name:"{api}"',
            f'application_number:ANDA* AND products.active_ingredients.name:{api.split()[0]}*',
        ]
        for search in attempts:
            try:
                recs = self._search(search)
            except Exception as e:
                print(f"[FDA] 定向抓取失败：{e}")
                return []
            if recs:
                return recs
        return []
