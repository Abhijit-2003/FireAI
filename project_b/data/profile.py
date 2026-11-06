"""
Raw Data Profiler for NYC 311 (2023) — Task 1 of Project B.

Profiles raw data to identify existing data quality anomalies:
- Counts, percentages, severity, and exact row examples.
"""

from __future__ import annotations
import csv
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List
from project_b.data.download import ensure_dataset, NYC_BOROUGH_ZIPS


def profile_raw_data(filepath: str | None = None) -> Dict[str, Any]:
    if filepath is None or not os.path.exists(filepath):
        filepath = ensure_dataset()

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    total_rows = len(rows)

    # Profiling trackers
    closed_before_created = []
    zip_borough_mismatches = []
    pii_instances = []
    swapped_coords = []
    exact_duplicates = []
    null_counts = {col: 0 for col in rows[0].keys()}

    seen_hashes = {}
    phone_pattern = re.compile(r"\b(?:\+?1[-.]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")

    for idx, r in enumerate(rows):
        # 1. Null counts
        for col, val in r.items():
            if not val or val.strip() == "":
                null_counts[col] += 1

        # 2. Closed Date earlier than Created Date
        c_str = r.get("Created Date", "")
        cl_str = r.get("Closed Date", "")
        if c_str and cl_str:
            try:
                c_dt = datetime.strptime(c_str, "%m/%d/%Y %I:%M:%S %p")
                cl_dt = datetime.strptime(cl_str, "%m/%d/%Y %I:%M:%S %p")
                if cl_dt < c_dt:
                    closed_before_created.append({
                        "row_index": idx,
                        "unique_key": r.get("Unique Key"),
                        "created": c_str,
                        "closed": cl_str,
                    })
            except Exception:
                pass

        # 3. ZIP inconsistent with Borough
        borough = r.get("Borough", "").upper()
        zip_c = r.get("Incident Zip", "")
        if borough in NYC_BOROUGH_ZIPS and zip_c:
            valid_zips = NYC_BOROUGH_ZIPS[borough]
            if zip_c not in valid_zips:
                # Check if it belongs to another borough
                owner_borough = next((b for b, z_list in NYC_BOROUGH_ZIPS.items() if zip_c in z_list), None)
                if owner_borough and owner_borough != borough:
                    zip_borough_mismatches.append({
                        "row_index": idx,
                        "unique_key": r.get("Unique Key"),
                        "borough": borough,
                        "zip": zip_c,
                        "expected_borough": owner_borough,
                    })

        # 4. Lat/Lng swap (NYC Lat ~ 40.7, Lng ~ -73.9)
        try:
            lat = float(r.get("Latitude", 0))
            lng = float(r.get("Longitude", 0))
            if lat < 0 and lng > 0:  # Lat is negative, Lng is positive
                swapped_coords.append({
                    "row_index": idx,
                    "unique_key": r.get("Unique Key"),
                    "lat": lat,
                    "lng": lng,
                })
        except ValueError:
            pass

        # 5. PII in free text fields
        res_desc = r.get("Resolution Description", "")
        phones = phone_pattern.findall(res_desc)
        emails = email_pattern.findall(res_desc)
        if phones or emails:
            pii_instances.append({
                "row_index": idx,
                "unique_key": r.get("Unique Key"),
                "phones": phones,
                "emails": emails,
                "text_snippet": res_desc[:120] + "...",
            })

        # 6. Exact duplicates
        row_tuple = tuple(sorted(r.items()))
        if row_tuple in seen_hashes:
            exact_duplicates.append({
                "row_index": idx,
                "duplicate_of": seen_hashes[row_tuple],
                "unique_key": r.get("Unique Key"),
            })
        else:
            seen_hashes[row_tuple] = idx

    report = {
        "dataset_path": filepath,
        "total_records_profiled": total_rows,
        "null_counts": null_counts,
        "anomalies_detected": {
            "closed_before_created": {
                "count": len(closed_before_created),
                "pct": round((len(closed_before_created) / total_rows) * 100, 3),
                "severity": "CRITICAL",
                "sample_examples": closed_before_created[:3],
            },
            "zip_borough_mismatch": {
                "count": len(zip_borough_mismatches),
                "pct": round((len(zip_borough_mismatches) / total_rows) * 100, 3),
                "severity": "HIGH",
                "sample_examples": zip_borough_mismatches[:3],
            },
            "lat_lng_swapped": {
                "count": len(swapped_coords),
                "pct": round((len(swapped_coords) / total_rows) * 100, 3),
                "severity": "CRITICAL",
                "sample_examples": swapped_coords[:3],
            },
            "pii_in_text": {
                "count": len(pii_instances),
                "pct": round((len(pii_instances) / total_rows) * 100, 3),
                "severity": "CRITICAL",
                "sample_examples": pii_instances[:3],
            },
            "exact_duplicates": {
                "count": len(exact_duplicates),
                "pct": round((len(exact_duplicates) / total_rows) * 100, 3),
                "severity": "MEDIUM",
                "sample_examples": exact_duplicates[:3],
            },
        }
    }

    return report


def print_profile_report(report: Dict[str, Any]):
    print("\n" + "="*80)
    print(f"NYC 311 (2023) RAW DATA QUALITY PROFILE — Total Rows: {report['total_records_profiled']}")
    print("="*80)
    anom = report["anomalies_detected"]
    for name, data in anom.items():
        print(f"\n[Problem: {name.upper()}] Severity: {data['severity']}")
        print(f"  Count: {data['count']} rows ({data['pct']}% of dataset)")
        if data['sample_examples']:
            print("  Examples:")
            for ex in data['sample_examples']:
                print(f"    - Row {ex['row_index']}: {ex}")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    rep = profile_raw_data()
    print_profile_report(rep)

