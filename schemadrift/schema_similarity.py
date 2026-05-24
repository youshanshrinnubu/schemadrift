"""Computes similarity scores between two schema snapshots."""

from dataclasses import dataclass
from typing import Dict, Set

from schemadrift.schema_snapshot import SchemaSnapshot


@dataclass
class SimilarityResult:
    source: str
    version_a: str
    version_b: str
    column_overlap_score: float  # Jaccard index on column names
    type_match_score: float      # fraction of shared columns with matching types
    overall_score: float         # weighted combination

    def to_dict(self) -> Dict:
        return {
            "source": self.source,
            "version_a": self.version_a,
            "version_b": self.version_b,
            "column_overlap_score": round(self.column_overlap_score, 4),
            "type_match_score": round(self.type_match_score, 4),
            "overall_score": round(self.overall_score, 4),
        }


def _column_names(snapshot: SchemaSnapshot) -> Set[str]:
    return {col.name for col in snapshot.columns}


def _column_type_map(snapshot: SchemaSnapshot) -> Dict[str, str]:
    return {col.name: col.data_type for col in snapshot.columns}


def compute_similarity(snap_a: SchemaSnapshot, snap_b: SchemaSnapshot) -> SimilarityResult:
    """Compute a similarity score between two snapshots of the same source."""
    names_a = _column_names(snap_a)
    names_b = _column_names(snap_b)

    union = names_a | names_b
    intersection = names_a & names_b

    if not union:
        column_overlap = 1.0
    else:
        column_overlap = len(intersection) / len(union)

    if not intersection:
        type_match = 1.0
    else:
        types_a = _column_type_map(snap_a)
        types_b = _column_type_map(snap_b)
        matches = sum(1 for col in intersection if types_a[col] == types_b[col])
        type_match = matches / len(intersection)

    overall = 0.6 * column_overlap + 0.4 * type_match

    return SimilarityResult(
        source=snap_a.source,
        version_a=snap_a.version,
        version_b=snap_b.version,
        column_overlap_score=column_overlap,
        type_match_score=type_match,
        overall_score=overall,
    )


def most_similar_version(
    target: SchemaSnapshot, candidates: list[SchemaSnapshot]
) -> SchemaSnapshot | None:
    """Return the candidate snapshot most similar to the target."""
    if not candidates:
        return None
    return max(candidates, key=lambda c: compute_similarity(target, c).overall_score)
