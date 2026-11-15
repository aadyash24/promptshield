"""Install local model assets on Windows and macOS using the active Python."""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from threading import Event
from urllib.request import Request

if __package__:
    from . import get_model, launch
else:
    import get_model
    import launch


def pull_model(report):
    request = Request(
        f"{launch.DEFAULT_OLLAMA_URL}/api/pull",
        data=json.dumps({"model": launch.DEFAULT_MODEL, "stream": True}).encode(),
        headers={"Content-Type": "application/json"},
    )
    last_status = None
    with launch.LOCAL_HTTP.open(request, timeout=600) as response:
        for line in response:
            event = json.loads(line)
            if event.get("error"):
                raise RuntimeError(event["error"])
            status = event.get("status")
            if status and status != last_status:
                report("qwen", "downloading", status)
                last_status = status
    if last_status != "success":
        raise RuntimeError("Ollama model download did not complete. Retry setup.")


def install(report, json_progress=False):
    services = []
    component = "ollama"
    try:
        ollama = launch.find_ollama()
        tags_url = f"{launch.DEFAULT_OLLAMA_URL}/api/tags"
        tags = launch.running_service(tags_url)
        if ollama is None and tags is None:
            if sys.platform == "win32":
                # Preserve the checksum-verified portable Windows installer.
                args = ["powershell.exe", "-NoProfile", "-NonInteractive",
                        "-ExecutionPolicy", "Bypass", "-File",
                        str(launch.ROOT / "setup.ps1")]
                if json_progress:
                    args.append("-JsonProgress")
                return subprocess.call(args)
            raise RuntimeError(
                "Install and open Ollama from https://ollama.com/download, then retry setup. "
                "On macOS, place Ollama.app in Applications."
            )
        report("ollama", "installed", "Ollama available.")

        component = "detector"
        if not get_model.is_installed(get_model.MODEL_DIR / get_model.NAME):
            report(component, "downloading", "Downloading b-tok2...")
            with tempfile.TemporaryDirectory(prefix="promptshield-model-") as stage:
                archive = Path(stage) / "b-tok2.zip"
                get_model.download(get_model.URL, archive)
                report(component, "verifying", "Verifying b-tok2...")
                if get_model.sha256_of(archive) != get_model.SHA256:
                    raise RuntimeError("The detector download checksum does not match. Retry setup.")
                try:
                    get_model.install(archive)
                except SystemExit as error:
                    raise RuntimeError(str(error)) from error
        report(component, "installed", "b-tok2 installed.")

        component = "ollama"
        if tags is None:
            launch.check_port("Ollama", launch.DEFAULT_OLLAMA_URL)
            report(component, "starting", "Starting Ollama...")
            services.append(("Ollama", subprocess.Popen(
                [str(ollama), "serve"], env=launch.ollama_environment(ollama),
                stdin=subprocess.DEVNULL,
            )))
            tags = launch.wait_for_json(tags_url, services, Event())
        report(component, "ready", "Ollama is responding.")

        component = "qwen"
        if not any(model.get("name") == launch.DEFAULT_MODEL for model in tags.get("models", [])):
            report(component, "downloading", f"Downloading {launch.DEFAULT_MODEL}...")
            pull_model(report)
            tags = launch.running_service(tags_url)
            if tags is None or not any(
                model.get("name") == launch.DEFAULT_MODEL for model in tags.get("models", [])
            ):
                raise RuntimeError("Ollama did not list Qwen after the download.")
        report(component, "installed", f"{launch.DEFAULT_MODEL} installed.")
        report("setup", "installed", "PromptShield model setup complete.")
        return 0
    except (OSError, ValueError, RuntimeError) as error:
        report(component, "failed", str(error))
        return 1
    finally:
        # Never terminate an Ollama instance that was already running.
        launch.stop_services(services)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json-progress", action="store_true")
    args = parser.parse_args()

    def report(component, state, message):
        if args.json_progress:
            print(json.dumps(dict(component=component, state=state, message=message)), flush=True)
        else:
            print(message, flush=True)

    return install(report, args.json_progress)


if __name__ == "__main__":
    sys.exit(main())
