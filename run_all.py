#!/usr/bin/env python3
"""
Single-command reproduction script for all Project A & Project B results.

Usage:
    python run_all.py
"""

import subprocess
import sys
import os

# Automatically load environment variables from .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def run_step(title: str, command: list[str]):
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)
    res = subprocess.run(command)
    if res.returncode != 0:
        print(f"\n[ERROR] Command failed with exit code {res.returncode}: {' '.join(command)}")
        sys.exit(res.returncode)


def main():
    print("Fire AI Take-Home Assignment — Rules vs LLMs")
    print("Reproducing every number, benchmark, and test result...\n")

    # Project A
    run_step("1. Project A: Income Tax Engine Tests", [sys.executable, "-m", "pytest", "project_a/tests/", "-v", "--tb=short"])
    run_step("2. Project A: Surcharge, Rebate & Benchmark Measurements", [sys.executable, "-m", "project_a.benchmarks"])

    # Project B
    run_step("3. Project B: NYC 311 Raw Data Profiling", [sys.executable, "-m", "project_b.data.profile"])
    run_step("4. Project B: Data Quality Detector & Hybrid Pipeline Tests", [sys.executable, "-m", "pytest", "project_b/tests/", "-v", "--tb=short"])
    run_step("5. Project B: 12-Problem Benchmarks across 3 Detector Families", [sys.executable, "-m", "project_b.benchmarks"])

    print("\n" + "=" * 80)
    print(" SUCCESS: ALL RESULTS REPRODUCED WITH ZERO ERRORS!")
    print(" Reports available in: RESULTS_A.md, RESULTS_B.md, DECISION_MATRIX.md, AI_USAGE.md")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()

