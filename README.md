# Office Raccoon Star-DART Skill

把 GitHub Star 从“收藏链接”变成“可检索、可复盘、可复用”的开源项目知识资产。

本仓库是一套面向办公小浣熊运行的 Skill：由办公小浣熊定时执行脚本检查 GitHub 公开 Star 列表，发现新增仓库后生成项目文档，写入飞书目录、飞书多维表格和飞书仪表盘，并在每周生成一份 Star 收藏回顾 PPT。

## 项目定位

开发者经常 Star 很多优秀开源项目，但真正做项目时仍然会忘记当初为什么收藏、如何复用、风险在哪里。Star-DART 的目标不是再做一个链接收藏夹，而是让每一次 Star 都进入一个可持续沉淀的办公知识流：

```text
GitHub Star 定时轮询
  ↓
发现飞书 Base 中尚未入库的新仓库
  ↓
办公小浣熊生成项目文档
  ↓
写入飞书目录页与飞书多维表格
  ↓
飞书仪表盘持续统计
  ↓
每周生成 PPT 回顾，强化记忆
```

## 当前输出

| 输出 | 位置 | 说明 |
| --- | --- | --- |
| 本轮仓库清单 | 小浣熊回复正文 | 只列出本轮新增 Star |
| 项目文档 | 飞书目录页下的子文档 | 每个新增仓库一份，是核心产物 |
| 目录入口 | 飞书目录页正文 | 追加项目文档和周回顾 PPT 链接 |
| 资产台账 | 飞书多维表格 | 替代本地 Excel 台账 |
| 仪表盘 | 飞书多维表格仪表盘 | 替代本地 HTML Dashboard |
| 周回顾 PPT | 飞书目录页下的 Slides / PPT | 每周总结本周 Star 收藏 |

默认不生成社群周报、xlsx、HTML Dashboard、docx 或 pdf。PPT 是周度回顾产物，不为每个 Star 单独生成。

## 仓库结构

```text
.
├── SKILL.md
├── README.md
├── .env.example
├── scripts/
│   └── check_new_stars.py
├── references/
│   ├── doc_template.md
│   ├── github_stars.md
│   ├── scheduled_task_prompts.md
│   ├── tags.md
│   ├── tags.json
│   └── weekly_ppt_template.md
├── examples/
│   ├── base_records_empty.json
│   ├── base_records_existing.json
│   └── sample_starred_repo.json
├── tests/
│   └── test_check_new_stars.py
└── docs/
    └── Star-DART-OPC-复赛路演大纲_产品重新梳理版.md
```

## 配置方式

复制环境变量模板：

```bash
cp .env.example .env
```

在 `.env` 中填写 GitHub、飞书目录页、飞书多维表格和轮询配置。不要把 `.env`、真实 GitHub 用户名、飞书链接、Base token、table id 或 dashboard id 提交到仓库。

关键变量：

| 变量 | 用途 |
| --- | --- |
| `GITHUB_USERNAME` | 要检查公开 Star 列表的 GitHub 用户名 |
| `GITHUB_TOKEN` | 可选，用于提高 GitHub API 限流额度 |
| `STAR_DART_WIKI_PARENT_NODE_TOKEN` | 飞书目录页父级 Wiki node token |
| `STAR_DART_DIRECTORY_DOC_TOKEN` | 飞书目录页 doc token |
| `STAR_DART_BASE_TOKEN` | 飞书多维表格 base token |
| `STAR_DART_BASE_TABLE_ID` | 飞书多维表格 table id |
| `STAR_DART_BASE_DASHBOARD_ID` | 飞书多维表格仪表盘 id |
| `STAR_DART_POLL_INTERVAL_SECONDS` | 轮询周期，默认 `10800` 秒 |
| `STAR_DART_POLL_LIMIT` | 每次检查最近 Star 数，默认 `30` |

## 本地演示

不访问 GitHub 或飞书，直接使用样例数据：

```bash
python3 scripts/check_new_stars.py \
  --sample examples/sample_starred_repo.json \
  --existing-json examples/base_records_empty.json
```

预期输出包括：

- 本轮新增 Star 仓库清单
- 办公小浣熊后续处理指令
- 可写入飞书 Base 的记录种子
- 定时轮询机制说明

如果要测试“已入库仓库不重复处理”：

```bash
python3 scripts/check_new_stars.py \
  --sample examples/sample_starred_repo.json \
  --existing-json examples/base_records_existing.json
```

## 办公小浣熊定时任务

本项目不设置 systemd、launchd 或 Windows Task Scheduler。定时执行交给办公小浣熊。

定时任务 Prompt 见：

```text
references/scheduled_task_prompts.md
```

推荐创建两个任务：

| 任务 | 频率 | 作用 |
| --- | --- | --- |
| GitHub Star 定时入库 | 每 3 小时 | 运行脚本，发现新增 Star 后生成项目文档并入库 |
| 每周 Star 回顾 PPT | 每周日 20:00 | 汇总本周新增 Star，生成一份回顾 PPT |

机制口径必须保持一致：本任务采用定时轮询，默认 3 小时，可由用户自行调整；当前小浣熊定时任务用于演示计划执行，GitHub Star 本身不会自动唤醒办公小浣熊。

## 真实运行命令

在办公小浣熊定时任务中进入本仓库目录后运行：

```bash
python3 scripts/check_new_stars.py
```

脚本职责很克制：

1. 读取 `.env`。
2. 调用 GitHub Star API。
3. 通过 `lark-cli base +record-list` 读取飞书 Base 已有仓库。
4. 对比仓库名称和 GitHub URL。
5. 只输出飞书 Base 中缺失的新增仓库。

脚本不会自行生成飞书文档、仪表盘或 PPT；这些动作由办公小浣熊按照 `SKILL.md` 和 `references/` 中的模板继续完成。

## 飞书资产闭环

新增 Star 处理时，办公小浣熊按以下顺序执行：

1. 参考 `references/doc_template.md` 为每个仓库生成项目文档。
2. 使用 `lark-cli` 在飞书目录页下创建子文档。
3. 在目录页正文追加项目文档入口。
4. 写入或更新飞书多维表格资产台账。
5. 确认飞书多维表格仪表盘可展示项目总数、技术方向分布、推荐动作分布和复用等级分布。

每周回顾时，办公小浣熊参考 `references/weekly_ppt_template.md` 生成 6-8 页 PPT，并把 PPT 放入同一个飞书目录页下，同时追加目录入口。

## 测试

运行单元测试：

```bash
python3 -m unittest discover -s tests
```

建议在提交前同时做一次敏感信息检查，确保没有把真实飞书链接、token、table id 或私人 GitHub 配置写入仓库文件。

## 边界

- GitHub Star 不会自动唤醒小浣熊；本项目使用定时轮询。
- 飞书 Base 是去重事实来源，不使用本地状态文件替代 Base。
- 项目文档不是 README 翻译，而是围绕“为什么值得 Star、如何复用、有什么风险”做结构化研判。
- 不把规划中的云服务、MCP 网络或商业化能力说成当前已完成能力。
