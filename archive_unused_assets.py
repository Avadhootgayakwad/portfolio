from pathlib import Path
from datetime import datetime
from urllib.parse import unquote
import argparse
import contextlib
import hashlib
import io
import json
import shutil

import validate_assets as validator


# ========================================
# CONFIGURATION
# ========================================

ROOT = Path(__file__).resolve().parent

SOURCE_EXTENSIONS = {
    ".html",
    ".css",
    ".js",
    ".json",
    ".md",
    ".txt",
    ".xml",
    ".svg",
    ".webmanifest",
    ".yaml",
    ".yml"
}

EXCLUDED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "optimized_assets",
    "__pycache__"
}


# ========================================
# FILE INTEGRITY
# ========================================

def file_hash(path):

    digest = hashlib.sha256()

    with path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):

            digest.update(chunk)

    return digest.hexdigest()


# ========================================
# SOURCE REFERENCE AUDIT
# ========================================

def collect_sources():

    sources = {}

    for path in ROOT.rglob("*"):

        if not path.is_file():
            continue

        relative = path.relative_to(ROOT)

        if any(
            part in EXCLUDED_DIRECTORIES
            for part in relative.parts
        ):
            continue

        if path.suffix.lower() not in SOURCE_EXTENSIONS:
            continue

        try:

            content = path.read_text(
                encoding="utf-8-sig"
            )

            sources[path] = unquote(
                content
            ).replace("\\", "/").lower()

        except (UnicodeError, OSError) as error:

            raise RuntimeError(
                f"Unable to audit {relative}: {error}"
            ) from error

    return sources


def find_references(asset, sources):

    filename = asset.name.lower()

    relative_path = (
        asset.relative_to(ROOT)
        .as_posix()
        .lower()
    )

    references = []

    for source, content in sources.items():

        if source == asset:
            continue

        if (
            relative_path in content
            or filename in content
        ):

            references.append(
                source.relative_to(ROOT).as_posix()
            )

    return references


# ========================================
# MAIN ENGINE
# ========================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Archive verified unused assets"
    )

    args = parser.parse_args()

    print("=" * 65)
    print("PORTFOLIO SAFE ASSET ARCHIVER")
    print("=" * 65)

    print(
        "Mode:",
        "APPLY" if args.apply else "DRY RUN"
    )

    # Execute existing asset validation.

    with contextlib.redirect_stdout(io.StringIO()):

        validator.main()

    if validator.ISSUES:

        raise SystemExit(
            "STOP: Broken references detected."
        )

    if validator.PLACEHOLDERS:

        raise SystemExit(
            "STOP: Resolve placeholder links first."
        )

    candidates = validator.find_unused_assets()

    sources = collect_sources()

    approved = []

    retained = []

    for asset in candidates:

        relative = asset.relative_to(ROOT)

        # Never archive optimized WebP files.

        if asset.suffix.lower() == ".webp":

            retained.append(asset)

            print(f"RETAIN WEBP | {relative}")

            continue

        references = find_references(
            asset,
            sources
        )

        if references:

            retained.append(asset)

            print(f"RETAIN REFERENCED | {relative}")

            for reference in references:

                print(f"  Found in: {reference}")

            continue

        approved.append(asset)

        print(f"ARCHIVE CANDIDATE | {relative}")

    total_bytes = sum(
        asset.stat().st_size
        for asset in approved
    )

    print("\n" + "=" * 65)
    print("ARCHIVE PLAN")
    print("=" * 65)

    print(f"Candidates: {len(candidates)}")
    print(f"Approved for archive: {len(approved)}")
    print(f"Retained: {len(retained)}")

    print(
        f"Recoverable storage: "
        f"{total_bytes / 1024 / 1024:.2f} MB"
    )

    if not args.apply:

        print("\nDRY RUN COMPLETE.")
        print("No files were moved or deleted.")

        return

    if not approved:

        print("No assets require archiving.")

        return

    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S"
    )

    archive = (
        ROOT.parent
        / f"portfolio-asset-archive-{timestamp}"
    )

    archive.mkdir(
        parents=True,
        exist_ok=False
    )

    manifest = []

    # Copy and verify all assets before removing any.

    for asset in approved:

        relative = asset.relative_to(ROOT)

        destination = archive / relative

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        original_hash = file_hash(asset)

        shutil.copy2(asset, destination)

        if file_hash(destination) != original_hash:

            raise RuntimeError(
                f"Backup verification failed: {relative}"
            )

        manifest.append({
            "original_path": relative.as_posix(),
            "archive_path": relative.as_posix(),
            "size_bytes": asset.stat().st_size,
            "sha256": original_hash
        })

    manifest_path = archive / "restore_manifest.json"

    manifest_path.write_text(
        json.dumps(manifest, indent=4),
        encoding="utf-8"
    )

    # Recheck originals before removing them.

    for asset, record in zip(approved, manifest):

        if file_hash(asset) != record["sha256"]:

            raise RuntimeError(
                f"Original changed during archive: {asset}"
            )

    for asset in approved:

        relative = asset.relative_to(ROOT)

        asset.unlink()

        print(f"ARCHIVED | {relative}")

    print("\n" + "=" * 65)
    print("ARCHIVE SUMMARY")
    print("=" * 65)

    print(f"Files archived: {len(approved)}")

    print(
        f"Storage removed from working tree: "
        f"{total_bytes / 1024 / 1024:.2f} MB"
    )

    print(f"Archive location: {archive}")

    print(f"Restoration manifest: {manifest_path}")

    print("All archived copies verified using SHA256.")


if __name__ == "__main__":
    main()