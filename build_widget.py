"""将 generic_drug_tracker 数据库导出为 Widget 数据快照，并生成 widget index.html。
用法：
  python build_widget.py <widget_workspace_dir>
每次主数据库更新后重跑本脚本即可刷新 Widget 数据。
"""
import json
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from src.db import get_conn, load_config  # noqa: E402


def export_snapshot():
    conn = get_conn()
    sources = load_config("sources.json")
    auth_meta = {a["code"]: {"country": a["country"], "authority": a["authority"]}
                 for a in sources["authorities"]}
    name2code = {a["authority"]: a["code"] for a in sources["authorities"]}

    with open(BASE / "config" / "api_aliases.json", encoding="utf-8") as f:
        aliases = {k: v for k, v in json.load(f).items() if not k.startswith("_")}
    with open(BASE / "config" / "reliance_rules.json", encoding="utf-8") as f:
        rules = json.load(f)["rules"]

    products = []
    for r in conn.execute(
        "SELECT country, authority, product_name, api_en, api_zh, applicant,"
        " approval_date, license_number, url FROM products"
    ):
        code = name2code.get(r["authority"], r["authority"])
        products.append({
            "c": code,
            "pn": r["product_name"],
            "api": r["api_en"],
            "aizh": r["api_zh"],
            "app": r["applicant"],
            "date": r["approval_date"],
            "lic": r["license_number"],
            "url": r["url"],
        })

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "authorities": auth_meta,
        "aliases": aliases,
        "rules": rules,
        "products": products,
    }


def main():
    workspace = Path(sys.argv[1])
    snapshot = export_snapshot()
    template = (BASE / "widget" / "template.html").read_text(encoding="utf-8")
    html = template.replace("__WIDGET_DATA__", json.dumps(snapshot, ensure_ascii=False))
    out = workspace / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"已生成 {out}（{len(snapshot['products'])} 条产品记录，"
          f"快照时间 {snapshot['generated_at']}）")


if __name__ == "__main__":
    main()
