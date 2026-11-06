# Fire AI — Rules vs LLMs Take-Home Assignment

> **Core thesis**: Know when a deterministic rule is the right tool, when an LLM earns its cost, and when the answer is a combination of both — backed by measurements.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your Gemini API key in .env
# Edit .env file or copy from template:
# cp .env.example .env
# Add: GEMINI_API_KEY="your-gemini-key"

# 3. Reproduce all results with a single command
python run_all.py
# Or via make:
# make run-all
```

## Project Structure

```
FireAI/
├── project_a/          # Income Tax Engine (3 implementations)
│   ├── models.py       # Pydantic data models
│   ├── tax_rules/      # Tax constants, deductions, rebate, surcharge, cess
│   ├── impl_rules/     # Task 2a: Hand-coded deterministic rules
│   ├── impl_llm_query/ # Task 2b: LLM computes tax per request
│   ├── impl_llm_compiled/ # Task 2c: LLM generates rules once
│   ├── nl_parser/      # Task 3: Free-text to structured input
│   ├── benchmarks.py   # Task 4: Measurement harness
│   └── tests/          # 200+ test cases, 50 NL inputs
│
├── project_b/          # Data Quality Checks
│   ├── data/           # NYC 311 data downloader & profiler
│   ├── injector/       # 12 corruption types
│   ├── detectors/      # Rules, Statistical, LLM detectors
│   ├── hybrid_pipeline.py
│   ├── benchmarks.py
│   └── tests/
│
├── RESULTS_A.md        # Project A comparison & final design
├── RESULTS_B.md        # Project B detection tables & scale design
├── DECISION_MATRIX.md  # Rule vs LLM justification per component
└── AI_USAGE.md         # AI tools used & error caught
```

## Project A — Income Tax Engine

Computes Indian income tax for salaried individuals under both old and new regimes (FY 2024-25 / AY 2025-26), with natural language input support.

### Three Implementations

| Implementation | Approach | When to Use |
|----------------|----------|-------------|
| `impl_rules` | Hand-coded Python rules | ✅ Production: deterministic, auditable, fast |
| `impl_llm_query` | Gemini API per request | ❌ Research only: non-deterministic, costly |
| `impl_llm_compiled` | LLM generates rules once | ⚠️ Bootstrap: useful for initial rule generation |

### Running Tests

```bash
# Run all Project A tests
python -m pytest project_a/tests/ -v

# Run specific test category
python -m pytest project_a/tests/test_rules.py -v -k "slab_boundary"
```

## Project B — Data Quality Checks

Detects 12 types of data quality problems in NYC 311 Service Request data using a tiered approach: cheap rules on every row, statistics per batch, LLM only on flagged rows.

### Running the Pipeline

```bash
# Profile raw data
python -m project_b.data.profile

# Run corruption injection + detection benchmarks
python -m project_b.benchmarks
```

## Key Decisions

See [DECISION_MATRIX.md](DECISION_MATRIX.md) for the full decision matrix with measurements.

**TL;DR**: Rules win on correctness, cost, and auditability. LLMs earn their cost only for:
1. Natural language parsing (Project A)
2. Semantic consistency checks (Project B — complaint↔descriptor, resolution↔status)
3. Near-duplicate confirmation (Project B)

## Requirements

- Python 3.10+
- Gemini API key (free tier)
- ~2GB disk space for NYC 311 data

## Author

Built as part of Fire AI's take-home assignment.

