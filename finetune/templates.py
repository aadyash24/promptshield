"""Prompt templates. Slots are defined in slots.py; {SLOT:n} fills but does not label.

Each entry: (id, domain, text, holdout). Templates with holdout=True are NEVER used for
training or validation, only for the test split, so the test measures how well the model
handles phrasings it has not seen. Holdouts were picked so every category appears in test.
"""

SENSITIVE = [
    # ---- personal identifiers ----
    ("P01", "personal", "Can you help me write an email to {PERSON} at {EMAIL} about rescheduling our meeting?", False),
    ("P02", "personal", "My name is {PERSON} and my phone number is {PHONE}. Draft a voicemail greeting for me.", False),
    ("P03", "personal", "I live at {ADDRESS}. What are some ways to lower my heating bill in the winter?", False),
    ("P04", "personal", "Please proofread my cover letter. My name is {PERSON}, I work at {WORKPLACE}, and you can reach me at {EMAIL}.", False),
    ("P05", "personal", "I was born on {DOB}. What would my astrology chart say about me?", False),
    ("P06", "personal", "Fill out this form for me. Name: {PERSON}, DOB: {DOB}, Address: {ADDRESS}, Phone: {PHONE}.", False),
    ("P07", "personal", "My SSN is {SSN}. How can I tell if someone has stolen my identity?", False),
    ("P08", "personal", "I need to renew my passport. The number on it is {PASSPORT}. What documents do I need?", False),
    ("P09", "personal", "My driver's license number is {DL}. How long does a renewal usually take?", True),
    ("P10", "personal", "Write a thank you note to my landlord {PERSON}. I rent a place at {ADDRESS}.", False),
    ("P11", "personal", "Hi, I'm a student at {WORKPLACE}. Can you explain how recursion works?", False),
    ("P12", "personal", "Rewrite this message so it sounds friendlier: 'Call {PERSON} back at {PHONE} today.'", False),
    ("P13", "personal", "My coworker {PERSON} keeps interrupting me in meetings. How do I bring it up with her?", True),
    ("P14", "personal", "Format this as a contact card: {PERSON}, {WORKPLACE}, {EMAIL}, {PHONE}.", True),
    ("P15", "personal", "Here is my resume info. Name: {PERSON}. Email: {EMAIL}. I graduated from {WORKPLACE} in 2024. Suggest improvements.", False),
    ("P16", "personal", "I'm filling out a background check. My SSN is {SSN} and my date of birth is {DOB}. Is it safe to submit this online?", False),
    ("P17", "personal", "can u help me write a text to {PERSON}? her number is {PHONE} lol", False),
    ("P18", "personal", "Summarize this note: {PERSON} lives at {ADDRESS} and was born on {DOB}.", True),
    ("P19", "personal", "Add {EMAIL} to the guest list and send the invite to {PERSON}.", False),
    ("P20", "personal", "I just moved to {ADDRESS}. Which utilities should I set up first?", False),
    # ---- financial ----
    ("F01", "financial", "I make {SALARY} a year. How much should I be saving for retirement?", False),
    ("F02", "financial", "My credit card number is {CARD}. It was charged twice at the same store. How do I dispute it?", False),
    ("F03", "financial", "I owe {BALANCE} on my student loans. Should I pay those off before investing?", False),
    ("F04", "financial", "My checking account number is {ACCT}. How do I set up direct deposit?", False),
    ("F05", "financial", "Here is my password for the bank site: {PASSWORD}. Can you check if it's strong?", False),
    ("F06", "financial", "My API key is {APIKEY}. Why does my script keep returning a 401 error?", False),
    ("F07", "financial", "I bank with {BANK} and my savings balance is {BALANCE}. Is a high-yield account worth it?", False),
    ("F08", "financial", "I just got a job offer for {SALARY} at {WORKPLACE}. How do I negotiate?", False),
    ("F09", "financial", "Help me budget. I have {BALANCE} in credit card debt and {BALANCE} in savings.", False),
    ("F10", "financial", "Debug this config: DB_PASSWORD={PASSWORD} and STRIPE_KEY={APIKEY}", True),
    ("F11", "financial", "My ATM PIN is {PIN}. Is that too easy to guess?", False),
    ("F12", "financial", "Pay the invoice with card {CARD}, expiring 09/28. Draft the confirmation email.", True),
    ("F13", "financial", "My account number is {ACCT} at {BANK}. How long does an ACH transfer take?", True),
    ("F14", "financial", "Explain my tax situation. I earned {SALARY} last year and I owe {BALANCE} to the IRS.", True),
    ("F15", "financial", "I use {BANK} for my paycheck. Is there a better bank for students?", True),
    ("F16", "financial", "const token = '{APIKEY}'; // why is this a security problem?", False),
    ("F17", "financial", "my ssn is {SSN} and my bank login password is {PASSWORD}, did i just mess up by pasting that here", False),
    # ---- medical ----
    ("M01", "medical", "I was diagnosed with {CONDITION} last year. What foods should I avoid?", False),
    ("M02", "medical", "I take {MEDICATION} every morning. Is it safe to drink coffee with it?", False),
    ("M03", "medical", "My doctor, {PROVIDER}, said my blood pressure is high. What lifestyle changes help?", False),
    ("M04", "medical", "My medical record number is {MRN}. How do I request a copy of my records?", False),
    ("M05", "medical", "My insurance member ID is {INSURANCE}. How do I check what my copay will be?", False),
    ("M06", "medical", "I've been living with {SENSITIVE_DX} for years. How do I talk about it with my employer?", False),
    ("M07", "medical", "I'm {PERSON}, and I was just diagnosed with {CONDITION}. Write a message to my professor asking for an extension.", False),
    ("M08", "medical", "Summarize this visit note: Patient {PERSON}, DOB {DOB}, MRN {MRN}, diagnosis {CONDITION}, prescribed {MEDICATION}.", False),
    ("M09", "medical", "I'm on {MEDICATION} for {CONDITION}. Can I take it with alcohol?", False),
    ("M10", "medical", "Help me write a note to my boss. I'm out this week for treatment of {SENSITIVE_DX}.", True),
    ("M11", "medical", "I have an appointment at {PROVIDER} on Friday for my {CONDITION}. What should I ask?", True),
    ("M12", "medical", "My daughter {PERSON} has {CONDITION}. What accommodations can her school offer?", True),
    ("M13", "medical", "ive had {CONDITION} since college and {MEDICATION} isnt working anymore", True),
    ("M14", "medical", "Insurance denied my claim. Member ID {INSURANCE}, claim for {CONDITION}. Draft an appeal letter.", True),
    ("M15", "medical", "I saw {PROVIDER} yesterday and was told I have {CONDITION}. What does that mean for my daily life?", False),
    ("M16", "medical", "My therapist thinks I may have {SENSITIVE_DX}. How do I prepare for the next session?", False),
]

NEGATIVE = [
    ("N01", "neg", "What are the common symptoms of {CONDITION:n} and how is it usually treated?", False),
    ("N02", "neg", "How does {CONDITION:n} affect the body over time?", False),
    ("N03", "neg", "Explain the difference between a Roth IRA and a traditional IRA.", False),
    ("N04", "neg", "What is a good strategy for paying off credit card debt faster?", False),
    ("N05", "neg", "How do I write a SQL query that joins two tables on a user ID?", False),
    ("N06", "neg", "Write a haiku about autumn leaves.", False),
    ("N07", "neg", "What does a US Social Security number look like? I know it's {FAKEFORMAT}, but why are there three parts?", True),
    ("N08", "neg", "A laptop costs {PRICE} and a tablet costs {PRICE}. Which is the better value for a college student?", False),
    ("N09", "neg", "Who was {HISTORICAL}, and what were they best known for?", False),
    ("N10", "neg", "Summarize the plot of {BOOK} in five sentences.", False),
    ("N11", "neg", "How do I reset my password on a website if I forgot it?", False),
    ("N12", "neg", "What is the best way to create a strong password I can actually remember?", False),
    ("N13", "neg", "What's the difference between a copay and a deductible?", False),
    ("N14", "neg", "Is {BANK:n} or {BANK:n} better for a student checking account?", True),
    ("N15", "neg", "Write a polite email asking my professor for an extension on the assignment due Friday.", False),
    ("N16", "neg", "Explain how an amortization schedule works for a {PRICE}000 mortgage at 6% over 30 years.", False),
    ("N17", "neg", "My code throws KeyError: 'user_id' on line 42. What could cause that?", False),
    ("N18", "neg", "Translate 'good morning, how are you?' into Spanish and French.", False),
    ("N19", "neg", "What are the common side effects of {MEDICATION:n} in general?", True),
    ("N20", "neg", "How much does a typical treatment for {CONDITION:n} cost in the US?", False),
    ("N21", "neg", "Write a short story about a detective named {PERSON:n} who solves a mystery in a small town.", True),
    ("N22", "neg", "Draft a LinkedIn post announcing that our team shipped a new feature. Keep it upbeat.", False),
    ("N23", "neg", "What is the format of a credit card number and what does the Luhn algorithm check?", False),
    ("N24", "neg", "An API key often looks like sk-xxxxxxxxxxxxxxxx. How should I store keys safely using environment variables?", False),
    ("N25", "neg", "Give me a three day itinerary for a trip to {CITY}.", False),
    ("N26", "neg", "I'm feeling tired lately. What are some tips to improve my sleep?", False),
    ("N27", "neg", "How should I prepare for a doctor's appointment so I don't forget anything?", False),
    ("N28", "neg", "What's the average salary of a software engineer in {CITY}?", False),
    ("N29", "neg", "Explain how HIPAA protects patient information.", False),
    ("N30", "neg", "What should I include on a resume for a first internship?", False),
    ("N31", "neg", "Convert 72 degrees Fahrenheit to Celsius and show the formula.", False),
    ("N32", "neg", "Version {VERSION} of the app crashes when I rotate the screen. Any idea why?", False),
    ("N33", "neg", "I'd like to spend about {PRICE} on a gift for a 10 year old who likes science. Any ideas?", False),
    ("N34", "neg", "What is the capital of {COUNTRY}, and what is it known for?", False),
    ("N35", "neg", "Compare {BANK:n} and {BANK:n} credit cards for travel rewards.", True),
    ("N36", "neg", "What does {SENSITIVE_DX:n} mean, and how is it usually diagnosed?", False),
    ("N37", "neg", "How do I politely tell my roommate that the kitchen needs cleaning?", False),
    ("N38", "neg", "Explain what a deductible is for health insurance in plain English.", False),
]

ALL = SENSITIVE + NEGATIVE


# ---- combinatorial hard negatives: general questions about medical, financial, tech, everyday topics ----
GEN_TOPICS = [
    # medical topics, no personal disclosure
    "type 2 diabetes", "high blood pressure", "asthma", "migraines", "sleep apnea", "anxiety disorders",
    "depression", "vaccines", "antibiotics", "cholesterol", "the flu", "seasonal allergies",
    "physical therapy", "nutrition labels", "intermittent fasting",
    # financial
    "index funds", "credit scores", "student loans", "mortgage rates", "Roth IRAs", "budgeting apps",
    "compound interest", "inflation", "tax deductions", "credit card rewards", "emergency funds",
    "cryptocurrency", "renting versus buying", "health insurance plans", "401(k) matching",
    # tech and security
    "SQL joins", "Python decorators", "REST APIs", "Git branching", "Docker containers",
    "machine learning basics", "unit testing", "password managers", "two-factor authentication",
    "phishing emails", "VPNs", "cloud storage", "React hooks", "recursion", "big O notation",
    # everyday
    "meal prepping", "public speaking", "job interviews", "time management", "learning Spanish",
    "running a 5k", "houseplants", "budget travel", "writing a resume", "note taking",
    "sleep hygiene", "remote work", "college applications", "negotiating a salary", "writing a cover letter",
]
GEN_FRAMES = [
    "Explain {T} in simple terms.",
    "Give me a short summary of {T}.",
    "What should a beginner know about {T}?",
    "Write three tips about {T}.",
    "What are common misconceptions about {T}?",
    "Create a five question quiz about {T}.",
    "How would you teach {T} to a high school student?",
    "Write a short blog intro about {T}.",
]
# every 5th topic is held out for the test split
GENERATED = [
    (f"G{ti:02d}{fi}", "neg", frame.format(T=topic), ti % 5 == 4)
    for ti, topic in enumerate(GEN_TOPICS)
    for fi, frame in enumerate(GEN_FRAMES)
]
