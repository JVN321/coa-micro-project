#!/usr/bin/env python3
from pathlib import Path
from build_graphs import count_hazards_in_lines

files = [
    Path('test1/test scripts/mixed_stream.s'),
    Path('test1/reordered_tests/mixed_stream_reordered.s')
]

for p in files:
    print(p)
    if not p.exists():
        print('  MISSING')
        continue
    with open(p, encoding='utf-8') as fh:
        print(' ', count_hazards_in_lines(fh.readlines()))
