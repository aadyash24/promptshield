import json
import sys
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import serve  # noqa: E402


def good(**kw):
    base = {"pid": "P01", "cond": "active", "task": "bank", "event": "send", "n": 2,
            "categories": ["GOV_ID"], "max_tier": 3, "disclosed": True, "warned": False, "ms": 1200}
    base.update(kw)
    return base


def test_clean_event_keeps_whitelisted_fields_only():
    out = serve.clean_event(good(text="my ssn is 527-61-3849", prompt="secret", extra=1))
    assert out is not None
    assert "text" not in out and "prompt" not in out and "extra" not in out
    assert out["categories"] == ["GOV_ID"]


def test_clean_event_rejects_bad_records():
    assert serve.clean_event(good(pid="../etc/passwd")) is None
    assert serve.clean_event(good(cond="both")) is None
    assert serve.clean_event(good(event="keystroke")) is None
    assert serve.clean_event("not a dict") is None


def test_category_field_cannot_smuggle_text():
    out = serve.clean_event(good(categories=["GOV_ID", "my ssn is 527-61-3849"]))
    assert out is not None and "categories" not in out  # a value-like string rejects the whole list


def test_assignment_is_balanced_and_sticky(tmp_path):
    a = serve.Assigner(tmp_path, seed=3)
    conds = [a.get(f"P{i:02d}") for i in range(10)]
    assert conds.count("active") == 5 and conds.count("silent") == 5
    assert a.get("P03") == conds[3]
    assert serve.Assigner(tmp_path).get("P03") == conds[3]  # survives a restart


def test_http_endpoints(tmp_path):
    det = serve.Detector()  # regex-only
    srv = ThreadingHTTPServer(("127.0.0.1", 0), serve.make_handler(det, tmp_path, serve.Assigner(tmp_path, 1)))
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    def post(path, obj):
        req = urllib.request.Request(base + path, json.dumps(obj).encode(), {"Content-Type": "application/json"})
        try:
            return json.load(urllib.request.urlopen(req))
        except urllib.error.HTTPError as e:
            return {"status": e.code}

    try:
        res = post("/detect", {"text": "my ssn is 527-61-3849"})
        assert res["mode"] == "regex" and res["findings"][0]["category"] == "GOV_ID"
        assert post("/detect", {"text": ""})["status"] == 400
        assert post("/log", good())["ok"] is True
        assert post("/log", good(cond="nope"))["status"] == 400
        written = (tmp_path / "P01.jsonl").read_text()
        assert "527-61" not in written and written.count("\n") == 1
        page = urllib.request.urlopen(base + "/mock/").read().decode()
        assert "ChatAssist" in page
        assert urllib.request.urlopen(base + "/health").status == 200
        try:
            urllib.request.urlopen(base + "/mock/../../finetune/serve.py")
            raise AssertionError("path traversal not blocked")
        except urllib.error.HTTPError as e:
            assert e.code == 404
    finally:
        srv.shutdown()
