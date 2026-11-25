"""
CSV writer utilities for neo4j-admin bulk import.

Provides helpers to write node and relationship CSVs from Python dicts.
All node IDs must be unique strings; relationships reference those IDs.
"""

import csv
from pathlib import Path
import os

EXPORT_DIR = Path(os.getenv("REHABKG_EXPORT_DIR", "export"))
NODES_DIR = EXPORT_DIR / "nodes"
RELS_DIR = EXPORT_DIR / "relationships"


def ensure_dirs():
    NODES_DIR.mkdir(parents=True, exist_ok=True)
    RELS_DIR.mkdir(parents=True, exist_ok=True)


def write_node_csv(label, rows, fields=None):
    """Write a node CSV file.
    
    Args:
        label: Node label, used as filename (e.g. "Exercise" -> nodes_exercise.csv)
        rows: List of dicts. Must contain ':ID' key. Other keys become properties.
        fields: Optional list of column order. If None, uses sorted keys.
    
    Returns:
        Number of rows written.
    """
    if not rows:
        return 0

    filename = f"nodes_{label.lower()}.csv"
    path = NODES_DIR / filename

    if fields is None:
        fields = [':ID'] + sorted(k for k in rows[0].keys() if k != ':ID')

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore",
                                restval="")
        writer.writeheader()
        writer.writerows(rows)

    print(f"  {filename}: {len(rows):,} nodes")
    return len(rows)


def write_rel_csv(rel_type, rows, fields=None):
    """Write a relationship CSV file.
    
    Args:
        rel_type: Relationship type, used as filename (e.g. "TARGETS_PRIMARY")
        rows: List of dicts with ':START_ID', ':END_ID', and optional properties.
        fields: Optional list of column order.
    
    Returns:
        Number of rows written.
    """
    if not rows:
        return 0

    filename = f"rel_{rel_type.lower()}.csv"
    path = RELS_DIR / filename

    if fields is None:
        fields = [':START_ID', ':END_ID', ':TYPE']
        if rows:
            extra = sorted(k for k in rows[0].keys() if k not in (':START_ID', ':END_ID', ':TYPE'))
            fields.extend(extra)

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore",
                                restval="")
        writer.writeheader()
        writer.writerows(rows)

    print(f"  {filename}: {len(rows):,} relationships")
    return len(rows)


def validate_ids():
    """Validate that all relationship endpoints exist in node CSVs.
    
    Returns:
        (total_nodes, total_rels, errors) tuple.
    """
    # Load all node IDs
    node_ids = set()
    for f in NODES_DIR.glob("*.csv"):
        with open(f) as fh:
            for row in csv.DictReader(fh):
                nid = row.get(":ID")
                if nid:
                    node_ids.add(nid)

    # Check relationships
    total_rels = 0
    errors = 0
    for f in sorted(RELS_DIR.glob("*.csv")):
        with open(f) as fh:
            reader = csv.DictReader(fh)
            missing_start = missing_end = 0
            for row in reader:
                total_rels += 1
                if row[":START_ID"] not in node_ids:
                    missing_start += 1
                if row[":END_ID"] not in node_ids:
                    missing_end += 1
            if missing_start or missing_end:
                print(f"  ❌ {f.name}: missing start={missing_start}, end={missing_end}")
                errors += 1

    return len(node_ids), total_rels, errors
