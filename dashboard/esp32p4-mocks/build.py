#!/usr/bin/env python3
"""Assemble the accepted, self-contained replay without external dependencies."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
parts = ['<script>window.REPLAY_DATA=' + (ROOT / 'data.json').read_text() + ';</script>']
for name in ('ui', 'layout', 'street', 'track', 'tuning', 'player'):
    source = (ROOT / f'{name}.js').read_text()
    if name == 'player':
        source = source.replace("let mode='street'", "let mode='track'")
    parts.append('<script>' + source + '</script>')
html = (ROOT / 'shell.html').read_text().replace('<!-- SCRIPTS -->', '\n'.join(parts))
html = html.replace('data-mode="street" aria-pressed="true"', 'data-mode="street" aria-pressed="false"')
html = html.replace('data-mode="track" aria-pressed="false"', 'data-mode="track" aria-pressed="true"')
(ROOT / 'replay.html').write_text(html)
