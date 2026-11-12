
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

        search_start = 0

        while True:
            start = message.find(detected_text, search_start)

            if start == -1:
                break

            end = start + len(detected_text)

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

            search_start = end

    return sorted(
        spans,
        key=lambda span: (span["start"], span["end"])
    )
