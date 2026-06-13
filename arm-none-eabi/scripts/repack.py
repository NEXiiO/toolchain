# Copyright (c) 2025 NEXiiO
# SPDX-License-Identifier: MIT
#
# @file    repack.py
# @author  NEXiiO R&D Team
# @date    2026-06-13 19:36:37
# @version 1.0.1
# @brief   Download xPack ARM GNU toolchain and repack for PlatformIO

# =============================================================================
# Imports
# =============================================================================
import json
import os
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

# =============================================================================
# Constants
# =============================================================================
ARM_VERSION   = "13.2.Rel1"       # output filename version label
XPACK_VERSION = "13.2.1-1.1"      # xPack release tag (same GCC, GitHub-hosted)
PIO_VERSION   = "1.90301.0"       # PlatformIO package version field
OUTPUT_DIR    = os.path.join(os.path.dirname(__file__), "..", "..", "..", "dist")

# xPack arm-none-eabi-gcc — GitHub releases, no SSL issues, stable URLs
# https://github.com/xpack-dev-tools/arm-none-eabi-gcc-xpack/releases
XPACK_BASE = (
    "https://github.com/xpack-dev-tools/arm-none-eabi-gcc-xpack"
    f"/releases/download/v{XPACK_VERSION}"
)

ASSETS = {
    "windows_x86_64": {
        "url": f"{XPACK_BASE}/xpack-arm-none-eabi-gcc-{XPACK_VERSION}-win32-x64.zip",
        "ext": "zip",
    },
    "linux_x86_64": {
        "url": f"{XPACK_BASE}/xpack-arm-none-eabi-gcc-{XPACK_VERSION}-linux-x64.tar.gz",
        "ext": "tar.gz",
    },
    "linux_aarch64": {
        "url": f"{XPACK_BASE}/xpack-arm-none-eabi-gcc-{XPACK_VERSION}-linux-arm64.tar.gz",
        "ext": "tar.gz",
    },
    "darwin_x86_64": {
        "url": f"{XPACK_BASE}/xpack-arm-none-eabi-gcc-{XPACK_VERSION}-darwin-x64.tar.gz",
        "ext": "tar.gz",
    },
    "darwin_arm64": {
        "url": f"{XPACK_BASE}/xpack-arm-none-eabi-gcc-{XPACK_VERSION}-darwin-arm64.tar.gz",
        "ext": "tar.gz",
    },
}

PACKAGE_JSON_TEMPLATE = {
    "name":        "toolchain-arm-none-eabi",
    "version":     PIO_VERSION,
    "description": f"GNU ARM Embedded Toolchain {ARM_VERSION} (xPack distribution)",
    "keywords":    ["toolchain", "arm", "gcc"],
    "system":      [],
}

# =============================================================================
# Functions
# =============================================================================
def _progress(count, block_size, total_size):
    if total_size > 0:
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
        with tarfile.open(src, "r:*") as tf:
            tf.extractall(dest_dir)


def _find_inner(extract_dir):
    entries = [e for e in os.listdir(extract_dir)
               if os.path.isdir(os.path.join(extract_dir, e))]
    if len(entries) != 1:
        raise RuntimeError(f"Expected 1 directory in {extract_dir}, got: {entries}")
    return os.path.join(extract_dir, entries[0])


def _write_package_json(inner_dir, os_tag):
    pkg = dict(PACKAGE_JSON_TEMPLATE)
    pkg["system"] = [os_tag]
    path = os.path.join(inner_dir, "package.json")
    with open(path, "w") as f:
        json.dump(pkg, f, indent=2)
        f.write("\n")
    print(f"  Wrote package.json -> {path}")


def _repack(inner_dir, os_tag):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_name = f"toolchain-arm-none-eabi-{ARM_VERSION}-{os_tag}.tar.gz"
    out_path = os.path.join(OUTPUT_DIR, out_name)
    print(f"  Packing -> {out_path}")
    with tarfile.open(out_path, "w:gz") as tar:
        tar.add(inner_dir, arcname=".")
    print(f"  Done: {os.path.getsize(out_path) // (1024 * 1024)} MB")
    return out_path


def repack_os(os_tag, info):
    print(f"\n{'=' * 60}")
    print(f"Processing: {os_tag}")
    print(f"{'=' * 60}")
    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, f"arm.{info['ext']}")
        _download(info["url"], src)
        extract_dir = os.path.join(tmpdir, "extracted")
        _extract(src, info["ext"], extract_dir)
        inner = _find_inner(extract_dir)
        _write_package_json(inner, os_tag)
        return _repack(inner, os_tag)


# =============================================================================
# Entry Point
# =============================================================================
if __name__ == "__main__":
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(ASSETS.keys())
    results = []
    for os_tag in targets:
        if os_tag not in ASSETS:
            print(f"Unknown OS tag: {os_tag}. Valid: {list(ASSETS.keys())}")
            sys.exit(1)
        path = repack_os(os_tag, ASSETS[os_tag])
        results.append(path)

    print(f"\n{'=' * 60}")
    print("All done. Assets:")
    for r in results:
        print(f"  {r}")
