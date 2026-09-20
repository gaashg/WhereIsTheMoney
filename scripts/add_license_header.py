# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Insert the project's AGPL license header into Python source files.

With no arguments, processes the files staged for commit and re-stages the ones
it changed; this is what the pre-commit hook does. With --all, processes every
tracked .py file instead, without touching the index.
"""

import re
import subprocess
import sys
from pathlib import Path

HEADER = (
    "# WhereIsTheMoney — Copyright (C) 2026 GaashG\n"
    "#\n"
    "# This program is free software: you can redistribute it and/or modify\n"
    "# it under the terms of the GNU Affero General Public License as published\n"
    "# by the Free Software Foundation, either version 3 of the License, or\n"
    "# (at your option) any later version. See <https://www.gnu.org/licenses/>.\n"
    "#\n"
    "# Additional terms under Section 7(b): see the NOTICE file.\n"
)

# Only the exact header counts as present. A stale or templated one (for example
# a PyCharm template still holding its placeholders) is recognised by this phrase
# and replaced, so a wrong name cannot slip through.
LICENSE_PHRASE = "General Public License"

# PEP 263 encoding declaration, allowed only on the first two lines.
ENCODING_DECLARATION = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*[-_.a-zA-Z0-9]+")


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], capture_output=True, text=True, check=True)
    return result.stdout


def _paths_from(output: str) -> list[Path]:
    return [Path(name) for name in output.split("\0") if name]


def staged_python_files() -> list[Path]:
    """Files added, copied or modified in the index."""
    return _paths_from(_git("diff", "--cached", "--name-only", "--diff-filter=ACM", "-z", "--", "*.py"))


def tracked_python_files() -> list[Path]:
    """Tracked files, plus new ones that are not ignored by .gitignore."""
    return _paths_from(
        _git("ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "*.py")
    )


def _drop_stale_header(lines: list[str], start: int) -> list[str]:
    """Remove a leading comment block that is a license header, plus blank lines."""
    end = start
    while end < len(lines) and lines[end].lstrip().startswith("#"):
        end += 1
    if not any(LICENSE_PHRASE in line for line in lines[start:end]):
        return lines

    while end < len(lines) and not lines[end].strip():
        end += 1
    return lines[:start] + lines[end:]


def add_header(path: Path) -> bool:
    """Add the header to path, keeping any shebang first. True if it changed."""
    # newline="" keeps the file's own line endings instead of translating them.
    text = path.read_text(encoding="utf-8", newline="")
    newline = "\r\n" if "\r\n" in text else "\n"
    header = HEADER.replace("\n", newline)
    if header in text:
        return False

    lines = text.splitlines(keepends=True)
    insert_at = 0
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if len(lines) > insert_at and ENCODING_DECLARATION.match(lines[insert_at]):
        insert_at += 1

    lines = _drop_stale_header(lines, insert_at)
    rest = "".join(lines[insert_at:])
    if rest.strip() and not rest.startswith(newline):
        rest = newline + rest

    with path.open("w", encoding="utf-8", newline="") as f:
        f.write("".join(lines[:insert_at]) + header + rest)
    return True


def main() -> int:
    process_all = "--all" in sys.argv[1:]
    files = tracked_python_files() if process_all else staged_python_files()

    changed = [path for path in files if path.is_file() and add_header(path)]
    for path in changed:
        print(f"added license header: {path.as_posix()}")

    if changed and not process_all:
        _git("add", "--", *(str(path) for path in changed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
