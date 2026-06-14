# Copyright (c) 2025 NEXiiO
# SPDX-License-Identifier: MIT
#
# @file    repack.py
# @author  NEXiiO R&D Team
# @date    2026-06-13 19:36:37
# @version 1.0.0
# @brief   Download RISC-V GNU toolchain and repack for PlatformIO

# =============================================================================
# Imports
# =============================================================================
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

# =============================================================================
# Constants
# =============================================================================
RISCV_VERSION = "13.2.0"
PIO_VERSION   = "1.130200.0"
OUTPUT_DIR    = os.path.join(os.path.dirname(__file__), "..", "..", "..", "dist")

# RISC-V GNU Toolchain releases from riscv-collab/riscv-gnu-toolchain
# Prebuilt binaries: https://github.com/riscv-collab/riscv-gnu-toolchain/releases
# These are the elf (bare-metal) variants targeting riscv32
RISCV_BASE = "https://github.com/riscv-collab/riscv-gnu-toolchain/releases/download/2023.10.18"

ASSETS = {
    "windows_x86_64": {
        "url": f"{RISCV_BASE}/riscv32-elf-ubuntu-22.04-gcc-nightly-2023.10.18-nightly.tar.gz",
        "ext": "tar.gz",
        # Note: Windows builds are not always provided officially.
        # Alternative: use xPack RISC-V toolchain for Windows.
        # https://github.com/xpack-dev-tools/riscv-none-elf-gcc-xpack/releases
    },
    "linux_x86_64": {
        "url": f"{RISCV_BASE}/riscv32-elf-ubuntu-22.04-gcc-nightly-2023.10.18-nightly.tar.gz",
        "ext": "tar.gz",
    },
    "linux_aarch64": {
        "url": f"{RISCV_BASE}/riscv32-elf-ubuntu-22.04-gcc-nightly-2023.10.18-nightly.tar.gz",
        "ext": "tar.gz",
    },
    "darwin_x86_64": {
        "url": f"{RISCV_BASE}/riscv32-elf-osx-12.6-gcc-nightly-2023.10.18-nightly.tar.gz",
        "ext": "tar.gz",
    },
    "darwin_arm64": {
        "url": f"{RISCV_BASE}/riscv32-elf-osx-12.6-gcc-nightly-2023.10.18-nightly.tar.gz",
        "ext": "tar.gz",
    },
}

PACKAGE_JSON_TEMPLATE = {
    "name":        "toolchain-riscv32-elf",
    "version":     PIO_VERSION,
    "description": f"RISC-V 32-bit GNU Toolchain {RISCV_VERSION}",
    "keywords":    ["toolchain", "riscv", "gcc"],
    "system":      [],
}

PIO_SYSTEM_TAG = {
    "windows_x86_64": "windows_amd64",
    "linux_x86_64":   "linux_x86_64",
    "linux_aarch64":  "linux_aarch64",
    "darwin_x86_64":  "darwin_x86_64",
    "darwin_arm64":   "darwin_arm64",
}

# =============================================================================
# Functions (identical to arm-none-eabi/scripts/repack.py)
# =============================================================================
def _progress(count, block_size, total_size):
    pct = min(100, int(count * block_size * 100 / total_size))
    sys.stdout.write(f"\r  Downloading... {pct:3d}%")
    sys.stdout.flush()

def _download(url, dest):
    print(f"  URL: {url}")
    urllib.request.urlretrieve(url, dest, reporthook=_progress)
    print()

def _extract(src, ext, dest_dir):
    os.makedirs(dest_dir, exist_ok=True)
    if ext == "zip":
        with zipfile.ZipFile(src) as zf:
            zf.extractall(dest_dir)
    else:
        with tarfile.open(src) as tf:
            tf.extractall(dest_dir)

def _find_inner(extract_dir):
    entries = [e for e in os.listdir(extract_dir)
               if os.path.isdir(os.path.join(extract_dir, e))]
    if len(entries) != 1:
        raise RuntimeError(f"Expected 1 directory, got: {entries}")
    return os.path.join(extract_dir, entries[0])

def _write_package_json(inner_dir, os_tag):
    pkg = dict(PACKAGE_JSON_TEMPLATE)
    pkg["system"] = [PIO_SYSTEM_TAG.get(os_tag, os_tag)]
    with open(os.path.join(inner_dir, "package.json"), "w") as f:
        json.dump(pkg, f, indent=2)
        f.write("\n")

def _repack(inner_dir, os_tag):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR,
          f"toolchain-riscv32-elf-{RISCV_VERSION}-{os_tag}.tar.gz")
    with tarfile.open(out, "w:gz") as tar:
        tar.add(inner_dir, arcname=".")
    print(f"  Done → {out} ({os.path.getsize(out) // (1024*1024)} MB)")
    return out

# =============================================================================
# Entry Point
# =============================================================================
if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(ASSETS.keys())
    for os_tag in targets:
        info = ASSETS[os_tag]
        with tempfile.TemporaryDirectory() as tmpdir:
            src = os.path.join(tmpdir, f"riscv.{info['ext']}")
            _download(info["url"], src)
            ex = os.path.join(tmpdir, "extracted")
            _extract(src, info["ext"], ex)
            inner = _find_inner(ex)
            _write_package_json(inner, os_tag)
            _repack(inner, os_tag)
