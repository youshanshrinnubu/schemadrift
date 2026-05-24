"""CLI commands for schema annotations."""

from __future__ import annotations

import argparse

from schemadrift.schema_annotations import Annotation, AnnotationStore


def cmd_annotation_add(args: argparse.Namespace) -> None:
    store = AnnotationStore(args.store_dir)
    annotation = Annotation(
        source=args.source,
        version=args.version,
        column=args.column or None,
        note=args.note,
        author=args.author,
    )
    store.add(annotation)
    target = f"column '{args.column}'" if args.column else "snapshot"
    print(
        f"Annotation added to {target} in {args.source}@{args.version} "
        f"by {args.author}."
    )


def cmd_annotation_list(args: argparse.Namespace) -> None:
    store = AnnotationStore(args.store_dir)
    annotations = store.get_for_version(args.source, args.version)
    if not annotations:
        print(f"No annotations for {args.source}@{args.version}.")
        return
    for a in annotations:
        col_label = f"[{a.column}]" if a.column else "[snapshot]"
        print(f"  {col_label} {a.author} ({a.created_at}): {a.note}")


def cmd_annotation_sources(args: argparse.Namespace) -> None:
    store = AnnotationStore(args.store_dir)
    sources = store.list_sources()
    if not sources:
        print("No annotated sources found.")
        return
    for s in sorted(sources):
        print(f"  {s}")


def register_annotation_commands(
    subparsers: argparse._SubParsersAction,
) -> None:
    p_add = subparsers.add_parser(
        "annotation-add", help="Add an annotation to a snapshot or column"
    )
    p_add.add_argument("source")
    p_add.add_argument("version")
    p_add.add_argument("note")
    p_add.add_argument("--author", default="unknown")
    p_add.add_argument("--column", default=None)
    p_add.set_defaults(func=cmd_annotation_add)

    p_list = subparsers.add_parser(
        "annotation-list", help="List annotations for a snapshot version"
    )
    p_list.add_argument("source")
    p_list.add_argument("version")
    p_list.set_defaults(func=cmd_annotation_list)

    p_src = subparsers.add_parser(
        "annotation-sources", help="List sources with annotations"
    )
    p_src.set_defaults(func=cmd_annotation_sources)
