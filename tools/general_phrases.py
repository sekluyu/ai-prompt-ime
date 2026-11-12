"""Project-authored prompt phrases, separate from upstream Danbooru tag data."""
import csv
import gzip
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

def merge(base_rows, variant='searchable'):
    # Regeneration replaces only this project's explicitly marked phrase layer.
    original = [r for r in base_rows if not r['tag'].startswith(PREFIX)]
    existing={(r['tag'],r['code']) for r in original}
    imported=[r for r in library_rows(variant) if (r['tag'].removeprefix(PREFIX),r['code']) not in existing]
    return original+color_rows()+fur_color_rows()+prompt_rows()+imported

def prompt_rows():
    source=ROOT/'data/general_prompts.tsv'
    rows=[]
    labels={}
    for row in csv.DictReader(source.open(encoding='utf-8'),delimiter='\t'):
        key=PREFIX+row['english']
        labels.setdefault(key,row['zh']+'〔'+row['category']+'〕')
        rows.append(dict(tag=key,zh=labels[key],code=row['code'],weight=10000))
    return rows

def fur_color_rows():
    colors=list(csv.DictReader((ROOT/'data/general_colors.tsv').open(encoding='utf-8'),delimiter='\t'))
    primary={}
    for color in colors:primary.setdefault(color['english'],color)
    result={}
    single_suffixes=['sepimao','pimao','semaopi','maopi','semaofa','maofa']
    reserved={color['code']+suffix for color in colors for suffix in single_suffixes}
    def add(text,zh,code):
        key=(PREFIX+text,code)
        result[key]=dict(tag=key[0],zh=zh+'〔皮毛配色〕',code=code,weight=10000)
    for a in colors:
        label=primary[a['english']]['zh']+'色皮毛'
        for suffix in single_suffixes:
            add(a['english']+' fur',label,a['code']+suffix)
        for b in colors:
            if a['english']==b['english']:continue
            label=primary[a['english']]['zh']+'＋'+primary[b['english']]['zh']+'色皮毛'
            ac,bc=a['code'],b['code']
            for noun in ['pimao','maopi','maofa']:
                for code in [ac+bc+'se'+noun,ac+'yu'+bc+'se'+noun,ac+'seyu'+bc+'se'+noun,ac+'se'+bc+'se'+noun,ac+bc+noun,ac+'he'+bc+'se'+noun,ac+'sehe'+bc+'se'+noun,ac+'seyu'+bc+'sede'+noun]:
                    if code not in reserved:
                        add(a['english']+' and '+b['english']+' fur',label,code)
    return list(result.values())

def library_rows(variant='searchable'):
    path=ROOT/'data/imported_terms.tsv.gz'
    with gzip.open(path,'rt',encoding='utf-8',newline='') as stream:
        rows=[]
        for r in csv.DictReader(stream,delimiter='\t'):
            if variant!='searchable' and r['scope']!='default':continue
            if not r['tag'].startswith(PREFIX):
                r['tag']=PREFIX+r['tag']
                r['zh']+='〔e621〕' if 'e621+mtt' in r['source'] else '〔合并词库〕'
            rows.append(r)
        return rows
