"""The opt-in --lines CLI option: one slug per stdin line."""
import importlib
import io
import subprocess
import sys
from unittest.mock import patch
import pytest

cli = importlib.import_module('slugify.__main__')


def run_cli(capsys, stdin, *argv):
    with patch.object(sys, 'stdin', io.StringIO(stdin)):
        cli.main(['slugify', *argv])
    return capsys.readouterr().out


def test_lines_prints_one_slug_per_input_line(capsys):
    out = run_cli(capsys, 'Hello World\nCafe au lait\n', '--stdin', '--lines')
    assert out == 'hello-world\ncafe-au-lait\n'


def test_stdin_without_lines_is_unchanged(capsys):
    out = run_cli(capsys, 'Hello World\nCafe au lait\n', '--stdin')
    assert out == 'hello-world-cafe-au-lait\n'


def test_lines_applies_other_options_to_each_line(capsys):
    out = run_cli(capsys, 'Hello World\nCafe au lait\n', '--stdin', '--lines', '--separator', '_')
    assert out == 'hello_world\ncafe_au_lait\n'
    out = run_cli(capsys, "a&#39;b\nc d\n", '--stdin', '--lines', '--algorithm', 'modern')
    assert out == 'a-b\nc-d\n'


def test_lines_handles_crlf_and_keeps_blank_lines_aligned(capsys):
    out = run_cli(capsys, 'One\r\n\r\nTwo Three\r\n', '--stdin', '--lines')
    assert out == 'one\n\ntwo-three\n'


def test_lines_with_empty_stdin_prints_nothing(capsys):
    assert run_cli(capsys, '', '--stdin', '--lines') == ''


def test_lines_requires_stdin(capsys):
    with pytest.raises(SystemExit) as error:
        cli.parse_args(['slugify', '--lines', 'Hello'])
    assert error.value.code == 2
    assert '--lines requires --stdin' in capsys.readouterr().err


def test_lines_absent_keeps_parsed_arguments_shape():
    with patch.object(sys, 'stdin', io.StringIO('Hello')):
        args = cli.parse_args(['slugify', '--stdin'])
    assert not hasattr(args, 'lines')
    assert not hasattr(cli.parse_args(['slugify', 'Hello']), 'lines')


def test_lines_subprocess():
    result = subprocess.run([sys.executable, '-m', 'slugify', '--stdin', '--lines'],
                            input='Hello World\nCafe au lait\n', capture_output=True, text=True, check=True)
    assert result.stdout.splitlines() == ['hello-world', 'cafe-au-lait']
