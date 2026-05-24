"""Validates schema snapshots against a set of rules and reports violations."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

from schemadrift.schema_snapshot import SchemaSnapshot


class ViolationLevel(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class ValidationRule:
    name: str
    description: str
    level: ViolationLevel


@dataclass
class Violation:
    rule_name: str
    level: ViolationLevel
    message: str
    column: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "rule_name": self.rule_name,
            "level": self.level.value,
            "message": self.message,
            "column": self.column,
        }


@dataclass
class ValidationReport:
    source: str
    version: str
    violations: List[Violation] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(v.level == ViolationLevel.ERROR for v in self.violations)

    @property
    def has_warnings(self) -> bool:
        return any(v.level == ViolationLevel.WARNING for v in self.violations)

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "version": self.version,
            "violations": [v.to_dict() for v in self.violations],
        }


BUILTIN_RULES: List[ValidationRule] = [
    ValidationRule("no_empty_schema", "Schema must have at least one column.", ViolationLevel.ERROR),
    ValidationRule("no_unnamed_columns", "All columns must have non-empty names.", ViolationLevel.ERROR),
    ValidationRule("no_untyped_columns", "All columns should have a declared type.", ViolationLevel.WARNING),
]


def validate_snapshot(snapshot: SchemaSnapshot, rules: Optional[List[ValidationRule]] = None) -> ValidationReport:
    """Run validation rules against a snapshot and return a report."""
    active_rules = rules if rules is not None else BUILTIN_RULES
    report = ValidationReport(source=snapshot.source, version=snapshot.version)

    for rule in active_rules:
        if rule.name == "no_empty_schema":
            if not snapshot.columns:
                report.violations.append(Violation(rule.name, rule.level, "Schema has no columns."))

        elif rule.name == "no_unnamed_columns":
            for col in snapshot.columns:
                if not col.name or not col.name.strip():
                    report.violations.append(
                        Violation(rule.name, rule.level, "Column has an empty name.", column=col.name)
                    )

        elif rule.name == "no_untyped_columns":
            for col in snapshot.columns:
                if not col.col_type or not col.col_type.strip():
                    report.violations.append(
                        Violation(rule.name, rule.level, f"Column '{col.name}' has no type declared.", column=col.name)
                    )

    return report
