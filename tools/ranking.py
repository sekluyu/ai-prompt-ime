"""Compile semantic tiers into native dictionary weights; no runtime full sort."""
import re

PREFIX = '__prompt__:'


def chinese_group(label):
    return re.sub(r'〔[^〕]*〕', '', label).strip()


def compiled_weights(rows):
    """Primary tier, Chinese group, original heat, then deterministic ties.

    Assign a compact global ordinal rather than a huge arithmetic weight: this
    preserves the hierarchy without losing small differences to native floats.
    Rime itself compares exact matches/remaining code length before this weight.
    """
    scores = {}
    for row in rows:
        group = chinese_group(row['zh'])
        scores[group] = max(scores.get(group, 0), int(row['weight']))
    ordered = sorted(rows, key=lambda row: (
        row['role'] != 'primary',
        -scores[chinese_group(row['zh'])],
        chinese_group(row['zh']),
        -int(row['weight']),
        row['tag'], row['code'],
    ))
    return {(row['tag'], row['code']): len(ordered) - i
            for i, row in enumerate(ordered)}
