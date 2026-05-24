import json
import os
import pytest
from unittest.mock import patch, MagicMock
from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.schema_policy import PolicyRule
from schemadrift.cli_policy import cmd_policy_check, cmd_policy_validate_file


@pytest.fixture
def store_dir(tmp_path):
    return str(tmp_path / "store")


@pytest.fixture
def policy_file(tmp_path):
    rules = [
        {
            "name": "no_blob",
            "description": "No blob columns",
            "forbidden_types": ["blob"],
            "required_columns": [],
        }
    ]
    path = str(tmp_path / "policy.json")
    with open(path, "w") as f:
        json.dump(rules, f)
    return path


def make_snapshot(columns, source="src", version="v1"):
    return SchemaSnapshot(
        source=source,
        version=version,
        columns=[ColumnSchema(name=n, col_type=t) for n, t in columns],
    )


def make_args(**kwargs):
    args = MagicMock()
    for k, v in kwargs.items():
        setattr(args, k, v)
    return args


def test_cmd_policy_check_passes(store_dir, policy_file, capsys):
    snap = make_snapshot([("id", "int"), ("name", "string")])
    args = make_args(source="src", policy_file=policy_file, version=None,
                     store_dir=store_dir, format="text")
    with patch("schemadrift.cli_policy.SnapshotStore") as MockStore:
        instance = MockStore.return_value
        instance.load_latest.return_value = snap
        cmd_policy_check(args)
    out = capsys.readouterr().out
    assert "PASSED" in out


def test_cmd_policy_check_fails_with_exit_code(store_dir, policy_file):
    snap = make_snapshot([("data", "blob")])
    args = make_args(source="src", policy_file=policy_file, version=None,
                     store_dir=store_dir, format="text")
    with patch("schemadrift.cli_policy.SnapshotStore") as MockStore:
        instance = MockStore.return_value
        instance.load_latest.return_value = snap
        with pytest.raises(SystemExit) as exc_info:
            cmd_policy_check(args)
    assert exc_info.value.code == 2


def test_cmd_policy_check_json_output(store_dir, policy_file, capsys):
    snap = make_snapshot([("id", "int")])
    args = make_args(source="src", policy_file=policy_file, version=None,
                     store_dir=store_dir, format="json")
    with patch("schemadrift.cli_policy.SnapshotStore") as MockStore:
        instance = MockStore.return_value
        instance.load_latest.return_value = snap
        cmd_policy_check(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "passed" in data
    assert data["passed"] is True


def test_cmd_policy_validate_file_valid(policy_file, capsys):
    args = make_args(policy_file=policy_file)
    cmd_policy_validate_file(args)
    out = capsys.readouterr().out
    assert "valid" in out.lower()
    assert "no_blob" in out


def test_cmd_policy_validate_file_missing_exits(tmp_path):
    args = make_args(policy_file=str(tmp_path / "nonexistent.json"))
    with pytest.raises(SystemExit):
        cmd_policy_validate_file(args)
