import csv
import json
from pathlib import Path
from scripts.validate_benchmark import inspect
from verdure.validate import BLOCKING

ROOT = Path(__file__).resolve().parents[1]


def test_benchmark_requirements():
    with (ROOT / 'data/verdure-benchmark-2026-11-09_22.csv').open(newline='', encoding='utf-8') as f:
        assert not inspect(list(csv.DictReader(f)))['structural_errors']


def test_organizer_messages_cover_blocking_reasons():
    messages = json.loads((ROOT / 'data/fix_it_messages.json').read_text())
    assert set(messages) - {'_note'} == BLOCKING
    assert all(0 < len(messages[k].split()) < 15 for k in BLOCKING)
