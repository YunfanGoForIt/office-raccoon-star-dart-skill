# 办公小浣熊定时任务 Prompt

本文件用于在办公小浣熊里创建两个定时任务。敏感信息不要写进 Prompt；统一放在本 Skill 目录的 `.env` 中。

## 任务一：GitHub Star 定时入库

推荐频率：每 3 小时一次。

```text
请按 `office-raccoon-star-dart` Skill 执行 GitHub Star 定时入库任务。

运行边界：
1. 不设置 systemd、launchd、Windows Task Scheduler 等系统级服务。
2. 本任务采用办公小浣熊定时执行；GitHub Star 本身不会自动唤醒小浣熊。
3. 所有敏感信息从当前 Skill 目录的 `.env` 读取，不要把 GitHub 用户名、飞书链接、Base token、table id 写进回复或 Skill 文档。
4. 当前作为演示任务，仅处理本机时区 `.env` 中 `STAR_DART_STARRED_SINCE` 起新增的 Star 仓库；默认从 `2026-07-02` 开始。

执行步骤：
1. 进入 `office-raccoon-star-dart-skill` 目录。
2. 运行 `python3 scripts/check_new_stars.py`。
3. 如果脚本提示本轮没有新增 Star，只回复无新增，并说明轮询仍会按 `.env` 中的周期继续。
4. 如果脚本输出“本轮新增 Star 仓库”，只处理脚本列出的新增仓库；不要处理 `2026-07-02` 之前 Star 的仓库，也不要重复处理 Base 已有记录。
5. 对每个新增仓库，参考 `references/doc_template.md` 生成一份项目文档，重点说明项目定位、为什么值得 Star、核心亮点、技术结构、适用场景、快速开始、边界与待确认。
6. 使用 `lark-cli` 在 `.env` 指定的飞书目录页下创建项目子文档。
7. 在同一个飞书目录页正文追加项目文档入口。
8. 确认 `.env` 指定的飞书多维表格资产台账是目录页下的 `bitable` 子节点；如果不在目录页下，先使用 `lark-cli wiki +move` 迁入，或在目录页下新建。
9. 写入或更新 `.env` 指定的飞书多维表格资产台账。
10. 确认飞书多维表格仪表盘基于最新台账可用；不要生成本地 HTML dashboard。

输出要求：
- 回复本轮新增仓库清单、创建的飞书子文档数量、目录页追加数量、Base 子节点状态、Base 写入数量、仪表盘状态。
- 不生成社群周报、xlsx、HTML dashboard、docx、pdf。
- PPT 只在每周回顾任务中生成，不在单次 Star 入库任务中生成。
- 机制说明必须写明：本任务采用定时轮询，默认 3 小时，可由用户自行调整；当前小浣熊定时任务用于演示计划执行，GitHub Star 本身不会自动唤醒小浣熊。
```

## 任务二：每周 Star 回顾 PPT

推荐频率：每周日 20:00。

```text
请按 `office-raccoon-star-dart` Skill 执行每周 Star 回顾 PPT 任务。

运行边界：
1. 本任务只做周度回顾，不重新抓取 GitHub Star。
2. 数据来源是 `.env` 指定且挂在目录页下的飞书多维表格资产台账，以及已经创建的项目子文档。
3. 所有敏感信息从当前 Skill 目录的 `.env` 读取，不要把飞书链接、Base token、table id 写进回复或 Skill 文档。

执行步骤：
1. 读取当前 Skill 的 `SKILL.md`。
2. 参考 `references/weekly_ppt_template.md` 规划 6-8 页周回顾 PPT。
3. 使用 `lark-cli base` 从 `.env` 指定的飞书多维表格读取本周新增 Star 记录。
4. 汇总本周新增数量、技术方向分布、推荐动作分布、复用等级分布。
5. 阅读本周收藏的所有star仓库的文档（按照飞书多维表格的链接），说明一句话定位、价值判断、下一步动作。
6. 使用办公小浣熊 ppt skill 能力生成一份精美 PPT。
7. 将 PPT 放入 `.env` 指定的飞书目录页下。
8. 在同一个飞书目录页正文追加本周 PPT 入口。

输出要求：
- 回复本周新增 Star 数、重点回顾项目数、PPT 标题、PPT 是否已放入目录页、目录页是否已追加入口。
- PPT 是周度记忆强化产物，不为每个 Star 单独生成 PPT。
- 不生成社群周报、xlsx、HTML dashboard、docx、pdf。
```
