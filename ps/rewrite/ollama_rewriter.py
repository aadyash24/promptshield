"""Rewrite the untouched original message using detector-provided sensitive spans."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen2.5:3b"
MAX_REWRITE_ATTEMPTS = 2
SYSTEM_PROMPT = """You are a precise privacy-removal editor.

Your task is to produce one clean, naturally written version of the original_message by removing the sensitive information identified in flagged_spans.

Follow these requirements:

1. Treat flagged_spans as the authoritative list of sensitive information. Remove every flagged value, including when multiple values or categories are present.

2. The original_message is provided unchanged. Read the entire message and understand its meaning before rewriting it.

3. Remove sensitive values completely. Never replace removed information with substitute text, labels, explanations, or invented details.

4. Reconstruct the surrounding sentence naturally. Remove unnecessary prepositions, connecting words, and grammatical fragments caused by removing sensitive information.

5. If a sentence only identifies private information, remove that sentence entirely.

6. If a sentence contains both private information and a separate meaningful request, preserve the request and remove only the private information and its unnecessary surrounding wording.

7. Preserve every unrelated action, request, name, date, deadline, time, amount, condition, and important detail.

8. When multiple sensitive values appear in the same sentence or across different sentences, remove all of them in the same rewrite. Consider their combined effect on sentence structure.

9. Never guess missing information. Do not invent recipients, contact details, relationships, or information that the user did not provide.

10. Do not duplicate sentences, repeat requests, summarize the message, or combine it with unrelated conversation content.

11. Maintain the original language and intended meaning. Make only the changes necessary to remove sensitive information and produce natural, grammatically correct writing.

12. Before responding, verify that every flagged value has been removed and that the remaining message reads as one complete, coherent message.

OUTPUT REQUIREMENTS:

Return exactly one rewritten version of the original_message.

Return only the rewritten message. Do not include explanations, headings, commentary, analysis, or any additional text."""


def _prepare_flagged_spans(original_message: str, flagged_spans: list[dict]) -> list[dict]:
    """Validate detector offsets and confirm they point into the untouched message."""
    if not isinstance(flagged_spans, list):
        raise TypeError("flagged_spans must be a list of detected span dictionaries.")

    prepared = []
    for index, span in enumerate(flagged_spans, start=1):
        if not isinstance(span, dict):
            raise TypeError(f"Flagged span {index} is not a dictionary.")

        try:
            start = int(span["start"])
            end = int(span["end"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Flagged span {index} has invalid character offsets.") from error

        if start < 0 or end <= start or end > len(original_message):
            raise ValueError(f"Flagged span {index} is outside the original message.")

        matched_text = original_message[start:end]
        supplied_text = span.get("text")
        if supplied_text is not None and supplied_text != matched_text:
            raise ValueError(
                f"Flagged span {index} text does not match its original-message offsets."
            )

        try:
            tier = int(span.get("tier", 1))
        except (TypeError, ValueError):
            tier = 1

        prepared.append({
            "start": start,
            "end": end,
            "text": matched_text,
            "category": str(span.get("category", "SENSITIVE")).upper(),
            "tier": tier,
        })

    prepared.sort(key=lambda item: (item["start"], item["end"]))

    # Overlapping spans from multiple detector categories make the instructions
    # ambiguous. Do not silently pass contradictory span boundaries to the model.
    for previous, current in zip(prepared, prepared[1:]):
        if current["start"] < previous["end"]:
            if current["start"] == previous["start"] and current["end"] == previous["end"]:
                continue
            raise ValueError(
                "Detector returned overlapping sensitive spans. Resolve overlaps before rewriting."
            )

    return prepared


def _compact(value: str) -> str:
    """Normalize formatting so reformatted copies of a flagged value can be caught."""
    return "".join(character.casefold() for character in value if character.isalnum())


def _validate_rewrite(content: str, flagged_spans: list[dict]) -> list[str]:
    """Return privacy violations; this checks output only and never edits model input."""
    violations = []
    output_folded = content.casefold()
    output_compact = _compact(content)

    for span in flagged_spans:
        value = span["text"].strip()
        if not value:
            continue
        exact_match = value.casefold() in output_folded
        compact_value = _compact(value)
        reformatted_match = len(compact_value) >= 7 and compact_value in output_compact
        if exact_match or reformatted_match:
            violations.append(
                f"A flagged {span['category']} value is still present in the rewrite."
            )

    if not content.strip():
        violations.append("The rewrite is empty.")

    return violations


class OllamaRewriter:
    """Send untouched source text and flagged spans to Ollama, then validate the result."""

    def __init__(
        self,
        base_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = 120,
    ):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _request(self, messages: list[dict]) -> dict:
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "keep_alive": "10m",
            "options": {
                "temperature": 0.0,
                "top_p": 0.9,
                "num_predict": 512,
            },
        }
        request_url = f"{self.base_url}/api/chat"
        request_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")

        request = Request(
            request_url,
            data=request_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                response_data = json.load(response)
            return response_data
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:1000]
            raise RuntimeError(f"Ollama returned HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                "Make sure Ollama is running and the model is installed."
            ) from error
        except TimeoutError as error:
            raise RuntimeError("Ollama timed out while generating the rewrite.") from error

    def rewrite(self, original_message: str, flagged_spans: list[dict]) -> str:
        """Rewrite the untouched message using the detector's exact flagged spans."""
        if not isinstance(original_message, str):
            raise TypeError("original_message must be a string.")
        if not original_message.strip():
            raise ValueError("Cannot rewrite an empty message.")

        spans = _prepare_flagged_spans(original_message, flagged_spans)
        if not spans:
            raise ValueError("Cannot rewrite without any detected sensitive spans.")

        user_data = {
            "original_message": original_message,
            "flagged_spans": spans,
            "span_offsets": "Python string indices; start inclusive, end exclusive",
        }
        user_prompt = (
            "Clean the original_message in this data. Remove every flagged span, "
            "preserve the user's meaning, and return only the cleaned message.\n\n"
            + json.dumps(user_data, ensure_ascii=False, indent=2)
        )

        last_violations = []
        for attempt in range(1, MAX_REWRITE_ATTEMPTS + 1):
            attempt_prompt = user_prompt
            if attempt > 1:
                retry_instruction = (
                    "\n\nThe previous rewrite failed validation: "
                    + " ".join(last_violations)
                    + " Start again from the original message. Remove every flagged value. "
                    "Do not add labels or replacement information. Return only the cleaned message."
                )
                attempt_prompt += retry_instruction
            response_data = self._request(
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": attempt_prompt},
                ]
            )
            content = (
                response_data.get("message", {}).get("content", "")
                if isinstance(response_data, dict)
                else ""
            )

            if not isinstance(content, str):
                content = ""
            content = content.strip()
            last_violations = _validate_rewrite(content, spans)
            if not last_violations:
                return content

        raise RuntimeError(
            "Qwen could not produce a clean rewrite after "
            f"{MAX_REWRITE_ATTEMPTS} attempts. Rewrite rejected: "
            + " ".join(last_violations)
        )
