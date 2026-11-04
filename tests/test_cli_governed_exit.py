"""Governed result failures produce nonzero CLI exit codes."""

import pytest
import typer

from apache_aiops.cli._common import governed


def test_error_exits_one():
    with pytest.raises(typer.Exit) as exc:
        governed({"error": "permission denied"})
    assert exc.value.exit_code == 1


def test_unknown_outcome_exits_two_even_with_error():
    with pytest.raises(typer.Exit) as exc:
        governed({"outcomeUnknown": True, "error": "lost response"})
    assert exc.value.exit_code == 2
