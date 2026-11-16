"""Keep participant decisions only while their sentence context is unchanged."""
import re
from difflib import SequenceMatcher


def sentence_range(text, start, end):
    left, right = 0, len(text)
    for boundary in re.finditer(r"(?<=[.!?])[^\S\n]+|\n+", text):
        if boundary.end() <= start:
            left = boundary.end()
        elif boundary.start() >= end:
            right = boundary.start()
            break
    return left, right


def remap_dismissals(before, after, decisions):
    retained, reset = {}, []
    blocks = SequenceMatcher(None, before, after, autojunk=False).get_matching_blocks()
    for key, reason in decisions.items():
        start, end, category = key
        left, right = sentence_range(before, start, end)
        for block in blocks:
            if block.a <= left and right <= block.a + block.size:
                shift = block.b - block.a
                new_left, new_right = sentence_range(after, start + shift, end + shift)
                if after[new_left:new_right] == before[left:right]:
                    retained[(start + shift, end + shift, category)] = reason
                    break
        else:
            reset.append((key, reason))
    return retained, reset
