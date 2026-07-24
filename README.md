# GENERIC-API-CHECKER · 仿制药全球许可查询

输入一个仿制药 API（活性成分，支持中英双语），即可查询该成分在全球主要市场已获上市许可的药品目录，并提示已被特定监管机构认证的技术证明文件（CTD/DMF 等）可在哪些国家/地区复用（基于监管互认与信赖机制）。

**在线使用**：https://wolwolwolf.github.io/GENERIC-API-CHECKER/

## 功能

- 🔎 **中英双语 API 查询**：支持英文通用名、中文译名及别名模糊匹配
- 🌍 **多市场许可目录**：覆盖美国（FDA）、欧盟（EC/EMA 集中程序）等官方公开数据
- 🔗 **许可链接**：每条记录附官方数据库原始链接
- 🤝 **互认地图**：基于 reliance / 互认规则，提示某监管机构批准的证明文件可在哪些国家复用
- 🔄 **每周自动更新**：GitHub Actions 每周一 09:17（北京时间）从官方来源抓取新批数据并重建页面

## 数据来源

| 市场 | 机构 | 来源 |
|------|------|------|
| 美国 | FDA | openFDA / Drugs@FDA |
| 欧盟 | 欧盟委员会 | Union Register of medicinal products |

其他市场（中国 NMPA、英国 MHRA、瑞士 Swissmedic、日本 PMDA、俄罗斯、东盟等）数据可通过 `imports/<CODE>.csv` 手工导入扩展。

## 本地运行

无需第三方依赖（纯 Python 标准库，Python ≥ 3.10）：

```bash
# 更新数据库（从官方来源抓取）
python main.py update --days 35

# 命令行查询
python main.py query "metformin"

# 重新生成静态查询页面 index.html
python build_widget.py .
```

## 目录结构

```
index.html            # 静态查询页面（GitHub Pages 入口，自动生成）
build_widget.py       # 从数据库生成 index.html
main.py               # CLI：update / query / schedule
src/                  # 抓取、数据库、互认规则引擎
config/               # 数据源、API 别名、互认规则配置
data/generics.db      # SQLite 许可目录数据库
imports/              # 手工导入的 CSV（其他市场）
widget/template.html  # 页面模板
```

## 免责声明

本工具仅聚合各国监管机构公开数据，供研究参考，不构成注册申报或法律意见。实际申报要求请以各监管机构官方规定为准。
