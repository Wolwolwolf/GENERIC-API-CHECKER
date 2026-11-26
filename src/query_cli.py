"""查询界面：输入仿制药 API（中/英文），显示各国同 API 相关公开产品记录、
来源链接，并提示可能相关的监管互认／依赖机制及其适用条件边界。"""
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

    print(f"\n已在 {len(by_country)} 个经济体/监管机构辖区发现同 API 相关公开产品记录，共 {len(rows)} 条：\n")
    auth_codes = set()
    for (country, authority), items in sorted(by_country.items()):
        print(f"● {country} — {authority}（{len(items)} 条）")
        for it in items[:10]:
            date = it["approval_date"] or "日期未知"
            lic = it["license_number"] or "-"
            print(f"    · {it['product_name']}  |  批准: {it['approval_date'] or date}  |  批件号: {lic}")
            if it["url"]:
                print(f"      链接: {it['url']}")
        if len(items) > 10:
            print(f"    … 其余 {len(items) - 10} 条略")
        # 归集机构代码用于关联可能相关的监管机制
        names = _authority_names()
        for code, label in names.items():
            if label.startswith(country) or authority in label or country in label:
                auth_codes.add(code)
    return auth_codes


def _print_hints(auth_codes):
    hints = reliance_hints(auth_codes)
    names = _authority_names()
    print("\n" + "-" * 72)
    print("潜在相关监管互认/依赖机制（须核对企业与项目适用条件）")
    print("-" * 72)
    if not hints:
        print("暂无命中的互认机制。")
        return
    print("以下提示由检索记录所属辖区关联触发，不代表查询企业已持有相应资料，"
          "也不代表资料可被目标国接受。须结合企业自身产品、生产场地、文件类型、"
          "出具机构、有效状态及目标国现行要求逐项核实。")
    for h in hints:
        targets = [names.get(c, c) for c in h["usable_in"]]
        target_str = "；".join(targets) if targets else "（无自动互认目标，见说明）"
        print(f"\n■ 机制 {h['id']} — {h['scope']}")
        print(f"  文件类型: {h['doc_type']}")
        print(f"  可能涉及的目标辖区: {target_str}")
        print(f"  说明: {h['note']}")
    print("\n提示：无论何种互认或依赖机制，均不构成目标国自动接受或批准；"
          "具体适用条件以目标机构现行规定和专业复核为准。")


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
