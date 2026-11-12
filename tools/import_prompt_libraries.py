"""Convert fixed n714/Physton/e621/MTT text snapshots; never execute upstream code.

Developer dependencies: pypinyin 0.55.0 and PyYAML 6.0.3. The resulting gzip TSV
is read by the standard-library-only builder; neither dependency is needed by users.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
HAN=re.compile(r'^[\u3400-\u9fff]+$')
FIELDS=['tag','zh','code','weight','scope','source']

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def convert(snapshot, destination=ROOT/'data'):
    import yaml
    from pypinyin import lazy_pinyin, Style, load_phrases_dict
    load_phrases_dict({'毛发':[['mao'],['fa']],'长毛':[['chang'],['mao']],'长发':[['chang'],['fa']], '角色':[['jue'],['se']],'特写':[['te'],['xie']],'脖颈':[['bo'],['jing']]})
    destination.mkdir(parents=True,exist_ok=True)
    meta=json.loads((snapshot/'snapshot.json').read_text(encoding='utf-8'))
    stats=Counter(); skipped=Counter(); rows={}; code_cache={}
    def code(zh):
        if zh not in code_cache:
            value=''.join(lazy_pinyin(zh,style=Style.NORMAL,errors=lambda x:[x])).lower().replace('ü','v')
            code_cache[zh]=value if re.fullmatch('[a-z]+',value) else None
        return code_cache[zh]
    def add(tag,zh,count,source,scope='default',kind=None):
        if not HAN.fullmatch(zh):skipped[source+':non_chinese_alias']+=1;return
        py=code(zh)
        if not py:skipped[source+':unmapped_reading']+=1;return
        if not tag or any(c in tag for c in '\t\r\n\0'):skipped[source+':invalid_output']+=1;return
        key=(tag,py)
        weight=min(9999,1+int(1000*math.log10(1+max(0,count))))
        label=zh if not kind else zh+'〔'+kind+'〕'
        if key in rows:
            old=rows[key]
            old['weight']=max(old['weight'],weight)
            old['source']=';'.join(sorted(set(old['source'].split(';'))|{source}))
            if scope=='default':old['scope']='default'
            stats['duplicate_tag_code']+=1
        else:
            rows[key]=dict(tag=tag,zh=label,code=py,weight=weight,scope=scope,source=source)
        stats[source+':accepted_aliases']+=1
    def atomic(text,source):
        text=' '.join(text.split())
        # A balanced outer wrapper around one term is emphasis, not literal text.
        match=re.fullmatch(r'(\(+)([^():]+)(\)+)',text)
        if match and len(match[1])==len(match[3]):
            text=match[2].strip();stats[source+':unweighted_single_term']+=1
        if len(text)>120 or any(c in text for c in ',，[]{}<>|\\') or re.search(r'\([^)]*:\s*[\d.]',text):
            skipped[source+':template_or_markup']+=1;return None
        if not re.search('[A-Za-z]',text):skipped[source+':no_english']+=1;return None
        return text
    # n714 has Chinese keys, English values, including a few complete templates.
    def walk(node,path):
        if not isinstance(node,yaml.MappingNode):return
        for key,value in node.value:
            if isinstance(value,yaml.MappingNode):walk(value,path)
            elif isinstance(value,yaml.ScalarNode):
                stats['n714:scalar_entries']+=1
                zh=key.value.strip();text=' '.join(value.value.split())
                # Import words/short phrases. Weighted and multi-tag templates are
                # recorded as excluded rather than escaped into misleading words.
                if not HAN.fullmatch(zh):skipped['n714:non_chinese_key']+=1;continue
                text=atomic(text,'n714')
                if text is None:continue
                add('__prompt__:'+text,zh,100000,'n714',kind='负面词' if '负面' in path.name else '提示词库')
    for path in sorted((snapshot/'n714/tags').glob('*.yml')):
        walk(yaml.compose(path.read_text(encoding='utf-8-sig')),path)
    # Compose preserves duplicate YAML keys; only tag mappings are vocabulary.
    def physton(node,context=''):
        if isinstance(node,yaml.SequenceNode):
            for child in node.value:physton(child,context)
        elif isinstance(node,yaml.MappingNode):
            names=[v.value for k,v in node.value if k.value=='name' and isinstance(v,yaml.ScalarNode)]
            context=context+'/'+('/'.join(names))
            for key,value in node.value:
                if key.value=='tags' and isinstance(value,yaml.MappingNode):
                    for en,zh in value.value:
                        stats['physton:source_entries']+=1
                        if not isinstance(en,yaml.ScalarNode) or not isinstance(zh,yaml.ScalarNode):
                            skipped['physton:non_scalar']+=1;continue
                        text=atomic(en.value,'physton')
                        if text is None:continue
                        for alias in re.split(r'[|,，]',zh.value):
                            add('__prompt__:'+text,alias.strip(),100000,'physton',kind='负面词' if '负面' in context or '反向' in context else '提示词库')
                elif key.value=='groups':physton(value,context)
    physton(yaml.compose((snapshot/'physton/group_tags/zh_CN.yaml').read_text(encoding='utf-8-sig')))
    # The e621 file has NO header. Keep its first row (anthro).
    e621_rows=list(csv.reader((snapshot/'e621/tag-lists/e621/e621_2026-10-01_pt20-ia-ed.csv').open(encoding='utf-8-sig',newline='')))
    e621={r[0]:r for r in e621_rows}
    e621_aliases=defaultdict(set)
    for r in e621_rows:
        if len(r)>3:
            for alias in r[3].split(','):
                if alias:e621_aliases[alias].add(r[0])
    stats['e621:source_rows']=len(e621_rows)
    mtt_rows=list(csv.DictReader((snapshot/'mtt/origin_database/tags_enhanced.csv').open(encoding='utf-8-sig',newline='')))
    stats['mtt:source_rows']=len(mtt_rows)
    alias_targets=defaultdict(set)
    for row in mtt_rows:
        for alias in re.split('[,，]',row['cn_name']):
            if HAN.fullmatch(alias.strip()):alias_targets[alias.strip()].add(row['name'])
    # cn_name also contains search-category keywords: e.g. "服装" occurs on
    # over a thousand different tags. These are not useful direct IME aliases.
    broad_aliases={alias for alias,targets in alias_targets.items() if len(targets)>64}
    stats['mtt:broad_alias_names_excluded']=len(broad_aliases)
    translated_e621=set(); untranslated_mtt=0
    for row in mtt_rows:
        tag=row['name'].strip()
        aliases=[]
        for value in re.split('[,，]',row['cn_name']):
            value=value.strip()
            if value in broad_aliases:skipped['mtt:broad_category_keyword']+=1
            elif value:aliases.append(value)
        valid=[v for v in aliases if HAN.fullmatch(v)]
        if not valid:untranslated_mtt+=1
        count=int(row['post_count'] or 0)
        scope='default' if row['category'] in {'0','5'} else 'searchable'
        for zh in aliases:add(tag,zh,count,'mtt',scope)
        # Reuse explicit bilingual aliases, never guess Chinese by deleting the
        # underscores in an English e621 tag. Both exact and declared alias joins
        # are evidenced by the pinned e621 CSV.
        targets=({tag} if tag in e621 else set())|e621_aliases.get(tag,set())
        for canonical in targets:
            e=e621[canonical]
            escope='default' if e[1] in {'0','5'} else 'searchable'
            for zh in valid:add(canonical,zh,int(e[2]),'e621+mtt',escope)
            if valid:translated_e621.add(canonical)
    stats['mtt:rows_without_usable_chinese']=untranslated_mtt
    stats['e621:tags_with_chinese_join']=len(translated_e621)
    stats['e621:tags_without_chinese_join']=len(e621)-len(translated_e621)
    output=sorted(rows.values(),key=lambda x:(x['tag'],x['code']))
    text=io.StringIO(newline='')
    writer=csv.DictWriter(text,fieldnames=FIELDS,delimiter='\t',lineterminator='\n')
    writer.writeheader();writer.writerows(output)
    raw=text.getvalue().encode('utf-8')
    target=destination/'imported_terms.tsv.gz'
    target.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0))
    stats['output:mappings']=len(output)
    stats['output:terms']=len({r['tag'] for r in output})
    stats['output:default_mappings']=sum(r['scope']=='default' for r in output)
    stats['output:searchable_mappings']=len(output)
    stats['output:default_terms']=len({r['tag'] for r in output if r['scope']=='default'})
    report={'sources':[{k:v for k,v in s.items() if k!='paths'} for s in meta['sources']],
            'source_files':meta['files'],'counts':dict(stats),'exclusions':dict(skipped),
            'generated_file':'data/imported_terms.tsv.gz','generated_sha256':sha(target),
            'uncompressed_sha256':hashlib.sha256(raw).hexdigest(),'uncompressed_bytes':len(raw),
            'compressed_bytes':target.stat().st_size,'dependencies':{'pypinyin':'0.55.0','PyYAML':'6.0.3'},
            'reading_status':'automatic pinyin; not individually human reviewed',
            'content_filter':'No adult-content filtering, consistent with existing corpus.',
            'n714_policy':'atomic words/short phrases; balanced single-term emphasis unwrapped; weighted/multi-tag templates excluded',
            'physton_policy':'zh_CN tag mappings only; explicit Chinese aliases split on pipe/comma; machine translations inherited, not human verified; no upstream extension code executed',
            'alias_policy':'MTT Chinese aliases shared by more than 64 distinct English tags are treated as category keywords and excluded; other aliases remain',
            'e621_policy':'exact tag or explicit English alias join to MTT Chinese aliases; unmatched English tags are not claimed as Chinese-input entries'}
    (destination/'library_sources.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'source_files','sources'}},ensure_ascii=False,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--snapshot',type=Path,required=True);p.add_argument('--output-dir',type=Path,default=ROOT/'data')
    a=p.parse_args();convert(a.snapshot,a.output_dir)
