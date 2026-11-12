"""Project-authored color phrases, separate from upstream Danbooru tag data."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MARKER = '〔通用短语〕'
PREFIX = '__prompt__:'

def color_rows():
    colors = list(csv.DictReader((ROOT/'data/general_colors.tsv').open(encoding='utf-8'), delimiter='\t'))
    primary = {}
    rows = []
    reserved = {code for color in colors for code in [color['code'],color['code']+'se',color['code']+'peise',color['code']+'sepeise']}
    def add(text, zh, code):
        rows.append(dict(tag=PREFIX+text, zh=zh+MARKER, code=code, weight=10000))
    for color in colors:
        primary.setdefault(color['english'], color)
        label = primary[color['english']]['zh']+'色'
        for code in [color['code'], color['code']+'se',color['code']+'peise',color['code']+'sepeise']:
            add(color['english'], label, code)
    for a in colors:
        for b in colors:
            if a['english'] == b['english']:
                continue
            text = a['english']+' and '+b['english']+' color scheme'
            label = primary[a['english']]['zh']+'＋'+primary[b['english']]['zh']+'配色'
            ac, bc = a['code'], b['code']
            for code in [ac+bc+'peise', ac+'se'+bc+'sepeise', ac+'seyu'+bc+'se']:
                if code not in reserved:
                    add(text, label, code)
    return rows

def merge(base_rows):
    # Regeneration replaces only this project's explicitly marked phrase layer.
    original = [r for r in base_rows if not r['zh'].endswith(MARKER)]
    return original+color_rows()
