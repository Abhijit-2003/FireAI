"""
Clarification Engine for Natural Language Tax Inputs.

Rule-based completeness, ambiguity, and contradiction checking.
Decides when clarifying questions must be asked instead of guessing.
"""

from __future__ import annotations
from typing import Any, List, Tuple


class Clarifier:
    """
    Checks structured extraction for missing fields, ambiguities, or contradictions.
    """

    @staticmethod
    def inspect(extracted_data: dict[str, Any], raw_text: str = "") -> Tuple[bool, List[str]]:
        """
        Evaluates extracted taxpayer input.
        Returns (is_ready_for_calculation: bool, list_of_clarifications: List[str]).
        """
        questions: List[str] = []

        # 1. Mandatory Core Fields
        gross = extracted_data.get("gross_salary")
        if gross is None or gross <= 0:
            questions.append("What is your total annual gross salary (CTC/earnings)?")

        age = extracted_data.get("age")
        if age is None or age <= 0:
            questions.append("What is your age as on 31st March? (Required to determine exemption limit & deductions)")

        # 2. Contradiction & Ambiguity Checks
        hra_received = extracted_data.get("hra_received", 0)
        rent_paid = extracted_data.get("rent_paid", 0)

        # Contradiction: Claiming rent without HRA or vice-versa when asking for HRA exemption
        if rent_paid > 0 and hra_received == 0:
            questions.append(
                f"You mentioned paying ₹{rent_paid:,} annual rent. How much HRA (House Rent Allowance) do you receive from your employer?"
            )
        elif hra_received > 0 and rent_paid == 0:
            # Check if text claims HRA exemption
            text_lower = raw_text.lower()
            if "exempt" in text_lower or "claim hra" in text_lower or "rent" in text_lower:
                questions.append(
                    "You receive HRA from your employer. How much annual rent do you pay to claim HRA tax exemption?"
                )

        basic = extracted_data.get("basic_salary") or 0
        da = extracted_data.get("da") or 0
        if gross and (basic + da > gross):
            questions.append(
                f"Your basic salary (₹{basic:,}) plus DA (₹{da:,}) exceeds your gross salary (₹{gross:,}). Could you please clarify your exact basic salary component?"
            )

        # Ambiguous city type when HRA is relevant
        city = extracted_data.get("city_type")
        if (hra_received > 0 and rent_paid > 0) and not city:
            questions.append(
                "Do you reside in a metro city (Delhi, Mumbai, Kolkata, Chennai) or a non-metro city? (Metro gets 50% basic allowance, non-metro gets 40%)"
            )

        # Contradictory Senior Citizen claims
        if extracted_data.get("is_self_senior") and age and age < 60:
            questions.append(
                f"You indicated being a senior citizen, but your stated age is {age}. Senior citizen benefits apply at age 60 and above. Please confirm your age."
            )

        is_complete = len(questions) == 0
        return is_complete, questions
