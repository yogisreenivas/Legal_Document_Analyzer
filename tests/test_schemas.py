"""
test_schemas.py - Unit tests for Pydantic output models.

Tests cover:
- Model creation with valid data
- Default values
- Required field validation
- Optional field handling
- DocumentExtraction with nested models
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
from pydantic import ValidationError
from app.schemas.output_models import (
    PartyInfo,
    Obligation,
    Condition,
    Deadline,
    Penalty,
    FinancialTerm,
    KeyClause,
    Citation,
    DocumentExtraction,
    AnalysisResult,
)


# ── Tests for Individual Models ───────────────────────────────


class TestPartyInfo:
    """Tests for the PartyInfo model."""

    def test_valid_party(self):
        party = PartyInfo(name="John Doe", role="Landlord", address="123 Main St")
        assert party.name == "John Doe"
        assert party.role == "Landlord"
        assert party.address == "123 Main St"

    def test_optional_address(self):
        party = PartyInfo(name="Jane Doe", role="Tenant")
        assert party.address is None

    def test_missing_required_field(self):
        with pytest.raises(ValidationError):
            PartyInfo(name="John Doe")  # Missing 'role'


class TestObligation:
    """Tests for the Obligation model."""

    def test_valid_obligation(self):
        ob = Obligation(
            party="Tenant",
            obligation="Pay rent by 5th of each month",
            section="Section 3.2",
            quote="rent is due on the 5th",
        )
        assert ob.party == "Tenant"
        assert "rent" in ob.obligation.lower()

    def test_optional_fields(self):
        ob = Obligation(party="Landlord", obligation="Maintain the property")
        assert ob.section is None
        assert ob.quote is None


class TestCondition:
    """Tests for the Condition model."""

    def test_valid_condition(self):
        cond = Condition(
            condition="If tenant fails to pay rent for 2 months",
            consequence="Landlord may terminate immediately",
            section="Section 7.3",
        )
        assert "pay rent" in cond.condition.lower()


class TestDeadline:
    """Tests for the Deadline model."""

    def test_valid_deadline(self):
        dl = Deadline(
            deadline="30 days",
            related_to="Termination notice period",
            section="Section 4",
        )
        assert dl.deadline == "30 days"


class TestPenalty:
    """Tests for the Penalty model."""

    def test_valid_penalty(self):
        pen = Penalty(
            penalty="Late payment fee",
            trigger="Rent not paid by 10th",
            amount="INR 200 per day",
            section="Section 3.4",
        )
        assert "200" in pen.amount


class TestFinancialTerm:
    """Tests for the FinancialTerm model."""

    def test_valid_financial_term(self):
        ft = FinancialTerm(
            description="Monthly rent",
            amount="INR 35,000",
            schedule="5th of each month",
            section="Section 3.1",
        )
        assert ft.amount == "INR 35,000"


class TestKeyclause:
    """Tests for the KeyClause model."""

    def test_valid_key_clause(self):
        kc = KeyClause(
            clause_type="Termination",
            summary="Either party may terminate with 30 days notice",
            section_reference="Section 4",
            key_quote="30 days written notice",
        )
        assert kc.clause_type == "Termination"


class TestCitation:
    """Tests for the Citation model."""

    def test_valid_citation(self):
        cite = Citation(source="nda.txt", page=1, chunk_id=3, quote="some text")
        assert cite.source == "nda.txt"

    def test_minimal_citation(self):
        cite = Citation(source="doc.pdf")
        assert cite.page is None
        assert cite.chunk_id is None


# ── Tests for Composite Models ────────────────────────────────


class TestDocumentExtraction:
    """Tests for the DocumentExtraction model."""

    def test_empty_extraction(self):
        """Should create a valid extraction with all empty lists."""
        ext = DocumentExtraction()
        assert ext.parties == []
        assert ext.obligations == []
        assert ext.conditions == []
        assert ext.deadlines == []
        assert ext.penalties == []
        assert ext.financial_terms == []

    def test_full_extraction(self):
        """Should create a valid extraction with nested models."""
        ext = DocumentExtraction(
            parties=[PartyInfo(name="Alice", role="Buyer")],
            obligations=[Obligation(party="Alice", obligation="Pay on time")],
            deadlines=[Deadline(deadline="30 days", related_to="Payment")],
        )
        assert len(ext.parties) == 1
        assert ext.parties[0].name == "Alice"
        assert len(ext.obligations) == 1


class TestAnalysisResult:
    """Tests for the AnalysisResult model."""

    def test_valid_result(self):
        result = AnalysisResult(
            task_type="qa",
            answer="The notice period is 30 days.",
            grounded=True,
        )
        assert result.task_type == "qa"
        assert result.grounded is True
        assert "AI-assisted" in result.disclaimer

    def test_default_disclaimer(self):
        """Disclaimer should be present by default."""
        result = AnalysisResult(task_type="summarize", answer="Summary here")
        assert "not a substitute" in result.disclaimer.lower()
