import json
import os
from urllib.request import Request, urlopen


class PromptShieldClient:
    def __init__(self, base_url=None):
        if base_url is None:
            base_url = os.environ.get("PROMPTSHIELD_DETECTOR_URL", "http://127.0.0.1:8765")
        self.base_url = base_url.rstrip("/")

    def detect(self, text):
        """Check a message using the PromptShield server."""

        payload = json.dumps({
            "text": text
        }).encode("utf-8")

        request = Request(
            f"{self.base_url}/detect",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        with urlopen(request, timeout=15) as response:
            result = json.load(response)

        if not isinstance(result, dict):
            raise ValueError("Invalid response from PromptShield detector")
        findings = result.get("findings")
        mode = result.get("mode", "unknown")
        if not isinstance(findings, list) or not isinstance(mode, str) or any(
            not isinstance(finding, dict)
            or not isinstance(finding.get("text"), str)
            or not finding["text"]
            or not isinstance(finding.get("category", "SENSITIVE"), str)
            or type(finding.get("tier", 1)) is not int
            or not 1 <= finding.get("tier", 1) <= 3
            for finding in findings
        ):
            raise ValueError("Invalid response from PromptShield detector")

        return {
            "findings": findings,
            "mode": mode,
        }
