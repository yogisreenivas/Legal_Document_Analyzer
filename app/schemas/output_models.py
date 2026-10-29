"""
output_models.py - Pydantic models for structured LLM output.

These models define the expected structure of extracted information
from legal documents. LangChain's PydanticOutputParser uses these
to validate and parse LLM responses into typed Python objects.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PartyInfo(BaseModel):
    """Information about a party (person or organization) in the agreement."""

    name: str = Field(description="Full name of the party")
    role: str = Field(description="Role in the agreement (e.g., Landlord, Tenant, Service Provider)")
    address: Optional[str] = Field(default=None, description="Address if mentioned in the document")


class Obligation(BaseModel):
    """A specific obligation that a party must fulfill."""

    party: str = Field(description="The party who has this obligation")
    obligation: str = Field(description="Description of what they must do")
    section: Optional[str] = Field(default=None, description="Section or clause reference")
    quote: Optional[str] = Field(default=None, description="Direct quote from the document")


class Condition(BaseModel):
    """A condition specified in the agreement."""

    condition: str = Field(description="The condition described")
    consequence: Optional[str] = Field(default=None, description="What happens if the condition is met or not met")
    section: Optional[str] = Field(default=None, description="Section or clause reference")


class Deadline(BaseModel):
    """A deadline or time-bound requirement in the agreement."""

    deadline: str = Field(description="The deadline or timeframe")
    related_to: str = Field(description="What this deadline relates to")
    section: Optional[str] = Field(default=None, description="Section or clause reference")


class Penalty(BaseModel):
    """A penalty clause in the agreement."""

    penalty: str = Field(description="Description of the penalty")
    trigger: str = Field(description="What triggers this penalty")
    amount: Optional[str] = Field(default=None, description="Monetary amount if specified")
    section: Optional[str] = Field(default=None, description="Section or clause reference")


class FinancialTerm(BaseModel):
    """A financial term or payment obligation."""

    description: str = Field(description="What the payment is for")
    amount: Optional[str] = Field(default=None, description="The amount specified")
    schedule: Optional[str] = Field(default=None, description="Payment schedule or due date")
    section: Optional[str] = Field(default=None, description="Section or clause reference")


class KeyClause(BaseModel):
    """A key clause identified in the document."""

    clause_type: str = Field(
        description="Type of clause (e.g., Termination, Payment, Confidentiality, "
                    "Liability, Indemnity, Governing Law, Dispute Resolution, "
                    "Renewal, Intellectual Property)"
    )
    summary: str = Field(description="Brief summary of what the clause says")
    section_reference: Optional[str] = Field(default=None, description="Section or clause number")
    key_quote: Optional[str] = Field(default=None, description="Key quote from the clause")


class Citation(BaseModel):
    """A citation reference to the source document."""

    source: str = Field(description="Source document filename")
    page: Optional[int] = Field(default=None, description="Page number")
    chunk_id: Optional[int] = Field(default=None, description="Chunk identifier")
    quote: Optional[str] = Field(default=None, description="Relevant quote from the source")


class DocumentExtraction(BaseModel):
    """Complete structured extraction from a legal document.

    This is the top-level model returned by the extract_obligations task.
    It contains all extracted parties, obligations, conditions, deadlines,
    penalties, and financial terms.
    """

    parties: List[PartyInfo] = Field(default_factory=list, description="Parties involved in the agreement")
    obligations: List[Obligation] = Field(default_factory=list, description="Obligations of each party")
    conditions: List[Condition] = Field(default_factory=list, description="Conditions specified in the agreement")
    deadlines: List[Deadline] = Field(default_factory=list, description="Deadlines and timeframes")
    penalties: List[Penalty] = Field(default_factory=list, description="Penalties for breaches or violations")
    financial_terms: List[FinancialTerm] = Field(default_factory=list, description="Financial terms and payment obligations")


class AnalysisResult(BaseModel):
    """Result of a document analysis task.

    This wraps the LLM's response along with metadata about
    the analysis (citations, groundedness check, task type).
    """

    task_type: str = Field(description="Type of analysis performed")
    answer: str = Field(description="The LLM's response")
    citations: List[Citation] = Field(default_factory=list, description="Citations supporting the answer")
    grounded: bool = Field(default=True, description="Whether the answer is grounded in the context")
    groundedness_explanation: Optional[str] = Field(default=None, description="Explanation of the groundedness check")
    disclaimer: str = Field(
        default="⚠️ AI-assisted analysis only. Not a substitute for professional legal advice.",
        description="Legal disclaimer"
    )
