"""Ruhi: personal identifiers slice (PERSON_NAME, WORKPLACE_SCHOOL, EMAIL, PHONE, HOME_ADDRESS,
DATE_OF_BIRTH, GOV_ID).

DRAFT SET. Rewrite these in your own voice before final numbers are reported. Keep all values
made up. Check with: python3.12 handwritten.py

Format: (prompt, [(exact text copied from the prompt, CATEGORY), ...]). An empty list means clean.
"""

PROMPTS = [
    # ---- sensitive (10) ----
    ("write a note for  my landlord, im renting 314 maple ridge dr, apt 2 and state that the is dryer broke again",
     [("314 maple ridge dr, apt 2", "HOME_ADDRESS")]),
    ("my name is Keisha Brandt and i was born on 07/22/2001 - would this make me a cancer or a leo?",
     [("Keisha Brandt", "PERSON_NAME"), ("07/22/2001", "DATE_OF_BIRTH")]),
    ("the job portal is asking for my ssn which is 418-36-7702 before the interview, should i be putting this number in??",
     [("418-36-7702", "GOV_ID")]),
    ("fix the grammar- Hello Mr. Delgado, this is Tyler from your chem lab section, my number is 865-555-0187 if you need anything",
     [("Delgado", "PERSON_NAME"), ("Tyler", "PERSON_NAME"), ("865-555-0187", "PHONE")]),
    ("rewrite my linkedin headline: junior at UT Knoxville studying cybersecurity, SWE @ Brightline Analytics Summer 2027",
     [("UT Knoxville", "WORKPLACE_SCHOOL"), ("Brightline Analytics", "WORKPLACE_SCHOOL")]),
    ("i lost my wallet w my drivers license in it, can someone use my number is T8830142 to scam me?",
     [("T8830142", "GOV_ID")]),
    ("can you make this sound more professional-  please send the lease to marcus.whitfield22@gmail.com and cc my mom, her email is dwhitfield@outlook.com",
     [("marcus.whitfield22@gmail.com", "EMAIL"), ("dwhitfield@outlook.com", "EMAIL")]),
    ("Turn this into a table with this information -  Name: Anika Rao | DOB: 1999-11-05 | Phone: (423) 555-0164 | Address: 89 Laurel Ave, Maryville, TN 37801",
     [("Anika Rao", "PERSON_NAME"), ("1999-11-05", "DATE_OF_BIRTH"), ("(423) 555-0164", "PHONE"),
      ("89 Laurel Ave, Maryville, TN 37801", "HOME_ADDRESS")]),
    ("my sister Jenna needs a passport for our trip, usiing my pasport ID which is A47219983, can i use mine as a reference on her application?",
     [("Jenna", "PERSON_NAME"), ("A47219983", "GOV_ID")]),
    ("write a text to my coworker sam reminding him the shift at Riverbend Coffee starts at 6, his cell is 6155550129",
     [("sam", "PERSON_NAME"), ("Riverbend Coffee", "WORKPLACE_SCHOOL"), ("6155550129", "PHONE")]),

    # ---- clean (5), the first four are hard negatives ----
    ("what does a us passport number look like? like is it letters and numbers or just numbers", []),
    ("who did taylor swift date before travis kelce?", []),
    ("write a short story about a girl named Wren Calloway who finds a map in her grandma's attic", []),
    ("whats the safest way to store documents like a birth certificate and social security card at home", []),
    ("give me a 3 day itinerary for nashville on a college budget", []),
]
