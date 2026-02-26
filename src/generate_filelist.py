import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List


def count_valid_lines(file_path: Path) -> int:
    count = 0
    with file_path.open("r", encoding="utf-8") as file:
        for raw_line in file:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            count += 1
    return count


def collect_file_data(release_dir: Path) -> List[Dict[str, object]]:
    result: List[Dict[str, object]] = []
    for file_path in sorted(release_dir.glob("*.txt")):
        modified = datetime.fromtimestamp(
            file_path.stat().st_mtime, tz=timezone.utc
        ).isoformat(timespec="seconds")
        result.append(
            {
                "name": file_path.name,
                "modified": modified,
                "lines": count_valid_lines(file_path),
            }
        )
    return result


def _write_filelist_js(file_data: List[Dict[str, object]], output_file: Path, repo_name: str) -> None:
    lines = [
        f"const repoName = {json.dumps(repo_name, ensure_ascii=False)};",
        "const fileData = [",
    ]
    for item in file_data:
        lines.append(f"  {json.dumps(item, ensure_ascii=False)},")
    lines.append("];")
    lines.append("")
    output_file.write_text("\n".join(lines), encoding="utf-8")


def generate_filelist(release_dir: Path, output_dir: Path, repo_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    file_data = collect_file_data(release_dir)
    file_list_path = output_dir / "fileList.js"
    _write_filelist_js(file_data, file_list_path, repo_name)

    project_root = Path(__file__).resolve().parent.parent
    index_source = project_root / "index.html"
    index_target = output_dir / "index.html"
    shutil.copy2(index_source, index_target)

    print(f"✅ 生成文件: {file_list_path}")
    print(f"✅ 复制文件: {index_target}")
    print(f"📊 文件数量: {len(file_data)}")


def main() -> int:
    parser = argparse.ArgumentParser(description="生成前端页面 fileList.js 与 index.html")
    parser.add_argument("release_dir", type=str, help="规则输出目录")
    parser.add_argument("output_dir", type=str, help="页面输出目录")
    parser.add_argument("--repo-name", type=str, default="unknown/repo", help="GitHub 仓库名 owner/repo")
    args = parser.parse_args()

    release_dir = Path(args.release_dir)
    output_dir = Path(args.output_dir)

    if not release_dir.is_dir():
        print(f"❌ release 目录不存在: '{release_dir}'")
        return 1

    generate_filelist(release_dir, output_dir, args.repo_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
