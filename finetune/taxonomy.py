"""Single source of truth for categories, domains and risk tiers.

Structure: every finding has a TYPE OF INFO (domain: personal | financial | medical) and,
within that domain, one of two tiers: 1 = somewhat sensitive, 2 = very sensitive.
These assignments are the team's working choice. To change one, edit CATEGORIES below
(name, domain, tier), then re-run make_dataset.py. Nothing else needs to change.
Note: the submitted proposal describes three tiers. See PLAN.md for the note on this change.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    name: str
    domain: str  # personal | financial | medical
    tier: int
    description: str


CATEGORIES = [
    # Tier 1: somewhat sensitive. Identifies a person or a private detail, but is not a direct path to fraud or serious harm.
    Category("PERSON_NAME", "personal", 1, "Name of a private individual (the writer or someone they know). Not public figures or fictional characters."),
    Category("WORKPLACE_SCHOOL", "personal", 1, "Employer, school, or university the writer is affiliated with."),
    Category("FIN_INSTITUTION", "financial", 1, "Bank, credit union, or broker the writer uses."),
    Category("MED_PROVIDER", "medical", 1, "Doctor, clinic, or hospital the writer or a relative has used."),
    Category("EMAIL", "personal", 1, "Email address."),
    Category("PHONE", "personal", 1, "Phone number."),
    Category("HOME_ADDRESS", "personal", 1, "Street address where someone lives."),
    Category("DATE_OF_BIRTH", "personal", 1, "Date of birth of the writer or someone they know."),
    Category("INCOME", "financial", 1, "The writer's salary or income."),
    Category("BALANCE_DEBT", "financial", 1, "Account balance, loan, or debt amount of the writer."),
    Category("MED_CONDITION", "medical", 1, "Ordinary medical condition the writer or a relative has."),
    Category("MEDICATION", "medical", 1, "Medication the writer or a relative takes."),
    # Tier 2: very sensitive. Direct path to fraud, theft, or serious harm.
    Category("GOV_ID", "personal", 2, "SSN, passport number, or driver's license number."),
    Category("CARD_NUMBER", "financial", 2, "Payment card number."),
    Category("BANK_ACCOUNT", "financial", 2, "Bank account or routing number."),
    Category("CREDENTIAL", "financial", 2, "Password, PIN, API key, or access token."),
    Category("MED_RECORD_ID", "medical", 2, "Medical record number or health insurance member ID."),
    Category("SENSITIVE_HEALTH", "medical", 2, "Mental health, HIV or STI, substance use, reproductive or genetic health information."),
]

BY_NAME = {c.name: c for c in CATEGORIES}
TIER_LABEL = {1: "somewhat sensitive", 2: "very sensitive"}
DOMAINS = ("medical", "financial", "personal")
DOMAIN_LABEL = {"medical": "Medical", "financial": "Finance", "personal": "Personal"}

# Annotation policy, shared by the generator and the handwritten test set.
POLICY = [
    "Flag information the writer discloses about themselves or people they know.",
    "Do not flag general questions about a topic (e.g. 'what is diabetes').",
    "Do not flag public figures, fictional characters, or example formats such as XXX-XX-XXXX.",
    "Vague symptoms with no named condition (e.g. 'I feel tired') are not flagged.",
    "Injuries (a torn ligament, a broken bone) and a medical device named on its own (an inhaler) are not flagged.",
    "Copy each finding exactly as written in the message.",
]
