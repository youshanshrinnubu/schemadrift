from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
import json
import os


@dataclass
class PolicyRule:
    name: str
    description: str
    forbidden_types: List[str] = field(default_factory=list)
    required_columns: List[str] = field(default_factory=list)
    max_columns: Optional[int] = None
    min_columns: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "forbidden_types": self.forbidden_types,
            "required_columns": self.required_columns,
            "max_columns": self.max_columns,
            "min_columns": self.min_columns,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PolicyRule":
        return cls(
            name=data["name"],
            description=data.get("description", ""),
            forbidden_types=data.get("forbidden_types", []),
            required_columns=data.get("required_columns", []),
            max_columns=data.get("max_columns"),
            min_columns=data.get("min_columns"),
        )


@dataclass
class PolicyViolation:
    rule_name: str
    message: str

    def to_dict(self) -> dict:
        return {"rule_name": self.rule_name, "message": self.message}


@dataclass
class PolicyResult:
    source: str
    version: str
    violations: List[PolicyViolation] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return len(self.violations) == 0

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "version": self.version,
            "passed": self.passed,
            "violations": [v.to_dict() for v in self.violations],
        }


def evaluate_policy(snapshot, rules: List[PolicyRule]) -> PolicyResult:
    from schemadrift.schema_snapshot import SchemaSnapshot

    violations: List[PolicyViolation] = []
    col_names = [c.name for c in snapshot.columns]
    col_types = [c.col_type for c in snapshot.columns]

    for rule in rules:
        for ft in rule.forbidden_types:
            matches = [c.name for c in snapshot.columns if c.col_type == ft]
            if matches:
                violations.append(PolicyViolation(
                    rule_name=rule.name,
                    message=f"Forbidden type '{ft}' found in columns: {', '.join(matches)}",
                ))
        for rc in rule.required_columns:
            if rc not in col_names:
                violations.append(PolicyViolation(
                    rule_name=rule.name,
                    message=f"Required column '{rc}' is missing",
                ))
        if rule.max_columns is not None and len(snapshot.columns) > rule.max_columns:
            violations.append(PolicyViolation(
                rule_name=rule.name,
                message=f"Column count {len(snapshot.columns)} exceeds max {rule.max_columns}",
            ))
        if rule.min_columns is not None and len(snapshot.columns) < rule.min_columns:
            violations.append(PolicyViolation(
                rule_name=rule.name,
                message=f"Column count {len(snapshot.columns)} is below min {rule.min_columns}",
            ))

    return PolicyResult(source=snapshot.source, version=snapshot.version, violations=violations)


def load_policy_rules(path: str) -> List[PolicyRule]:
    with open(path, "r") as f:
        data = json.load(f)
    return [PolicyRule.from_dict(r) for r in data]
