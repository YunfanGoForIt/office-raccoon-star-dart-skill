import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_new_stars.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_new_stars", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckNewStarsTest(unittest.TestCase):
    def test_existing_repo_keys_from_base_payload(self):
        module = load_module()
        payload = {
            "data": {
                "items": [
                    {
                        "fields": {
                            "仓库名称": "example/existing",
                            "GitHub URL": "https://github.com/example/existing",
                        }
                    }
                ]
            }
        }

        keys = module.existing_repo_keys_from_payload(payload)

        self.assertIn("example/existing", keys)
        self.assertIn("https://github.com/example/existing", keys)

    def test_find_new_repos_compares_name_and_url(self):
        module = load_module()
        repos = [
            module.StarRepo("example/existing", "https://github.com/example/existing", "", "", "", 1, 1, "MIT"),
            module.StarRepo("example/new", "https://github.com/example/new", "", "", "", 2, 1, "Apache-2.0"),
        ]

        new_repos = module.find_new_repos(repos, {"example/existing"})

        self.assertEqual([repo.full_name for repo in new_repos], ["example/new"])

    def test_cli_sample_outputs_office_raccoon_task_without_tokens(self):
        sample = {
            "starred_at": "2026-07-02T10:00:00Z",
            "repo": {
                "full_name": "example/new",
                "description": "New project",
                "html_url": "https://github.com/example/new",
                "language": "Python",
                "stargazers_count": 42,
                "forks_count": 3,
                "license": {"spdx_id": "MIT"},
            },
        }
        existing = {"data": {"items": []}}

        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as sample_file:
            json.dump(sample, sample_file)
            sample_path = sample_file.name

        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as existing_file:
            json.dump(existing, existing_file)
            existing_path = existing_file.name

        try:
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--sample",
                    sample_path,
                    "--existing-json",
                    existing_path,
                ],
                cwd=REPO_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
        finally:
            Path(sample_path).unlink(missing_ok=True)
            Path(existing_path).unlink(missing_ok=True)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Star-DART 新增 Star 检查结果", result.stdout)
        self.assertIn("example/new", result.stdout)
        self.assertIn("办公小浣熊后续处理指令", result.stdout)
        self.assertIn("PPT 只在每周回顾任务中生成", result.stdout)


if __name__ == "__main__":
    unittest.main()
