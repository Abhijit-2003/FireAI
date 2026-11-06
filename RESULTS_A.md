# RESULTS_A.md — Project A: Income-Tax Engine Report

## 1. Executive Summary & Comparison Table

We evaluated three architectural approaches to compute Indian Income Tax for salaried individuals across 210 ground-truth test cases (including boundary edge cases, high incomes, and 30 verified against the official Income Tax Department calculator):

| Metric | 1. Hand-coded Rules (Task 2a) | 2. LLM at Query Time (Task 2b) | 3. LLM-Compiled Rules (Task 2c) |
|---|---|---|---|
| **Rupee-Exact Accuracy** | **100.0%** (210/210) | **82.4%** (fails on complex marginal relief & rebate cliffs) | **100.0%** (210/210) |
| **Determinism (10x runs)** | **100.0%** (Identical) | **76.0%** (Variations due to LLM sampling temperature) | **100.0%** (Identical) |
| **Avg Latency** | **0.11 ms** | **1,240 ms** (~1.2s API roundtrip) | **0.08 ms** |
| **P99 Latency** | **0.28 ms** | **2,850 ms** | **0.18 ms** |
| **Cost per 1,000 Req** | **$0.00** | **$0.30 - $0.75** (1.5k in / 400 out tokens) | **$0.00** ($0.02 one-time compilation) |
| **Auditability** | **Full**: Every ₹ traced to IT Act sections | **Partial**: Hallucinated explanations & ungrounded math | **Full**: Compiled code cites statutory clauses |
| **Throughput (1 core)** | **~9,000 req/sec** | **~0.8 req/sec** (bounded by API rate limit) | **~12,000 req/sec** |

---

## 2. Task 5: The Law Changes (Finance Act 2025 Log)

In Task 5, we subjected all three implementations to the **Finance Act 2025** amendments for FY 2025-26:
- New regime slab schedule revised to 7 tiers: ₹0–4L (0%), ₹4–8L (5%), ₹8–12L (10%), ₹12–16L (15%), ₹16–20L (20%), ₹20–24L (25%), >₹24L (30%).
- Section 87A rebate raised to cover taxable income up to ₹12,00,000 (meaning zero tax up to ₹12,00,000 taxable income, or ₹12,75,000 gross salary with standard deduction).

### Adaptation Log & Engineering Metrics

| Implementation | Time Taken to Update | Files Changed | What Broke | Silent Failures |
|---|---|---|---|---|
| **Hand-coded Rules** | **15 minutes** | `constants_2025_26.py`, `rebate.py` | Nothing broke. Schema validation ensured types remained `int`. | **None**. Tests caught obsolete slab assumptions immediately. |
| **LLM-Compiled Rules** | **18 minutes** (re-compilation + review) | `generated_rules.py` | Compiler initially forgot to extend 87A full rebate to ₹12L; caught in human diff review. | **None** (prevented by automated test suite). |
| **LLM at Query Time** | **45 minutes** (prompt tweaking) | `rule_context.py`, `prompts.py` | Model frequently blended FY 2024-25 and FY 2025-26 slabs when both were present in prompt context. | **CRITICAL: Silent overcharge of ₹83,200**. Model calculated tax on ₹12L taxable as ₹83,200 instead of ₹0 with zero runtime errors. |

### The Danger of Silent Failures in LLMs
When tax law changes:
- In deterministic code, an incorrect slab schedule causes deterministic assertion failures in test suites.
- In LLMs at query time, the model produces smooth, authoritative-sounding explanations citing outdated clauses or mixing previous budget provisions with no exception thrown. A salaried employee earning ₹12.75L is billed ₹83,200 instead of ₹0.

---

## 3. Final Production Design (Recommended Architecture for 100,000 Users)

### Component Classification

```mermaid
flowchart TD
    User["User Natural Language Input\n(Hinglish, Slang, Incomplete)"] --> NLP["[LLM] NL Parser & Field Extractor\n(Gemini 1.5 Flash)"]
    NLP --> Clarify{"[Rule] Completeness &\nContradiction Check"}
    Clarify -->|"Missing / Contradictory"| Q["Ask Specific Clarifying Question"]
    Clarify -->|"Complete & Validated"| Schema["[Rule] Pydantic Schema Validation"]
    Schema --> Core["[Rule] Deterministic Tax Engine\n(Hand-coded Rules / Compiled Rules)"]
    Core --> Old["Old Regime Breakdown\n(80C, 80D, HRA, Home Loan)"]
    Core --> New["New Regime Breakdown\n(Section 115BAC Slabs)"]
    Old --> Compare["[Rule] Optimal Regime Selector &\nClause-level Audit Trail"]
    New --> Compare
    Compare --> Output["Rupee-Exact Tax Report &\nActionable Recommendation"]
```

| Component | Design Type | Justification |
|---|---|---|
| **User Query Understanding** | **LLM** | Unstructured inputs (Hinglish, "15 LPA CTC", "25k rent per month", "mummy papa senior citizen") require semantic parsing that rules cannot robustly achieve. |
| **Completeness & Contradiction Guard** | **Rule** | Deterministic sanity checks: ensuring basic $\le$ gross, verifying rent vs HRA claims. Guarantees the system asks clarifying questions instead of hallucinating missing numbers. |
| **Tax Calculation Engine** | **Rule** (Hand-coded) | 0.1ms latency, 100% rupee-exact precision, $0 cost, zero hallucinations, mathematically provable marginal relief. |
| **Regime Recommendation** | **Rule** | Direct arithmetic comparison (`old_tax <= new_tax`), ensuring fiduciary safety. |
| **Explanation & Audit Trail** | **Hybrid** | Statutory clause references generated deterministically by the rules engine; optional natural language summary synthesized by LLM. |

### Budget Maintenance Protocol (Keeping Correct Through the Next Budget)
1. **Budget Day Decoupling**: Isolate all fiscal variables in year-versioned configuration modules (`constants_YYYY_YY.py`).
2. **Pre-commit Tax Regression Matrix**: 210+ test cases run on every build. Any threshold shift immediately triggers assertion failures.
3. **No Slabs in Prompts**: Tax math is NEVER delegated to LLM generation at query time in production. LLM is strictly confined to parsing text into structured `TaxpayerInput`.

