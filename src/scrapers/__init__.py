"""数据源注册表：按 config/sources.json 装配各监管机构适配器。
adapter 类型：
- fda：openFDA 实时抓取
- ema：欧盟共同体注册簿 XLSX
- csv：官方检索结果手工导出后放入 imports/<CODE>.csv，由导入器合并
"""
from .base import import_csv_files
from .ema import EmaScraper
from .fda import FdaScraper


def build_scrapers(sources_cfg, resolver):
    scrapers = {}
    for cfg in sources_cfg["authorities"]:
        adapter = cfg.get("adapter")
        if adapter == "fda":
            scrapers[cfg["code"]] = FdaScraper(cfg, resolver)
        elif adapter == "ema":
            scrapers[cfg["code"]] = EmaScraper(cfg, resolver)
        # csv 类型不实例化 scraper，由 updater 调 import_csv_files
    return scrapers
