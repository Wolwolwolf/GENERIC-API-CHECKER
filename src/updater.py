"""更新器：调度各数据源抓取新获批仿制药并合并入库。"""
from datetime import datetime, timedelta

from .db import get_conn, set_meta, get_meta, upsert_products, load_config
from .aliases import AliasResolver
from .scrapers import build_scrapers
from .scrapers.base import import_csv_files


def run_update(days_back=None, verbose=True):
    """执行一次更新。
    days_back: 覆盖回溯天数；默认从上次成功更新起算，首次默认回溯 30 天。
    """
    conn = get_conn()
    sources_cfg = load_config("sources.json")
    resolver = AliasResolver()
    scrapers = build_scrapers(sources_cfg, resolver)

    last = get_meta(conn, "last_update")
    if days_back is not None:
        start = datetime.now() - timedelta(days=days_back)
    elif last:
        start = datetime.fromisoformat(last) - timedelta(days=1)  # 重叠一天防漏
    else:
        start = datetime.now() - timedelta(days=30)
    start_s, end_s = start.strftime("%Y%m%d"), datetime.now().strftime("%Y%m%d")

    total_new = 0
    # 1) 实时数据源
    for code, scraper in scrapers.items():
        if verbose:
            print(f"→ 更新 {code} ...")
        try:
            if hasattr(scraper, "fetch_window"):
                recs = scraper.fetch_window(start_s, end_s)
            else:
                recs = scraper.fetch_new(since=start)
        except Exception as e:
            print(f"  [{code}] 失败：{e}")
            continue
        if recs:
            n_new, _ = upsert_products(conn, recs)
            total_new += n_new
            if verbose:
                print(f"  [{code}] 合并 {len(recs)} 条，新增 {n_new} 条")
        elif verbose:
            print(f"  [{code}] 无新数据")

    # 2) CSV 手工导入源（各官方检索系统导出文件）
    for cfg in sources_cfg["authorities"]:
        if cfg.get("adapter") != "csv":
            continue
        recs = import_csv_files(conn, resolver, cfg)
        if recs:
            n_new, _ = upsert_products(conn, recs)
            total_new += n_new
            if verbose:
                print(f"  [{cfg['code']}] 从 imports/{cfg['code']}.csv 导入 {len(recs)} 条，新增 {n_new} 条")

    set_meta(conn, "last_update", datetime.now().isoformat(timespec="seconds"))
    if verbose:
        print(f"更新完成，本次新增 {total_new} 条记录。")
    return total_new


def targeted_fetch(api_en):
    """查询时若本地无数据，对启用的实时源做定向抓取补库。"""
    conn = get_conn()
    sources_cfg = load_config("sources.json")
    resolver = AliasResolver()
    scrapers = build_scrapers(sources_cfg, resolver)
    added = 0
    for code, scraper in scrapers.items():
        recs = scraper.fetch_api(api_en) or []
        if recs:
            n_new, _ = upsert_products(conn, recs)
            added += n_new
            print(f"  [{code}] 定向抓取并新增 {n_new} 条")
    return added
