import json
from urllib.request import Request, urlopen


class PromptShieldClient:
    def __init__(self, base_url="http://127.0.0.1:8765"):
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

        return {
            "findings": result.get("findings", []),
            "mode": result.get("mode", "unknown")
        }
