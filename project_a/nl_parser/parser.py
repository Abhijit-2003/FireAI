"""
Natural Language Parser for Taxpayer Descriptions.

Combines LLM extraction with rule-based clarification and regex fallback
to convert free-text into a validated TaxpayerInput.
"""

from __future__ import annotations
import json
import os
import re
from typing import Any, Dict, List, Optional, Union

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from project_a.models import TaxpayerInput, AgeCategory
from project_a.impl_rules.calculator import _dict_to_taxpayer_input
from project_a.nl_parser.clarifier import Clarifier
from project_a.nl_parser.prompts import NL_EXTRACTION_SYSTEM_PROMPT


class NLParseResult:
    """Result of parsing natural language text."""

    def __init__(
        self,
        is_complete: bool,
        taxpayer_input: Optional[TaxpayerInput] = None,
        clarification_questions: Optional[List[str]] = None,
        raw_extracted: Optional[Dict[str, Any]] = None,
    ):
        self.is_complete = is_complete
        self.taxpayer_input = taxpayer_input
        self.clarification_questions = clarification_questions or []
        self.raw_extracted = raw_extracted or {}

    def to_dict(self) -> dict[str, Any]:
        return {
            "is_complete": self.is_complete,
            "has_input": self.taxpayer_input is not None,
            "clarification_questions": self.clarification_questions,
            "raw_extracted": self.raw_extracted,
        }


class NLParser:
    """
    Parses unstructured user descriptions in English and Hinglish into TaxpayerInput.
    """

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.model_name = model_name
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self._client = None
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=NL_EXTRACTION_SYSTEM_PROMPT,
                    generation_config={"response_mime_type": "application/json"}
                )
            except Exception:
                self._client = None

    def parse(self, text: str) -> NLParseResult:
        """Parse natural language description into TaxpayerInput or clarifying questions."""
        extracted: dict[str, Any] = {}

        if self._client:
            try:
                resp = self._client.generate_content(f"Parse this text:\n{text}")
                extracted = json.loads(resp.text.strip())
            except Exception:
                extracted = self._regex_fallback_extract(text)
        else:
            extracted = self._regex_fallback_extract(text)

        # Check for completeness, ambiguities, contradictions
        is_complete, questions = Clarifier.inspect(extracted, raw_text=text)

        if not is_complete:
            return NLParseResult(
                is_complete=False,
                taxpayer_input=None,
                clarification_questions=questions,
                raw_extracted=extracted,
            )

        # Build TaxpayerInput
        inp = _dict_to_taxpayer_input(extracted)
        return NLParseResult(
            is_complete=True,
            taxpayer_input=inp,
            clarification_questions=[],
            raw_extracted=extracted,
        )

    def _regex_fallback_extract(self, text: str) -> dict[str, Any]:
        """Robust deterministic rule-based extractor for Hinglish and English text."""
        d: dict[str, Any] = {
            "gross_salary": None,
            "basic_salary": None,
            "da": 0,
            "hra_received": 0,
            "rent_paid": 0,
            "city_type": None,
            "age": None,
            "section_80c": 0,
            "section_80ccd_1b": 0,
            "section_80d_self": 0,
            "section_80d_parents": 0,
            "parents_senior_citizen": False,
            "home_loan_interest": 0,
            "financial_year": "2024-25",
        }

        t_lower = text.lower()

        # Gross Salary / LPA / Lakh
        m_lpa = re.search(r"(\d+(?:\.\d+)?)\s*(?:lpa|lakh|lac|l)\b", t_lower)
        if m_lpa and ("earn" in t_lower or "salary" in t_lower or "ctc" in t_lower or "kamaata" in t_lower or "package" in t_lower or "gross" in t_lower):
            d["gross_salary"] = int(float(m_lpa.group(1)) * 100_000)

        m_num = re.search(r"(?:salary|ctc|package|earn|earning|income)\s*(?:of|is|:)?\s*(?:rs\.?|inr|₹)?\s*(\d{5,8})", t_lower)
        if m_num and not d["gross_salary"]:
            d["gross_salary"] = int(m_num.group(1))

        # Basic Salary
        m_basic = re.search(r"basic\s*(?:salary)?\s*(?:is|of|:)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|l)?", t_lower)
        if m_basic:
            val = float(m_basic.group(1))
            d["basic_salary"] = int(val * 100_000) if val < 100 else int(val)

        # HRA Received
        m_hra = re.search(r"hra\s*(?:received|component)?\s*(?:is|of|:)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(lakh|lac|l|k)?\b", t_lower)
        if m_hra:
            val = float(m_hra.group(1))
            unit = m_hra.group(2) or ""
            if unit == "k":
                d["hra_received"] = int(val * 1_000)
            elif unit in ["lakh", "lac", "l"] or val < 100:
                d["hra_received"] = int(val * 100_000)
            else:
                d["hra_received"] = int(val)

        # Rent paid (monthly vs annual) - both "rent 25k/month" and "25k rent per month"
        m_rent_m = re.search(r"(?:rent\s*(?:of|is|:)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(k)?|(\d+(?:\.\d+)?)\s*(k)?\s*rent)\s*(?:per month|pm|/month|har mahine)", t_lower)
        if m_rent_m:
            val_str = m_rent_m.group(1) or m_rent_m.group(3)
            unit_str = m_rent_m.group(2) or m_rent_m.group(4) or ""
            val = float(val_str)
            val = val * 1000 if (unit_str == "k" or val < 100) else val
            d["rent_paid"] = int(val * 12)
        else:
            m_rent = re.search(r"(?:rent\s*(?:paid|deta)?\s*(?:of|is|:)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(lakh|lac|l|k)?|(\d+(?:\.\d+)?)\s*(lakh|lac|l|k)?\s*rent)", t_lower)
            if m_rent and not ("no rent" in t_lower or "zero rent" in t_lower):
                val_str = m_rent.group(1) or m_rent.group(3)
                unit = m_rent.group(2) or m_rent.group(4) or ""
                val = float(val_str)
                if unit == "k":
                    d["rent_paid"] = int(val * 1000 * 12) if val < 100 else int(val * 1000)
                elif unit in ["lakh", "lac", "l"] or val < 100:
                    d["rent_paid"] = int(val * 100_000)
                else:
                    d["rent_paid"] = int(val)

        # City Metro vs Non-metro
        if any(c in t_lower for c in ["delhi", "mumbai", "kolkata", "chennai", "metro"]):
            d["city_type"] = "metro"
        elif any(c in t_lower for c in ["bangalore", "bengaluru", "hyderabad", "pune", "non-metro", "village", "town"]):
            d["city_type"] = "non_metro"

        # Age
        m_age = re.search(r"\b(?:age|aged|am|saal)\s*(?:is|of|:)?\s*(\d{2})\b|\b(\d{2})\s*(?:years old|yr old|saal ka|saal ki)\b", t_lower)
        if m_age:
            a_val = m_age.group(1) or m_age.group(2)
            d["age"] = int(a_val)

        # 80C (PPF, ELSS, PF, LIC, school fee) - handles both "ppf 1.5L" and "1.5L in ppf"
        m_80c = re.search(r"(?:(?:80c|ppf|elss|pf|lic|provident fund)\s*(?:mein|of|is|:)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(lakh|lac|l|k)?|(\d+(?:\.\d+)?)\s*(lakh|lac|l|k)?\s*(?:in|mein)\s*(?:80c|ppf|elss|pf|lic|provident fund))", t_lower)
        if m_80c:
            val_str = m_80c.group(1) or m_80c.group(3)
            unit_str = m_80c.group(2) or m_80c.group(4) or ""
            val = float(val_str)
            if unit_str == "k":
                d["section_80c"] = int(val * 1000)
            elif unit_str in ["lakh", "lac", "l"] or val <= 15:
                d["section_80c"] = int(val * 100_000)
            else:
                d["section_80c"] = int(val)

        # 80CCD NPS
        m_nps = re.search(r"(?:nps|80ccd)\s*(?:mein|of|is|:)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|l|k)?", t_lower)
        if m_nps:
            val = float(m_nps.group(1))
            if "k" in m_nps.group(0):
                d["section_80ccd_1b"] = int(val * 1000)
            elif val <= 10:
                d["section_80ccd_1b"] = int(val * 100_000)
            else:
                d["section_80ccd_1b"] = int(val)

        # 80D Health Insurance
        m_80d = re.search(r"(?:health insurance|medical insurance|mediclaim|80d)\s*(?:of|is|:)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(?:k)?", t_lower)
        if m_80d:
            val = float(m_80d.group(1))
            d["section_80d_self"] = int(val * 1000) if ("k" in m_80d.group(0) or val < 100) else int(val)

        if "parents" in t_lower and ("senior" in t_lower or "bujurg" in t_lower):
            d["parents_senior_citizen"] = True

        # Home loan interest
        m_hl = re.search(r"(?:home loan|housing loan)\s*(?:interest)?\s*(?:of|is|:)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*(?:lakh|lac|l|k)?", t_lower)
        if m_hl:
            val = float(m_hl.group(1))
            if "k" in m_hl.group(0):
                d["home_loan_interest"] = int(val * 1000)
            elif val <= 20:
                d["home_loan_interest"] = int(val * 100_000)
            else:
                d["home_loan_interest"] = int(val)

        return d
