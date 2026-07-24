"""欧盟数据源：欧盟共同体注册簿（Union Register，集中程序批准药品）。
官方列表页将完整注册簿以 JSON 内嵌（var dataSet = [...]），本适配器直接解析。
失败时回退为手工导入 imports/EU.csv。
注意：共同体注册簿仅含集中程序产品；MRP/DCP 产品分散在各成员国 NCA 及 CMDh MRI 数据库。
"""
import json
import re
import urllib.request

from .base import BaseScraper, import_csv_files

LIST_URL = ("https://ec.europa.eu/health/documents/community-register/"
            "html/reg_hum_act.htm")
DETAIL_BASE = ("https://ec.europa.eu/health/documents/community-register/"
               "html/h{id}.htm")


class EmaScraper(BaseScraper):
    code = "EU"

    def fetch_new(self, since=None):
        try:
            return self._fetch_register()
        except Exception as e:
            print(f"[EU] 自动解析共同体注册簿失败：{e}")
            print("[EU] 请从以下页面手工导出后放入 imports/EU.csv：")
            print(f"     {self.cfg.get('official_url')}")
            return import_csv_files(None, self.resolver, self.cfg)

    def _fetch_register(self):
        req = urllib.request.Request(LIST_URL, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=120) as r:
            html = r.read().decode("utf-8", "ignore")
        m = re.search(r"var\s+dataSet\s*=\s*(\[.*?\])\s*;", html, re.S)
        if not m:
            raise RuntimeError("页面中未找到 dataSet JSON")
        data = json.loads(m.group(1), strict=False)
        out = []
        for item in data:
            name = (item.get("name") or "").strip()
            inn = (item.get("inn") or "").strip()
            if not name or not inn:
                continue
            eu = item.get("eu_num") or {}
            lic = eu.get("display", "")
            link = DETAIL_BASE.format(id=eu.get("id", "")) if eu.get("id") else self.cfg.get("official_url", "")
            for api_part in re.split(r"[/;,]", inn):
                api_part = api_part.strip()
                if not api_part:
                    continue
                out.append({
                    "country": self.cfg["country"],
                    "authority": self.cfg["authority"],
                    "product_name": name,
                    "api_en": api_part.lower(),
                    "api_zh": self.resolver.zh_for(api_part),
                    "applicant": (item.get("company") or "").strip(),
                    "approval_date": None,  # 列表页不含批准日期
                    "license_number": lic,
                    "url": link,
                    "source": "EU Union Register",
                })
        return out
