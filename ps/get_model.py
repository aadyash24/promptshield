#!/usr/bin/env python3
"""Download the final detector (b-tok2) and unpack it into model/b-tok2.

    python get_model.py                       # download from the GitHub Release, check it, unpack it
    python get_model.py --zip ~/Downloads/b-tok2.zip    # use a zip you already have, no download
    python get_model.py --force               # replace a copy that is already there

b-tok2 is one DistilBERT token classifier trained on all 18 categories (medical, financial, personal).
It is too big for a normal git commit, so it lives on the repo's Releases page. After this runs,
`python serve.py` finds it by default.
"""
import argparse
import hashlib
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
MODEL_DIR = HERE / "model"
NAME = "b-tok2"
URL = "https://github.com/aadyash24/promptshield/releases/download/model-b-tok2/b-tok2.zip"
SHA256 = "31385e2a42d590160732a3e4c7ae6cd08056be26a490f66cc73b52053b30b026"
NEEDED = ["model.safetensors", "config.json", "tokenizer.json", "tokenizer_config.json"]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def is_installed(folder):
    folder = Path(folder)
    return all((folder / name).is_file() for name in NEEDED)


def download(url, dest):
    with urllib.request.urlopen(url) as resp, open(dest, "wb") as out:
        total = int(resp.headers.get("Content-Length") or 0)
        done = 0
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            out.write(chunk)
            done += len(chunk)
            if total:
                print(f"\r  downloaded {done / 1e6:.0f} of {total / 1e6:.0f} MB", end="", flush=True)
    print()


def install(zip_path, out_dir=MODEL_DIR, name=NAME):
    """Unpack the zip into out_dir/name. Refuses paths that would land outside out_dir."""
    out_dir = Path(out_dir).resolve()
    with zipfile.ZipFile(zip_path) as z:
        for member in z.namelist():
            target = (out_dir / member).resolve()
            if out_dir != target and out_dir not in target.parents:
                raise SystemExit(f"Unsafe path in the zip: {member}")
        z.extractall(out_dir)
    folder = out_dir / name
    if not is_installed(folder):
        raise SystemExit(f"The zip did not contain a complete model folder at {folder}. Needed: {', '.join(NEEDED)}")
    return folder


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", help="use this local b-tok2.zip instead of downloading")
    ap.add_argument("--force", action="store_true", help="replace the copy in model/ if there is one")
    args = ap.parse_args()

    target = MODEL_DIR / NAME
    if is_installed(target) and not args.force:
        print(f"{target} is already there. Use --force to replace it.")
        return 0
    if args.force and target.exists():
        shutil.rmtree(target)

    if args.zip:
        zip_path = Path(args.zip).expanduser()
        if not zip_path.is_file():
            raise SystemExit(f"No file at {zip_path}")
    else:
        tmp = tempfile.mkdtemp()
        zip_path = Path(tmp) / "b-tok2.zip"
        print(f"downloading {URL}")
        download(URL, zip_path)

    got = sha256_of(zip_path)
    if got != SHA256:
        raise SystemExit(f"Checksum does not match (got {got[:12]}..., expected {SHA256[:12]}...). "
                         "The file is damaged or is a different model. Not installing it.")
    folder = install(zip_path)
    print(f"installed the final detector at {folder}")
    print("start it with: python serve.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
