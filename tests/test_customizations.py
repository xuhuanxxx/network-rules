import json
from pathlib import Path

import pytest

from src.customizations import (
    apply_customizations,
    load_customization_config,
    resolve_customization_path,
)


def test_resolve_customization_path_relative():
    resolved = resolve_customization_path("config/customizations.json")
    project_root = Path(__file__).resolve().parent.parent
    assert resolved == project_root / "config/customizations.json"


def test_load_customization_config_file_not_found():
    config = load_customization_config(Path("/tmp/not-exists-customizations.json"))
    assert config == {}


def test_load_customization_config_invalid_schema(tmp_path):
    config_file = tmp_path / "customizations.json"
    config_file.write_text(json.dumps({"exclude_includes": [{"from_file": "microsoft"}]}), encoding="utf-8")

    with pytest.raises(ValueError):
        load_customization_config(config_file)


def test_apply_customizations_exclude_includes(tmp_path):
    source_dir = tmp_path / "data"
    source_dir.mkdir()
    source_file = source_dir / "microsoft"
    source_file.write_text(
        "\n".join(
            [
                "include:github",
                "include:github @cn",
                "include:github@ads",
                "include:github-pages",
                "domain:microsoft.com",
                "",
            ]
        ),
        encoding="utf-8",
    )

    config = {
        "exclude_includes": [
            {
                "from_file": "microsoft",
                "exclude": ["github"],
            }
        ]
    }
    apply_customizations(source_dir, config)

    content = source_file.read_text(encoding="utf-8")
    assert "include:github\n" not in content
    assert "include:github @cn\n" not in content
    assert "include:github@ads\n" not in content
    assert "include:github-pages\n" in content
    assert "domain:microsoft.com\n" in content
