from __future__ import annotations

import argparse
import errno
import os
import sys
from typing import Any

from .slugify import slugify, DEFAULT_SEPARATOR


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Slug string")

    input_group = parser.add_argument_group(description="Input")
    input_group.add_argument("input_string", nargs='*',
                             help='Text to slugify')
    input_group.add_argument("--stdin", action='store_true',
                             help="Take the text from STDIN")
    input_group.add_argument("--lines", action='store_true', default=argparse.SUPPRESS,
                             help="With --stdin, slugify each input line separately and print one slug per line")

    parser.add_argument("--no-entities", action='store_false', dest='entities', default=True,
                        help="Do not convert HTML entities to unicode")
    parser.add_argument("--no-decimal", action='store_false', dest='decimal', default=True,
                        help="Do not convert HTML decimal to unicode")
    parser.add_argument("--no-hexadecimal", action='store_false', dest='hexadecimal', default=True,
                        help="Do not convert HTML hexadecimal to unicode")
    parser.add_argument("--max-length", type=int, default=0,
                        help="Output string length, 0 for no limit")
    parser.add_argument("--word-boundary", action='store_true', default=False,
                        help="Truncate to complete word even if length ends up shorter than --max_length")
    parser.add_argument("--save-order", action='store_true', default=False,
                        help="When set and --max_length > 0 return whole words in the initial order")
    parser.add_argument("--separator", type=str, default=DEFAULT_SEPARATOR,
                        help="Separator between words. By default " + DEFAULT_SEPARATOR)
    parser.add_argument("--stopwords", nargs='+',
                        help="Words to discount")
    parser.add_argument("--regex-pattern",
                        help="Python regex pattern for disallowed characters")
    parser.add_argument("--no-lowercase", action='store_false', dest='lowercase', default=True,
                        help="Activate case sensitivity")
    parser.add_argument("--replacements", nargs='+',
                        help="""Additional replacement rules e.g. "|->or", "%%->percent".""")
    parser.add_argument("--allow-unicode", action='store_true', default=False,
                        help="Allow unicode characters")

    parser.add_argument('--algorithm', choices=('legacy', 'modern'), default=argparse.SUPPRESS,
                        help='Slug algorithm (legacy default; modern explicitly opts into changed output)')
    parser.add_argument('--backend', choices=('auto', 'text-unidecode', 'unidecode', 'anyascii'),
                        default=argparse.SUPPRESS, help='Transliteration backend (auto preserves legacy preference)')
    parser.add_argument('--replacement-stage', choices=('both', 'pre', 'post'), default=argparse.SUPPRESS,
                        help='Apply replacement rules before, after, or both sides of cleanup')

    args = parser.parse_args(argv[1:])

    if args.input_string and args.stdin:
        parser.error("Input strings and --stdin cannot work together")

    if getattr(args, 'lines', False) and not args.stdin:
        parser.error("--lines requires --stdin")

    if args.replacements:
        def split_check(repl: str) -> list[str]:
            SEP = '->'
            if SEP not in repl:
                parser.error("Replacements must be of the form: ORIGINAL{SEP}REPLACED".format(SEP=SEP))
            return repl.split(SEP, 1)
        args.replacements = [split_check(repl) for repl in args.replacements]

    if args.input_string:
        args.input_string = " ".join(args.input_string)
    elif args.stdin:
        args.input_string = sys.stdin.read()

    if not args.input_string:
        args.input_string = ''

    return args


def slugify_params(args: argparse.Namespace) -> dict[str, Any]:
    params = dict(
        text=args.input_string,
        entities=args.entities,
        decimal=args.decimal,
        hexadecimal=args.hexadecimal,
        max_length=args.max_length,
        word_boundary=args.word_boundary,
        save_order=args.save_order,
        separator=args.separator,
        stopwords=args.stopwords,
        lowercase=args.lowercase,
        replacements=args.replacements,
        allow_unicode=args.allow_unicode
    )
    # Preserve historical parameter shape; omitted options use the API defaults.
    for option in ('algorithm', 'backend', 'replacement_stage'):
        if hasattr(args, option):
            params[option] = getattr(args, option)
    if args.regex_pattern is not None:
        params['regex_pattern'] = args.regex_pattern
    return params


def main(argv: list[str] | None = None) -> None:
    """ Run this program """
    if argv is None:
        argv = sys.argv
    args = parse_args(argv)
    params = slugify_params(args)
    try:
        if getattr(args, 'lines', False):
            # Split on '\n' only: str.splitlines() would also break on \f, \v,
            # \x1c-\x1e, \x85,   and   inside a line.
            lines = args.input_string.split('\n')
            if lines[-1] == '':
                lines.pop()
            for line in lines:
                if line.endswith('\r'):
                    line = line[:-1]
                print(slugify(**dict(params, text=line)))
        else:
            print(slugify(**params))
    except KeyboardInterrupt:
        sys.exit(-1)
    except OSError as error:
        # The reader went away (e.g. output piped to `head`). Windows reports a
        # closed pipe as EINVAL rather than BrokenPipeError.
        if not (isinstance(error, BrokenPipeError)
                or (sys.platform == 'win32' and error.errno == errno.EINVAL)):
            raise
        # Point stdout at devnull so the interpreter's final flush cannot raise again.
        try:
            devnull = os.open(os.devnull, os.O_WRONLY)
            os.dup2(devnull, sys.stdout.fileno())
        except (OSError, ValueError):
            pass
        sys.exit(1)


if __name__ == '__main__':
    main()
