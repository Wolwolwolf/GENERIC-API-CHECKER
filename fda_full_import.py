"""FDA 全量仿制药导入：解析 Drugs@FDA 官方数据文件（drugsfda.zip），
导入所有 ANDA（简化新药申请=仿制药）产品，替换旧 openFDA 增量数据。
剔除停产（Discontinued）与暂定批准（None/tentative）产品。
"""
import csv
import io
import sys
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))
from src.db import get_conn, load_config, upsert_products  # noqa: E402

ZIP_PATH = BASE.parent / "drugsfda.zip"
KEEP_STATUS = {"1", "2"}  # 1=Prescription, 2=OTC；剔除 3=Discontinued, 4=Tentative


def read_table(zf, name):
    with zf.open(name) as fh:
        text = io.TextIOWrapper(fh, encoding="utf-8", errors="replace")
        yield from csv.DictReader(text, delimiter="\t")


def main():
    aliases = {k: v for k, v in load_config("api_aliases.json").items()
               if not k.startswith("_")}
    en2zh = {en: info.get("zh", "") for en, info in aliases.items()}
    var2en = {}
    for en, info in aliases.items():
        for v in info.get("variants", []):
            var2en[v.lower()] = en

    def zh_for(ing: str) -> str:
        key = ing.strip().lower()
        if key in en2zh:
            return en2zh[key]
        if key in var2en:
            return en2zh.get(var2en[key], "")
        # 单成分带盐型：尝试前缀匹配
        for en, zh in en2zh.items():
            if zh and key.startswith(en) and len(en) >= 5:
                return zh
        return ""

    with zipfile.ZipFile(ZIP_PATH) as zf:
        # 1) ANDA 申请
        anda = {}
        for row in read_table(zf, "Applications.txt"):
            if row["ApplType"].strip().upper() == "ANDA":
                anda[row["ApplNo"].strip()] = row["SponsorName"].strip()
        print(f"ANDA 申请数：{len(anda)}")

        # 2) 在售状态
        status = {}
        for row in read_table(zf, "MarketingStatus.txt"):
            status[(row["ApplNo"].strip(), row["ProductNo"].strip())] = row["MarketingStatusID"].strip()

        # 3) 最早批准日期
        ap_date = {}
        for row in read_table(zf, "Submissions.txt"):
            if row["SubmissionStatus"].strip().upper() != "AP":
                continue
            a = row["ApplNo"].strip()
            d = (row["SubmissionStatusDate"] or "")[:10]
            if d and (a not in ap_date or d < ap_date[a]):
                ap_date[a] = d

        # 4) 产品
        records, skipped = [], 0
        for row in read_table(zf, "Products.txt"):
            a, p = row["ApplNo"].strip(), row["ProductNo"].strip()
            if a not in anda:
                continue
            st = status.get((a, p), "")
            if st and st not in KEEP_STATUS:
                skipped += 1
                continue
            name = (row["DrugName"] or "").strip().title()
            form = (row["Form"] or "").replace(";", ", ").title()
            strength = (row["Strength"] or "").strip()
            ing = (row["ActiveIngredient"] or "").strip()
            if not name or not ing:
                continue
            pn = f"{name} {form} {strength}".strip()
            records.append({
                "country": "美国",
                "authority": "US FDA (CDER/OGD)",
                "product_name": pn,
                "api_en": ing.lower(),
                "api_zh": zh_for(ing),
                "applicant": anda[a].title(),
                "approval_date": ap_date.get(a, ""),
                "license_number": f"ANDA {a}-{p}",
                "url": f"https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm?event=overview.process&ApplNo={int(a)}",
                "source": "Drugs@FDA 官方数据文件",
            })

    print(f"在售 ANDA 产品：{len(records)}（剔除停产/暂定 {skipped}）")

    conn = get_conn()
    cur = conn.execute("DELETE FROM products WHERE country='美国'")
    print(f"删除旧 FDA 记录：{cur.rowcount}")
    conn.commit()
    n_new, _ = upsert_products(conn, records)
    print(f"导入完成：新增 {n_new} 条")


if __name__ == "__main__":
    main()
