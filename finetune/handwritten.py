#!/usr/bin/env python3
"""Hand-labeled, realistic test prompts. Written by hand (not templates), so this is the
most honest test of whether the model works on natural language.

TEAM TODO: each teammate adds 15 prompts in their OWN file, handwritten_extra/<yourname>.py
(copy handwritten_extra/_template.py), in their own writing style, labeled with the policy in
taxonomy.py. Separate files mean no merge conflicts. This file holds the starter set only.
Check your file with `python handwritten.py`. data/handwritten.jsonl is generated, not committed.

Format: (prompt, [(exact text copied from the prompt, CATEGORY), ...]). Tier comes from
taxonomy.py. An empty list means the prompt contains nothing sensitive.
"""
import json
from pathlib import Path

from taxonomy import BY_NAME

PROMPTS = [
    ("hey so i just found out i have celiac disease and my doc at Riverside Family Clinic wants me to go gluten free, any meal prep ideas for a broke college student?",
     [("celiac disease", "MED_CONDITION"), ("Riverside Family Clinic", "MED_PROVIDER")]),
    ("Can you rewrite this to sound more professional: Hi Marcus, it's Priya. Can you send the invoice to priya.raman88@gmail.com? Thanks",
     [("Marcus", "PERSON_NAME"), ("Priya", "PERSON_NAME"), ("priya.raman88@gmail.com", "EMAIL")]),
    ("I'm applying for a mortgage and my lender asked for my SSN, 512-48-9034. Is it normal to email it?",
     [("512-48-9034", "GOV_ID")]),
    ("What is the difference between an HSA and an FSA?", []),
    ("Write a python function that validates a credit card number using the Luhn algorithm.", []),
    ("my password for the wifi is Sunshine#2024 lol is that bad?",
     [("Sunshine#2024", "CREDENTIAL")]),
    ("I make about $92,000 at Deloitte and still can't save anything. Where is my money going?",
     [("$92,000", "INCOME"), ("Deloitte", "WORKPLACE_SCHOOL")]),
    ("Explain how metformin works.", []),
    ("My insurance denied my son's ADHD treatment. Help me write an appeal. His name is Daniel Okafor, DOB 06/14/2015.",
     [("ADHD", "MED_CONDITION"), ("Daniel Okafor", "PERSON_NAME"), ("06/14/2015", "DATE_OF_BIRTH")]),
    ("What's a good name for a golden retriever puppy?", []),
    ("I live at 2210 Cherry Hill Rd, Apt 4B, Nashville, TN 37203 and my landlord won't fix the heat. What are my rights?",
     [("2210 Cherry Hill Rd, Apt 4B, Nashville, TN 37203", "HOME_ADDRESS")]),
    ("Convert this to JSON: name=Sofia Lindqvist, phone=+1 (423) 555-0198, employer=Oak Ridge National Laboratory",
     [("Sofia Lindqvist", "PERSON_NAME"), ("+1 (423) 555-0198", "PHONE"), ("Oak Ridge National Laboratory", "WORKPLACE_SCHOOL")]),
    ("How do I stop my AWS key from being leaked? Mine is AKIAIOSFODNN7EXAMPLE and I pushed it to GitHub by accident.",
     [("AKIAIOSFODNN7EXAMPLE", "CREDENTIAL")]),
    ("Summarize the key provisions of the Affordable Care Act.", []),
    ("I've been on sertraline 100mg for 2 years for anxiety and I want to taper off. Is that safe?",
     [("sertraline 100mg", "MEDICATION"), ("anxiety", "SENSITIVE_HEALTH")]),
    ("Our team lunch is at noon on Friday. Can you draft a calendar invite?", []),
    ("Hi, this is Jordan Blake from Acme Logistics. Can you draft a reply to a customer asking for a refund?",
     [("Jordan Blake", "PERSON_NAME"), ("Acme Logistics", "WORKPLACE_SCHOOL")]),
    ("My Visa 4539 1488 0343 6467 got declined at the gas station but I have money in my account. Why would that happen?",
     [("4539 1488 0343 6467", "CARD_NUMBER")]),
    ("What are the symptoms of a panic attack and how do I stop one?", []),
    ("Write a bio for me: I'm Amara Nwosu, a junior studying nursing at Pellissippi State, and I volunteer at the animal shelter.",
     [("Amara Nwosu", "PERSON_NAME"), ("Pellissippi State", "WORKPLACE_SCHOOL")]),
    ("I owe $18,400 on my car loan. Should I refinance at a lower rate?",
     [("$18,400", "BALANCE_DEBT")]),
    ("Explain recursion to a 10 year old.", []),
    ("My online banking password is B1ueFish!77, please remind me what it is later.",
     [("B1ueFish!77", "CREDENTIAL")]),
    ("How do I request my medical records from a hospital? I'm patient 7745521 at Saint Mary's.",
     [("7745521", "MED_RECORD_ID"), ("Saint Mary's", "MED_PROVIDER")]),
    ("What's the best way to ask my boss for a raise? I currently earn $64k.",
     [("$64k", "INCOME")]),
    ("Give me 5 tips for a first date.", []),
    ("I got my results back and I'm HIV positive. I don't know who to tell first.",
     [("HIV positive", "SENSITIVE_HEALTH")]),
    ("Please translate to Spanish: 'My name is Elena Petrova and my date of birth is March 3, 1998.'",
     [("Elena Petrova", "PERSON_NAME"), ("March 3, 1998", "DATE_OF_BIRTH")]),
    ("Can you check this code? const apiKey = 'sk-proj-8Hk2LmQ9xR4vTz7Wn3Yc6BdF1gJ5pA0e';",
     [("sk-proj-8Hk2LmQ9xR4vTz7Wn3Yc6BdF1gJ5pA0e", "CREDENTIAL")]),
    ("I took a screenshot of my passport, number X12345678, and now I'm worried. What should I do?",
     [("X12345678", "GOV_ID")]),
    ("Compare Chase and Bank of America credit cards for travel rewards.", []),
    ("Who is the CEO of Microsoft and when did he start?", []),
    ("My Outlook keeps crashing when I open attachments. How do I fix it?", []),
    ("im 24 and my bank is Navy Federal, got $3,200 in checking. is it dumb to put it all in a CD?",
     [("Navy Federal", "FIN_INSTITUTION"), ("$3,200", "BALANCE_DEBT")]),
    ("Can you help me write a cover letter? You can reach me at (865) 555-0142 or tanvi.shah@utk.edu.",
     [("(865) 555-0142", "PHONE"), ("tanvi.shah@utk.edu", "EMAIL")]),
    ("What does a typical SSN look like? I know it's XXX-XX-XXXX but I'm writing a form validator.", []),
    ("Write a story about a detective named Mara Voss who investigates a missing violin.", []),
    ("my therapist says i have PTSD and the meds from Dr. Okonkwo aren't helping, how do i talk to her about switching?",
     [("PTSD", "SENSITIVE_HEALTH"), ("Dr. Okonkwo", "MED_PROVIDER")]),
    ("Here's our onboarding doc for the new hire Carlos Mendes (born 11/02/1996, lives at 77 Birchwood Lane, Knoxville). Summarize it in 3 bullets.",
     [("Carlos Mendes", "PERSON_NAME"), ("11/02/1996", "DATE_OF_BIRTH"), ("77 Birchwood Lane, Knoxville", "HOME_ADDRESS")]),
]


def all_prompts():
    """Starter prompts plus every handwritten_extra/*.py file (files starting with _ are skipped)."""
    import importlib.util

    out = list(PROMPTS)
    for f in sorted((Path(__file__).parent / "handwritten_extra").glob("[!_]*.py")):
        spec = importlib.util.spec_from_file_location(f"hw_{f.stem}", f)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        out += list(mod.PROMPTS)
    return out


def build():
    rows = []
    for i, (prompt, spans) in enumerate(all_prompts()):
        findings = []
        for text, cat in spans:
            assert cat in BY_NAME, f"unknown category {cat} in prompt {i}"
            start = prompt.find(text)
            assert start >= 0, f"span not found in prompt {i}: {text!r}"
            findings.append({"text": text, "category": cat, "tier": BY_NAME[cat].tier, "start": start, "end": start + len(text)})
        findings.sort(key=lambda f: f["start"])
        rows.append({"id": f"hand-{i:03d}", "prompt": prompt, "findings": findings,
                     "template_ids": [], "kind": "sensitive" if findings else "negative", "split": "handwritten"})
    return rows


if __name__ == "__main__":
    out = Path(__file__).parent / "data"
    out.mkdir(exist_ok=True)
    rows = build()
    with open(out / "handwritten.jsonl", "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    pos = sum(1 for r in rows if r["findings"])
    print(f"wrote {len(rows)} prompts ({pos} with findings, {len(rows) - pos} clean)")
