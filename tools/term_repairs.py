"""Apply reviewed dictionary corrections without changing upstream snapshots."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = '__prompt__:'


def repair_rows(rows):
    with (ROOT/'data/term_corrections.tsv').open(encoding='utf-8') as stream:
        rules = {(r['english'], r['code'], r['zh']): r
                 for r in csv.DictReader(stream, delimiter='\t')}
    result = []
    for original in rows:
        row = dict(original)
        key = (row['tag'].removeprefix(PREFIX), row['code'], row['zh'].split('〔', 1)[0])
        rule = rules.get(key)
        if rule:
            if rule['action'] == 'remove':
                continue
            row['code'] = rule['new_code'] or row['code']
            if rule['new_zh']:
                marker = row['zh'][len(key[2]):]
                row['zh'] = rule['new_zh'] + marker
        result.append(row)
    return result


def expansion_rows():
    with (ROOT/'data/expanded_prompts.tsv').open(encoding='utf-8') as stream:
        return [dict(tag=PREFIX+r['english'], zh=r['zh']+'〔'+r['category']+'〕',
                     code=r['code'], weight=int(r['weight']), role=r['role'])
                for r in csv.DictReader(stream, delimiter='\t')]


def repair_target_keys():
    with (ROOT/'data/term_corrections.tsv').open(encoding='utf-8') as stream:
        rules = {(r['english'], r['code'], r['zh']): r
                 for r in csv.DictReader(stream, delimiter='\t')}
    return {(r['new_code'] or r['code'], r['english'])
            for r in rules.values() if r['action'] != 'remove'}
