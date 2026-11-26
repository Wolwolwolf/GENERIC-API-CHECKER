# GENERIC-API-CHECKER · 仿制药全球许可查询

输入一个仿制药 API（活性成分，支持中英双语），即可查询该成分在已接入市场公开来源覆盖范围内的相关获批产品记录，并了解与检索记录所属辖区可能相关的监管互认与依赖机制。

**在线使用**：https://wolwolwolf.github.io/GENERIC-API-CHECKER/

## 功能

- 🔎 **中英双语 API 查询**：支持英文通用名、中文译名及别名模糊匹配
- 🌍 **多市场产品记录**：覆盖美国（FDA）、欧盟（EC/EMA 集中程序）等官方公开数据
- 🔗 **来源链接**：每条记录附官方数据库原始链接或机构入口
- 🤝 **监管机制提示**：基于 reliance / 互认规则库，提示可能相关的机制；不代表查询企业已持有相应文件或满足适用条件
- 🔄 **每周自动更新**：GitHub Actions 每周一 09:17（北京时间）刷新美国 FDA 的 openFDA 时间窗增量和欧盟 Union Register，并重建页面

## 数据来源

| 市场 | 机构 | 来源 |
|------|------|------|
| 美国 | FDA | openFDA / Drugs@FDA |
| 欧盟 | 欧盟委员会 | Union Register of medicinal products（集中程序产品） |
| 中国 | NMPA / CDE | 化学药品目录集（中国上市药品目录集） |
| 英国 | MHRA | MHRA Products（Azure Search 公开 API） |
| 日本 | PMDA | PMDA 医药品情报检索（已导入记录；后续增量走导入脚本） |

其他市场（瑞士 Swissmedic、俄罗斯、东盟等）数据可通过 `imports/<CODE>.csv` 手工导入扩展。

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

## 使用边界

本工具仅聚合各国监管机构公开数据，供研究参考，不构成注册申报或法律意见。实际申报要求请以各监管机构官方规定为准。

互认／依赖提示由 API 检索结果所属辖区关联触发，仅表示存在可能相关的监管机制；不代表查询企业已持有相应资料、满足适用条件或可获得目标国接受。具体适用性须结合企业自身产品、生产场地、资料类型、出具机构、有效状态及目标国现行要求逐项核实。
