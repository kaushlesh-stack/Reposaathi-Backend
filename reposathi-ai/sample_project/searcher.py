
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MAX_FILE_SIZE = 50_000
MAX_RESULTS = 50


def search_code(keyword: str) -> list[dict]:
    """Search for a keyword in Python files inside sample_project."""

    keyword = keyword.strip()

    if not keyword:
        return []

    results = []

    for file_path in ROOT.rglob("*.py"):

        # Skip test files
        if file_path.name.startswith("test_"):
            continue

        # Skip hidden folders and Python cache folders
        if any(
            part.startswith(".") or part == "__pycache__"
            for part in file_path.relative_to(ROOT).parts
        ):
            continue

        try:
            # Skip files that are too large
            if file_path.stat().st_size > MAX_FILE_SIZE:
                continue

            lines = file_path.read_text(
                encoding="utf-8"
            ).splitlines()

            for line_number, line in enumerate(lines, start=1):
                if keyword.casefold() in line.casefold():
                    results.append({
                        "file": file_path.name,
                        "line": line_number,
                        "code": line.strip(),
                    })

                    if len(results) >= MAX_RESULTS:
                        return results

        except (OSError, UnicodeError):
            # Skip files that cannot be read
            continue

    return results
