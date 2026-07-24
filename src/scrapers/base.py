"""数据源适配器基类与通用 CSV 导入器。"""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
IMPORTS_DIR = BASE_DIR / "imports"


class BaseScraper:
    code = "BASE"

    def __init__(self, cfg, resolver):
        self.cfg = cfg
        self.resolver = resolver

    def fetch_new(self, since=None):
        """返回新获批产品记录列表。子类实现。"""
        raise NotImplementedError

    def fetch_api(self, api_en):
        """按 API 名定向抓取（用于即时补充）。可选实现。"""
        return []


def import_csv_files(conn_upsert, resolver, authority_cfg):
    """从 imports/ 目录读取 <CODE>.csv 手工导出文件。
    必需列: product_name, api_en
    可选列: api_zh, applicant, approval_date, license_number, url
    """
    path = IMPORTS_DIR / f"{authority_cfg['code']}.csv"
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            api_en = (row.get("api_en") or "").strip()
            if not api_en or not (row.get("product_name") or "").strip():
                continue
            records.append({
                "country": authority_cfg["country"],
                "authority": authority_cfg["authority"],
                "product_name": row["product_name"].strip(),
                "api_en": api_en.lower(),
                "api_zh": (row.get("api_zh") or "").strip() or resolver.zh_for(api_en),
                "applicant": (row.get("applicant") or "").strip(),
                "approval_date": (row.get("approval_date") or "").strip(),
                "license_number": (row.get("license_number") or "").strip(),
                "url": (row.get("url") or "").strip() or authority_cfg.get("official_url", ""),
                "source": f"官方导出导入({path.name})",
            })
    return records
