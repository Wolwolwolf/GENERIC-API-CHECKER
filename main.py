"""全球仿制药许可查询与跟踪工具
用法：
  python main.py query "阿托伐他汀"     查询单个 API
  python main.py query                  进入交互模式
  python main.py update [--days 30]     立即执行一次更新（默认回溯 30 天或自上次更新起）
  python main.py schedule               启动常驻进程，每 7 天自动更新
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.query_cli import query, repl  # noqa: E402
from src.updater import run_update  # noqa: E402
from src.scheduler import run_scheduler  # noqa: E402


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return
    cmd = args[0]
    if cmd == "query":
        if len(args) > 1:
            query(" ".join(args[1:]))
        else:
            repl()
    elif cmd == "update":
        days = None
        if "--days" in args:
            i = args.index("--days")
            days = int(args[i + 1])
        run_update(days_back=days)
    elif cmd == "schedule":
        run_scheduler()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
