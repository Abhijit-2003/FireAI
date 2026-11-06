"""
Prompt templates for LLM at query time.
"""

from __future__ import annotations
import json
from typing import Any
from project_a.impl_llm_query.rule_context import TAX_RULES_TEXT_FY_2024_25, TAX_RULES_TEXT_FY_2025_26

SYSTEM_PROMPT = """You are an expert Indian Income Tax computation engine.
Your task is to compute the exact rupee-level income tax for a salaried individual for both Old and New Tax Regimes, following the official Income Tax Act rules strictly.

You must return a valid JSON object strictly matching this schema:
{
  "old_regime": {
    "taxable_income": int,
    "tax_before_rebate": int,
    "rebate_87a": int,
    "tax_after_rebate": int,
    "surcharge": int,
    "cess": int,
    "total_tax": int,
    "audit_trail": [string]
  },
  "new_regime": {
    "taxable_income": int,
    "tax_before_rebate": int,
    "rebate_87a": int,
    "tax_after_rebate": int,
    "surcharge": int,
    "cess": int,
    "total_tax": int,
    "audit_trail": [string]
  },
  "recommended_regime": "old" | "new",
  "tax_savings": int,
  "explanation": string
}

Ensure:
- All monetary amounts are non-negative integers.
- Exact rupee precision.
- Trace every deduction and calculation to its section in the audit trail.
- Section 288B rounding to nearest rupee.
"""

def build_query_prompt(taxpayer_data: dict[str, Any], fy: str = "2024-25") -> str:
    rules = TAX_RULES_TEXT_FY_2025_26 if fy == "2025-26" else TAX_RULES_TEXT_FY_2024_25
    return f"""### OFFICIAL INCOME TAX RULES:
{rules}

### TAXPAYER DETAILS:
{json.dumps(taxpayer_data, indent=2)}

Please compute the exact income tax for both regimes according to the provided rules.
Return ONLY valid JSON matching the schema.
"""

