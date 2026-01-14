import argparse
import re
from dataclasses import dataclass, field
from os import environ
from pathlib import Path
from typing import List, Dict

min_lines_env: str = environ.get("MIN_LINES", "1")
min_lines: int = 1
base_attr: str = environ.get("BASE_ATTR", "")
addon_attrs: List[str] = ["@cn", "@ads"]
try:
    min_lines = int(min_lines_env)
except ValueError:
    print("‼️变量错误: MIN_LINES")

processed: Dict[str, List[str]] = {}


@dataclass
class Entry:
    type: str
    value: str
    attr: str
    data: list = field(default_factory=list)


def format_doc(file_path: Path):
    result: List[str] = []
    try:
        with file_path.open("r", encoding="utf-8") as file:
            content = file.read()
        no_hash = re.sub(r'#.*', '', content)
        no_space = re.sub(r'[ \t]+', '', no_hash)
        result = re.findall(r'\S.*', no_space)
    except FileNotFoundError:
        print(f"⚠️未知文件: {file_path.name}")
    return result


def format_line(line_content: str):
    first, _, rest = line_content.partition("@")
    type, _, value = first.partition(":")
    if type == first:
        type, value = "domain", first
    attrs: List[str] = [f"@{attr}" for attr in rest.split("@")] if rest else []
    data = []
    return type, value, set(attrs + [base_attr]), data


class DocumentProcessor:

    def __init__(self, content: List[str], source_dir: Path, release_dir: Path, chain: List[str]):
        self.content = content
        self.source_dir = source_dir
        self.release_dir = release_dir
        self.chain = chain
        self.result: List[str] = []

    def process(self):
        content = self.content
        source_dir = self.source_dir
        release_dir = self.release_dir
        chain = self.chain
        name: str = chain[-1]
        result: List[str] = []
        if name in chain[:-1]:
            info = "♻️循环引用"
        else:
            if name in processed:
                result = processed[name]
                info = "💨处理过咯"
            else:
                attrs_set: set[str] = set()
                entries: List[Entry] = []
                for line in content:
                    type, value, attrs, data = format_line(line)
                    attrs_set.update(attrs)
                    if type == "full":
                        data = [f"{value}\n"]
                    elif type == "domain":
                        data = [f".{value}\n"]
                    elif type == "include":
                        sub_source_file: Path = source_dir / value
                        sub_content = format_doc(sub_source_file)
                        doc = DocumentProcessor(sub_content, source_dir, release_dir, self.chain + [value])
                        doc.process()
                        data = doc.result
                    for attr in attrs:
                        entries.append(Entry(type=type, value=value, attr=attr, data=data))
                if len(entries) == 0:
                    info = "⏺️空白文件"
                elif len(entries) < min_lines:
                    info = "🆖行数太少"
                else:
                    for attr in attrs_set:
                        if attr not in addon_attrs + [base_attr]:
                            continue
                        page: List[str] = []
                        for entry in entries:
                            if entry.attr == attr:
                                page.extend(entry.data)
                        page.sort()
                        if attr == base_attr:
                            result = page
                        if not page:
                            continue
                        page_file = release_dir / f"{name}{attr}.txt"
                        with page_file.open("w", encoding="utf-8") as file:
                            file.write(f"# 来源: https://github.com/v2fly/domain-list-community/tree/master/data/{name}\n\n")
                            file.writelines(page)
                    processed.update({name: result})
                    info = "🆗处理完成"
        print(f"{info}, 路径：{' -> '.join(chain)}")
        self.result = result


def main():
    parser = argparse.ArgumentParser(description='把 v2fly/domain-list-community 转换为 surge、clash 的 domain set')
    parser.add_argument('source_dir', type=str, help='数据目录')
    parser.add_argument('release_dir', type=str, help='输出目录')
    args = parser.parse_args()

    source_dir: Path = Path(args.source_dir)
    release_dir: Path = Path(args.release_dir)

    print(f"📂 扫描目录: {source_dir.absolute()}")
    if not source_dir.is_dir():
        print(f"❌ 数据目录不存在: '{source_dir}'")
        return

    release_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    for source_file in source_dir.glob('*'):
        if source_file.is_file() and source_file.suffix == "":
            content = format_doc(source_file)
            doc = DocumentProcessor(content, source_dir, release_dir, [source_file.stem])
            doc.process()
            count += 1
    
    if count == 0:
        print("⚠️ 未发现任何待处理文件")
    else:
        print(f"🎉 全部完成! 处理了 {count} 个文件")


if __name__ == '__main__':
    main()
