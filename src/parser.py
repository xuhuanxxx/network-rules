import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set, Tuple


@dataclass
class Entry:
    type: str
    value: str
    attr: Set[str]
    neg_attr: Set[str] = field(default_factory=set)
    data: List[str] = field(default_factory=list)

    @property
    def output_tags(self) -> Set[str]:
        return self.attr | self.neg_attr


def format_doc(file_path: Path) -> List[str]:
    result: List[str] = []
    try:
        with file_path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue
                if stripped.startswith('regexp:'):
                    comment_idx = stripped.find(' #')
                    if comment_idx != -1:
                        stripped = stripped[:comment_idx]
                else:
                    stripped = re.sub(r'#.*', '', stripped)
                no_space = stripped.replace(' ', '').replace('\t', '')
                if no_space:
                    result.append(no_space)
    except FileNotFoundError:
        print(f"⚠️未知文件: {file_path.name}")
    return result


def parse_attrs(attr_str: str) -> Tuple[Set[str], Set[str]]:
    positive = set()
    negative = set()
    if not attr_str:
        return positive, negative
    
    for attr in attr_str.split('@'):
        if not attr:
            continue
        if attr.startswith('-') or attr.startswith('!'):
            negative.add(f"@!{attr[1:]}")
        else:
            positive.add(f"@{attr}")
    return positive, negative


def format_line(line_content: str) -> Tuple[str, str, Set[str], Set[str]]:
    type_check, colon, rest_of_line = line_content.partition(":")
    if colon and type_check == "regexp":
        return "regexp", rest_of_line, set(), set()

    first, sep, rest = line_content.partition("@")
    type_prefix, _, value = first.partition(":")

    if type_prefix == first:
        type_prefix = "domain"
        value = first

    pos_attrs, neg_attrs = parse_attrs(rest)

    return type_prefix, value, pos_attrs, neg_attrs


def entry_to_domain(entry: Entry) -> str:
    if entry.type == "full":
        return f"{entry.value}\n"
    elif entry.type == "domain":
        return f".{entry.value}\n"
    elif entry.type == "keyword":
        return f"keyword:{entry.value}\n"
    elif entry.type == "regexp":
        return f"regexp:{entry.value}\n"
    return f".{entry.value}\n"
