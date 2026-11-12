"""Start the PromptShield detector and bundled Ollama server."""

import json
import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from threading import Event, Thread
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener

if __package__:
    from .get_model import MODEL_DIR, NAME, is_installed
    from .rewrite.ollama_rewriter import DEFAULT_MODEL, DEFAULT_OLLAMA_URL
else:
    from get_model import MODEL_DIR, NAME, is_installed
    from rewrite.ollama_rewriter import DEFAULT_MODEL, DEFAULT_OLLAMA_URL


ROOT = Path(__file__).resolve().parent
DETECTOR_URL = "http://127.0.0.1:8765"
OLLAMA_EXE = ROOT / "runtime" / "ollama" / "ollama.exe"
OLLAMA_MODELS = MODEL_DIR / "ollama"
STARTUP_TIMEOUT = 120
LOCAL_HTTP = build_opener(ProxyHandler({}))


def check_port(name, url):
    address = urlsplit(url)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if os.name == "nt":
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        try:
            probe.bind((address.hostname, address.port))
        except OSError as error:
            raise RuntimeError(f"{name} cannot bind to {address.netloc}: {error}") from error


def check_running(services):
    for name, process in services:
        status = process.poll()
        if status is not None:
            raise RuntimeError(f"{name} exited with status {status}. See its output above.")


def wait_for_json(url, services, closing):
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while time.monotonic() < deadline:
        if closing.is_set():
            raise KeyboardInterrupt
        check_running(services)
        try:
            with LOCAL_HTTP.open(url, timeout=2) as response:
                return json.load(response)
        except (URLError, TimeoutError):
            time.sleep(0.25)
    raise RuntimeError(f"Timed out waiting for {url}. See the service output above.")


def stop_services(services):
    for _, process in reversed(services):
        if process.poll() is None:
            process.terminate()
    for _, process in reversed(services):
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()


def find_ollama():
    candidates = [OLLAMA_EXE, shutil.which("ollama.exe")]
    if os.environ.get("LOCALAPPDATA"):
        candidates.append(Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama" / "ollama.exe")
    return next((Path(path) for path in candidates if path and Path(path).is_file()), None)


def running_service(url):
    try:
        with LOCAL_HTTP.open(url, timeout=2) as response:
            return json.load(response)
    except URLError:
        return None


def smoke_test():
    email = "alex@example.com"
    request = Request(
        f"{DETECTOR_URL}/detect",
        data=json.dumps({"text": f"My email address is {email}."}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with LOCAL_HTTP.open(request, timeout=30) as response:
        result = json.load(response)
    if result.get("mode") != "token" or not any(
        finding.get("text") == email for finding in result.get("findings", [])
    ):
        raise RuntimeError("b-tok2 did not flag the synthetic email in its startup check.")

    request = Request(
        f"{DEFAULT_OLLAMA_URL}/api/chat",
        data=json.dumps({
            "model": DEFAULT_MODEL,
            "messages": [{"role": "user", "content": "Reply with the word ready."}],
            "stream": False,
            "options": {"num_predict": 8},
        }).encode(),
        headers={"Content-Type": "application/json"},
    )
    with LOCAL_HTTP.open(request, timeout=120) as response:
        result = json.load(response)
    if not result.get("message", {}).get("content", "").strip():
        raise RuntimeError("Qwen returned an empty response in its startup check.")


def main():
    gui = sys.argv[1:] == ["--gui"]
    closing = Event()
    shutdown_requested = Event()

    def report(component, state, message):
        if gui:
            print(json.dumps(dict(component=component, state=state, message=message)), flush=True)
        else:
            print(message, flush=True)

    if gui:
        def watch_stdin():
            for line in sys.stdin:
                if line.strip() == "stop":
                    shutdown_requested.set()
                    break
            closing.set()

        Thread(target=watch_stdin, daemon=True).start()

    services = []
    try:
        checkpoint = is_installed(MODEL_DIR / NAME)
        ollama = find_ollama()
        tags_url = f"{DEFAULT_OLLAMA_URL}/api/tags"
        tags = running_service(tags_url) if gui else None
        report("detector", "installed" if checkpoint else "missing", "b-tok2 installed." if checkpoint else "b-tok2 is missing.")
        report("ollama", "installed" if ollama or tags is not None else "missing",
               "Ollama available." if ollama or tags is not None else "Ollama is missing.")
        if not checkpoint or (not ollama and tags is None):
            return 3

        if tags is None:
            check_port("Ollama", DEFAULT_OLLAMA_URL)
            ollama_env = os.environ.copy()
            ollama_env["OLLAMA_HOST"] = urlsplit(DEFAULT_OLLAMA_URL).netloc
            ollama_env["OLLAMA_NO_CLOUD"] = "1"
            if ollama == OLLAMA_EXE:
                ollama_env["OLLAMA_MODELS"] = str(OLLAMA_MODELS)
            report("ollama", "starting", "Starting Ollama…")
            services.append(("Ollama", subprocess.Popen(
                [str(ollama), "serve"], env=ollama_env, stdin=subprocess.DEVNULL,
            )))
            tags = wait_for_json(tags_url, services, closing)
        report("ollama", "ready", "Ollama is responding.")
        if not any(model.get("name") == DEFAULT_MODEL for model in tags.get("models", [])):
            report("qwen", "missing", f"{DEFAULT_MODEL} is missing. Run ps/setup.ps1 to install it.")
            return 3
        report("qwen", "ready", f"{DEFAULT_MODEL} is available.")

        health_url = f"{DETECTOR_URL}/health"
        health = running_service(health_url) if gui else None
        if health is None:
            check_port("Detector", DETECTOR_URL)
            report("detector", "starting", "Starting b-tok2…")
            services.append(("Detector", subprocess.Popen(
                [sys.executable, "-u", str(ROOT / "serve.py")], stdin=subprocess.DEVNULL,
            )))
            health = wait_for_json(health_url, services, closing)
        if health.get("mode") != "token":
            raise RuntimeError(f"Expected detector mode 'token', got {health.get('mode')!r}. Check the model and Python dependencies.")

        if gui:
            report("setup", "checking", "Testing the detector and Qwen with synthetic input…")
            smoke_test()
            check_running(services)
        report("detector", "ready", f"Detector ready at {DETECTOR_URL}.")
        report("setup", "ready", "PromptShield is ready." if gui else "Press Ctrl+C to stop both services.")
        while not closing.wait(0.5):
            check_running(services)
        if not shutdown_requested.is_set():
            raise RuntimeError("The GUI control pipe closed unexpectedly.")
        return 0
    except KeyboardInterrupt:
        if gui and not shutdown_requested.is_set():
            message = (
                "The GUI control pipe closed unexpectedly."
                if closing.is_set() else "The launcher received an unexpected interrupt."
            )
            report("setup", "failed", message)
            return 1
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        report("setup", "failed", f"Launch failed: {error}")
        return 1
    finally:
        stop_services(services)


if __name__ == "__main__":
    sys.exit(main())
