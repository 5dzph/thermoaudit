"""Run the packaged examples, then open the local HTML reports."""

import os
from pathlib import Path
import sys
import webbrowser

from thermoaudit.__main__ import main


if __name__ == '__main__':
    root = Path(__file__).resolve().parent
    os.chdir(root)
    codes = [main(['audit', 'examples/balanced_hx.json', '--out', 'reports']),
             main(['pareto', 'examples/candidates.csv', '--out', 'reports'])]
    if any(codes):
        raise SystemExit(max(codes))
    if '--no-open' not in sys.argv:
        for name in ('audit', 'pareto'):
            webbrowser.open((root / 'reports' / f'{name}.html').as_uri())
    print('Done. Open reports/audit.html and reports/pareto.html.')
