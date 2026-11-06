"""
Rule Compiler — compiles natural language tax rules text into executable Python code.

Demonstrates the one-time compilation step for Task 2c.
"""

from __future__ import annotations
import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from project_a.impl_llm_query.rule_context import TAX_RULES_TEXT_FY_2024_25

COMPILER_PROMPT = """You are an expert compiler that turns Indian Income Tax laws and statutory provisions into executable, bug-free Python 3.10 functions.

Requirements for generated code:
1. Pure integer arithmetic where possible, Section 288B rounding (>=50 paise to nearest rupee).
2. Explicit function docstrings citing the Income Tax Act sections.
3. Fully compatible with Pydantic models.
4. Support both Old and New Tax Regimes.
"""

class RuleCompiler:
    """
    Compiles statutory rule text into executable code using LLM once.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

    def compile_rules_to_file(self, output_path: str) -> bool:
        """
        Compiles tax rules text into output python file.
        In production, calls Gemini API once to emit python code.
        """
        # If API key available, call model; otherwise the pre-compiled generated_rules.py is used.
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                resp = model.generate_content(
                    f"{COMPILER_PROMPT}\n\nCompile these rules:\n{TAX_RULES_TEXT_FY_2024_25}"
                )
                code = resp.text.replace("```python", "").replace("```", "")
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(code)
                return True
            except Exception:
                return False
        return True

