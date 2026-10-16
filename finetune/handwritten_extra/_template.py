"""Copy this file to handwritten_extra/<yourname>.py and write 15 prompts.

Write them the way YOU would really talk to a chatbot: lowercase, typos, pasted text, whatever.
Aim for about 10 prompts that contain sensitive info from your slice's categories, plus 5 clean
ones. At least 2 clean ones should be hard negatives (they mention a sensitive topic or look like
a value but contain nothing real, for example "what is a normal blood sugar range?").

Format: (prompt, [(exact text copied from the prompt, CATEGORY), ...])
An empty list means nothing in the prompt is sensitive. Categories are listed in taxonomy.py.
Everything the writer shares about themselves or people they know counts. Public figures,
fictional characters, example formats like XXX-XX-XXXX and general questions do not.

Check your file: python handwritten.py   (it fails with a clear message if a span is not found)
All values must be made up. Never use a real person's data, including your own.
"""

PROMPTS = [
    # ("my doc at Riverside Clinic says i have asthma, what inhaler should i ask about?",
    #  [("Riverside Clinic", "MED_PROVIDER"), ("asthma", "MED_CONDITION")]),
    # ("what is a normal resting heart rate?", []),
]
