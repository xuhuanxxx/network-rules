from pathlib import Path
from typing import List, Dict, Set, Tuple

from .parser import Entry, format_doc, format_line, entry_to_domain


class DocumentProcessor:
    def __init__(
        self,
        content: List[str],
        source_dir: Path,
        release_dir: Path,
        chain: List[str],
        processed: Dict[str, Tuple[List[str], List[Entry]]],
        min_lines: int = 1,
        tag_policies: Dict[str, Dict[str, bool]] = None
    ):
        self.content = content
        self.source_dir = source_dir
        self.release_dir = release_dir
        self.chain = chain
        self.processed = processed
        self.min_lines = min_lines
        self.tag_policies = tag_policies or {}
        self.result: List[str] = []
        self.entries: List[Entry] = []
        self.attrs_set: Set[str] = set()

    def process(self):
        content = self.content
        source_dir = self.source_dir
        release_dir = self.release_dir
        chain = self.chain
        name: str = chain[-1]
        result: List[str] = []

        if name in chain[:-1]:
            info = "♻️循环引用"
            print(f"{info}, 路径：{' -> '.join(chain)}")
            self.result = result
            return

        if name in self.processed:
            result, entries = self.processed[name]
            info = "💨处理过咯"
            print(f"{info}, 路径：{' -> '.join(chain)}")
            self.result = result
            self.entries = entries
            return

        attrs_set: Set[str] = set()
        entries: List[Entry] = []

        for line in content:
            type_prefix, value, pos_attrs, neg_attrs = format_line(line)
            if type_prefix == "include":
                entry = Entry(
                    type=type_prefix,
                    value=value,
                    attr=set(),
                    neg_attr=set(),
                    data=[]
                )
            else:
                attrs_set.update(pos_attrs)
                attrs_set.update(neg_attrs)
                entry = Entry(
                    type=type_prefix,
                    value=value,
                    attr=pos_attrs,
                    neg_attr=neg_attrs,
                    data=[]
                )

            if type_prefix == "full":
                entry.data = [entry_to_domain(entry)]
            elif type_prefix == "domain":
                entry.data = [entry_to_domain(entry)]
            elif type_prefix == "keyword":
                entry.data = [entry_to_domain(entry)]
            elif type_prefix == "regexp":
                entry.data = [entry_to_domain(entry)]
            elif type_prefix == "include":
                sub_source_file: Path = source_dir / value
                include_pos_attrs = pos_attrs
                include_neg_attrs = neg_attrs

                if value in self.processed:
                    _, include_entries = self.processed[value]
                else:
                    sub_content = format_doc(sub_source_file)
                    doc = DocumentProcessor(
                        sub_content,
                        source_dir,
                        release_dir,
                        self.chain + [value],
                        self.processed,
                        self.min_lines,
                        self.tag_policies
                    )
                    doc.process()
                    include_entries = doc.entries

                filtered = self._filter_entries_by_attrs(
                    include_entries, include_pos_attrs, include_neg_attrs
                )
                entry.data = []
                for fe in filtered:
                    entry.data.extend(fe.data)

            entries.append(entry)

        if len(entries) == 0:
            info = "⏺️空白文件"
            print(f"{info}, 路径：{' -> '.join(chain)}")
        elif len(entries) < self.min_lines:
            info = "🆖行数太少"
            print(f"{info}, 路径：{' -> '.join(chain)}")
        else:
            result = []
            for e in entries:
                result.extend(e.data)
            result.sort()

            if result:
                base_file = release_dir / f"{name}.txt"
                with base_file.open("w", encoding="utf-8") as file:
                    file.write(f"# 来源: https://github.com/v2fly/domain-list-community/tree/master/data/{name}\n\n")
                    file.writelines(result)

            output_attrs = attrs_set.copy()
            for attr in output_attrs:
                if not self._is_output_attr_enabled(attr):
                    continue
                page: List[str] = []
                for entry in entries:
                    if attr in entry.output_tags:
                        page.extend(entry.data)
                page.sort()
                if not page:
                    continue
                page_file = release_dir / f"{name}{attr}.txt"
                with page_file.open("w", encoding="utf-8") as file:
                    file.write(f"# 来源: https://github.com/v2fly/domain-list-community/tree/master/data/{name}\n\n")
                    file.writelines(page)
            
            info = "🆗处理完成"
            print(f"{info}, 路径：{' -> '.join(chain)}")

        self.processed[name] = (result, entries)
        self.result = result
        self.entries = entries
        self.attrs_set = attrs_set

    def _filter_entries_by_attrs(
        self,
        entries: List[Entry],
        pos_attrs: Set[str],
        neg_attrs: Set[str]
    ) -> List[Entry]:
        if not pos_attrs and not neg_attrs:
            return entries

        neg_canonical: Set[str] = set()
        for neg in neg_attrs:
            if neg.startswith("@!"):
                neg_canonical.add(f"@{neg[2:]}")
            else:
                neg_canonical.add(neg)

        result = []
        for entry in entries:
            has_pos = not pos_attrs or pos_attrs.issubset(entry.attr)
            has_neg = not neg_canonical or not neg_canonical.intersection(entry.attr)
            if has_pos and has_neg:
                result.append(entry)
        return result

    def _is_output_attr_enabled(self, attr: str) -> bool:
        tag, polarity = self._split_tag_polarity(attr)
        if not tag:
            return False
        policy = self.tag_policies.get(tag, {})
        enabled = policy.get(polarity, False)
        return bool(enabled)

    def _split_tag_polarity(self, attr: str) -> Tuple[str, str]:
        if attr.startswith("@!"):
            return attr[2:], "neg"
        if attr.startswith("@"):
            return attr[1:], "pos"
        return "", "pos"
