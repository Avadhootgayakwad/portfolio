from pathlib import Path
import hashlib
import csv

try:
    from PIL import Image, features
except ImportError:
    raise SystemExit(
        "Pillow is required. Run: python -m pip install Pillow"
    )


# ========================================
# CONFIGURATION
# ========================================

ROOT = Path(__file__).resolve().parent

SOURCE_DIR = ROOT / "Images"

OUTPUT_DIR = ROOT / "optimized_assets"

REPORT_DIR = OUTPUT_DIR / "reports"

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
}

MINIMUM_SAVINGS = 5.0


# ========================================
# VALIDATION
# ========================================

if not SOURCE_DIR.is_dir():
    raise SystemExit("Images directory not found.")

if not features.check("webp"):
    raise SystemExit("WebP support is unavailable.")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ========================================
# UTILITY FUNCTIONS
# ========================================

def calculate_hash(file_path):

    sha256 = hashlib.sha256()

    with file_path.open("rb") as file:

        for chunk in iter(
            lambda: file.read(65536), b""
        ):
            sha256.update(chunk)

    return sha256.hexdigest()


def to_kb(size):

    return round(size / 1024, 2)


# ========================================
# IMAGE OPTIMIZATION
# ========================================

def optimize_image(source):

    relative_path = source.relative_to(SOURCE_DIR)

    destination = (
        OUTPUT_DIR
        / "Images"
        / relative_path.parent
        / f"{source.name}.webp"
    )

    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    original_size = source.stat().st_size

    with Image.open(source) as image:

        width, height = image.size

        if getattr(image, "is_animated", False):
            raise ValueError("Animated image skipped.")

        has_transparency = (
            "A" in image.getbands()
            or "transparency" in image.info
        )

        image = image.convert(
            "RGBA" if has_transparency else "RGB"
        )

        # Lossless compression preserves dashboard text.

        image.save(
            destination,
            format="WEBP",
            lossless=True,
            quality=100,
            method=6
        )

    optimized_size = destination.stat().st_size

    savings = (
        (original_size - optimized_size)
        / original_size
    ) * 100

    if savings < MINIMUM_SAVINGS:

        destination.unlink()

        optimized_size = original_size
        savings = 0
        status = "ORIGINAL RETAINED"
        output_path = ""

    else:

        status = "OPTIMIZED"

        output_path = destination.relative_to(
            ROOT
        ).as_posix()

    return {
        "file": relative_path.as_posix(),
        "width": width,
        "height": height,
        "original_kb": to_kb(original_size),
        "optimized_kb": to_kb(optimized_size),
        "savings_percentage": round(savings, 2),
        "status": status,
        "output_path": output_path,
        "original_bytes": original_size,
        "optimized_bytes": optimized_size,
    }


# ========================================
# MAIN OPTIMIZATION ENGINE
# ========================================

def main():

    print("=" * 65)
    print("PORTFOLIO IMAGE OPTIMIZATION ENGINE")
    print("=" * 65)

    images = sorted(
        path
        for path in SOURCE_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    )

    results = []
    duplicate_results = []
    known_hashes = {}

    total_original = 0
    total_optimized = 0

    optimized_count = 0
    retained_count = 0
    failed_count = 0

    print(f"\nImages discovered: {len(images)}\n")

    for image_path in images:

        try:

            file_hash = calculate_hash(image_path)

            if file_hash in known_hashes:

                duplicate_results.append({
                    "original": known_hashes[file_hash],
                    "duplicate": image_path.relative_to(
                        ROOT
                    ).as_posix()
                })

            else:

                known_hashes[file_hash] = (
                    image_path.relative_to(ROOT).as_posix()
                )

            result = optimize_image(image_path)

            results.append(result)

            total_original += result["original_bytes"]
            total_optimized += result["optimized_bytes"]

            if result["status"] == "OPTIMIZED":

                optimized_count += 1

            else:

                retained_count += 1

            print(
                f'{result["status"]:<20} | '
                f'{result["file"]} | '
                f'{result["original_kb"]} KB -> '
                f'{result["optimized_kb"]} KB | '
                f'{result["savings_percentage"]}%'
            )

        except Exception as error:

            failed_count += 1

            print(
                f"FAILED | {image_path.name} | {error}"
            )


    # ========================================
    # GENERATE REPORTS
    # ========================================

    report_path = (
        REPORT_DIR / "image_optimization_report.csv"
    )

    fieldnames = [
        "file",
        "width",
        "height",
        "original_kb",
        "optimized_kb",
        "savings_percentage",
        "status",
        "output_path",
        "original_bytes",
        "optimized_bytes",
    ]

    with report_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(results)

    duplicate_report = (
        REPORT_DIR / "duplicate_images.csv"
    )

    with duplicate_report.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=["original", "duplicate"]
        )

        writer.writeheader()
        writer.writerows(duplicate_results)


    # ========================================
    # FINAL SUMMARY
    # ========================================

    savings_percentage = (
        (
            (total_original - total_optimized)
            / total_original
        ) * 100
        if total_original
        else 0
    )

    print("\n" + "=" * 65)
    print("OPTIMIZATION SUMMARY")
    print("=" * 65)

    print(f"Total images discovered: {len(images)}")
    print(f"Images optimized: {optimized_count}")
    print(f"Originals retained: {retained_count}")
    print(f"Failed images: {failed_count}")
    print(f"Duplicate images: {len(duplicate_results)}")

    print(
        f"Original size: "
        f"{to_kb(total_original)} KB"
    )

    print(
        f"Potential optimized size: "
        f"{to_kb(total_optimized)} KB"
    )

    print(
        f"Potential storage saved: "
        f"{to_kb(total_original - total_optimized)} KB"
    )

    print(
        f"Potential reduction: "
        f"{savings_percentage:.2f}%"
    )

    print(f"\nReports saved to: {REPORT_DIR}")

    print("\nOriginal images remain unchanged.")

    print("=" * 65)


if __name__ == "__main__":
    main()