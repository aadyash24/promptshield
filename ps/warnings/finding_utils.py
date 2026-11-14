
import re


def locate_findings(message, findings):
    """
    Match detector findings to character ranges in a message.

    Returns:
        [
            {
                "start": int,
                "end": int,
                "text": str,
                "category": str,
                "tier": int
            },
            ...
        ]

    Positions use Python string indices.
    """

    spans = []
    seen = set()

    for finding in findings:
        detected_text = finding.get("text", "")

        if not detected_text:
            continue

        start, end = finding.get("start"), finding.get("end")
        if "start" in finding or "end" in finding:
            if (type(start) is not int or type(end) is not int
                    or not 0 <= start < end <= len(message)
                    or message[start:end] != detected_text):
                continue
            ranges = [(start, end)]
        else:
            # Older detectors return text only. Avoid matches inside larger words.
            pattern = re.escape(detected_text)
            if detected_text[0].isalnum():
                pattern = r"(?<!\w)" + pattern
            if detected_text[-1].isalnum():
                pattern += r"(?!\w)"
            ranges = (match.span() for match in re.finditer(pattern, message))

        for start, end in ranges:
            key = (
                start,
                end,
                finding.get("category", "SENSITIVE")
            )

            if key not in seen:
                spans.append({
                    "start": start,
                    "end": end,
                    "text": detected_text,
                    "category": finding.get(
                        "category", "SENSITIVE"
                    ),
                    "tier": finding.get("tier", 1)
                })
                seen.add(key)

    return sorted(
        spans,
        key=lambda span: (span["start"], span["end"])
    )
