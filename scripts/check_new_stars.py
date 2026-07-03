#!/usr/bin/env python3
"""
Check a GitHub user's public Star list and compare it with a Feishu Base ledger.

This script is designed for Office Raccoon's scheduled task:
- Office Raccoon runs this script periodically.
- The script fetches recent public GitHub Stars.
- The script reads the Feishu Base ledger through lark-cli.
- Repositories missing from Base are printed as a Star-DART processing task.

It does not start a system service, trigger OpenClaw, or generate documents by itself.
Office Raccoon should continue with SKILL.md after this script reports new repos.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any


DEFAULT_POLL_INTERVAL_SECONDS = 3 * 60 * 60
DEFAULT_LIMIT = 30
DEFAULT_STARRED_SINCE = "2026-07-02"
BASE_REPO_FIELD = "仓库名称"
BASE_URL_FIELD = "GitHub URL"


@dataclass(frozen=True)
class StarRepo:
    full_name: str
    html_url: str
    description: str
    starred_at: str
    language: str
    stars: int | None
    forks: int | None
    license_name: str


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github.star+json",
        "User-Agent": "office-raccoon-star-dart",
    }
    token = env("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def fetch_recent_public_stars(username: str, limit: int) -> list[StarRepo]:
    if not username:
        raise ValueError("请在 .env 中设置 GITHUB_USERNAME")

    params = urllib.parse.urlencode(
        {
            "per_page": max(1, min(limit, 100)),
            "sort": "created",
            "direction": "desc",
        }
    )
    url = f"https://api.github.com/users/{urllib.parse.quote(username)}/starred?{params}"
    request = urllib.request.Request(url, headers=github_headers())

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API 请求失败：HTTP {exc.code} {detail}") from exc

    repos: list[StarRepo] = []
    for item in payload:
        repo = item.get("repo", item)
        license_info = repo.get("license") or {}
        repos.append(
            StarRepo(
                full_name=repo.get("full_name", ""),
                html_url=repo.get("html_url", ""),
                description=repo.get("description") or "",
                starred_at=item.get("starred_at") or repo.get("created_at", ""),
                language=repo.get("language") or "",
                stars=repo.get("stargazers_count"),
                forks=repo.get("forks_count"),
                license_name=license_info.get("spdx_id") or license_info.get("name") or "",
            )
        )
    return [repo for repo in repos if repo.full_name and repo.html_url]


def run_lark_cli_record_list(base_token: str, table_id: str, limit: int = 200, offset: int = 0) -> dict[str, Any]:
    command = [
        "lark-cli",
        "base",
        "+record-list",
        "--as",
        "user",
        "--base-token",
        base_token,
        "--table-id",
        table_id,
        "--field-id",
        BASE_REPO_FIELD,
        "--field-id",
        BASE_URL_FIELD,
        "--limit",
        str(limit),
        "--offset",
        str(offset),
        "--format",
        "json",
    ]
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "lark-cli base +record-list failed")
    return json.loads(result.stdout)


def iter_record_field_maps(payload: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            fields = node.get("fields")
            if isinstance(fields, dict):
                records.append(fields)
            for key in ("records", "items", "data"):
                if key in node:
                    visit(node[key])
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(payload)
    return records


def normalize_cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        parts = [normalize_cell(item) for item in value]
        return " ".join(part for part in parts if part).strip()
    if isinstance(value, dict):
        for key in ("text", "link", "url", "name"):
            if key in value:
                return normalize_cell(value[key])
        return " ".join(normalize_cell(item) for item in value.values()).strip()
    return str(value).strip()


def existing_repo_keys_from_payload(payload: Any) -> set[str]:
    keys: set[str] = set()
    for fields in iter_record_field_maps(payload):
        repo_name = normalize_cell(fields.get(BASE_REPO_FIELD))
        github_url = normalize_cell(fields.get(BASE_URL_FIELD))
        if repo_name:
            keys.add(repo_name.lower())
        if github_url:
            keys.add(github_url.rstrip("/").lower())
    return keys


def fetch_existing_repo_keys(base_token: str, table_id: str) -> set[str]:
    if not base_token or not table_id:
        raise ValueError("请设置 STAR_DART_BASE_TOKEN 和 STAR_DART_BASE_TABLE_ID，脚本需要用 Base 作为去重来源")

    keys: set[str] = set()
    offset = 0
    limit = 200
    while True:
        payload = run_lark_cli_record_list(base_token, table_id, limit=limit, offset=offset)
        page_keys = existing_repo_keys_from_payload(payload)
        keys.update(page_keys)
        record_count = len(iter_record_field_maps(payload))
        if record_count < limit:
            break
        offset += limit
    return keys


def find_new_repos(stars: list[StarRepo], existing_keys: set[str]) -> list[StarRepo]:
    new_repos: list[StarRepo] = []
    for repo in stars:
        repo_key = repo.full_name.lower()
        url_key = repo.html_url.rstrip("/").lower()
        if repo_key not in existing_keys and url_key not in existing_keys:
            new_repos.append(repo)
    return new_repos


def parse_since_datetime(value: str) -> datetime | None:
    normalized = value.strip()
    if not normalized:
        return None
    if len(normalized) == 10:
        local_tz = datetime.now().astimezone().tzinfo
        return datetime.combine(datetime.fromisoformat(normalized).date(), time.min, tzinfo=local_tz).astimezone(timezone.utc)
    parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_starred_at(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def filter_repos_starred_since(stars: list[StarRepo], since: datetime | None) -> list[StarRepo]:
    if since is None:
        return stars
    return [repo for repo in stars if (starred_at := parse_starred_at(repo.starred_at)) is not None and starred_at >= since]


def repo_to_base_seed(repo: StarRepo) -> dict[str, Any]:
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
    source_user = env("GITHUB_USERNAME") or "配置的 GitHub 用户"
    return {
        "仓库名称": repo.full_name,
        "项目名称": repo.full_name.split("/", 1)[-1],
        "GitHub URL": repo.html_url,
        "Star 时间": repo.starred_at,
        "入库日期": now,
        "语言": repo.language,
        "Stars": repo.stars,
        "Forks": repo.forks,
        "License": repo.license_name,
        "触发来源": f"GitHub Star 定时轮询：{source_user} starred_at={repo.starred_at}",
        "轮询周期": f"默认每 {DEFAULT_POLL_INTERVAL_SECONDS // 3600} 小时，可由用户自行调整",
        "状态": "待生成文档",
    }


def render_markdown(new_repos: list[StarRepo], checked_count: int, starred_since: str = "") -> str:
    poll_interval = env("STAR_DART_POLL_INTERVAL_SECONDS", str(DEFAULT_POLL_INTERVAL_SECONDS))
    filter_line = f"- 演示筛选范围：仅处理本机时区 `{starred_since}` 起新增的 Star 仓库\n" if starred_since else ""
    if not new_repos:
        return (
            "# Star-DART 新增 Star 检查结果\n\n"
            f"- 检查最近 Star 数：{checked_count}\n"
            f"{filter_line}"
            f"- 轮询周期：{poll_interval} 秒\n"
            "- 结果：本轮没有发现飞书多维表格中缺失的新增 Star 仓库。\n\n"
            "机制说明：本任务采用定时轮询，默认 3 小时，可由用户自行调整；"
            "GitHub Star 本身不会自动唤醒办公小浣熊。\n"
        )

    lines = [
        "# Star-DART 新增 Star 检查结果",
        "",
        f"- 检查最近 Star 数：{checked_count}",
        *( [f"- 演示筛选范围：仅处理本机时区 `{starred_since}` 起新增的 Star 仓库"] if starred_since else [] ),
        f"- 新增待处理仓库：{len(new_repos)}",
        f"- 轮询周期：{poll_interval} 秒",
        "",
        "## 本轮新增 Star 仓库",
        "",
        "| 仓库 | GitHub URL | Star 时间 | 语言 | Stars | Forks | License |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for repo in new_repos:
        lines.append(
            f"| {repo.full_name} | {repo.html_url} | {repo.starred_at} | {repo.language} | "
            f"{repo.stars if repo.stars is not None else ''} | {repo.forks if repo.forks is not None else ''} | {repo.license_name} |"
        )

    lines.extend(
        [
            "",
            "## 办公小浣熊后续处理指令",
            "",
            "请按 `office-raccoon-star-dart` Skill 继续处理以上新增仓库：",
            "",
            "1. 为每个仓库生成一份飞书项目子文档，内容参考 `references/doc_template.md`。",
            "2. 在飞书目录页追加项目文档入口。",
            "3. 写入或更新飞书多维表格资产台账。",
            "4. 更新飞书多维表格仪表盘。",
            "5. 不生成社群周报、xlsx、HTML dashboard、docx/pdf；PPT 只在每周回顾任务中生成。",
            "",
            "## Base 记录种子",
            "",
            "处理每个仓库时，可参考以下 JSON 字段写入飞书 Base：",
            "",
            "```json",
            json.dumps([repo_to_base_seed(repo) for repo in new_repos], ensure_ascii=False, indent=2),
            "```",
            "",
            "机制说明：本任务采用定时轮询，默认 3 小时，可由用户自行调整；"
            "GitHub Star 本身不会自动唤醒办公小浣熊。",
        ]
    )
    return "\n".join(lines) + "\n"


def load_sample(path: str) -> list[StarRepo]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if isinstance(data, dict):
        data = [data]
    repos: list[StarRepo] = []
    for item in data:
        repo = item.get("repo", item)
        license_info = repo.get("license") or {}
        repos.append(
            StarRepo(
                full_name=repo.get("full_name", ""),
                html_url=repo.get("html_url", ""),
                description=repo.get("description") or "",
                starred_at=item.get("starred_at") or repo.get("created_at", ""),
                language=repo.get("language") or "",
                stars=repo.get("stargazers_count"),
                forks=repo.get("forks_count"),
                license_name=license_info.get("spdx_id") or license_info.get("name") or "",
            )
        )
    return [repo for repo in repos if repo.full_name and repo.html_url]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check GitHub Stars against Feishu Base")
    parser.add_argument("--limit", type=int, default=None, help=f"检查最近 Star 数，默认读取 STAR_DART_POLL_LIMIT 或 {DEFAULT_LIMIT}")
    parser.add_argument(
        "--starred-since",
        default=None,
        help=f"只处理该时间之后 Star 的仓库，支持本机时区 YYYY-MM-DD 或 ISO 时间；默认读取 STAR_DART_STARRED_SINCE 或 {DEFAULT_STARRED_SINCE}",
    )
    parser.add_argument("--sample", help="读取本地 GitHub Star 样例 JSON，不访问 GitHub")
    parser.add_argument("--existing-json", help="读取本地 Base record-list JSON，不调用 lark-cli；用于测试或演示")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON，而不是 Markdown")
    parser.add_argument("--env-file", default=".env", help="加载的 env 文件路径，默认 ./.env")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(Path(args.env_file))

    limit = args.limit if args.limit is not None else int(env("STAR_DART_POLL_LIMIT", str(DEFAULT_LIMIT)))
    stars = load_sample(args.sample) if args.sample else fetch_recent_public_stars(env("GITHUB_USERNAME"), limit)
    starred_since_value = args.starred_since if args.starred_since is not None else env("STAR_DART_STARRED_SINCE", DEFAULT_STARRED_SINCE)
    starred_since = parse_since_datetime(starred_since_value)
    filtered_stars = filter_repos_starred_since(stars, starred_since)
    if args.existing_json:
        existing_payload = json.loads(Path(args.existing_json).read_text(encoding="utf-8"))
        existing_keys = existing_repo_keys_from_payload(existing_payload)
    else:
        existing_keys = fetch_existing_repo_keys(env("STAR_DART_BASE_TOKEN"), env("STAR_DART_BASE_TABLE_ID"))

    new_repos = find_new_repos(filtered_stars, existing_keys)

    if args.json:
        print(
            json.dumps(
                {
                    "checked_count": len(stars),
                    "filtered_count": len(filtered_stars),
                    "starred_since": starred_since_value,
                    "starred_since_utc": starred_since.isoformat() if starred_since else "",
                    "new_count": len(new_repos),
                    "new_repos": [repo.__dict__ for repo in new_repos],
                    "base_seed_records": [repo_to_base_seed(repo) for repo in new_repos],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(render_markdown(new_repos, checked_count=len(stars), starred_since=starred_since_value))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
