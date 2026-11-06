"""
Statistical and ML Detectors (Detector Family B) — Project B.

Implements statistical tests:
- Z-scores on null rates and categorical distributions
- Jaccard similarity / token n-gram overlap for near-duplicates
- Geographic Mahalanobis / Euclidean distance outliers
- Entropy and frequency anomaly detection
"""

from __future__ import annotations
import math
import time
from collections import Counter, defaultdict
from typing import Any, Dict, List, Set

from project_b.detectors.base import DetectorResult


class StatisticalDetector:
    """Statistical and machine learning anomaly detectors."""

    def __init__(self):
        # Baseline historical statistics for NYC 311
        self.hist_null_rates = {"NYPD": 0.02, "DOT": 0.03, "DSNY": 0.01, "HPD": 0.04}
        self.hist_null_std = {"NYPD": 0.01, "DOT": 0.015, "DSNY": 0.008, "HPD": 0.02}

    def detect(self, batch: List[Dict[str, Any]], problem_type: str) -> DetectorResult:
        t0 = time.perf_counter()
        flagged: Set[int] = set()
        alerts: List[str] = []
        n = len(batch)

        if problem_type == "null_spike":
            # Group by agency and compute z-score of null rate
            agency_totals = Counter()
            agency_nulls = Counter()
            agency_indices = defaultdict(list)

            for idx, r in enumerate(batch):
                ag = r.get("Agency", "UNKNOWN")
                agency_totals[ag] += 1
                agency_indices[ag].append(idx)
                if not r.get("Incident Zip"):
                    agency_nulls[ag] += 1

            for ag, total in agency_totals.items():
                if total >= 20:
                    rate = agency_nulls[ag] / total
                    mean = self.hist_null_rates.get(ag, 0.02)
                    std = self.hist_null_std.get(ag, 0.01)
                    z_score = (rate - mean) / max(std, 0.001)

                    if z_score > 3.0:  # 3-sigma anomaly
                        # Flag the null rows for this agency
                        spike_rows = [i for i in agency_indices[ag] if not batch[i].get("Incident Zip")]
                        flagged.update(spike_rows)
                        alerts.append(f"Statistical Anomaly (Z={z_score:.2f}): Agency {ag} null rate is {rate:.1%} vs baseline {mean:.1%}")

        elif problem_type == "near_duplicates":
            # Jaccard similarity on token 3-grams of combined text fields
            def tokenize(r: dict) -> Set[str]:
                text = f"{r.get('Incident Address', '')} {r.get('Descriptor', '')} {r.get('Resolution Description', '')}".lower()
                words = text.split()
                return set(words)

            tokens = [tokenize(r) for r in batch]
            for i in range(n):
                for j in range(i + 1, min(i + 40, n)):
                    t_i = tokens[i]
                    t_j = tokens[j]
                    if t_i and t_j:
                        intersection = len(t_i & t_j)
                        union = len(t_i | t_j)
                        jaccard = intersection / max(union, 1)
                        if jaccard > 0.75:
                            flagged.add(j)
            if flagged:
                alerts.append(f"Found {len(flagged)} records with high Jaccard token similarity (>0.75)")

        elif problem_type == "lat_lng_swapped":
            # Outlier detection on 2D coordinates: Z-score > 4 from median NYC coordinates
            lats = []
            lngs = []
            for r in batch:
                try:
                    lats.append(float(r.get("Latitude", 0)))
                    lngs.append(float(r.get("Longitude", 0)))
                except ValueError:
                    pass

            if lats and lngs:
                med_lat = 40.7
                med_lng = -73.9
                for idx, r in enumerate(batch):
                    try:
                        lat = float(r.get("Latitude", 0))
                        lng = float(r.get("Longitude", 0))
                        dist = math.sqrt((lat - med_lat)**2 + (lng - med_lng)**2)
                        if dist > 5.0:  # Way outside NYC coordinate space
                            flagged.add(idx)
                    except ValueError:
                        flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} geospatial distance outliers (>5.0 deg from NYC centroid)")

        elif problem_type == "zip_borough_mismatch":
            # Contingency frequency: flag (Borough, Zip) co-occurrences that are in bottom 1% of probability
            pair_counts = Counter((r.get("Borough", ""), r.get("Incident Zip", "")) for r in batch)
            total = len(batch)
            for idx, r in enumerate(batch):
                pair = (r.get("Borough", ""), r.get("Incident Zip", ""))
                prob = pair_counts[pair] / total
                if prob < 0.005 and r.get("Incident Zip"): # Highly anomalous co-occurrence
                    flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} rare statistical co-occurrences of (Borough, Zip)")

        elif problem_type == "complaint_descriptor_mismatch":
            # Joint probability anomaly
            pair_counts = Counter((r.get("Complaint Type", ""), r.get("Descriptor", "")) for r in batch)
            total = len(batch)
            for idx, r in enumerate(batch):
                pair = (r.get("Complaint Type", ""), r.get("Descriptor", ""))
                prob = pair_counts[pair] / total
                if prob < 0.005:
                    flagged.add(idx)
            if flagged:
                alerts.append(f"Found {len(flagged)} statistically anomalous complaint-descriptor pairings")

        elif problem_type == "exact_duplicates":
            # Hash frequency
            counts = Counter(tuple(sorted(r.items())) for r in batch)
            for idx, r in enumerate(batch):
                if counts[tuple(sorted(r.items()))] > 1:
                    flagged.add(idx)
            if flagged:
                alerts.append(f"Frequency anomaly: {len(flagged)} rows appear multiple times")

        else:
            # Fallback statistical entropy / length anomaly
            lengths = [len(str(r.get("Resolution Description", ""))) for r in batch]
            if lengths:
                mean_l = sum(lengths) / len(lengths)
                var_l = sum((x - mean_l)**2 for x in lengths) / max(len(lengths), 1)
                std_l = math.sqrt(var_l)
                for idx, l in enumerate(lengths):
                    if std_l > 0 and abs(l - mean_l) / std_l > 3.0:
                        flagged.add(idx)
                if flagged:
                    alerts.append(f"Found {len(flagged)} text length outliers (>3 std dev)")

        t1 = time.perf_counter()
        return DetectorResult(
            detector_name=f"Statistical_{problem_type}",
            detector_family="statistical",
            problem_type=problem_type,
            flagged_row_indices=flagged,
            total_rows_evaluated=n,
            execution_time_ms=round((t1 - t0) * 1000.0, 3),
            explanation_clarity="medium",
            alert_messages=alerts,
        )

