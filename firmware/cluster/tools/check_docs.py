#!/usr/bin/env python3
"""Check local Markdown links in the new firmware documentation."""
from pathlib import Path
import re
from urllib.parse import unquote

root = Path(__file__).resolve().parents[3]
paths = list((root / 'docs/firmware').rglob('*.md'))
paths += list((root / 'firmware/cluster').glob('*.md'))
errors = []
for path in paths:
    for match in re.finditer(r'\[[^\]]*\]\(([^)]+)\)', path.read_text()):
        target = match.group(1).strip('<>').split('#', 1)[0]
        if not target or re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target):
            continue
        if not (path.parent / unquote(target)).exists():
            errors.append(f'{path.relative_to(root)}: missing local target {target}')
if errors:
    raise SystemExit('\n'.join(errors))
print(f'Firmware documentation links checked: {len(paths)} files')
