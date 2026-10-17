"""Aadya: medical slice (MED_PROVIDER, MED_CONDITION, MEDICATION, MED_RECORD_ID, SENSITIVE_HEALTH).

STARTER SET. These are drafts so the file is not empty. Rewrite them in your own voice, add more,
and keep all values made up. Check with: python handwritten.py
"""

PROMPTS = [
    ("my doc at Riverside Family Clinic says i have asthma, what inhaler questions should i ask her",
     [("Riverside Family Clinic", "MED_PROVIDER"), ("asthma", "MED_CONDITION")]),
    ("been on sertraline 100 mg for 3 months and still feel flat, is that normal",
     [("sertraline 100 mg", "MEDICATION")]),
    ("my mrn is 4471823, how do i get my chart sent to a new doctor",
     [("4471823", "MED_RECORD_ID")]),
    ("insurance member id BXN482910376, why was my mri denied",
     [("BXN482910376", "MED_RECORD_ID")]),
    ("im scared to tell my roommate i tested positive for HIV, how do i bring it up",
     [("HIV", "SENSITIVE_HEALTH")]),
    ("write an email to my professor, i have ulcerative colitis and had a flare up during the midterm",
     [("ulcerative colitis", "MED_CONDITION")]),
    ("my dad takes warfarin and lisinopril, can he have grapefruit",
     [("warfarin", "MEDICATION"), ("lisinopril", "MEDICATION")]),
    ("Dr. Patel at Knoxville Orthopedic Clinic wants surgery for my torn acl, how should i get a second opinion",
     [("Dr. Patel", "MED_PROVIDER"), ("Knoxville Orthopedic Clinic", "MED_PROVIDER")]),
    ("since the miscarriage in march i havent been sleeping, what should i tell my therapist",
     [("miscarriage", "SENSITIVE_HEALTH")]),
    ("Patient: Jordan Ellis, MRN 20931456, dx hypothyroidism, rx levothyroxine 75 mcg. summarize for the handoff note",
     [("Jordan Ellis", "PERSON_NAME"), ("20931456", "MED_RECORD_ID"), ("hypothyroidism", "MED_CONDITION"), ("levothyroxine 75 mcg", "MEDICATION")]),
    ("what is a normal fasting blood sugar range?", []),
    ("explain how metformin works in the body for my pharmacology quiz", []),
    ("how do i find a good dermatologist in a new city", []),
    ("my medical record number should be on the top of the bill right? where is it usually printed", []),
    ("what are the early symptoms of multiple sclerosis, just curious after a documentary", []),
]
