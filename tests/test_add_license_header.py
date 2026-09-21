# WhereIsTheMoney — Copyright (C) 2026 GaashG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version. See <https://www.gnu.org/licenses/>.
#
# Additional terms under Section 7(b): see the NOTICE file.

"""Tests for scripts.add_license_header.

Files are written under tmp_path, and git is replaced by a fake wherever the
script would call it, so the repository is never touched.
"""

import subprocess
import sys
from pathlib import Path

import pytest

from scripts import add_license_header
from scripts.add_license_header import HEADER

BODY = "import os\n\nprint(os.name)\n"


@pytest.fixture
def source(tmp_path):
    """Return a function that writes a .py file with the given bytes."""

    def write(text: str, name: str = "module.py") -> Path:
        path = tmp_path / name
        path.write_bytes(text.encode("utf-8"))
        return path

    return write


def content(path: Path) -> str:
    return path.read_bytes().decode("utf-8")


# --- add_header, positive cases ---------------------------------------------


def test_the_header_goes_first_with_a_blank_line_after_it(source):
    path = source(BODY)

    assert add_license_header.add_header(path) is True
    assert content(path) == HEADER + "\n" + BODY


def test_a_file_with_the_header_is_left_alone(source):
    path = source(HEADER + "\n" + BODY)

    assert add_license_header.add_header(path) is False
    assert content(path) == HEADER + "\n" + BODY


def test_adding_twice_changes_nothing_the_second_time(source):
    path = source(BODY)
    add_license_header.add_header(path)
    once = content(path)

    assert add_license_header.add_header(path) is False
    assert content(path) == once


def test_an_empty_file_gets_the_header_alone(source):
    path = source("")

    add_license_header.add_header(path)

    assert content(path) == HEADER


def test_a_shebang_stays_first(source):
    path = source("#!/usr/bin/env python\n" + BODY)

    add_license_header.add_header(path)

    assert content(path) == "#!/usr/bin/env python\n" + HEADER + "\n" + BODY


def test_an_encoding_declaration_stays_before_the_header(source):
    path = source("# -*- coding: utf-8 -*-\n" + BODY)

    add_license_header.add_header(path)

    assert content(path) == "# -*- coding: utf-8 -*-\n" + HEADER + "\n" + BODY


def test_a_shebang_and_an_encoding_declaration_both_stay_first(source):
    first_lines = "#!/usr/bin/env python\n# coding=utf-8\n"
    path = source(first_lines + BODY)

    add_license_header.add_header(path)

    assert content(path) == first_lines + HEADER + "\n" + BODY


def test_windows_line_endings_are_kept(source):
    path = source(BODY.replace("\n", "\r\n"))

    add_license_header.add_header(path)

    assert content(path) == (HEADER + "\n" + BODY).replace("\n", "\r\n")


def test_a_stale_license_header_is_replaced(source):
    stale = ("# ${PROJECT_NAME} — Copyright (C) ${YEAR} ${USER}\n"
             "# GNU Affero General Public License\n\n")
    path = source(stale + BODY)

    assert add_license_header.add_header(path) is True
    assert content(path) == HEADER + "\n" + BODY


def test_an_ordinary_leading_comment_is_kept(source):
    comment = "# Helpers for reading the bank's files.\n"
    path = source(comment + BODY)

    add_license_header.add_header(path)

    assert content(path) == HEADER + "\n" + comment + BODY


def test_hebrew_in_the_file_survives(source):
    path = source('NAME = "שופרסל"\n')

    add_license_header.add_header(path)

    assert content(path).endswith('NAME = "שופרסל"\n')


# --- helpers ----------------------------------------------------------------


def test_git_output_is_split_on_nul_characters():
    output = "a.py\0dir/b.py\0"

    assert add_license_header._paths_from(output) == [Path("a.py"), Path("dir/b.py")]


def test_no_git_output_gives_no_paths():
    assert add_license_header._paths_from("") == []


# --- main -------------------------------------------------------------------


@pytest.fixture
def git(monkeypatch):
    """Replace _git, record its calls, and return them."""
    calls: list[tuple[str, ...]] = []
    listed: dict[str, str] = {"diff": "", "ls-files": ""}

    def fake_git(*args: str) -> str:
        calls.append(args)
        return listed.get(args[0], "")

    monkeypatch.setattr(add_license_header, "_git", fake_git)
    return calls, listed


def run_main(monkeypatch, *arguments: str) -> int:
    monkeypatch.setattr(sys, "argv", ["add_license_header.py", *arguments])
    return add_license_header.main()


def test_staged_files_get_the_header_and_are_staged_again(git, source, monkeypatch, capsys):
    calls, listed = git
    path = source(BODY)
    listed["diff"] = f"{path}\0"

    assert run_main(monkeypatch) == 0

    assert content(path).startswith(HEADER)
    assert calls[-1] == ("add", "--", str(path))
    assert "added license header" in capsys.readouterr().out


def test_all_mode_does_not_touch_the_index(git, source, monkeypatch):
    calls, listed = git
    path = source(BODY)
    listed["ls-files"] = f"{path}\0"

    run_main(monkeypatch, "--all")

    assert content(path).startswith(HEADER)
    assert [call[0] for call in calls] == ["ls-files"]


def test_nothing_is_staged_when_nothing_changed(git, source, monkeypatch, capsys):
    calls, listed = git
    listed["diff"] = f"{source(HEADER + chr(10) + BODY)}\0"

    run_main(monkeypatch)

    assert [call[0] for call in calls] == ["diff"]
    assert capsys.readouterr().out == ""


def test_a_listed_path_that_is_not_a_file_is_skipped(git, tmp_path, monkeypatch):
    calls, listed = git
    listed["diff"] = f"{tmp_path / 'deleted.py'}\0"

    assert run_main(monkeypatch) == 0
    assert [call[0] for call in calls] == ["diff"]


# --- negative cases ---------------------------------------------------------


def test_a_file_that_is_not_utf8_raises(tmp_path):
    path = tmp_path / "latin1.py"
    path.write_bytes('NAME = "café"\n'.encode("latin-1"))

    with pytest.raises(UnicodeDecodeError):
        add_license_header.add_header(path)


def test_a_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        add_license_header.add_header(tmp_path / "absent.py")


def test_a_failing_git_command_raises(tmp_path, monkeypatch):
    """Outside a repository git exits with an error, which is not hidden."""
    monkeypatch.chdir(tmp_path)

    with pytest.raises(subprocess.CalledProcessError):
        add_license_header._git("diff", "--cached")
