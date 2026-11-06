"""
Tests for Natural Language Parser and Clarification Engine.
"""

import json
import pytest
from project_a.nl_parser.parser import NLParser
from project_a.nl_parser.clarifier import Clarifier


def _load_nl_inputs():
    with open("project_a/tests/nl_inputs.json", "r", encoding="utf-8") as f:
        return json.load(f)


NL_CASES = _load_nl_inputs()


class TestNLParser:
    """Test NL parsing across styles (English, Hinglish, incomplete, contradictory)."""

    def test_complete_formal_input(self):
        parser = NLParser()
        text = "I earn 12 lakh per annum salary in Delhi. My basic salary is 6 lakh. I receive HRA of 3 lakh. I pay rent of 25000 per month. I am 32 years old. I invested 1.5 lakh in PPF."
        res = parser.parse(text)
        assert res.is_complete is True
        assert res.taxpayer_input is not None
        assert res.taxpayer_input.gross_salary == 1200000
        assert res.taxpayer_input.basic_salary == 600000
        assert res.taxpayer_input.hra_received == 300000
        assert res.taxpayer_input.rent_paid == 300000
        assert res.taxpayer_input.investment_80c == 150000
        assert res.taxpayer_input.is_metro is True

    def test_hinglish_input(self):
        parser = NLParser()
        text = "Meri salary 15 LPA hai Mumbai mein, age 29 saal hai, basic salary 8 lakh hai, aur 80C me 1.5 lakh invest kiya."
        res = parser.parse(text)
        assert res.is_complete is True
        assert res.taxpayer_input.gross_salary == 1500000
        assert res.taxpayer_input.age_category.value == "below_60"
        assert res.taxpayer_input.is_metro is True

    def test_incomplete_asks_clarification(self):
        parser = NLParser()
        text = "I want to calculate my income tax. I have invested 1.5 lakh in 80C."
        res = parser.parse(text)
        assert res.is_complete is False
        assert len(res.clarification_questions) > 0
        assert any("gross salary" in q.lower() for q in res.clarification_questions)
        assert any("age" in q.lower() for q in res.clarification_questions)

    def test_contradictory_rent_without_hra_asks_clarification(self):
        parser = NLParser()
        text = "My salary is 18 lakh, age is 35. I pay 30k rent per month in Delhi and want HRA exemption."
        res = parser.parse(text)
        assert res.is_complete is False
        assert any("hra" in q.lower() for q in res.clarification_questions)

    @pytest.mark.parametrize("nl_case", NL_CASES[:20], ids=[c["id"] for c in NL_CASES[:20]])
    def test_all_sample_nl_cases(self, nl_case):
        parser = NLParser()
        res = parser.parse(nl_case["input_text"])
        # Either parses completely or generates helpful clarifying questions
        assert res.is_complete or len(res.clarification_questions) > 0
