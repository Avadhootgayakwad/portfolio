from pathlib import Path
import subprocess
import json
import os
import shutil
import statistics


# ========================================
# CONFIGURATION
# ========================================

ROOT = Path(__file__).resolve().parent

BASE_URL = "http://127.0.0.1:5500"

REPORT_DIR = ROOT / "performance_audit"

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

LIGHTHOUSE = (
    ROOT
    / "node_modules"
    / "lighthouse"
    / "cli"
    / "index.js"
)

PAGES = {
    "homepage": "/index.html",

    "insightpilot-ai":
        "/projects/insightpilot-ai.html",

    "global-superstore":
        "/projects/global-superstore.html",

    "ai-document-analyzer":
        "/projects/ai-document-analyzer.html",

    "sustainex":
        "/projects/sustainex-ecom.html"
}

DEVICES = [
    "desktop",
    "mobile"
]


# ========================================
# CHROME DETECTION
# ========================================

def find_chrome():

    candidates = [
        os.environ.get("CHROME_PATH"),

        shutil.which("chrome"),

        shutil.which("chromium"),

        str(
            Path(
                os.environ.get(
                    "PROGRAMFILES",
                    "C:/Program Files"
                )
            )
            / "Google/Chrome/Application/chrome.exe"
        ),

        str(
            Path(
                os.environ.get(
                    "PROGRAMFILES(X86)",
                    "C:/Program Files (x86)"
                )
            )
            / "Google/Chrome/Application/chrome.exe"
        ),

        str(
            Path(
                os.environ.get(
                    "LOCALAPPDATA",
                    ""
                )
            )
            / "Google/Chrome/Application/chrome.exe"
        )
    ]

    for candidate in candidates:

        if candidate and Path(candidate).is_file():

            return candidate

    return None


# ========================================
# REPORT EXTRACTION
# ========================================

def extract_score(report, category):

    score = (
        report
        .get("categories", {})
        .get(category, {})
        .get("score")
    )

    if score is None:

        return None

    return round(score * 100)


def extract_metric(report, audit_id):

    audit = (
        report
        .get("audits", {})
        .get(audit_id, {})
    )

    value = audit.get("numericValue")

    return (
        round(value, 3)
        if isinstance(value, (int, float))
        else None
    )


# ========================================
# LIGHTHOUSE AUDIT
# ========================================

def run_audit(page_name, page_path, device, env):

    report_path = (
        REPORT_DIR
        / f"{page_name}-{device}.json"
    )

    if report_path.exists():

        report_path.unlink()

    command = [
        "node",
        str(LIGHTHOUSE),

        BASE_URL + page_path,

        "--output=json",

        f"--output-path={report_path}",

        "--quiet",

        "--chrome-flags=--headless",

        "--only-categories="
        "performance,accessibility,"
        "best-practices,seo"
    ]

    if device == "desktop":

        command.append(
            "--preset=desktop"
        )

    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        timeout=240
    )

    if process.returncode != 0:

        raise RuntimeError(
            process.stderr
            or process.stdout
            or "Lighthouse execution failed."
        )

    if not report_path.is_file():

        raise RuntimeError(
            "Lighthouse report was not created."
        )

    report = json.loads(
        report_path.read_text(
            encoding="utf-8"
        )
    )

    if report.get("runtimeError"):

        raise RuntimeError(
            str(report["runtimeError"])
        )

    return {
        "page": page_name,

        "device": device,

        "status": "COMPLETED",

        "performance":
            extract_score(
                report,
                "performance"
            ),

        "accessibility":
            extract_score(
                report,
                "accessibility"
            ),

        "best_practices":
            extract_score(
                report,
                "best-practices"
            ),

        "seo":
            extract_score(
                report,
                "seo"
            ),

        "fcp_ms":
            extract_metric(
                report,
                "first-contentful-paint"
            ),

        "lcp_ms":
            extract_metric(
                report,
                "largest-contentful-paint"
            ),

        "tbt_ms":
            extract_metric(
                report,
                "total-blocking-time"
            ),

        "cls":
            extract_metric(
                report,
                "cumulative-layout-shift"
            ),

        "speed_index_ms":
            extract_metric(
                report,
                "speed-index"
            ),

        "report":
            str(report_path.relative_to(ROOT))
    }


# ========================================
# MAIN ENGINE
# ========================================

def main():

    print("=" * 70)
    print("PORTFOLIO PERFORMANCE AUDIT ENGINE")
    print("=" * 70)

    if not LIGHTHOUSE.is_file():

        raise SystemExit(
            "Lighthouse is missing. "
            "Install it using npm."
        )

    chrome = find_chrome()

    if not chrome:

        raise SystemExit(
            "Google Chrome was not detected. "
            "Set CHROME_PATH to your browser executable."
        )

    env = os.environ.copy()

    env["CHROME_PATH"] = chrome

    results = []

    print(f"\nBrowser: {chrome}")

    print("\nStarting Lighthouse audits...\n")

    for page_name, page_path in PAGES.items():

        print("\n" + "-" * 70)

        print(f"PAGE: {page_name}")

        print("-" * 70)

        for device in DEVICES:

            print(
                f"\nRunning {device} audit...",
                flush=True
            )

            try:

                result = run_audit(
                    page_name,
                    page_path,
                    device,
                    env
                )

                results.append(result)

                print(
                    f"Performance   : "
                    f'{result["performance"]}'
                )

                print(
                    f"Accessibility : "
                    f'{result["accessibility"]}'
                )

                print(
                    f"Best Practices: "
                    f'{result["best_practices"]}'
                )

                print(
                    f"SEO           : "
                    f'{result["seo"]}'
                )

                print(
                    f"FCP           : "
                    f'{result["fcp_ms"]} ms'
                )

                print(
                    f"LCP           : "
                    f'{result["lcp_ms"]} ms'
                )

                print(
                    f"TBT           : "
                    f'{result["tbt_ms"]} ms'
                )

                print(
                    f"CLS           : "
                    f'{result["cls"]}'
                )

                print(
                    f"Speed Index   : "
                    f'{result["speed_index_ms"]} ms'
                )

            except Exception as error:

                results.append({
                    "page": page_name,
                    "device": device,
                    "status": "ERROR",
                    "error": str(error)
                })

                print(f"ERROR: {error}")

    summary_path = (
        REPORT_DIR
        / "performance_summary.json"
    )

    summary_path.write_text(
        json.dumps(
            results,
            indent=4
        ),
        encoding="utf-8"
    )

    completed = [
        result
        for result in results
        if result["status"] == "COMPLETED"
    ]

    errors = len(results) - len(completed)

    print("\n" + "=" * 70)
    print("PERFORMANCE AUDIT SUMMARY")
    print("=" * 70)

    print(f"Pages tested: {len(PAGES)}")

    print(f"Total audits: {len(results)}")

    print(f"Completed: {len(completed)}")

    print(f"Execution errors: {errors}")

    for category in [
        "performance",
        "accessibility",
        "best_practices",
        "seo"
    ]:

        scores = [
            result[category]
            for result in completed
            if result[category] is not None
        ]

        if scores:

            average = statistics.mean(scores)

            print(
                f"Average {category}: "
                f"{average:.2f}/100"
            )

    print("\nDEVICE PERFORMANCE")

    for device in DEVICES:

        scores = [
            result["performance"]
            for result in completed
            if result["device"] == device
            and result["performance"] is not None
        ]

        if scores:

            print(
                f"{device.capitalize()}: "
                f"{statistics.mean(scores):.2f}/100"
            )

    print(f"\nSummary: {summary_path}")

    print(
        "\nNo portfolio HTML, CSS or JavaScript "
        "files were modified."
    )

    print("=" * 70)


if __name__ == "__main__":

    main()
