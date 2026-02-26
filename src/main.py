import argparse
import json
import os
from pathlib import Path
from typing import Any, List, Dict, Tuple

from .parser import format_doc, Entry
from .processor import DocumentProcessor


def resolve_policy_path(policy_file_env: str) -> Path:
    raw_path = Path(policy_file_env)
    if raw_path.is_absolute():
        return raw_path
    project_root = Path(__file__).resolve().parent.parent
    return project_root / raw_path


def load_tag_policies(policy_path: Path) -> Dict[str, Dict[str, bool]]:
    try:
        with policy_path.open("r", encoding="utf-8") as file:
            raw: Any = json.load(file)
    except FileNotFoundError:
        print(f"⚠️ 配置文件不存在，忽略标签输出: '{policy_path}'")
        return {}
    except json.JSONDecodeError as err:
        print(f"❌ 配置文件 JSON 格式错误: {err}")
        raise

    if not isinstance(raw, dict):
        raise ValueError("tag 策略配置必须是对象，格式: {\"tag\": {\"pos\": true, \"neg\": false}}")

    normalized: Dict[str, Dict[str, bool]] = {}
    for tag, policy in raw.items():
        if not isinstance(tag, str) or not tag:
            raise ValueError(f"无效标签名: {tag}")
        if not isinstance(policy, dict):
            raise ValueError(f"标签 '{tag}' 的策略必须是对象")

        pos = policy.get("pos", False)
        neg = policy.get("neg", False)

        if not isinstance(pos, bool):
            raise ValueError(f"标签 '{tag}' 的 pos 必须是布尔值")
        if not isinstance(neg, bool):
            raise ValueError(f"标签 '{tag}' 的 neg 必须是布尔值")

        normalized[tag] = {"pos": pos, "neg": neg}

    return normalized


def main():
    min_lines_env: str = os.environ.get("MIN_LINES", "1")
    policy_file_env: str = os.environ.get("TAG_POLICY_FILE", "config/tag_policies.json")
    
    try:
        min_lines = int(min_lines_env)
    except ValueError:
        print("‼️变量错误: MIN_LINES")
        min_lines = 1

    parser = argparse.ArgumentParser(
        description='把 v2fly/domain-list-community 转换为 surge、clash 的 domain set'
    )
    parser.add_argument('source_dir', type=str, help='数据目录')
    parser.add_argument('release_dir', type=str, help='输出目录')
    args = parser.parse_args()

    source_dir: Path = Path(args.source_dir)
    release_dir: Path = Path(args.release_dir)

    print(f"📂 扫描目录: {source_dir.absolute()}")
    if not source_dir.is_dir():
        print(f"❌ 数据目录不存在: '{source_dir}'")
        return

    resolved_policy_path = resolve_policy_path(policy_file_env)

    try:
        tag_policies = load_tag_policies(resolved_policy_path)
    except json.JSONDecodeError:
        print(f"❌ TAG_POLICY_FILE JSON 解析失败: 原始值='{policy_file_env}', 解析路径='{resolved_policy_path}'")
        return
    except ValueError as err:
        print(f"❌ TAG_POLICY_FILE 配置非法: {err}; 原始值='{policy_file_env}', 解析路径='{resolved_policy_path}'")
        return

    release_dir.mkdir(parents=True, exist_ok=True)
    
    processed: Dict[str, Tuple[List[str], List[Entry]]] = {}
    count = 0
    
    for source_file in source_dir.glob('*'):
        if source_file.is_file() and source_file.suffix == "":
            content = format_doc(source_file)
            doc = DocumentProcessor(
                content,
                source_dir,
                release_dir,
                [source_file.stem],
                processed,
                min_lines,
                tag_policies=tag_policies
            )
            doc.process()
            count += 1
    
    if count == 0:
        print("⚠️ 未发现任何待处理文件")
    else:
        print(f"🎉 全部完成! 处理了 {count} 个文件")


if __name__ == '__main__':
    main()
