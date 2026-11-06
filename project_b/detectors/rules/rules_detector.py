"""
Declarative Rules and Schema Checks (Detector Family A) — Project B.
"""

from __future__ import annotations
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Set

from project_b.detectors.base import DetectorResult
from project_b.data.download import NYC_BOROUGH_ZIPS

EXPECTED_COLUMNS = {
    "Unique Key", "Created Date", "Closed Date", "Agency", "Agency Name",
    "Complaint Type", "Descriptor", "Location Type", "Incident Zip",
    "Incident Address", "Street Name", "City", "Status",
    "Resolution Description", "Borough", "Latitude", "Longitude"
}

VALID_COMPLAINT_DESCRIPTORS = {
    "Noise - Residential": {"Loud Music/Party", "Banging/Pounding", "Loud Talking"},
    "Illegal Parking": {"Blocked Hydrant", "Posted Parking Sign Violation", "Double Parked"},
    "Blocked Driveway": {"No Access", "Partial Access"},
    "Heat/Hot Water": {"Entire Building", "Apartment Only"},
    "Street Condition": {"Pothole", "Cave-in", "Rough Roadway"},
    "Sanitation Condition": {"Garbage or Litter", "Dirty Sidewalk"},
    "Water System": {"Hydrant Running Full", "No Water"},
    "Damaged Tree": {"Branch Cracked and Will Fall", "Tree Leaning"},
}

PHONE_REGEX = re.compile(r"\b(?:\+?1[-.]?)?\(?[2-9]\d{2}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
DATE_REGEX = re.compile(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2} (?:AM|PM)$")


class RulesDetector:
    """Fast, deterministic, declarative rule checks on batch rows."""

    def detect(self, batch: List[Dict[str, Any]], problem_type: str) -> DetectorResult:
        t0 = time.perf_counter()
        flagged: Set[int] = set()
        alerts: List[str] = []
        n = len(batch)

        if problem_type == "renamed_dropped_col":
            if batch:
                actual_cols = set(batch[0].keys())
                missing = EXPECTED_COLUMNS - actual_cols
                unexpected = actual_cols - EXPECTED_COLUMNS
                if missing or unexpected:
                    flagged.update(range(n))
                    alerts.append(f"Schema violation: Missing {missing}, Unexpected {unexpected}")

        elif problem_type == "col_type_change":
            for idx, r in enumerate(batch):
                zip_val = str(r.get("Incident Zip", "")).strip()
                if zip_val and not (zip_val.isdigit() and len(zip_val) == 5):
                    flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} records with invalid ZIP type/format")

        elif problem_type == "date_format_switch":
            for idx, r in enumerate(batch):
                c_date = str(r.get("Created Date", ""))
                if not DATE_REGEX.match(c_date):
                    flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} records with non-standard date format")

        elif problem_type == "lat_lng_swapped":
            for idx, r in enumerate(batch):
                try:
                    lat = float(r.get("Latitude", 0))
                    lng = float(r.get("Longitude", 0))
                    # NYC is strictly Lat in [40.4, 41.0] and Lng in [-74.3, -73.6]
                    if lat < 0 or lng > 0:
                        flagged.add(idx)
                except ValueError:
                    flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} records with inverted geographic coordinates")

        elif problem_type == "exact_duplicates":
            seen = {}
            for idx, r in enumerate(batch):
                row_key = tuple(sorted(r.items()))
                if row_key in seen:
                    flagged.add(idx)
                else:
                    seen[row_key] = idx
            if flagged:
                alerts.append(f"Found {len(flagged)} exact duplicate rows")

        elif problem_type == "near_duplicates":
            # Rule heuristic: same Agency + Address + Complaint Type within same batch
            seen_signatures = {}
            for idx, r in enumerate(batch):
                sig = (r.get("Agency"), r.get("Incident Address"), r.get("Complaint Type"))
                if sig[0] and sig[1]:
                    if sig in seen_signatures:
                        flagged.add(idx)
                    else:
                        seen_signatures[sig] = idx
            if flagged:
                alerts.append(f"Found {len(flagged)} potential duplicate submissions at same address")

        elif problem_type == "null_spike":
            # Rule threshold: if NYPD Incident Zip null rate > 20%
            nypd_rows = [i for i, r in enumerate(batch) if r.get("Agency") == "NYPD"]
            nypd_nulls = [i for i in nypd_rows if not batch[i].get("Incident Zip")]
            if nypd_rows and (len(nypd_nulls) / len(nypd_rows) > 0.15):
                flagged.update(nypd_nulls)
                alerts.append(f"Alert: NYPD Incident Zip null rate {len(nypd_nulls)/len(nypd_rows):.1%} exceeds 15% threshold")

        elif problem_type == "closed_before_created":
            for idx, r in enumerate(batch):
                c_str = r.get("Created Date")
                cl_str = r.get("Closed Date")
                if c_str and cl_str:
                    try:
                        c_dt = datetime.strptime(c_str, "%m/%d/%Y %I:%M:%S %p")
                        cl_dt = datetime.strptime(cl_str, "%m/%d/%Y %I:%M:%S %p")
                        if cl_dt < c_dt:
                            flagged.add(idx)
                    except Exception:
                        pass
            if flagged:
                alerts.append(f"Found {len(flagged)} records where ticket Closed Date is before Created Date")

        elif problem_type == "zip_borough_mismatch":
            for idx, r in enumerate(batch):
                b = r.get("Borough", "").upper()
                z = str(r.get("Incident Zip", ""))
                if b in NYC_BOROUGH_ZIPS and z:
                    if z not in NYC_BOROUGH_ZIPS[b]:
                        flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} records where Incident Zip does not belong to specified Borough")

        elif problem_type == "complaint_descriptor_mismatch":
            for idx, r in enumerate(batch):
                c = r.get("Complaint Type", "")
                d = r.get("Descriptor", "")
                if c in VALID_COMPLAINT_DESCRIPTORS:
                    if d not in VALID_COMPLAINT_DESCRIPTORS[c]:
                        flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} records with invalid Complaint-Descriptor combinations")

        elif problem_type == "resolution_status_contradiction":
            for idx, r in enumerate(batch):
                status = str(r.get("Status", "")).lower()
                res = str(r.get("Resolution Description", "")).lower()
                if "closed" in status and ("unresolved" in res or "remains open" in res):
                    flagged.add(idx)
                elif "open" in status and ("completely resolved" in res or "closed permanently" in res):
                    flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} records with direct status vs resolution description contradiction")

        elif problem_type == "pii_in_text":
            for idx, r in enumerate(batch):
                res = str(r.get("Resolution Description", ""))
                if PHONE_REGEX.search(res) or EMAIL_REGEX.search(res):
                    flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} records containing unredacted phone numbers or emails")

        t1 = time.perf_counter()
        return DetectorResult(
            detector_name=f"Rules_{problem_type}",
            detector_family="rules",
            problem_type=problem_type,
            flagged_row_indices=flagged,
            total_rows_evaluated=n,
            execution_time_ms=round((t1 - t0) * 1000.0, 3),
            explanation_clarity="high",
            alert_messages=alerts,
        )
