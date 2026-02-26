import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List


def resolve_customization_path(config_env: str) -> Path:
    raw_path = Path(config_env)
    if raw_path.is_absolute():
        return raw_path
    project_root = Path(__file__).resolve().parent.parent
    return project_root / raw_path


def load_customization_config(config_path: Path) -> Dict[str, Any]:
    try:
        with config_path.open("r", encoding="utf-8") as file:
            raw: Any = json.load(file)
    except FileNotFoundError:
        print(f"⚠️ 自定义配置文件不存在，跳过预处理: '{config_path}'")
        return {}
    except json.JSONDecodeError as err:
        print(f"❌ 自定义配置 JSON 格式错误: {err}")
        raise

    if not isinstance(raw, dict):
        raise ValueError("customization 配置必须是对象")

    exclude_includes = raw.get("exclude_includes", [])
    if not isinstance(exclude_includes, list):
        raise ValueError("exclude_includes 必须是数组")

    for idx, rule in enumerate(exclude_includes):
        if not isinstance(rule, dict):
            raise ValueError(f"exclude_includes[{idx}] 必须是对象")
        from_file = rule.get("from_file")
        if not isinstance(from_file, str) or not from_file:
            raise ValueError(f"exclude_includes[{idx}].from_file 必须是非空字符串")
        exclude = rule.get("exclude")
        if not isinstance(exclude, list) or not exclude:
            raise ValueError(f"exclude_includes[{idx}].exclude 必须是非空数组")
        for j, item in enumerate(exclude):
            if not isinstance(item, str) or not item:
                raise ValueError(f"exclude_includes[{idx}].exclude[{j}] 必须是非空字符串")

    return raw


def _parse_include_target(line: str) -> str:
    # include 的目标文件名总在 include: 之后，到第一个空白或 @ 为止。
    match = re.match(r"^\s*include:([^\s@#]+)", line)
    if not match:
        return ""
    return match.group(1)


def apply_exclude_includes(source_dir: Path, rules: List[Dict[str, Any]]) -> None:
    for rule in rules:
        source_name = rule["from_file"]
        excludes = set(rule["exclude"])
        source_file = source_dir / source_name

        if not source_file.exists():
            print(f"⚠️ 自定义配置目标不存在，跳过: '{source_file}'")
            continue

        lines = source_file.read_text(encoding="utf-8").splitlines(keepends=True)
        kept_lines: List[str] = []
        removed_count = 0

        for line in lines:
            target = _parse_include_target(line)
            if target and target in excludes:
                removed_count += 1
                continue
            kept_lines.append(line)

        source_file.write_text("".join(kept_lines), encoding="utf-8")
        print(f"🧹 预处理完成: {source_name}, 删除 include 行 {removed_count} 条")


def apply_customizations(source_dir: Path, config: Dict[str, Any]) -> None:
    rules = config.get("exclude_includes", [])
    if not rules:
        print("ℹ️ 未配置 exclude_includes，跳过预处理")
        return
    apply_exclude_includes(source_dir, rules)


def main() -> int:
    parser = argparse.ArgumentParser(description="应用构建前数据预处理规则")
    parser.add_argument("source_dir", type=str, help="数据目录")
    parser.add_argument(
        "--config",
        type=str,
        default=os.environ.get("CUSTOMIZATION_FILE", "config/customizations.json"),
        help="预处理配置文件路径，默认读取 CUSTOMIZATION_FILE 或 config/customizations.json",
    )
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    if not source_dir.is_dir():
        print(f"❌ 数据目录不存在: '{source_dir}'")
        return 1

    config_path = resolve_customization_path(args.config)
    try:
        config = load_customization_config(config_path)
    except (json.JSONDecodeError, ValueError) as err:
        print(f"❌ 自定义配置非法: {err}; 解析路径='{config_path}'")
        return 1

    apply_customizations(source_dir, config)
    return 0


if __name__ == "__main__":
    sys.exit(main())
