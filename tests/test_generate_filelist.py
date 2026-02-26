from pathlib import Path

from src.generate_filelist import collect_file_data, count_valid_lines, generate_filelist


def test_count_valid_lines(tmp_path):
    test_file = tmp_path / "rules.txt"
    test_file.write_text(
        "\n".join(
            [
                "# comment",
                "",
                "google.com",
                "  ",
                "keyword:ads",
            ]
        ),
        encoding="utf-8",
    )
    assert count_valid_lines(test_file) == 2


def test_collect_file_data_sorted(tmp_path):
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    (release_dir / "b.txt").write_text("b.com\n", encoding="utf-8")
    (release_dir / "a.txt").write_text("a.com\n", encoding="utf-8")

    data = collect_file_data(release_dir)
    assert [item["name"] for item in data] == ["a.txt", "b.txt"]
    assert all("modified" in item for item in data)
    assert all(item["lines"] == 1 for item in data)


def test_generate_filelist_outputs_files(tmp_path):
    release_dir = tmp_path / "release"
    release_dir.mkdir()
    (release_dir / "google.txt").write_text("# header\n\n.google.com\n", encoding="utf-8")

    output_dir = tmp_path / "pages"
    generate_filelist(release_dir, output_dir, "owner/repo")

    file_list = output_dir / "fileList.js"
    index_file = output_dir / "index.html"
    assert file_list.exists()
    assert index_file.exists()

    content = file_list.read_text(encoding="utf-8")
    assert 'const repoName = "owner/repo";' in content
    assert '"name": "google.txt"' in content
    assert '"lines": 1' in content
