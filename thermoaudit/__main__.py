"""python -m thermoaudit audit CASE.json --out reports"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from . import __version__, analyze_candidates, audit
from .pareto import read_candidates
from .report import render_html
from .validation import ValidationError


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description="Audit steady-state process data or screen supplied candidates.")
    parser.add_argument('--version', action='version', version=__version__)
    commands = parser.add_subparsers(dest='command', required=True)
    for command in ('audit', 'pareto'):
        sub = commands.add_parser(command)
        sub.add_argument('input', type=Path)
        sub.add_argument('--out', type=Path, default=Path('reports'), help='Output directory; same report names are replaced.')
        if command == 'pareto':
            sub.add_argument('--weights', nargs=3, type=float, default=(1, 1, 1), metavar=('SEC', 'EXERGY', 'CAPEX'))
    args = parser.parse_args(argv)
    try:
        if args.input.stat().st_size > 10 * 1024 * 1024:
            raise ValidationError('input exceeds 10 MiB limit')
        raw = args.input.read_bytes()
        if args.command == 'audit':
            data = audit(json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique_object))
        else:
            data = analyze_candidates(read_candidates(args.input), args.weights)
        data['metadata'] = {'version': __version__, 'input_sha256': hashlib.sha256(raw).hexdigest()}
        json_path, html_path = args.out / f'{args.command}.json', args.out / f'{args.command}.html'
        if args.input.resolve() in (json_path.resolve(), html_path.resolve()):
            raise ValidationError('output would overwrite input; choose another --out directory')
        encoded = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + '\n'
        html = render_html(data, args.command)
        args.out.mkdir(parents=True, exist_ok=True)
        json_path.write_text(encoded, encoding='utf-8')
        html_path.write_text(html, encoding='utf-8')
        print(f"{args.command}: {data.get('status', 'OK')}")
        print(f"JSON: {json_path}\nHTML: {html_path}")
        return 1 if data.get('status') == 'FAIL' else 0
    except (ValidationError, OSError, UnicodeError, ValueError, RecursionError, OverflowError) as exc:
        print(f"thermoaudit: {exc}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
