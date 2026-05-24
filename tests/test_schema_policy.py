import pytest
from schemadrift.schema_snapshot import SchemaSnapshot, ColumnSchema
from schemadrift.schema_policy import (
    PolicyRule,
    PolicyViolation,
    PolicyResult,
    evaluate_policy,
)


def make_snapshot(columns, source="src", version="v1"):
    return SchemaSnapshot(
        source=source,
        version=version,
        columns=[ColumnSchema(name=n, col_type=t) for n, t in columns],
    )


def make_rule(**kwargs):
    return PolicyRule(name=kwargs.get("name", "test_rule"), description="", **{k: v for k, v in kwargs.items() if k != "name"})


def test_no_violations_when_rules_empty():
    snap = make_snapshot([("id", "int"), ("name", "string")])
    result = evaluate_policy(snap, [])
    assert result.passed
    assert result.violations == []


def test_forbidden_type_triggers_violation():
    snap = make_snapshot([("id", "int"), ("data", "blob")])
    rule = PolicyRule(name="no_blob", description="", forbidden_types=["blob"])
    result = evaluate_policy(snap, [rule])
    assert not result.passed
    assert len(result.violations) == 1
    assert "blob" in result.violations[0].message


def test_required_column_missing_triggers_violation():
    snap = make_snapshot([("name", "string")])
    rule = PolicyRule(name="require_id", description="", required_columns=["id"])
    result = evaluate_policy(snap, [rule])
    assert not result.passed
    assert any("id" in v.message for v in result.violations)


def test_required_column_present_no_violation():
    snap = make_snapshot([("id", "int"), ("name", "string")])
    rule = PolicyRule(name="require_id", description="", required_columns=["id"])
    result = evaluate_policy(snap, [rule])
    assert result.passed


def test_max_columns_exceeded_triggers_violation():
    snap = make_snapshot([("a", "int"), ("b", "int"), ("c", "int")])
    rule = PolicyRule(name="max_cols", description="", max_columns=2)
    result = evaluate_policy(snap, [rule])
    assert not result.passed
    assert any("max" in v.message for v in result.violations)


def test_min_columns_not_met_triggers_violation():
    snap = make_snapshot([("id", "int")])
    rule = PolicyRule(name="min_cols", description="", min_columns=3)
    result = evaluate_policy(snap, [rule])
    assert not result.passed
    assert any("min" in v.message for v in result.violations)


def test_multiple_rules_multiple_violations():
    snap = make_snapshot([("data", "blob")])
    rules = [
        PolicyRule(name="no_blob", description="", forbidden_types=["blob"]),
        PolicyRule(name="require_id", description="", required_columns=["id"]),
    ]
    result = evaluate_policy(snap, rules)
    assert not result.passed
    assert len(result.violations) == 2


def test_policy_result_to_dict_structure():
    snap = make_snapshot([("id", "int")])
    rule = PolicyRule(name="require_name", description="", required_columns=["name"])
    result = evaluate_policy(snap, [rule])
    d = result.to_dict()
    assert "source" in d
    assert "version" in d
    assert "passed" in d
    assert "violations" in d
    assert isinstance(d["violations"], list)


def test_policy_rule_roundtrip():
    rule = PolicyRule(
        name="test",
        description="desc",
        forbidden_types=["blob"],
        required_columns=["id"],
        max_columns=10,
        min_columns=1,
    )
    restored = PolicyRule.from_dict(rule.to_dict())
    assert restored.name == rule.name
    assert restored.forbidden_types == rule.forbidden_types
    assert restored.required_columns == rule.required_columns
    assert restored.max_columns == rule.max_columns
    assert restored.min_columns == rule.min_columns
