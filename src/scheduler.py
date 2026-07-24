"""每周自动更新调度器（进程内常驻模式）。
用法：python main.py schedule
进程每小时检查一次；距上次更新满 7 天即自动执行更新。
如需无人值守，建议改用 Windows 任务计划程序（见 README）。
"""
import time
from datetime import datetime

from .db import get_conn, get_meta
from .updater import run_update

INTERVAL_DAYS = 7
CHECK_SECONDS = 3600


def due(conn):
    last = get_meta(conn, "last_update")
    if not last:
        return True
    return (datetime.now() - datetime.fromisoformat(last)).days >= INTERVAL_DAYS


def run_scheduler():
    print("每周自动更新调度器已启动（Ctrl+C 退出）。")
    while True:
        conn = get_conn()
        if due(conn):
            print(f"[{datetime.now():%Y-%m-%d %H:%M}] 到达更新周期，开始抓取…")
            try:
                run_update()
            except Exception as e:
                print(f"更新失败：{e}")
        else:
            last = get_meta(conn, "last_update")
            print(f"[{datetime.now():%Y-%m-%d %H:%M}] 未到周期（上次更新：{last}），一小时后再检查。")
        conn.close()
        time.sleep(CHECK_SECONDS)
