"""Single source of truth for categories and risk tiers.

ASSUMPTION: these tier assignments are OUR PROPOSAL, not copied from the project
proposal. If the proposal defines the three risk tiers differently, edit CATEGORIES
below (name, domain, tier), then re-run make_dataset.py. Nothing else needs to change.

Tier 1 = low, 2 = medium, 3 = high. Domains match the timeline: personal identifiers,
financial, medical.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    name: str
    domain: str  # personal | financial | medical
    tier: int
    description: str


CATEGORIES = [
    # Tier 1: low. Weakly identifying on its own.
    Category("PERSON_NAME", "personal", 1, "Name of a private individual (the writer or someone they know). Not public figures or fictional characters."),
    Category("WORKPLACE_SCHOOL", "personal", 1, "Employer, school, or university the writer is affiliated with."),
    Category("FIN_INSTITUTION", "financial", 1, "Bank, credit union, or broker the writer uses."),
    Category("MED_PROVIDER", "medical", 1, "Doctor, clinic, or hospital the writer or a relative has used."),
    # Tier 2: medium. Identifies or exposes a private detail.
    Category("EMAIL", "personal", 2, "Email address."),
    Category("PHONE", "personal", 2, "Phone number."),
    Category("HOME_ADDRESS", "personal", 2, "Street address where someone lives."),
    Category("DATE_OF_BIRTH", "personal", 2, "Date of birth of the writer or someone they know."),
    Category("INCOME", "financial", 2, "The writer's salary or income."),
    Category("BALANCE_DEBT", "financial", 2, "Account balance, loan, or debt amount of the writer."),
    Category("MED_CONDITION", "medical", 2, "Ordinary medical condition the writer or a relative has."),
    Category("MEDICATION", "medical", 2, "Medication the writer or a relative takes."),
    # Tier 3: high. Direct path to fraud, theft, or serious harm.
    Category("GOV_ID", "personal", 3, "SSN, passport number, or driver's license number."),
    Category("CARD_NUMBER", "financial", 3, "Payment card number."),
    Category("BANK_ACCOUNT", "financial", 3, "Bank account or routing number."),
    Category("CREDENTIAL", "financial", 3, "Password, PIN, API key, or access token."),
    Category("MED_RECORD_ID", "medical", 3, "Medical record number or health insurance member ID."),
    Category("SENSITIVE_HEALTH", "medical", 3, "Mental health, HIV or STI, substance use, reproductive or genetic health information."),
]

BY_NAME = {c.name: c for c in CATEGORIES}
TIER_LABEL = {1: "low", 2: "medium", 3: "high"}

# Annotation policy, shared by the generator and the handwritten test set.
POLICY = [
    "Flag information the writer discloses about themselves or people they know.",
    "Do not flag general questions about a topic (e.g. 'what is diabetes').",
    "Do not flag public figures, fictional characters, or example formats such as XXX-XX-XXXX.",
    "Vague symptoms with no named condition (e.g. 'I feel tired') are not flagged.",
    "Copy each finding exactly as written in the message.",
]
