from pathlib import Path

import pytest

from src.main import load_tag_policies, resolve_policy_path


def test_resolve_policy_path_relative():
    resolved = resolve_policy_path("config/tag_policies.json")
    project_root = Path(__file__).resolve().parent.parent
    assert resolved == project_root / "config/tag_policies.json"


def test_resolve_policy_path_absolute(tmp_path):
    absolute_path = tmp_path / "tag_policies.json"
    resolved = resolve_policy_path(str(absolute_path))
    assert resolved == absolute_path


def test_load_tag_policies_file_not_found():
    policies = load_tag_policies(Path("/tmp/not-exists-tag-policies.json"))
    assert policies == {}


def test_load_tag_policies_defaults_missing_fields(tmp_path):
    config_file = tmp_path / "tag_policies.json"
    config_file.write_text('{"cn":{"pos":true},"ads":{}}', encoding="utf-8")

    policies = load_tag_policies(config_file)

    assert policies["cn"] == {"pos": True, "neg": False}
    assert policies["ads"] == {"pos": False, "neg": False}
