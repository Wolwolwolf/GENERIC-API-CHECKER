"""查询界面：输入仿制药 API（中/英文），显示各国已获批同 API 药品、
许可链接，并提示相同技术证明文件可在哪些相关国家使用。"""
from collections import defaultdict

from .aliases import AliasResolver
from .db import get_conn, query_by_api, load_config
from .reliance import reliance_hints
from .updater import targeted_fetch

CODE2NAME = {}


def _authority_names():
    global CODE2NAME
    if not CODE2NAME:
        cfg = load_config("sources.json")
        CODE2NAME = {a["code"]: f"{a['country']}（{a['authority']}）" for a in cfg["authorities"]}
    return CODE2NAME


def _print_results(rows, api_en, api_zh):
    title = f"{api_en}"
    if api_zh:
        title = f"{api_zh} / {api_en}"
    print("\n" + "=" * 72)
    print(f"查询 API：{title}")
    print("=" * 72)

    by_country = defaultdict(list)
    for r in rows:
        by_country[(r["country"], r["authority"])].append(r)

    print(f"\n已在 {len(by_country)} 个经济体/监管机构辖区发现同 API 获批产品，共 {len(rows)} 条：\n")
    auth_codes = set()
    for (country, authority), items in sorted(by_country.items()):
        print(f"● {country} — {authority}（{len(items)} 条）")
        for it in items[:10]:
            date = it["approval_date"] or "日期未知"
            lic = it["license_number"] or "-"
            print(f"    · {it['product_name']}  |  批准: {date}  |  批件号: {lic}")
            if it["url"]:
                print(f"      链接: {it['url']}")
        if len(items) > 10:
            print(f"    … 其余 {len(items) - 10} 条略")
        # 归集机构代码用于互认推断
        names = _authority_names()
        for code, label in names.items():
            if label.startswith(country) or authority in label or country in label:
                auth_codes.add(code)
    return auth_codes


def _print_hints(auth_codes):
    hints = reliance_hints(auth_codes)
    names = _authority_names()
    print("\n" + "-" * 72)
    print("技术证明文件互认/依赖提示（基于现行互认机制规则库）")
    print("-" * 72)
    if not hints:
        print("暂无命中的互认机制。")
        return
    for h in hints:
        targets = [names.get(c, c) for c in h["usable_in"]]
        target_str = "；".join(targets) if targets else "（无自动互认目标，见说明）"
        print(f"\n■ 机制 {h['id']} — {h['scope']}")
        print(f"  文件类型: {h['doc_type']}")
        print(f"  可使用于: {target_str}")
        print(f"  说明: {h['note']}")
    print("\n提示：除『疗效结论互认（制度化）』外，其余机制均不替代目标国注册程序，"
          "仅可减少重复检查或走依赖/简略审评通道。")


def query(api_text, allow_fetch=True):
    resolver = AliasResolver()
    api_en, api_zh = resolver.normalize(api_text)
    conn = get_conn()
    rows = query_by_api(conn, api_en, api_zh)
    if not rows and allow_fetch:
        print("本地数据库暂无记录，正在向实时数据源定向抓取…")
        targeted_fetch(api_en)
        rows = query_by_api(conn, api_en, api_zh)
    if not rows:
        print(f"\n未找到 {api_text} 的相关获批记录。可尝试英文通用名，"
              f"或先运行 python main.py update 扩充数据库。")
        return
    codes = _print_results(rows, api_en, api_zh)
    _print_hints(codes)


def repl():
    print("全球仿制药许可查询（输入中/英文 API 名，q 退出）")
    while True:
        try:
            t = input("\nAPI> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if t.lower() in ("q", "quit", "exit"):
            break
        if t:
            query(t)
