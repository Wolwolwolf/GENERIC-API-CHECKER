# 仿制药全球许可查询系统 · 使用与维护说明（一页纸）

> 文档修订：2026-11-26 ｜ 数据规模以页面快照为准（2026-07-24 快照为 49,924 条）

## 一、这是什么

一个纯静态网页工具：输入仿制药 API（中/英/日文）或厂家名称，即时显示该 API 在
**美国、欧盟、英国、中国、日本** 已接入官方来源覆盖范围内的相关获批产品记录（含来源链接），
并根据互认规则库提示与检索记录所属辖区可能相关的监管互认／依赖机制。
互认地图覆盖：美、欧、英、瑞士、日、中、俄、印度、东盟十国。

| 入口 | 地址 |
|---|---|
| 公开网页（可分享他人） | https://wolwolwolf.github.io/GENERIC-API-CHECKER/ |
| 本地离线版 | 工作区根目录 `仿制药全球许可查询.html`（双击即用） |
| 对话内 Widget | Kimi Work 对话中的「仿制药全球许可查询」卡片 |
| 源码仓库 | https://github.com/Wolwolwolf/GENERIC-API-CHECKER |

## 二、数据从哪来（2026-07-24 快照为 49,924 条）

| 辖区 | 条数 | 来源与更新方式 |
|---|---|---|
| 美国 FDA | 20,662 | Drugs@FDA 全量 ANDA 导入；日常周更通过 openFDA 按时间窗增量更新；需要全量校正时重跑 `fda_full_import.py` |
| 中国 NMPA | 16,567 | CDE 化学药品目录集（浏览器自动化全量抓取）。更新 = 重新抓取后跑 `import_nmpa.py` |
| 英国 MHRA | 10,470 | MHRA Products 抓取。更新 = 重跑 `mhra_fetch.py` |
| 欧盟 | 1,543 | Union Register 集中程序产品。GitHub Actions 每周自动刷新 |
| 日本 PMDA | 682 | PMDA 医药品情报检索（347 个 API）。增量 = 重抓后跑 `import_pmda.py` |
| 印度 CDSCO | 0（待导入） | 官网无公开注册库，走手工 CSV 通道（见下） |
| 俄罗斯 GRLS | 0（已暂停） | 检索强制验证码 + 必填筛选字段，自动抓取已放弃，可手工 CSV |

## 三、日常维护操作

### 1. 手工导入新辖区 / 补充数据（印度、东盟、瑞士等）
1. 把数据整理成 CSV 放进 `generic_drug_tracker/imports/<机构代码>.csv`
   - 必填列：`api_en`（英文通用名小写）、`product_name`
   - 可选列：`api_zh`、`applicant`、`approval_date`、`license_number`、`url`
   - 模板：`imports/CDSCO.csv`（`#` 开头为注释行）
2. 运行对应导入脚本：`cd generic_drug_tracker && python import_cdsco.py`
   （无专属脚本时走通用 CSV 通道，机构代码见 `config/sources.json`）
3. 执行下方「发布更新」。

### 2. 发布更新（重建三处页面 + 上线）
在 `NVBP&GENERICS` 工作区下依次执行：
```bash
cp generic_drug_tracker/widget/template.html generic-api-checker-site/widget/template.html
cp generic_drug_tracker/config/sources.json generic-api-checker-site/config/sources.json
cp generic_drug_tracker/data/generics.db generic-api-checker-site/data/generics.db
cd generic-api-checker-site && python build_widget.py . && cd ..
cd generic_drug_tracker && python build_widget.py "<Widget workspace 路径>" && cd ..
cp generic-api-checker-site/index.html "仿制药全球许可查询.html"
cd generic-api-checker-site && git add -A && git commit -m "update" && git push
```
推送后约 60–75 秒 GitHub Pages 自动部署完成。
（Widget workspace 路径见交接笔记；git 代理已配置 127.0.0.1:10809）

### 3. 周更
- 自动：GitHub Actions 每周刷新美国 FDA 的 openFDA 时间窗增量和欧盟 Union Register。
- 其余辖区按月/按季度手工重跑各自抓取脚本即可，无需每周。

## 四、关键文件

| 文件 | 作用 |
|---|---|
| `generic_drug_tracker/data/generics.db` | 主数据库（SQLite，唯一事实源） |
| `generic_drug_tracker/config/api_aliases.json` | API 别名库（350 条，中/英/日） |
| `generic_drug_tracker/config/reliance_rules.json` | 技术证明文件互认规则库 |
| `generic_drug_tracker/config/sources.json` | 18 个机构数据源配置 |
| `generic_drug_tracker/widget/template.html` | 页面模板（改界面只改它，再同步到 site） |
| `generic_drug_tracker/build_widget.py` | 把数据库+模板合成单文件网页 |

## 五、已知限制

- MHRA 记录无厂家字段 → 厂家检索查不到英国结果（API 检索正常）
- PMDA 抓取按 INN 全量收录，含原研产品，不仅限于仿制药
- 印度/俄罗斯暂无数据；东盟十国仅有规则与界面占位，未接入产品库
- 互认提示由 API 检索结果所属辖区关联触发，仅表示该辖区存在可能相关的监管机制；不代表查询企业已持有相应资料、满足适用条件或可获得目标国接受。须结合企业自身产品、生产场地、资料类型、出具机构、有效状态及目标国现行要求逐项核实。互认／依赖提示不替代目标国注册程序或专业复核

---
维护人：Wolwolwolf ｜ 本文件随仓库分发（MAINTENANCE.md）
