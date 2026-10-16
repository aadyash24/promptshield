"""Fake value generators for template slots. Everything here is synthetic.

A template slot looks like {PERSON}. Add ':n' ({PERSON:n}) to fill it with a value but
NOT label it, which is how hard negatives reuse the same value pools.
"""
import random
import re
import string

from faker import Faker

from taxonomy import BY_NAME

# slot -> category it produces when labeled
SLOT_CATEGORY = {
    "PERSON": "PERSON_NAME",
    "WORKPLACE": "WORKPLACE_SCHOOL",
    "BANK": "FIN_INSTITUTION",
    "PROVIDER": "MED_PROVIDER",
    "EMAIL": "EMAIL",
    "PHONE": "PHONE",
    "ADDRESS": "HOME_ADDRESS",
    "DOB": "DATE_OF_BIRTH",
    "SALARY": "INCOME",
    "BALANCE": "BALANCE_DEBT",
    "CONDITION": "MED_CONDITION",
    "MEDICATION": "MEDICATION",
    "SSN": "GOV_ID",
    "PASSPORT": "GOV_ID",
    "DL": "GOV_ID",
    "CARD": "CARD_NUMBER",
    "ACCT": "BANK_ACCOUNT",
    "PASSWORD": "CREDENTIAL",
    "APIKEY": "CREDENTIAL",
    "PIN": "CREDENTIAL",
    "MRN": "MED_RECORD_ID",
    "INSURANCE": "MED_RECORD_ID",
    "SENSITIVE_DX": "SENSITIVE_HEALTH",
}
# slots that are never labeled
NEUTRAL = {"PRICE", "CITY", "HISTORICAL", "BOOK", "COUNTRY", "VERSION", "FAKEFORMAT"}

assert all(c in BY_NAME for c in SLOT_CATEGORY.values())

SLOT_RE = re.compile(r"\{([A-Z_]+)(:n)?\}")

CONDITIONS = [
    "type 2 diabetes", "asthma", "hypertension", "rheumatoid arthritis", "migraines",
    "celiac disease", "epilepsy", "Crohn's disease", "polycystic ovary syndrome",
    "sleep apnea", "hypothyroidism", "psoriasis", "lupus", "anemia", "ADHD",
    "chronic back pain", "eczema", "high cholesterol", "ulcerative colitis", "fibromyalgia",
]
SENSITIVE_DX = [
    "HIV", "bipolar disorder", "clinical depression", "PTSD", "opioid use disorder",
    "alcohol use disorder", "schizophrenia", "hepatitis C", "generalized anxiety disorder",
    "an eating disorder", "a BRCA1 mutation", "herpes",
]
MEDICATIONS = [
    "metformin 500 mg", "lisinopril", "an albuterol inhaler", "sertraline 50 mg",
    "levothyroxine", "atorvastatin", "insulin glargine", "Adderall", "prednisone",
    "amoxicillin", "omeprazole", "gabapentin 300 mg", "birth control pills", "Zoloft",
]
BANKS = [
    "Chase", "Bank of America", "Wells Fargo", "Navy Federal", "Capital One", "Citibank",
    "US Bank", "Truist", "Fidelity", "Ally Bank", "Regions Bank", "First Horizon",
    "Charles Schwab", "PNC", "Credit Union of Tennessee",
]
EMAIL_DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "icloud.com", "hotmail.com", "utk.edu", "proton.me"]
ORG_SUFFIX = ["Logistics", "Analytics", "Health", "Systems", "Partners", "Labs", "Capital", "Dental", "Consulting", "Robotics", "Foods", "Realty"]
SCHOOLS = [
    "the University of Tennessee", "Pellissippi State", "Georgia Tech", "Ohio State", "Vanderbilt",
    "UNC Chapel Hill", "Oak Ridge National Laboratory", "Clemson", "Purdue", "Rutgers",
]
CLINIC_SUFFIX = ["Medical Center", "Family Clinic", "Urgent Care", "Health Partners", "General Hospital", "Women's Health Center", "Cardiology Associates", "Pediatrics"]
HISTORICAL = ["Napoleon Bonaparte", "Marie Curie", "Abraham Lincoln", "Ada Lovelace", "Nelson Mandela", "Albert Einstein", "Frida Kahlo", "Alan Turing"]
BOOKS = ["Pride and Prejudice", "The Great Gatsby", "1984", "To Kill a Mockingbird", "Dune", "Frankenstein", "The Hobbit"]
COUNTRIES = ["Portugal", "Kenya", "Peru", "Vietnam", "Norway", "Chile", "Japan", "Morocco"]
CITIES = ["Lisbon", "Nashville", "Kyoto", "Denver", "Chicago", "Cape Town", "Austin", "Seattle", "Boston", "Montreal"]
WORDS = ["sunshine", "tiger", "maple", "falcon", "orbit", "pepper", "river", "monkey", "violet", "summer", "dragon", "cookie"]
STATES = ["TN", "GA", "NC", "OH", "CA", "TX", "NY", "VA", "FL", "IL", "WA", "MA"]


def luhn_digit(partial: str) -> str:
    total = 0
    for i, ch in enumerate(reversed(partial)):
        d = int(ch)
        if i % 2 == 0:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)


class Filler:
    """Deterministic given a seed."""

    def __init__(self, seed: int):
        self.r = random.Random(seed)
        self.fake = Faker("en_US")
        self.fake.seed_instance(seed)

    def value(self, slot: str) -> str:
        return getattr(self, "g_" + slot.lower())()

    # personal
    def g_person(self):
        if self.r.random() < 0.15:
            return self.fake.first_name()
        return f"{self.fake.first_name()} {self.fake.last_name()}"

    def g_workplace(self):
        if self.r.random() < 0.35:
            return self.r.choice(SCHOOLS)
        return f"{self.fake.last_name()} {self.r.choice(ORG_SUFFIX)}"

    def g_email(self):
        first, last = self.fake.first_name().lower(), self.fake.last_name().lower()
        local = self.r.choice([f"{first}.{last}", f"{first}{last}", f"{first[0]}{last}", f"{first}_{last}{self.r.randint(1, 99)}"])
        return f"{local}@{self.r.choice(EMAIL_DOMAINS)}"

    def g_phone(self):
        area = self.r.randint(201, 989)
        exch = 555 if self.r.random() < 0.5 else self.r.randint(201, 989)
        last = self.r.randint(100, 199) if exch == 555 else self.r.randint(0, 9999)
        a, b, c = area, exch, f"{last:04d}"
        return self.r.choice([f"({a}) {b}-{c}", f"{a}-{b}-{c}", f"{a}.{b}.{c}", f"+1 {a} {b} {c}", f"{a}{b}{c}"])

    def g_address(self):
        street = self.fake.street_address()
        city, st, z = self.fake.city(), self.r.choice(STATES), self.fake.postcode()
        return self.r.choice([f"{street}, {city}, {st} {z}", f"{street}, {city}", street])

    def g_dob(self):
        y, m, d = self.r.randint(1955, 2008), self.r.randint(1, 12), self.r.randint(1, 28)
        months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        return self.r.choice([f"{months[m - 1]} {d}, {y}", f"{m:02d}/{d:02d}/{y}", f"{d} {months[m - 1]} {y}", f"{y}-{m:02d}-{d:02d}"])

    def g_ssn(self):
        area = self.r.choice([n for n in range(1, 899) if n != 666])
        s = f"{area:03d}-{self.r.randint(1, 99):02d}-{self.r.randint(1, 9999):04d}"
        return s if self.r.random() < 0.85 else s.replace("-", "")

    def g_passport(self):
        return self.r.choice(string.ascii_uppercase) + "".join(self.r.choice(string.digits) for _ in range(8))

    def g_dl(self):
        return self.r.choice(string.ascii_uppercase) + "".join(self.r.choice(string.digits) for _ in range(self.r.choice([7, 8])))

    # financial
    def g_salary(self):
        k = self.r.randint(28, 260)
        return self.r.choice([f"${k * 1000 + self.r.randint(0, 9) * 100:,}", f"${k}k", f"${k},000", f"${self.r.randint(2200, 15000):,} a month"])

    def g_balance(self):
        n = self.r.choice([self.r.randint(120, 900), self.r.randint(1000, 9999), self.r.randint(10000, 95000)])
        return f"${n:,}"

    def g_bank(self):
        return self.r.choice(BANKS)

    def g_card(self):
        kind = self.r.choice(["4", "4", "5", "37"])
        length = 15 if kind == "37" else 16
        body = kind + "".join(self.r.choice(string.digits) for _ in range(length - 1 - len(kind)))
        num = body + luhn_digit(body)
        if length == 15:
            return f"{num[:4]} {num[4:10]} {num[10:]}"
        sep = self.r.choice([" ", "-", ""])
        return sep.join(num[i:i + 4] for i in range(0, 16, 4))

    def g_acct(self):
        return "".join(self.r.choice(string.digits) for _ in range(self.r.choice([9, 10, 11, 12])))

    def g_password(self):
        w = self.r.choice(WORDS)
        w = w.capitalize() if self.r.random() < 0.7 else w
        return f"{w}{self.r.randint(1, 9999)}{self.r.choice('!#$%&*')}"

    def g_apikey(self):
        alnum = string.ascii_letters + string.digits
        kind = self.r.choice(["sk", "ghp", "AKIA", "sk-proj"])
        if kind == "sk":
            return "sk-" + "".join(self.r.choice(alnum) for _ in range(32))
        if kind == "sk-proj":
            return "sk-proj-" + "".join(self.r.choice(alnum + "_-") for _ in range(36))
        if kind == "ghp":
            return "ghp_" + "".join(self.r.choice(alnum) for _ in range(36))
        return "AKIA" + "".join(self.r.choice(string.ascii_uppercase + string.digits) for _ in range(16))

    def g_pin(self):
        return "".join(self.r.choice(string.digits) for _ in range(self.r.choice([4, 4, 6])))

    # medical
    def g_condition(self):
        return self.r.choice(CONDITIONS)

    def g_sensitive_dx(self):
        return self.r.choice(SENSITIVE_DX)

    def g_medication(self):
        return self.r.choice(MEDICATIONS)

    def g_provider(self):
        if self.r.random() < 0.4:
            return f"Dr. {self.fake.last_name()}"
        return f"{self.fake.city()} {self.r.choice(CLINIC_SUFFIX)}"

    def g_mrn(self):
        return "".join(self.r.choice(string.digits) for _ in range(self.r.choice([7, 8])))

    def g_insurance(self):
        return "".join(self.r.choice(string.ascii_uppercase) for _ in range(3)) + "".join(self.r.choice(string.digits) for _ in range(9))

    # neutral
    def g_price(self):
        return f"${self.r.choice([19, 49, 89, 199, 450, 899, 1200, 1500])}"

    def g_city(self):
        return self.r.choice(CITIES)

    def g_historical(self):
        return self.r.choice(HISTORICAL)

    def g_book(self):
        return self.r.choice(BOOKS)

    def g_country(self):
        return self.r.choice(COUNTRIES)

    def g_version(self):
        return f"{self.r.randint(1, 9)}.{self.r.randint(0, 20)}.{self.r.randint(0, 9)}"

    def g_fakeformat(self):
        return self.r.choice(["XXX-XX-XXXX", "XXX-XX-XXXX", "XXXX-XXXX-XXXX-XXXX"])


def render(template: str, filler: Filler):
    """Fill a template. Returns (text, findings) with exact character offsets."""
    from taxonomy import BY_NAME as cats

    text, findings, pos = "", [], 0
    for m in SLOT_RE.finditer(template):
        text += template[pos:m.start()]
        slot, neutral = m.group(1), bool(m.group(2))
        val = filler.value(slot)
        start = len(text)
        text += val
        if slot in SLOT_CATEGORY and not neutral:
            cat = SLOT_CATEGORY[slot]
            findings.append({"text": val, "category": cat, "tier": cats[cat].tier, "start": start, "end": len(text)})
        elif slot not in SLOT_CATEGORY and slot not in NEUTRAL:
            raise KeyError(f"unknown slot {slot}")
        pos = m.end()
    text += template[pos:]
    return text, findings
