"""
Corruption Injector for NYC 311 Data — Task 2 of Project B.

Injects all 12 problem types at controlled rates and tracks ground-truth labels:
  a. Renamed or dropped column
  b. Column type change (numbers as strings or corrupted formatting)
  c. Date format switch partway through a batch (e.g. ISO-8601 to US or DD/MM/YYYY)
  d. Latitude and longitude swapped
  e. Exact duplicates
  f. Near-duplicates (same request, slightly altered timestamp or text)
  g. Null spike in one agency's records
  h. Closed date earlier than created date
  i. ZIP code inconsistent with borough
  j. Complaint Type inconsistent with Descriptor
  k. Resolution Description contradicting Status
  l. Personal data (phone numbers, emails, names) inside free-text fields
"""

from __future__ import annotations
import copy
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List, Set, Tuple

PROBLEM_TYPES = [
    "renamed_dropped_col",
    "col_type_change",
    "date_format_switch",
    "lat_lng_swapped",
    "exact_duplicates",
    "near_duplicates",
    "null_spike",
    "closed_before_created",
    "zip_borough_mismatch",
    "complaint_descriptor_mismatch",
    "resolution_status_contradiction",
    "pii_in_text",
]

BOROUGH_MISMATCH_MAP = {
    "MANHATTAN": "11201",     # Brooklyn ZIP in Manhattan
    "BROOKLYN": "10001",      # Manhattan ZIP in Brooklyn
    "QUEENS": "10451",         # Bronx ZIP in Queens
    "BRONX": "10301",          # Staten Island ZIP in Bronx
    "STATEN ISLAND": "11354",  # Queens ZIP in Staten Island
}

CONTRADICTORY_COMPLAINTS = {
    "Noise - Residential": "Pothole",
    "Illegal Parking": "Loud Music/Party",
    "Heat/Hot Water": "Blocked Hydrant",
    "Street Condition": "Entire Building",
}


class CorruptionInjector:
    """
    Injects 12 data quality corruption types into batches of NYC 311 records.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        random.seed(seed)

    def inject(
        self,
        batch: List[Dict[str, Any]],
        problem_type: str,
        rate: float = 0.05,
    ) -> Tuple[List[Dict[str, Any]], Set[int]]:
        """
        Injects a specific corruption into a clean batch.
        Returns:
            (corrupted_batch, set_of_corrupted_row_indices)
        """
        records = [copy.deepcopy(r) for r in batch]
        n = len(records)
        target_count = max(1, int(n * rate))
        affected_indices: Set[int] = set()

        if problem_type == "renamed_dropped_col":
            # Batch-level schema corruption
            col_to_corrupt = "Incident Zip"
            action = "drop" if random.random() < 0.5 else "rename"
            for idx in range(n):
                affected_indices.add(idx)
                if action == "drop":
                    records[idx].pop(col_to_corrupt, None)
                else:
                    val = records[idx].pop(col_to_corrupt, None)
                    records[idx]["Postal_Code_Zip"] = val

        elif problem_type == "col_type_change":
            # Column type change: Incident Zip corrupted into non-numeric string or corrupt string
            sample_indices = random.sample(range(n), target_count)
            for idx in sample_indices:
                affected_indices.add(idx)
                records[idx]["Incident Zip"] = "ZIP_UNAVAIL_" + str(random.randint(100, 999))

        elif problem_type == "date_format_switch":
            # Partway through the batch, switch date format from MM/DD/YYYY HH:MM:SS AM/PM to YYYY-MM-DD HH:MM:SS
            start_idx = n - target_count
            for idx in range(start_idx, n):
                affected_indices.add(idx)
                dt_str = records[idx]["Created Date"]
                try:
                    dt = datetime.strptime(dt_str, "%m/%d/%Y %I:%M:%S %p")
                    records[idx]["Created Date"] = dt.strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass

        elif problem_type == "lat_lng_swapped":
            sample_indices = random.sample(range(n), target_count)
            for idx in sample_indices:
                affected_indices.add(idx)
                records[idx]["Latitude"], records[idx]["Longitude"] = (
                    records[idx]["Longitude"],
                    records[idx]["Latitude"],
                )

        elif problem_type == "exact_duplicates":
            sample_indices = random.sample(range(n - target_count), target_count)
            for i, src_idx in enumerate(sample_indices):
                dest_idx = n - target_count + i
                affected_indices.add(dest_idx)
                records[dest_idx] = copy.deepcopy(records[src_idx])

        elif problem_type == "near_duplicates":
            sample_indices = random.sample(range(n - target_count), target_count)
            for i, src_idx in enumerate(sample_indices):
                dest_idx = n - target_count + i
                affected_indices.add(dest_idx)
                dupe = copy.deepcopy(records[src_idx])
                dupe["Unique Key"] = str(int(dupe["Unique Key"]) + 9000000)
                # Alter timestamp slightly (+2 minutes) and append typo to text
                try:
                    dt = datetime.strptime(dupe["Created Date"], "%m/%d/%Y %I:%M:%S %p")
                    dupe["Created Date"] = (dt + timedelta(minutes=2)).strftime("%m/%d/%Y %I:%M:%S %p")
                except Exception:
                    pass
                dupe["Resolution Description"] += " [Follow-up citizen duplicate ticket]"
                records[dest_idx] = dupe

        elif problem_type == "null_spike":
            # One specific agency (e.g. NYPD) has a massive spike of nulls in Incident Zip
            target_agency = "NYPD"
            agency_rows = [i for i, r in enumerate(records) if r.get("Agency") == target_agency]
            spike_indices = random.sample(agency_rows, min(len(agency_rows), target_count))
            for idx in spike_indices:
                affected_indices.add(idx)
                records[idx]["Incident Zip"] = ""

        elif problem_type == "closed_before_created":
            sample_indices = random.sample(range(n), target_count)
            for idx in sample_indices:
                affected_indices.add(idx)
                c_str = records[idx]["Created Date"]
                try:
                    c_dt = datetime.strptime(c_str, "%m/%d/%Y %I:%M:%S %p")
                    # Closed date 4 hours BEFORE created date
                    records[idx]["Closed Date"] = (c_dt - timedelta(hours=4)).strftime("%m/%d/%Y %I:%M:%S %p")
                    records[idx]["Status"] = "Closed"
                except Exception:
                    pass

        elif problem_type == "zip_borough_mismatch":
            sample_indices = random.sample(range(n), target_count)
            for idx in sample_indices:
                affected_indices.add(idx)
                borough = records[idx].get("Borough", "MANHATTAN")
                records[idx]["Incident Zip"] = BOROUGH_MISMATCH_MAP.get(borough, "11201")

        elif problem_type == "complaint_descriptor_mismatch":
            sample_indices = random.sample(range(n), target_count)
            for idx in sample_indices:
                affected_indices.add(idx)
                c_type = records[idx]["Complaint Type"]
                records[idx]["Descriptor"] = CONTRADICTORY_COMPLAINTS.get(c_type, "Pothole in Living Room")

        elif problem_type == "resolution_status_contradiction":
            sample_indices = random.sample(range(n), target_count)
            for idx in sample_indices:
                affected_indices.add(idx)
                # Status is 'Closed', but resolution explicitly states still open/investigating, or vice-versa
                if random.random() < 0.5:
                    records[idx]["Status"] = "Closed"
                    records[idx]["Resolution Description"] = "The violation is active and currently UNRESOLVED. Case remains open for inspection."
                else:
                    records[idx]["Status"] = "Open"
                    records[idx]["Resolution Description"] = "The condition was inspected and completely RESOLVED. Violation closed permanently."

        elif problem_type == "pii_in_text":
            sample_indices = random.sample(range(n), target_count)
            pii_payloads = [
                " Call citizen John Doe at (212) 555-0199 for access.",
                " Contact complainant Jane Smith via email: jsmith99@gmail.com.",
                " Officer badge #4821 Robert Davis direct cell: 917-555-8833.",
            ]
            for idx in sample_indices:
                affected_indices.add(idx)
                records[idx]["Resolution Description"] += random.choice(pii_payloads)

        return records, affected_indices

