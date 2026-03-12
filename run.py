import subprocess
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) >= 2:
        folder = Path(sys.argv[1]).resolve()
        tests_dir     = folder / "test scripts"
        reordered_dir = folder / "reordered_tests"
        results_dir   = folder / "results"

        if not tests_dir.exists():
            print(f"[error] 'test scripts' folder not found inside: {folder}")
            sys.exit(1)

        extra = [
            "--tests-dir",     str(tests_dir),
            "--reordered-dir", str(reordered_dir),
            "--results-dir",   str(results_dir),
        ]
        print(f"Test folder : {folder}")
    else:
        extra = []
        print("Using default project directories.")

    scripts = ["reorder_all.py", "run_benchmarks.py", "analyse_results.py"]
    for script in scripts:
        print(f"\n--- Running {script} ---")
        subprocess.run([sys.executable, script] + extra, check=True)


if __name__ == "__main__":
    main()
