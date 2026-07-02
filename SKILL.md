---
name: office-raccoon-star-dart
description: 在办公小浣熊中运行的 Star-DART OPC 专用 Skill。把 GitHub 新增 Star 仓库沉淀为仓库清单、飞书子文档、飞书多维表格台账、飞书多维表格仪表盘，并每周生成 Star 收藏回顾 PPT。用于小浣熊定时轮询 GitHub Star、生成项目文档、维护飞书目录和周回顾简报。
---

# Office Raccoon Star-DART Skill

本 Skill 运行在办公小浣熊里。它只做 Star-DART OPC 复赛演示真正需要的闭环：**新增 Star → 项目文档 → 飞书目录 → Base 台账/仪表盘 → 每周 PPT 回顾**。

## 安全配置

不要把 GitHub 用户名、飞书文档链接、Wiki token、Base token、table id 等私人信息写进 `SKILL.md`。运行前从 `.env` 读取配置；`.env` 不入库，只提交 `.env.example`。

配置变量：

| 变量 | 含义 |
| --- | --- |
| `GITHUB_USERNAME` | 要检查公开 Star 列表的 GitHub 用户名 |
| `GITHUB_TOKEN` | 可选；用于提高 GitHub API 限流额度，读取公开 Star 不强制需要 |
| `STAR_DART_WIKI_PARENT_NODE_TOKEN` | 飞书目录页对应的父级 Wiki node token，用于创建子文档或子节点 |
| `STAR_DART_DIRECTORY_DOC_URL` | 飞书目录页 URL，用于在目录正文追加条目 |
| `STAR_DART_DIRECTORY_DOC_TOKEN` | 飞书目录页 doc token；如只有 URL，先用 `lark-cli wiki +node-get` 或 `docs +fetch` 解析 |
| `STAR_DART_BASE_URL` | Star-DART 资产台账所在飞书 Base 链接；没有时可留空并新建 |
| `STAR_DART_BASE_TOKEN` | 已解析的 Base token；有 URL 时优先重新解析确认 |
| `STAR_DART_BASE_TABLE_ID` | 资产台账表 ID |
| `STAR_DART_BASE_DASHBOARD_ID` | Star-DART 仪表盘 ID；创建后写入 `.env`，便于更新看板 |
| `STAR_DART_POLL_INTERVAL_SECONDS` | 轮询周期，默认 `10800`，即 3 小时 |
| `STAR_DART_POLL_LIMIT` | 每次检查最近 Star 数，默认 `30` |
| `STAR_DART_WEEKLY_PPT_CRON` | 每周回顾 PPT 的计划时间说明，例如 `每周日 20:00` |

## 触发任务

当定时任务要求检查 `${GITHUB_USERNAME}` 的公开 Star 列表时，按本 Skill 执行。

办公小浣熊定时任务 Prompt 见 `references/scheduled_task_prompts.md`：一个用于每 3 小时检查新增 Star，一个用于每周生成回顾 PPT。

机制口径必须保持准确：

- 采用定时轮询，不是 GitHub Star 自动唤醒小浣熊。
- 默认轮询周期为 3 小时，可由用户通过 `.env` 自行调整。
- 当前小浣熊定时任务用于演示计划执行。
- 发现新增 Star 后，小浣熊负责生成文档、写入飞书多维表格、维护仪表盘和目录页。
- 不设置 systemd、launchd、Windows Task Scheduler 等系统级服务；使用办公小浣熊自己的定时任务功能执行脚本。

## 定时任务脚本

脚本入口：

```bash
python3 scripts/check_new_stars.py
```

脚本职责：

1. 读取 `.env`。
2. 调用 GitHub 公共 Star API，获取 `${GITHUB_USERNAME}` 最近 Star。
3. 用 `lark-cli base +record-list` 读取飞书 Base 中已有的 `仓库名称` 和 `GitHub URL`。
4. 对比 GitHub Star 与 Base 台账，只输出 Base 中缺失的新增仓库。
5. 把新增仓库渲染成办公小浣熊后续处理指令。

脚本不做的事：

- 不启动常驻服务。
- 不调用 OpenClaw webhook。
- 不自行生成飞书文档、Base 记录、仪表盘或 PPT。
- 不用本地状态文件替代飞书 Base 去重；飞书 Base 是入库事实来源。

办公小浣熊定时任务推荐命令：

```bash
cd /path/to/office-raccoon-star-dart-skill
python3 scripts/check_new_stars.py
```

如果脚本输出“本轮新增 Star 仓库”，小浣熊继续执行本 Skill 的“新增 Star”流程；如果没有新增仓库，只报告无新增即可。

演示或测试时可用本地样例，不访问 GitHub 或飞书：

```bash
python3 scripts/check_new_stars.py \
  --sample ./examples/sample_starred_repo.json \
  --existing-json ./examples/base_records_empty.json
```

## 输出范围

### 新增 Star 立即输出

| 输出 | 存放位置 | 说明 |
| --- | --- | --- |
| 仓库清单 | 小浣熊回复正文 | 只列出本轮新增仓库，方便用户快速确认 |
| 项目文档 | 飞书目录页下的子文档 | 每个 Star 仓库一份文档，是最重要的产物 |
| 目录条目 | 飞书目录页正文 | 追加项目文档链接，保持目录可浏览 |
| 资产台账 | 飞书多维表格 | 替代本地 Excel，不默认生成 xlsx |
| 仪表盘 | 飞书多维表格仪表盘 | 替代本地 HTML data-dashboard |

### 每周回顾输出

| 输出 | 存放位置 | 说明 |
| --- | --- | --- |
| 周回顾 PPT | 飞书目录页下的 Slides 子节点 | 总结本周 Star 收藏，用于强化记忆和复盘 |
| 周回顾目录条目 | 飞书目录页正文 | 追加 PPT 链接，和项目文档放在同一目录 |

### 不要默认输出

- 不生成 xlsx 资产台账。
- 不生成 HTML data-dashboard。
- 不生成社群周报文案。
- 不生成 docx / pdf 交付物。
- 不把规划中的云端订阅、MCP 网络说成已经完成。

## 执行流程：新增 Star

### 0. 运行脚本发现新增仓库

先由办公小浣熊定时任务运行：

```bash
python3 scripts/check_new_stars.py
```

脚本已经完成 GitHub Star 抓取和飞书 Base 比对。后续只处理脚本输出的新增仓库，不要重复处理 Base 中已有记录。

### 1. 生成仓库清单

先给出本轮新增仓库清单，只需要清楚，不需要写长报告。

```markdown
## 本轮新增 Star 仓库

| 仓库 | GitHub URL | Star 时间 | 触发来源 |
| --- | --- | --- | --- |
| owner/repo | https://github.com/owner/repo | 2026-xx-xxTxx:xx:xxZ | GitHub Star 定时轮询 |
```

如果本轮没有新增 Star：

```markdown
本轮没有发现新增 Star 仓库。轮询机制仍按默认 3 小时或用户自定义周期继续运行。
```

### 2. 为每个仓库生成项目文档

每个仓库生成一份独立 Markdown 文档，内容参考 `references/doc_template.md`。

文档原则：

- 不是翻译 README，而是提炼项目核心价值。
- 必须说明项目定位、为什么值得 Star、核心亮点、技术结构、适用场景和快速开始。
- README 或公开资料中没有的信息不要编造。
- 技术术语、函数名、变量名、包名保留英文。
- 标题格式：`{中文标题} - {owner/repo}`。

飞书写入前，必须先读取当前 `lark-cli` 内置文档规则：

```bash
lark-cli skills read lark-shared
lark-cli skills read lark-doc references/lark-doc-create.md
lark-cli skills read lark-doc references/lark-doc-md.md
```

推荐写入方式：先把 Markdown 内容保存为当前工作目录下的相对文件，例如 `./_star_doc_owner_repo.md`，再用 `@file` 写入，避免 shell 转义问题。

```bash
lark-cli docs +create \
  --as user \
  --parent-token "$STAR_DART_WIKI_PARENT_NODE_TOKEN" \
  --title "{中文标题} - {owner/repo}" \
  --doc-format markdown \
  --content @_star_doc_owner_repo.md
```

记录返回结果中的文档 URL、doc token 或 wiki node token，后续写入目录页和 Base 的 `文档链接` 字段。

### 3. 更新飞书目录页

新增项目文档后，必须把文档链接追加到目录页正文。目录页用于统一浏览项目文档和每周 PPT。

写入前读取文档更新规则：

```bash
lark-cli skills read lark-doc references/lark-doc-update.md
lark-cli skills read lark-doc references/lark-doc-md.md
```

追加条目格式：

```markdown
## Star 项目档案

- 2026-xx-xx｜[项目中文标题 - owner/repo](文档链接)｜技术方向｜推荐动作
```

推荐命令：

```bash
lark-cli docs +update \
  --as user \
  --doc "$STAR_DART_DIRECTORY_DOC_TOKEN" \
  --command append \
  --doc-format markdown \
  --content "- 2026-xx-xx｜[项目中文标题 - owner/repo](文档链接)｜技术方向｜推荐动作"
```

若目录页本身是 Wiki 链接，先用 `lark-cli wiki +node-get --as user --node-token "$STAR_DART_WIKI_PARENT_NODE_TOKEN"` 或等价命令解析真实文档对象；不要把 wiki token 猜成 doc token。

### 4. 写入飞书多维表格资产台账

资产台账使用飞书多维表格，不再使用 Excel。

如果用户已经提供 Base 链接或 token，先解析真实 `base_token`、`table_id`：

```bash
lark-cli skills read lark-base
lark-cli base +url-resolve --url "$STAR_DART_BASE_URL" --as user
```

如果需要新建 Base：

```bash
lark-cli skills read lark-base references/lark-base-field-json.md

lark-cli base +base-create \
  --as user \
  --name "Star-DART OPC 开源项目资产台账" \
  --table-name "Star 仓库资产" \
  --time-zone Asia/Shanghai \
  --fields '[{"name":"仓库名称","type":"text"},{"name":"项目名称","type":"text"},{"name":"GitHub URL","type":"text","style":{"type":"url"}},{"name":"Star 时间","type":"datetime"},{"name":"入库日期","type":"datetime"},{"name":"技术方向","type":"select","options":[{"name":"AI Agent / Skill"},{"name":"开发工具"},{"name":"知识资源 / Awesome List"},{"name":"前端 / 可视化"},{"name":"其他"}]},{"name":"推荐动作","type":"select","options":[{"name":"优先生成项目文档"},{"name":"优先拆解为 Skill/Agent 复用案例"},{"name":"纳入资源索引"},{"name":"进入观察池"},{"name":"暂不入库"}]},{"name":"复用等级","type":"select","options":[{"name":"高"},{"name":"中"},{"name":"低"}]},{"name":"一句话简介","type":"text"},{"name":"价值判断","type":"text"},{"name":"文档链接","type":"text","style":{"type":"url"}},{"name":"触发来源","type":"text"},{"name":"轮询周期","type":"text"},{"name":"语言","type":"text"},{"name":"Stars","type":"number"},{"name":"Forks","type":"number"},{"name":"License","type":"text"},{"name":"状态","type":"select","options":[{"name":"待生成文档"},{"name":"已生成文档"},{"name":"待补资料"},{"name":"观察中"}]}]'
```

写记录前必须读取 Base 写入规则，并确认真实字段：

```bash
lark-cli skills read lark-base references/lark-base-record-upsert.md
lark-cli skills read lark-base references/lark-base-cell-value.md
lark-cli base +field-list --as user --base-token "$STAR_DART_BASE_TOKEN" --table-id "$STAR_DART_BASE_TABLE_ID"
```

写入记录：

```bash
lark-cli base +record-upsert \
  --as user \
  --base-token "$STAR_DART_BASE_TOKEN" \
  --table-id "$STAR_DART_BASE_TABLE_ID" \
  --json '{
    "仓库名称": "owner/repo",
    "项目名称": "repo",
    "GitHub URL": "https://github.com/owner/repo",
    "Star 时间": "2026-07-02 10:00:00",
    "入库日期": "2026-07-02 10:00:00",
    "技术方向": "AI Agent / Skill",
    "推荐动作": "优先生成项目文档",
    "复用等级": "高",
    "一句话简介": "一句话说明项目是什么",
    "价值判断": "说明为什么值得沉淀或观察",
    "文档链接": "https://example.feishu.cn/docx/xxx",
    "触发来源": "GitHub Star 定时轮询：${GITHUB_USERNAME} starred_at=...",
    "轮询周期": "默认每 3 小时，可由用户自行调整",
    "语言": "TypeScript",
    "Stars": 1234,
    "Forks": 56,
    "License": "MIT",
    "状态": "已生成文档"
  }'
```

同一个仓库不要重复创建多条记录。若已存在，先查出 `record_id`，再带 `--record-id` 更新。

### 5. 更新飞书多维表格仪表盘

仪表盘使用飞书多维表格仪表盘，不再生成独立 HTML dashboard。

仪表盘至少包含：

| 模块 | 类型 | 指标 |
| --- | --- | --- |
| 项目总数 | 指标卡 | 当前台账记录数 |
| 技术方向分布 | 饼图或柱状图 | 按 `技术方向` 分组 |
| 推荐动作分布 | 柱状图 | 按 `推荐动作` 分组 |
| 复用等级分布 | 环形图或柱状图 | 按 `复用等级` 分组 |

创建或修改仪表盘前必须读取当前 `lark-cli` 仪表盘规则：

```bash
lark-cli skills read lark-base references/lark-base-dashboard.md
lark-cli skills read lark-base references/dashboard-block-data-config.md
```

如需新建仪表盘：

```bash
lark-cli base +dashboard-create \
  --as user \
  --base-token "$STAR_DART_BASE_TOKEN" \
  --name "Star-DART OPC 仪表盘"
```

创建图表块时，必须先用 `+table-list` 和 `+field-list` 确认真正的表名和字段名；`data_config` 使用表名和字段名，不使用猜测的 ID。

## 执行流程：每周 PPT 回顾

每周定时任务从飞书 Base 读取本周新增 Star 记录，生成一份精美 PPT，帮助用户回顾和强化记忆。PPT 不是每个仓库立即生成，而是周度汇总。

内容参考 `references/weekly_ppt_template.md`，建议 6-8 页：

1. 本周 Star 总览。
2. 分类分布和关键数字。
3. 最值得优先研究的 3 个项目。
4. 可复用 Skill / Agent / 工作流灵感。
5. 观察池与风险提醒。
6. 下周建议动作。

创建 PPT 前，必须读取当前 `lark-cli` Slides 规则：

```bash
lark-cli skills read lark-shared
lark-cli skills read lark-slides
lark-cli skills read lark-slides references/xml-schema-quick-ref.md
lark-cli skills read lark-slides references/planning-layer.md
lark-cli skills read lark-slides references/visual-planning.md
lark-cli skills read lark-slides references/asset-planning.md
lark-cli skills read lark-slides references/validation-checklist.md
```

创建方式：

```bash
lark-cli slides +create \
  --as user \
  --title "Star-DART 周回顾｜2026-Wxx"
```

复杂多页 PPT 先创建空白演示文稿，再按 `lark-slides` 规则逐页追加 XML。创建后必须回读验证页数、关键元素和布局风险。

将 PPT 放入同一飞书目录：

```bash
lark-cli wiki +node-create \
  --as user \
  --space-id my_library \
  --parent-node-token "$STAR_DART_WIKI_PARENT_NODE_TOKEN" \
  --obj-type slides \
  --title "Star-DART 周回顾｜2026-Wxx"
```

如果 `slides +create` 已经创建了演示文稿而 `wiki +node-create` 无法直接绑定现有对象，则使用 `lark-cli wiki +node-create --node-type shortcut --origin-node-token "<slides_wiki_node_token>"` 创建快捷方式，或按 `lark-wiki` / `lark-drive` 当前规则移动到目录页下；不要伪造链接。

最后把 PPT 链接追加到目录页正文：

```markdown
## 每周 Star 回顾 PPT

- 2026-Wxx｜[Star-DART 周回顾](PPT链接)｜本周新增 N 个 Star｜重点：xxx / xxx / xxx
```

## 最终回复用户

新增 Star 任务完成后：

```markdown
已完成本轮 Star-DART 处理：

- 仓库清单：本轮新增 {N} 个仓库。
- 项目文档：已在飞书目录页下创建 {N} 个子文档。
- 目录维护：已在目录页追加 {N} 条项目文档入口。
- 资产台账：已写入飞书多维表格 {N} 条记录。
- 仪表盘：已更新飞书多维表格仪表盘。

机制说明：本任务采用定时轮询，默认 3 小时，可由用户自行调整；当前小浣熊定时任务用于演示计划执行，GitHub Star 本身不会自动唤醒小浣熊。
```

每周 PPT 任务完成后：

```markdown
已完成 Star-DART 本周回顾：

- 周回顾 PPT：已生成并放入飞书目录页下。
- 目录维护：已在目录页追加本周 PPT 入口。
- 覆盖范围：本周新增 {N} 个 Star，重点回顾 {M} 个项目。
```

## 质量检查

每次执行后检查：

- 仓库清单没有遗漏本轮新增 Star。
- 每个新增 Star 都有一个飞书子文档。
- 每个子文档都创建在 `.env` 指定的飞书目录页下。
- 目录页正文已追加项目文档或周回顾 PPT 入口。
- 每个子文档都符合 `references/doc_template.md` 的结构。
- 飞书多维表格中每个新增 Star 都有一条记录。
- 台账记录包含文档链接，能从 Base 跳转到对应项目文档。
- 仪表盘来自飞书多维表格，不是本地 HTML。
- 每周 PPT 只在周回顾任务中生成，不在每个 Star 入库时生成。
- 没有默认生成社群周报、xlsx、HTML dashboard、docx、pdf。
- 没有在 `SKILL.md` 或提交文件中硬编码私人 GitHub 信息、飞书链接或 token。
