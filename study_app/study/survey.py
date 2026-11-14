"""Versioned post-task questions; common items are identical across conditions."""

SURVEY_VERSION = "disclosure_v1"
MAX_RESPONSE_CHARS = 2000

COMMON_QUESTIONS = (
    ("ai_use", "What did you use the AI assistant for during this task? If you did not use it, what led you to that choice?"),
    ("detail_selection", "How did you decide which details from Maya's profile to include in messages to the AI assistant? What made a detail seem useful or unnecessary?"),
    ("disclosure_changes", "Before sending messages to the AI assistant, did you leave out, remove, or make any personal, medical, or financial details less specific? Describe what you changed and why, or explain why you kept the details as they were."),
    ("task_friction", "What, if anything, made it difficult to use the AI assistant or finish your letter? Did this affect how much you used the assistant or what you sent?"),
)

ACTIVE_QUESTIONS = (
    ("feedback_effect", "Did you notice any highlights or privacy feedback while composing messages? If so, how did you respond, and why? Describe any effect on what you sent, including no effect. If you noticed none, say so."),
    ("rewrite_effect", "Did you use 'Rewrite this detail'? If so, what did you expect it to do, and did the result preserve the information you wanted the assistant to use? Describe any edits or problems. If you did not use it, what led to that choice?"),
)


def questions_for(condition):
    return COMMON_QUESTIONS + (ACTIVE_QUESTIONS if condition in ("active", "dev") else ())
